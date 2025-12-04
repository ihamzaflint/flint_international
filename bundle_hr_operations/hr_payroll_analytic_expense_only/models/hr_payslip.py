# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    
    def _prepare_line_values(self, line, account_id, date, debit, credit):
        res = super(HrPayslip, self)._prepare_line_values(line, account_id, date, debit, credit)
        account = self.env['account.account'].browse(account_id)
        if account.account_type in ('asset_receivable', 'liability_payable'):
            res['analytic_account_id'] = False
        return res

    def _get_existing_lines(self, line_ids, line, account_id, debit, credit):
        account = self.env['account.account'].browse(account_id)
        if account.account_type in ('asset_receivable', 'liability_payable'):
            for line_id in line_ids:
                if (line_id['name'] == line.name
                    and line_id['account_id'] == account_id
                    and ((line_id['debit'] > 0 and credit <= 0) or (line_id['credit'] > 0 and debit <= 0))):
                    return line_id
            return False
        return super(HrPayslip, self)._get_existing_lines(line_ids, line, account_id, debit, credit)