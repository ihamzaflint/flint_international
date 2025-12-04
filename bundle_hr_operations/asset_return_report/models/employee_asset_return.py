# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class EmployeeAssetReturn(models.Model):
    _name = "employee.asset.return"
    _description = "Employee Asset Return"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'asset_return_no'
    _rec_names_search = ['asset_return_no', 'employee_id']
    _order = 'id desc'

    handover_id = fields.Many2one('employee.asset.handover', string="Handover ID", domain=[('state', '=', 'active')],
                                  required=True, tracking=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", related='handover_id.employee_id',
                                  relation='ear_employee_id_rel', required=True, tracking=True)
    job_id = fields.Many2one('hr.job', string="Job Title", related='employee_id.job_id', tracking=True)
    department_id = fields.Many2one('hr.department', string="Department", related='employee_id.department_id',
                                    tracking=True)
    identification_no = fields.Char(string="ID No.", related='employee_id.identification_id', tracking=True)
    form_no = fields.Char(string="Form No", required=True, default='ISMS-AHF-01', tracking=True)
    note = fields.Text(string="Note", required=True, tracking=True)
    return_date = fields.Date(string="Return Date", required=True, tracking=True)
    asset_return_no = fields.Char(string='Asset Return No.', copy=False, readonly=True, default='New')

    device_line_ids = fields.One2many("employee.asset.return.line", "handover_id", string="Devices", tracking=True)
    return_employee_id = fields.Many2one('hr.employee', string="Return To",
                                         relation='ear_return_employee_id_rel', required=True, tracking=True)
    return_by_employee_id = fields.Many2one('hr.employee', string="Return By",
                                            relation='ear_return_by_employee_id_rel', required=True, tracking=True)

    state = fields.Selection([('draft', 'Draft'),
                              ('active', 'Active')], string='State', default='draft', tracking=True)

    def create(self, vals):
        if vals.get('asset_return_no', _('New')) == _('New'):
            vals['asset_return_no'] = self.env['ir.sequence'].next_by_code('employee.asset.return') or _('New')
        res = super(EmployeeAssetReturn, self).create(vals)
        return res

    @api.onchange('handover_id')
    def _onchange_handover_id(self):
        for rec in self:
            # Clear existing lines
            rec.device_line_ids = [(5, 0, 0)]

            lines = []
            for l in rec.handover_id.device_line_ids:
                lines.append((0, 0, {
                    'asset': l.asset,
                    'type': l.type,
                    'model': l.model,
                    'serial_number': l.serial_number,
                    'asset_number': l.asset_number,
                }))

            # Assign all lines at once
            rec.device_line_ids = lines

    def button_active(self):
        for rec in self:
            rec.state = 'active'

    def button_draft(self):
        for rec in self:
            rec.state = 'draft'


class EmployeeDeviceInfoLine(models.Model):
    _name = "employee.asset.return.line"
    _description = "Employee Device Information Line"

    handover_id = fields.Many2one("employee.asset.return", string="Handover Form")
    asset = fields.Char(string="Asset", required=True)
    type = fields.Char(string="Type", required=True)
    model = fields.Char(string="Model", required=True)
    serial_number = fields.Char(string="Serial Number (S/N)", required=True)
    asset_number = fields.Char(string="Asset Number", required=True)
