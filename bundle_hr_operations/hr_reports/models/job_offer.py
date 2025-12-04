# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from pkg_resources import require


class JobOffer(models.Model):
    _name = "job.offer"
    _description = "Job Offer"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "name"
    _order = "id desc"

    project_id = fields.Many2one('project.project', string='Project', required=True, store=True )
    name = fields.Char(string='Name', required=True, store=True)
    name_ar = fields.Char(string='اسم', required=True, store=True)
    contract_status = fields.Char(string='Contract Status', required=True, store=True)
    contract_status_ar = fields.Char(string='حالة العقد', required=True, store=True)
    position = fields.Char(string='Position', required=True, store=True)
    position_ar = fields.Char(string='الوظيفة', required=True, store=True)
    employee_type = fields.Selection([
        ('saudi', 'Saudi'),
        ('non_saudi', 'Non-Saudi')
    ], string='Employee Type', required=True, store=True, default='saudi', )
    gosi = fields.Char(string='GOSI', store=True)
    ticket_char = fields.Char(string='Ticket', store=True)
    expected_start_date = fields.Date(string='Expected Start Date', required=True, store=True)
    date_from = fields.Date(string="Start Date", required=True, store=True)
    date_to = fields.Date(string="End Date", required=True, store=True)
    p_f = fields.Char(string='P.F', required=True, store=True)
    p_f_ar = fields.Char(string='صندوق الادخار', required=True, store=True)
    medical_care = fields.Char(string='Medical Care', required=True, store=True)
    medical_care_ar = fields.Char(string='الرعاية الطبية', required=True, store=True)
    vacation = fields.Char(string='Vacation', required=True, store=True)
    vacation_ar = fields.Char(string='الإجازة', required=True, store=True)
    probation_period = fields.Char(string='Probation Period', required=True, store=True)
    probation_period_ar = fields.Char(string='فترة التجربة', required=True, store=True)
    # HTML fields for content
    html_content_en = fields.Html(string='Job Offer (English)', required=True, store=True)
    html_content_ar = fields.Html(string='عرض العمل (عربي)', required=True, store=True)
    job_offer_line_ids = fields.One2many('job.offer.line', 'job_offer_id', string='Job Offer Lines')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm')
    ], default='draft')
    # Conditional logic
    @api.onchange('employee_type')
    def _onchange_employee_type(self):
        if self.employee_type == 'saudi':
            self.ticket_char = False
        elif self.employee_type == 'non_saudi':
            self.gosi = False

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_confirm(self):
        for rec in self:
            rec.state = 'confirm'


class JobOfferLine(models.Model):
    _name = "job.offer.line"
    _description = "Job Offer Letter Line"

    job_offer_id = fields.Many2one('job.offer', string='Job Offer')
    allowance_name_en = fields.Char(string='Allowance Name', required=True, store=True)
    allowance_amount = fields.Float(string='Allowance Amount', required=True, store=True)
    allowance_name_ar = fields.Char(string='إسم البدل', required=True, store=True)
