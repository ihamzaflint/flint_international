from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    logistic_order_id = fields.Many2one('logistic.order', string='Logistic Order')
    government_payment_id = fields.Many2one('government.payment', string='Government Payment')