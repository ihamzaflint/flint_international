# -*- coding: utf-8 -*-
from odoo import api, models

class FlightLogisticsReport(models.AbstractModel):
    _name = 'report.scs_operation.report_flight_logistics'
    _description = 'Flight Logistics Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['logistic.order'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'logistic.order',
            'docs': docs,
        }
