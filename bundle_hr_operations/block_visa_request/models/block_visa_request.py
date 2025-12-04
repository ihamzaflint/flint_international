from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

class BlockVisaRequest(models.Model):
    _name = 'block.visa.request'
    _description = 'Block Visa Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Reference', required=True, copy=False, 
                      readonly=True, default=lambda self: _('New'))
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                default=lambda self: self.env.company)
    # Company Information
    cr_number = fields.Char(string='CR Number', required=True, tracking=True)
    cr_expiry_date = fields.Date(string='CR Expiry Date', required=True, tracking=True)
    operating_license = fields.Char(string='Operating License Number', required=True)
    operating_license_expiry = fields.Date(string='Operating License Expiry')
    contact_person = fields.Many2one('res.users', string='Contact Person', required=True)
    contact_number = fields.Char(string='Contact Number')
    
    # Project Information
    project_name = fields.Char(string='Project Name', required=True)
    project_duration = fields.Integer(string='Project Duration (months)', required=True)
    start_date = fields.Date(string='Expected Start Date')
    end_date = fields.Date(string='Expected End Date', compute='_compute_end_date', store=True)
    
    # Employee Requirements
    total_visas_requested = fields.Integer(string='Number of Visas Requested', required=True)
    available_quota = fields.Integer(string='Available Visa Quota', compute='_compute_quota')
    
    # Saudization Details
    total_employees = fields.Integer(string='Total Employees')
    saudi_employees = fields.Integer(string='Saudi Employees')
    saudization_percentage = fields.Float(string='Saudization %', 
                                        compute='_compute_saudization', store=True)
    saudization_plan = fields.Text(string='Saudization Action Plan')
    
    # Status and Workflow
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    # Related Documents
    attachment_ids = fields.Many2many('ir.attachment', string='Documents')
    
    # Job Categories
    job_category_ids = fields.One2many('block.visa.job.category', 'request_id', 
                                      string='Job Categories')

    @api.depends('project_duration', 'start_date')
    def _compute_end_date(self):
        for record in self:
            if record.start_date and record.project_duration:
                record.end_date = record.start_date + timedelta(days=record.project_duration * 30)
            else:
                record.end_date = False

    @api.depends('total_employees', 'saudi_employees')
    def _compute_saudization(self):
        for record in self:
            if record.total_employees:
                record.saudization_percentage = (record.saudi_employees / record.total_employees) * 100
            else:
                record.saudization_percentage = 0.0

    def _compute_quota(self):
        for record in self:
            # This should be integrated with MHRSD API or quota management system
            record.available_quota = 100  # Example value

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('block.visa.request') or _('New')
        return super(BlockVisaRequest, self).create(vals_list)

    def action_submit(self):
        self.ensure_one()
        if not self.job_category_ids:
            raise UserError(_('Please add at least one job category before submitting.'))
        self.state = 'submitted'

    def action_approve(self):
        self.ensure_one()
        self.state = 'approved'

    def action_reject(self):
        self.ensure_one()
        self.state = 'rejected'

    def action_cancel(self):
        self.ensure_one()
        self.state = 'cancelled'
