from odoo import models, fields


class CRMStage(models.Model):
    _inherit = "crm.stage"

    probability_per = fields.Float("Probability %")
