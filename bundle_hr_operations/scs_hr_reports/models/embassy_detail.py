from odoo import models, fields


class EmbassyDetails(models.Model):
    _name = 'embassy.detail'

    name = fields.Char("Embassy Name in English")
    name_arabic = fields.Char("Embassy Name in Arabic")
