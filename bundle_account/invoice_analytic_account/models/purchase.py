# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _prepare_invoice(self):
        self.ensure_one()
        res = super()._prepare_invoice()
        analytic_accounts = self.env['account.move'].search(
            [('partner_id', '=', self.partner_id.id),
             ('move_type', '=', 'in_invoice')]).mapped('analytic_account_id')
        if analytic_accounts:
            res['analytic_account_id'] = analytic_accounts[0].id
        return res
