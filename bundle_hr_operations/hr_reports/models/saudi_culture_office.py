# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class SaudiCultureOfficeReport(models.Model):
    _name = "saudi.culture.office"
    _description = "Saudi Culture Office"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "name"
    _order = "id desc"

    employee_id = fields.Many2one('hr.employee', string='Employee Name', required=True, store=True)
    name = fields.Char( string='Name', required=True, store=True)
    name_ar = fields.Char( string='اسم', required=True, store=True)
    id_number = fields.Char( string='ID Number', required=True, store=True)
    passport_number = fields.Char( string='Passport Number', required=True, store=True)
    start_date = fields.Date(string='Start Date', required=True, store=True)
    end_date = fields.Date(string='End Date', required=True, store=True)
    actual_job_role= fields.Many2one('hr.job',string='Actual Job Role', required=True, store=True)
    file_number = fields.Char( string='File Number', required=True, store=True)
    identification_id = fields.Char( string='Identification No', required=True, store=True)
    nationality = fields.Many2one('res.country',string='Nationality', required=True, store=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm')
    ], default='draft')

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        for rec in self:
            rec.write({
                'name': rec.employee_id.name or '',
                'name_ar': rec.employee_id.ar_name or '',
                'id_number': rec.employee_id.client_employee_id or '',
                'passport_number': rec.employee_id.passportNumber or '',
                'start_date': rec.employee_id.contract_id.date_start or '',
                'end_date': rec.employee_id.contract_id.date_end or '',
                'actual_job_role': rec.employee_id.job_id or '',
                'file_number': rec.employee_id.registration_number or '',
                'identification_id': rec.employee_id.identification_id or '',
            })

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_confirm(self):
        for rec in self:
            rec.state = 'confirm'