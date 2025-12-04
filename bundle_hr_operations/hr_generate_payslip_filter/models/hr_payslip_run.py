# -*- coding: utf-8 -*-
from odoo import fields, models, api

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    final_settlement_batch = fields.Boolean('Final Settlement Batch', help='Batch for In-Active employees (Resigned or Terminated).')