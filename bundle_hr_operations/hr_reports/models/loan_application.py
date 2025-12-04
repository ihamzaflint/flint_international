from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class LoanApplication(models.Model):
    _name = 'loan.application'
    _description = 'Loan Application Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "name"
    _order = "id desc"

    # Application Info
    application_number = fields.Char(string='Application Number', required=True, )
    application_year = fields.Char(string='Year', required=True, default=fields.Date.today().strftime('%Y'))
    file_number = fields.Char(string='File Number', required=True, store=True)
    employee_id = fields.Many2one('hr.employee', string='Employee Name', required=True, store=True)
    name = fields.Char(string='Name', required=True, store=True)
    name_ar = fields.Char(string='اسم', required=True, store=True)
    nationality = fields.Many2one('res.country', string='Nationality', required=True, store=True)
    account_number = fields.Char(string='Account Number', required=True, store=True)
    employee_number = fields.Char(string='Job Number')
    id_number = fields.Char(string='ID Number', required=True, store=True)
    actual_job_role = fields.Many2one('hr.job', string='Actual Job Role', required=True, store=True)
    department_project = fields.Many2one('hr.department', string='Department', required=True, store=True)
    employment_status = fields.Selection([
        ('permanent', 'Permanent'),
        ('probation', 'Probation'),
        ('contract', 'Contract')
    ], string='Employment Status', default='permanent')
    employment_date = fields.Date(tring='Employment Date', required=True, store=True)
    employment_contract = fields.Char(string='Employment Contract')
    salary_transfer_date = fields.Char(string='Salary Payment Date', default='First of Month')
    loan_application_line_ids = fields.One2many('loan.application.line', 'loan_application_id',
                                                string='Job Offer Lines')

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        for rec in self:
            rec.write({
                'file_number': rec.employee_id.registration_number,
                'name': rec.employee_id.name,
                'name_ar': rec.employee_id.ar_name,
                'nationality': rec.employee_id.country_id,
                'account_number': rec.employee_id.bank_account_id.acc_number,
                'id_number': rec.employee_id.client_employee_id,
                'actual_job_role': rec.employee_id.job_id,
                'department_project': rec.employee_id.department_id,
                'employment_date': rec.employee_id.contract_id.date_start,
            })

    @api.model
    def _get_default_number(self):
        return self.env['ir.sequence'].next_by_code('loan.application.sequence')

    # State actions
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm')
    ], default='draft')

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_confirm(self):
        for rec in self:
            rec.state = 'confirm'


class LoanApplicationLine(models.Model):
    _name = 'loan.application.line'
    _description = "Loan Application Line"

    loan_application_id = fields.Many2one('loan.application', string='Loan Application')
    allowance_name_en = fields.Char(string='Allowance Name')
    allowance_amount = fields.Float(string='Allowance Amount')
    allowance_name_ar = fields.Char(string='إسم البدل')
