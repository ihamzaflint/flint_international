from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    employee_id = fields.Many2one('hr.employee', string='Sales Person', tracking=True)
