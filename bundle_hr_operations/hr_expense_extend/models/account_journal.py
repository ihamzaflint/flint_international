# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccountJournalExt(models.Model):
    _inherit = 'account.journal'

    # For visibility purposes
    is_petty_cash = fields.Boolean(default=False, string="Petty Cash")
    petty_cash_limit = fields.Integer(string="Cash Limit")
    petty_cash_user_ids = fields.Many2many('res.users', string="Managers")


    @api.onchange('type')
    def _onchange_type(self):
        for rec in self:
            rec.is_petty_cash = False

    @api.onchange('is_petty_cash')
    def _onchange_is_petty_cash(self):
        for rec in self:
            rec.petty_cash_limit = 0
            rec.petty_cash_user_ids = [(5, 0, 0)]

