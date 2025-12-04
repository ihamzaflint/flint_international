# -*- coding: utf-8 -*-
import io
import json
from odoo import http, _
from odoo.http import content_disposition, request
from odoo.tools.misc import xlsxwriter
from datetime import datetime


class PerformanceReportController(http.Controller):

    @http.route('/performance_dynamic_xlsx_reports', type='http', auth='user')
    def generate_xlsx_report(self, **kw):
        report_data = json.loads(kw.get('report_data', '[]'))
        report_date = json.loads(kw.get('options', '[]'))

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Performance Report')

        date_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter'
        })

        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#AAAAAA',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })

        cell_format = workbook.add_format({'border': 1})

        headers = ['Sequence', 'Name', 'Reason']
        col_widths = [len(header) for header in headers]

        date_from_only_date = datetime.strptime(report_date['date_from'], "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
        date_to_only_date = datetime.strptime(report_date['date_to'], "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
        date_range_text = f"Report Date: {date_from_only_date} To {date_to_only_date}"
        worksheet.merge_range(0, 0, 0, len(headers) - 1, date_range_text, date_format)

        for col, header in enumerate(headers):
            worksheet.write(1, col, header, header_format)

        row = 2
        for rec in report_data:
            worksheet.write(row, 0, rec['sequence'], cell_format)
            worksheet.write(row, 1, rec['name'], cell_format)
            worksheet.write(row, 2, rec['rejection_reason'], cell_format)

            col_widths[0] = max(col_widths[0], len(rec['sequence']))
            col_widths[1] = max(col_widths[1], len(rec['name']))
            col_widths[2] = max(col_widths[2], len(rec['rejection_reason']))

            row += 1

        for col, width in enumerate(col_widths):
            worksheet.set_column(col, col, width + 2)

        workbook.close()
        xlsx_data = output.getvalue()
        response = request.make_response(
            xlsx_data,
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', content_disposition('Performance Report.xlsx'))
            ]
        )
        return response
