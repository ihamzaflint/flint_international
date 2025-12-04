from odoo import api, fields, models
import calendar

class ExportBatchXlsx(models.AbstractModel):
    _name = 'report.account_move_print.acc_debit_credit_report'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Account Debit Credit Report'

    def generate_xlsx_report(self, workbook, data, records):
        sheet = workbook.add_worksheet('Sheet1')

        #Set the column widths
        sheet.set_column(0, 0, 20)
        sheet.set_column(1, 1, 20)
        sheet.set_column(2, 2, 25)
        sheet.set_column(3, 3, 15)
        sheet.set_column(4, 4, 40)
        sheet.set_column(5, 5, 40)
        sheet.set_column(6, 6, 15)
        sheet.set_column(7, 7, 25)
        sheet.set_column(8, 8, 40)
        sheet.set_column(9, 9, 25)
        sheet.set_column(10, 10, 40)

        date_style = workbook.add_format({
                'align': 'center', 'font_name': 'Arial', 'font_size': 13, 'border': 1, 'text_wrap': True, 'valign': 'vcenter', 'num_format': 'dd-mm-yyyy'})
        format_head = workbook.add_format({'bold': False, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'bg_color': '#3497d9', 'border': 1})
        format_center = workbook.add_format({'bold': False, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'bg_color': 'white', 'border': 1})
        format_left = workbook.add_format({'bold': False, 'font_color': 'black', 'align': 'left', 'valign': 'vcenter', 'bg_color': 'white', 'border': 1})
        format_signature = workbook.add_format({'bold': True, 'underline': True, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'bg_color': 'white', 'border': 1, })

        row = 0
        sheet.write(row, 0, 'Posting Date', format_head)
        sheet.write(row, 1, 'Creation Date', format_head)
        sheet.write(row, 2, 'Document No.', format_head)
        sheet.write(row, 3, 'G/L Account No.', format_head)
        sheet.write(row, 4, 'G/L Account Name', format_head)
        sheet.write(row, 5, 'Description', format_head)
        sheet.write(row, 6, 'Currency', format_head)
        sheet.write(row, 7, 'Amount', format_head)
        sheet.write(row, 8, 'Comment', format_head)
        sheet.write(row, 9, 'User ID', format_head)
        sheet.write(row, 10, 'cost center', format_head)
        col = 0
        moves = self.env['account.move'].search([
            ('state', '=', 'posted'),
            ('date', '>=', data.get("start_date")),
            ('date', '<=', data.get("end_date")),
        ])
        for move in moves:
            for line in move.line_ids:
                final_amount = 0
                amount = line.credit or line.debit
                if line.credit:
                    final_amount = amount * -1
                if line.debit:
                    final_amount = amount
                row += 1

                sheet.write(row, col+0, move.date or '', date_style)
                sheet.write(row, col+1, move.create_date or '', date_style)
                sheet.write(row, col+2, move.name or "", format_center)
                sheet.write(row, col+3, line.account_id.code or " ", format_center)
                sheet.write(row, col+4, line.account_id.name or " ", format_center)
                sheet.write(row, col+5, line.name or " ", format_center)
                sheet.write(row, col+6, line.currency_id.name, format_center)
                sheet.write(row, col+7, final_amount, format_center)
                sheet.write(row, col+8, '', format_center)
                sheet.write(row, col+9, move.create_uid.name or '', format_center)
                sheet.write(row, col+10, line.analytic_account_id.name or '', format_center)  

