# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account",
                                          domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                          check_company=True,
                                          help="Analytic account to which this invoice"
                                               " is linked for financial management. "
                                               "Use an analytic account to record cost and revenue on your project.")
