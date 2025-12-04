# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.template'

    is_recruitment_service = fields.Boolean(string='Is Recruitment Service')
