from odoo import fields, models


class SisterCompany(models.Model):
    _name = 'sister.company'
    _description = 'Sister Company'

    name = fields.Char('Name', required=True)
    sponsorship_number = fields.Char('Sponsorship Number', required=True)
