# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccountPaymentRegisterExt(models.TransientModel):
    _inherit = 'account.payment.register'

    petty_cash_limit = fields.Integer(string="Petty Cash (Available)", compute="_compute_petty_cash_limit")
    is_petty_journal = fields.Boolean(compute="_compute_is_petty_journal")

    @api.depends('journal_id')
    def _compute_is_petty_journal(self):
        for rec in self:
            if rec.journal_id.is_petty_cash:
                rec.is_petty_journal = True

            else:
                rec.is_petty_journal = False

    @api.depends('journal_id')
    def _compute_petty_cash_limit(self):
        for rec in self:
            if rec.journal_id:
                # Using journal's default_account_id (usually how journals are linked to accounts)
                account = rec.journal_id.default_account_id
                if account:
                    move_lines = self.env['account.move.line'].search([
                        ('account_id', '=', account.id)
                    ])
                    total_debit = sum(line.debit for line in move_lines)
                    total_credit = sum(line.credit for line in move_lines)
                    rec.petty_cash_limit = total_debit - total_credit
                else:
                    rec.petty_cash_limit = 0.0
            else:
                rec.petty_cash_limit = 0.0

    def action_create_payments(self):
        for rec in self:
            if rec.journal_id.is_petty_cash:
                if self.env.user.id not in rec.journal_id.petty_cash_user_ids.ids:
                    raise ValidationError(_("You are not the allowed petty cash manager for this transaction!"))

                if rec.amount > rec.petty_cash_limit:
                    raise ValidationError(_("The amount is greater than the available petty cash!"))


        # Calling the original method after all conditional checks
        return super().action_create_payments()

