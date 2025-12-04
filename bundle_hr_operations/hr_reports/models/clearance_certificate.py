# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class ClearanceCertificate(models.Model):
    _name = "clearance.certificate"
    _description = "Clearance Certificate"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "name"
    _order = "id desc"

    employee_id = fields.Many2one('hr.employee', string='Employee Name', required=True, store=True)
    name = fields.Char(string='Name', required=True, store=True)
    name_ar = fields.Char(string='اسم', required=True, store=True)
    project_id = fields.Many2one('client.project', required=True, store=True)
    company_id = fields.Many2one('sister.company', string='Company Name', required=True, store=True)
    actual_job_role = fields.Many2one('hr.job', string='Actual Job Role', required=True, store=True)
    id_number = fields.Char(string='ID Number', required=True, store=True)
    start_date = fields.Date(string='Start Date', required=True, store=True)
    end_date = fields.Date(string='End Date', required=True, store=True)
    status = fields.Selection([
        ('active', 'Active'),
        ('terminated', 'Terminated'),
        ('resigned', 'Resigned'),
    ], string='Status', default='resigned', required=True, store=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm')
    ], default='draft')

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        for rec in self:
            rec.write({
                'name': rec.employee_id.name,
                'name_ar': rec.employee_id.ar_name,
                'project_id': rec.employee_id.project_id.id,
                'actual_job_role': rec.employee_id.job_id.id,
                'id_number': rec.employee_id.client_employee_id,
                'start_date': rec.employee_id.contract_id.date_start,
                'end_date': rec.employee_id.contract_id.date_end,
            })

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_confirm(self):
        for rec in self:
            rec.state = 'confirm'
