from odoo import models,fields


class AccountPaymentRegisterInherit(models.TransientModel):
    _inherit = 'account.payment.register'

    journal_id = fields.Many2one(
        domain="[('company_id', '=', company_id), ('type', 'in', ('bank', 'cash')), ('not_payment_method', '=',False)]")