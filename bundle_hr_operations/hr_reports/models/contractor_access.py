# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class ContractorAccess(models.Model):
    _name = "contractor.access"
    _description = "Contractor Access"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "name"
    _order = "id desc"

    name = fields.Char(string='Contractor Name', required=True, store=True)
    company_name = fields.Char(string="Company Name", required=True, store=True)
    cr_number = fields.Char(string="Commercial Registration Number", required=True, store=True)
    employee_name = fields.Char(string="Employee Name", required=True, store=True)
    identity_id = fields.Char(string="Identity ID", required=True, store=True)
    job_position = fields.Char(string="Work With Us As", required=True, store=True)
    nationality = fields.Char(string="Nationality", required=True, store=True)
    contract_no = fields.Char(string="Contract No", required=True, store=True)
    contract_validity = fields.Char(string="Contract Validity", required=True, store=True)
    work_description = fields.Text(string="Work Description", required=True, store=True)
    job_title = fields.Char(string="Job Title", required=True, store=True)
    signature = fields.Char(string="Signature", required=True, store=True)
    date = fields.Date(string="Date", required=True, store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm')
    ], default='draft', required=True, store=True)

    # def action_active(self):
    #     for rec in self:
    #         rec.state = 'active'

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_confirm(self):
        for rec in self:
            rec.state = 'confirm'
