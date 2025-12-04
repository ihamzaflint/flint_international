from odoo import models, fields


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    is_mea_payslip = fields.Boolean("Is MEA Payslip?")
