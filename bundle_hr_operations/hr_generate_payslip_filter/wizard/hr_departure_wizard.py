# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from odoo import api, fields, models

class HrDepartureWizard(models.TransientModel):
    _inherit = 'hr.departure.wizard'

    def action_register_departure(self):
        super(HrDepartureWizard, self).action_register_departure()
        contracts = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id),
                                                               ('state','=','open')])
        contracts.write({'state':'close'})