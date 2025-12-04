# -*- coding: utf-8 -*-
from odoo import models, fields, _, api
from odoo.exceptions import UserError, ValidationError


class ResPartnerExt(models.Model):
    _inherit = "res.partner"

    cr_number = fields.Char(string='CR Number')
