# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class NoDesireToRenewContract(models.Model):
    _name = "no.desire.to.renew.contract"
    _description = "No Desire to Renew Contract"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "name"
    _order = "id desc"

    employee_id = fields.Many2one('hr.employee', string='Employee Name', required=True, store=True)
    name = fields.Char(string='Name', required=True, store=True)
    name_ar = fields.Char(string='اسم', required=True, store=True)
    company_id = fields.Many2one('sister.company', string='Company Name', required=True, store=True)
    start_date = fields.Date(string='Start Date', required=True, store=True)
    end_date = fields.Date(string='End Date', required=True, store=True)
    current_date = fields.Date(string="Current Date", required=True, store=True, default=fields.Date.context_today)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm')
    ], default='draft', required=True, store=True, )

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        for rec in self:
            rec.write({
                'name': rec.employee_id.name or '',
                'name_ar': rec.employee_id.ar_name or '',
                'start_date': rec.employee_id.contract_id.date_start or '',
                'end_date': rec.employee_id.contract_id.date_end or '',
            })

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_confirm(self):
        for rec in self:
            rec.state = 'confirm'
