# -*- coding: utf-8 -*-
from odoo import fields, models

class DepartureReason(models.Model):
    _inherit = "hr.departure.reason"

    exclude_from_batch = fields.Boolean('Exclude From Batch', help='Employees Archived with this reason will not be included in any payslip batch.')
