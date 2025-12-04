from odoo import models, fields


class SaibPayrollWizard(models.TransientModel):
    _name = 'saib.payroll.wizard'
    _description = 'Generate Payroll Wizard'

    payroll_date = fields.Date('Payroll Date', required=True)
    department_id = fields.Many2one('hr.department', 'Department')
    include_all_employees = fields.Boolean('Include All Employees')
    employee_ids = fields.Many2many('hr.employee', string='Employees')
    payment_method = fields.Selection([
        ('wps', 'WPS System'),
        ('direct', 'Direct Transfer')
    ], string='Payment Method', required=True)
    bank_account_id = fields.Many2one('res.partner.bank', string='Bank Account')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    def action_generate_payroll(self):
        # Implementation for generating payroll
        pass