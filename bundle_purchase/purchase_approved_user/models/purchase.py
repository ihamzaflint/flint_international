# -*- coding: utf-8 -*-
from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    created_user_id = fields.Many2one('res.users', string='Created By', index=True, default=lambda self: self.env.user, check_company=True, readonly=True)
    approved_user_id = fields.Many2one('res.users', string='Approved By', index=True, check_company=True, readonly=True)

    def button_confirm(self):
        # adding approved_user_id
        for order in self:
            order.approved_user_id = self.env.uid
        return super().button_confirm()