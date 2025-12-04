from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError


class ExportIqamaXlsx(models.AbstractModel):
    _name = 'report.scs_hr_payroll.export_emp_iqama'
    _description = 'report for iqama export'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, records):
        sheet = workbook.add_worksheet('Expiring in 90 days')

        #Set the column widths
        sheet.set_column(0, 0, 14)
        sheet.set_column(1, 1, 40)
        sheet.set_column(2, 2, 40)
        sheet.set_column(3, 3, 20)

        format_head = workbook.add_format({'bold': False, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'bg_color': '#3497d9', 'border': 1})
        format_center = workbook.add_format({'bold': False, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'bg_color': 'white', 'border': 1})
        format_center_date = workbook.add_format({'bold': False, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'bg_color': 'white', 'border': 1, 'num_format': 'dd/mm/yyyy'})

        row = 0
        col = 0
        sheet.write(row, col, 'Emp ID', format_head)
        sheet.write(row, col + 1, 'Name of the Employee', format_head)
        sheet.write(row, col + 2, 'Project', format_head)
        sheet.write(row, col + 3, 'Iqama Expiry Date', format_head)

        employee_ids = self.env['hr.employee'].search(
            [
                ("visa_expire", ">=", fields.Date.today()),
                ("visa_expire", "<=", fields.Date.today() + relativedelta(months=+3)),
            ],
            order="visa_expire",
        )
        if not employee_ids:
            raise UserError(_("No Employee Found"))
        for emp_id in employee_ids:
            row += 1
            sheet.write(row, col, emp_id.registration_number or '', format_center)
            sheet.write(row, col + 1, emp_id.name or '', format_center)
            sheet.write(row, col + 2, emp_id.contract_id.analytic_account_id.display_name or '', format_center)
            sheet.write(row, col + 3, emp_id.visa_expire or '', format_center_date)

        # Add Sheet for Last 60 Days Expire
        sheet1 = workbook.add_worksheet('Last 60 Days Expire')

        #Set the column widths
        sheet1.set_column(0, 0, 14)
        sheet1.set_column(1, 1, 40)
        sheet1.set_column(2, 2, 40)
        sheet1.set_column(3, 3, 20)


        row = 0
        col = 0
        sheet1.write(row, col, 'Emp ID', format_head)
        sheet1.write(row, col + 1, 'Name of the Employee', format_head)
        sheet1.write(row, col + 2, 'Project', format_head)
        sheet1.write(row, col + 3, 'Iqama Expiry Date', format_head)

        employee_ids = self.env['hr.employee'].search(
            [
                ("visa_expire", ">=", fields.Date.today() + relativedelta(months=-2)),
                ("visa_expire", "<=", fields.Date.today()),
            ],
            order="visa_expire",
        )
        if not employee_ids:
            raise UserError(_("No Employee Found"))
        for emp_id in employee_ids:
            row += 1
            sheet1.write(row, col, emp_id.registration_number or '', format_center)
            sheet1.write(row, col + 1, emp_id.name or '', format_center)
            sheet1.write(row, col + 2, emp_id.contract_id.analytic_account_id.display_name or '', format_center)
            sheet1.write(row, col + 3, emp_id.visa_expire or '', format_center_date)