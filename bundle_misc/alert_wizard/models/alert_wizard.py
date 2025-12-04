# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AlertWizard(models.TransientModel):
    _name = "general.alert.wizard"
    _description = "Alert Wizard"

    message = fields.Text('Message', readonly=True)
