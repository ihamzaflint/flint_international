# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class SalaryIncrement(models.Model):
    _name = "salary.increment"
    _description = "Salary Increment"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "name"
    _order = "id desc"

    employee_id = fields.Many2one('hr.employee', string='Employee Name', required=True, store=True)
    name = fields.Char(string='Name', required=True, store=True)
    ar_name = fields.Char(string='اسم', required=True, store=True)
    project_id = fields.Many2one('client.project', required=True, store=True)
    company_id = fields.Many2one('sister.company', string='Company Name', required=True, store=True)
    html_points_en = fields.Html(string='English Points', required=True, store=True)
    html_points_ar = fields.Html(string='Arabic Points', required=True, store=True)
    start_date = fields.Date(string="Start Date", required=True, store=True)
    work_effective_date = fields.Date(string="W.E.F Date", required=True, store=True)
    contract_date = fields.Date(string="Contract Date", required=True, store=True)
    salary_increment_line_ids = fields.One2many('salary.increment.line', 'salary_increment_id',
                                                string='Salary Increment Lines')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm')
    ], default='draft')

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        for rec in self:
            rec.write({
                'name': rec.employee_id.name or '',
                'ar_name': rec.employee_id.ar_name or '',
                'project_id': rec.employee_id.project_id.id or '',
            })

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_confirm(self):
        for rec in self:
            rec.state = 'confirm'


class JobOfferLIne(models.Model):
    _name = "salary.increment.line"
    _description = "Job Offer Letter Line"

    salary_increment_id = fields.Many2one('salary.increment', string='Job Offer')
    allowance_name_en = fields.Char(string='Allowance Name', required=True, store=True)
    allowance_amount = fields.Float(string='Allowance Amount', required=True, store=True)
    allowance_name_ar = fields.Char(string='إسم البدل', required=True, store=True)
