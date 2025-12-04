from odoo import models, fields


class ResCountry(models.Model):
    _inherit = 'res.country'

    country_name_arabic = fields.Char("Name in Arabic")
