from odoo import models, fields


class HrJob(models.Model):
    _inherit = 'hr.job'

    work_location_id = fields.Many2one('hr.work.location', "Work Location")
    name_arabic = fields.Char("Name in Arabic")
