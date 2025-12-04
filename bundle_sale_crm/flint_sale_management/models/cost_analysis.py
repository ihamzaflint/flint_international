from odoo import _, models, fields, api
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round


class CostAnalysis(models.Model):
    _name = "cost.analysis"
    _description = "Cost Analysis Line"

    name = fields.Char("Candidate Names")




class CostAnalysisLine(models.Model):
    _name = "cost.analysis.line"
    _description = "Cost Analysis Line"