from odoo import models, fields


class AccountJournalInherit(models.Model):
    _inherit = 'account.journal'

    not_payment_method = fields.Boolean(string=" Don't Use as a Payment Method")