from odoo import api, fields, models


class ExperienceLevel(models.Model):
    _name = 'experience.level'
    _description = 'Experience Level'

    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)