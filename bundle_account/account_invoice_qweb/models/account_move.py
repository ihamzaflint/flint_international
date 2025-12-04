# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    x_mea_invoice = fields.Boolean('Is Mea Invoice')

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        res = super(AccountMove, self)._onchange_partner_id()
        if self.partner_id.partner_bank_id:
            self.partner_bank_id = self.partner_id.partner_bank_id.id or self.partner_id.parent_id.partner_bank_id.id
        return res

    @api.depends('line_ids')
    def _get_adjustment_amount(self):
        for move in self:
            amount = 0.0
            for line in move.line_ids:
                if not line.product_id.adjustment_product:
                    continue
                amount += (line.quantity * line.price_unit)
            move.adjustment_amount_calc = amount

    period_of_supply = fields.Char(string='Period of Supply', copy=True)
    internal_ref = fields.Char(string='Internal Reference', copy=False)
    contract_no = fields.Char(string='Contract No', copy=False)
    # adjustment_amount_cal = fields.Float(string='Adjustment Amount', digits='Product Price')
    adjustment_amount_calc = fields.Monetary(string='Adjustment Amount', store=True, readonly=True,
                                             compute='_get_adjustment_amount')

    def get_usd_amount(self, amount):
        us_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
        if us_currency and (self.currency_id.id != us_currency.id):
            if amount and us_currency.rate:
                amount = float(round(amount * us_currency.rate, us_currency.decimal_places))
        return amount

    def get_sar_amount(self, amount):
        sar_currency = self.env['res.currency'].search([('name', '=', 'SAR')], limit=1)
        if sar_currency and (self.currency_id.id != sar_currency.id):
            if amount and sar_currency.rate:
                amount = float(round(amount / self.currency_id.rate, sar_currency.decimal_places))
        amount = '{:,.2f}'.format(amount)
        return str(amount) + ' ' + sar_currency.name

    def get_sequence(self):
        seq = self.internal_ref or ''
        if self.name and seq:
            seq = str(seq)
            # +"/"+ str(self.name.split("/")[2])
        return seq

    def get_untaxed_amount_without_adjustment(self):
        total_untaxed = 0.0
        for line in self.line_ids:
            if not line.product_id.adjustment_product:
                # Untaxed amount.
                total_untaxed += (line.quantity * line.price_unit)
        return total_untaxed

    @api.constrains('internal_ref')
    def _check_internal_ref(self):
        for rec in self.filtered(lambda l: l.internal_ref and l.move_type == 'out_invoice'):
            if self.search([('internal_ref', '=', rec.internal_ref), ('id', '!=', rec.id)]):
                raise UserError(_("Internal Reference already exist"))


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    arabic_label = fields.Char()
    internal_ref = fields.Char('Internal Ref' ,related="move_id.internal_ref", store=True)
