# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountMoveExt(models.Model):
    _inherit = 'account.move'

    # Overridden from source to copy=True
    invoice_user_id = fields.Many2one(
        string='Salesperson',
        comodel_name='res.users',
        copy=True,
        tracking=True,
        compute='_compute_invoice_default_sale_person',
        store=True,
        readonly=False,
    )
    supply_period_id = fields.Many2one('res.supply.period', string='Period of Supply',
                                       domain=[('state', '=', 'active')], copy=True)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        for rec in self:
            if rec.partner_id:
                rec.invoice_user_id = rec.partner_id.user_id.id or False

    @api.onchange('supply_period_id')
    def _onchange_supply_period_id(self):
        for rec in self:
            if rec.supply_period_id:
                rec.period_of_supply = rec.supply_period_id.display_name or False

    @api.constrains('supply_period_id')
    def _check_supply_period_id(self):
        for rec in self:
            if rec.move_type == 'out_invoice' and not rec.supply_period_id:
                raise ValidationError(_("Please select a period of supply."))

    def button_self_period_of_supply_change(self):
        for rec in self:
            rec.period_of_supply = rec.supply_period_id.display_name or None

    def button_all_period_of_supply_change(self):
        for rec in self.env['account.move'].search([('supply_period_id', '!=', False)]):
            for move in rec:
                move.period_of_supply = move.supply_period_id.display_name or None
