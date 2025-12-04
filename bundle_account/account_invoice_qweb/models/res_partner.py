# -*- coding: utf-8 -*-

from odoo import models, fields

class Partner(models.Model):
    _inherit = "res.partner"

    partner_bank_id = fields.Many2one(
        "res.partner.bank",
        string="Recipient Bank",
    )
    def _compute_bank_partner_id(self):
        for rec in self:
            rec.bank_partner_id = (
                rec.company_id.partner_id or self.env.company.partner_id
            )

    bank_partner_id = fields.Many2one(
        "res.partner",
        compute="_compute_bank_partner_id",
    )
    ar_name = fields.Char(string='Arabic Name')


class Company(models.Model):
    _inherit = 'res.company'

    ar_name = fields.Char(string='Arabic Name')