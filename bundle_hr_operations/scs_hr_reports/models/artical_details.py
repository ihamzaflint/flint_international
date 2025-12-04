from odoo import models, fields


class ArticalDetails(models.TransientModel):
    _name = 'artical.detail'

    name = fields.Text("Issue in English")
    name_arabic = fields.Text("Issue in Arabic")
    hr_templ_id = fields.Many2one('hr.template.report.wiz', string="Template")
