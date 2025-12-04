# -*- coding: utf-8 -*-
from odoo import models, fields, _, api
from odoo.exceptions import UserError, ValidationError


class CRMActivityReport(models.Model):
    _inherit = "crm.activity.report"

