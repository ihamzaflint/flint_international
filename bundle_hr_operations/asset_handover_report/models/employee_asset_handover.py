# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class EmployeeAssetHandover(models.Model):
    _name = "employee.asset.handover"
    _description = "Employee Asset Handover"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'asset_handover_no'
    _rec_names_search = ['asset_handover_no', 'employee_id']
    _order = 'id desc'

    asset_handover_no = fields.Char(string='Asset Handover No.', copy=False, readonly=True, default='New')
    employee_id = fields.Many2one('hr.employee', string="Employee", relation='edi_employee_id_rel', required=True,
                                  tracking=True)
    job_id = fields.Many2one('hr.job', string="Job Title", related='employee_id.job_id', tracking=True)
    department_id = fields.Many2one('hr.department', string="Department", related='employee_id.department_id',
                                    tracking=True)
    identification_no = fields.Char(string="ID No.", related='employee_id.identification_id', tracking=True)
    form_no = fields.Char(string="Form No", required=True, default='ISMS-AHF-01', tracking=True)
    handover_date = fields.Date(string="Handover Date", required=True, tracking=True)
    device_line_ids = fields.One2many("employee.asset.handover.line", "handover_id", string="Devices", tracking=True)
    handover_employee_id = fields.Many2one('hr.employee', string="Handover By",
                                           relation='edi_handover_employee_id_rel', required=True, tracking=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('active', 'Active')], string='State', default='draft', tracking=True)

    def create(self, vals):
        if vals.get('asset_handover_no', _('New')) == _('New'):
            vals['asset_handover_no'] = self.env['ir.sequence'].next_by_code('employee.asset.handover') or _('New')
        res = super(EmployeeAssetHandover, self).create(vals)
        return res

    def button_active(self):
        for rec in self:
            rec.state = 'active'

    def button_draft(self):
        for rec in self:
            rec.state = 'draft'


class EmployeeDeviceInfoLine(models.Model):
    _name = "employee.asset.handover.line"
    _description = "Employee Device Information Line"

    handover_id = fields.Many2one("employee.asset.handover", string="Handover Form")
    asset = fields.Char(string="Asset", required=True)
    type = fields.Char(string="Type", required=True)
    model = fields.Char(string="Model", required=True)
    serial_number = fields.Char(string="Serial Number (S/N)", required=True)
    asset_number = fields.Char(string="Asset Number", required=True)
