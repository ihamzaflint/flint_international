# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class ContractExtension(models.Model):
    _name = "contract.extension"
    _description = "Contract Extension"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "name"
    _order = "id desc"

    # name = fields.Char(string='Name', required=True,  store=True)
    employee_id = fields.Many2one('hr.employee', string='Employee Name', required=True, store=True)
    name = fields.Char(string='Name', required=True, store=True)
    name_ar = fields.Char(string='اسم', required=True, store=True)
    file_number = fields.Char(string='File Number', required=True, store=True)
    id_number = fields.Char(string='ID Number', required=True, store=True)
    reference = fields.Char(string="Reference", required=True, store=True)
    current_date = fields.Date(string="Today's Date", default=fields.Date.context_today, required=True, store=True)
    renew_date = fields.Date(string="Renew Date", required=True, store=True)
    end_date = fields.Date(string="End Date", required=True, store=True)
    new_expiry_date = fields.Date(string="New Expiry Date", required=True, store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm')
    ], default='draft', required=True, store=True)

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        for rec in self:
            rec.write({
                'name': rec.employee_id.name or '',
                'name_ar': rec.employee_id.ar_name or '',
                'file_number': rec.employee_id.registration_number or '',
                'id_number': rec.employee_id.iqama_number or '',
            })

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_confirm(self):
        for rec in self:
            rec.state = 'confirm'
