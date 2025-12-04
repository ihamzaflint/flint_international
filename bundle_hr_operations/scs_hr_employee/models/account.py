
from odoo import fields, models

class Account(models.Model):
	_inherit = "account.account"

	is_payroll_adj = fields.Boolean(
	    string='Payroll Adjustments', copy=False
	)

