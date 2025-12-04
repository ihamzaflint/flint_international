# -*- coding: utf-8 -*-
from odoo import models, api
from datetime import datetime


class PurchaseOrderReport(models.AbstractModel):
    _name = 'report.era_recruitment_opportunity.performance_report_pdf'
    _description = 'Purchase Order Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        report_lines = data.get('report_data', []) if data else []
        date_from = datetime.strptime(data.get('context', {}).get('date_from', False), "%Y-%m-%d %H:%M:%S").strftime(
            "%Y-%m-%d")
        date_to = datetime.strptime(data.get('context', {}).get('date_to', False), "%Y-%m-%d %H:%M:%S").strftime(
            "%Y-%m-%d")

        return {
            'docs': report_lines,
            'data': data,
            'date_from': date_from,
            'date_to': date_to,
        }
