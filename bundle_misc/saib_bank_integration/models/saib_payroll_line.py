from odoo import models, fields

class SaibPayrollLine(models.Model):
    _name = 'saib.payroll.line'
    _description = 'SAIB Payroll Line'

    payroll_id = fields.Many2one('saib.payroll', string='Payroll')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    amount = fields.Monetary('Amount', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.company.currency_id)
    bank_account = fields.Char('Bank Account', required=False)
