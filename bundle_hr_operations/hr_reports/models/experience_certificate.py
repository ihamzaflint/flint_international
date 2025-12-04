# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class ExperienceCertificate(models.Model):
    _name = "experience.certificate"
    _description = "Experience Certificate"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "name"
    _order = "id desc"

    employee_id = fields.Many2one('hr.employee', string='Employee Name', required=True, store=True)
    name = fields.Char(string='Name', required=True, store=True)
    name_ar = fields.Char(string='اسم', required=True, store=True)
    file_number = fields.Char(string='File Number', required=True, store=True)
    project_id = fields.Many2one('client.project', required=True, store=True)
    company_id = fields.Many2one('sister.company', string='Company Name', required=True, store=True)
    nationality = fields.Many2one('res.country', string='Nationality', required=True, store=True)
    iqama_profession = fields.Many2one('employee.profession', string='Profession In Iqama', required=True, store=True)
    actual_job_role = fields.Many2one('hr.job', string='Actual Job Role', required=True, store=True)
    id_number = fields.Char(string='ID Number', required=True, store=True)
    joining_date = fields.Date(string='Joining Date', required=True, store=True)
    last_date = fields.Date(string='Last Date', required=True, store=True)
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
                'file_number': rec.employee_id.registration_number or '',
                'project_id': rec.employee_id.project_id.id or '',
                'nationality': rec.employee_id.country_id.id or '',
                'iqama_profession': rec.employee_id.profession_id.id or '',
                'actual_job_role': rec.employee_id.job_id.id or '',
                'id_number': rec.employee_id.client_employee_id or '',
                'joining_date': rec.employee_id.contract_id.date_start or '',
                'last_date': rec.employee_id.contract_id.date_end or '',
            })

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_confirm(self):
        for rec in self:
            rec.state = 'confirm'
