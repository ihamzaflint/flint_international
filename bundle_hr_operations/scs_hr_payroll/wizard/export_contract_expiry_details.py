from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError


class ExportContractExpiryXlsx(models.AbstractModel):
    _name = 'report.scs_hr_payroll.export_emp_contract_expiry'
    _description = 'Export Contract Expiry Details'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, records):
        sheet = workbook.add_worksheet('Expiring in 90 days')

        #Set the column widths
        sheet.set_column(0, 0, 14)
        sheet.set_column(1, 1, 40)
        sheet.set_column(2, 2, 40)
        sheet.set_column(3, 3, 20)
        sheet.set_column(4, 4, 20)

        format_head = workbook.add_format({'bold': False, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'bg_color': '#3497d9', 'border': 1})
        format_center = workbook.add_format({'bold': False, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'bg_color': 'white', 'border': 1})
        format_center_date = workbook.add_format({'bold': False, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'bg_color': 'white', 'border': 1, 'num_format': 'dd/mm/yyyy'})

        row = 0
        col = 0
        sheet.write(row, col, 'Emp ID', format_head)
        sheet.write(row, col + 1, 'Name of the Employee', format_head)
        sheet.write(row, col + 2, 'Project', format_head)
        sheet.write(row, col + 3, 'Start Date', format_head)
        sheet.write(row, col + 4, 'End Date', format_head)

        # for contract_id in self.env['hr.contract'].browse(data.get('contract_ids')):
        contract_ids = self.env['hr.contract'].search(
            [
                ("date_end", ">=", fields.Date.today()),
                ("date_end", "<=", fields.Date.today() + relativedelta(months=+3)),
            ],
            order="date_end",
        )
        if not contract_ids:
            raise UserError(_("No Contract Details Found"))
        for contract_id in contract_ids:
            row += 1
            sheet.write(row, col, contract_id.employee_id.registration_number or '', format_center)
            sheet.write(row, col + 1, contract_id.employee_id.name or '', format_center)
            sheet.write(row, col + 2, contract_id.employee_id.contract_id.analytic_account_id.display_name or '', format_center)
            sheet.write(row, col + 3, contract_id.date_start or '', format_center_date)
            sheet.write(row, col + 4, contract_id.date_end or '', format_center_date)

        # Add Sheet for Last 60 Days Expire
        sheet1 = workbook.add_worksheet('Last 60 Days Expire')
        sheet1.set_column(0, 0, 14)
        sheet1.set_column(1, 1, 40)
        sheet1.set_column(2, 2, 40)
        sheet1.set_column(3, 3, 20)
        sheet1.set_column(4, 4, 20)

        row = 0
        col = 0
        sheet1.write(row, col, 'Emp ID', format_head)
        sheet1.write(row, col + 1, 'Name of the Employee', format_head)
        sheet1.write(row, col + 2, 'Project', format_head)
        sheet1.write(row, col + 3, 'Start Date', format_head)
        sheet1.write(row, col + 4, 'End Date', format_head)

        # for contract_id in self.env['hr.contract'].browse(data.get('contract_ids')):
        contract_ids = self.env['hr.contract'].search(
            [
                ("date_end", ">=", fields.Date.today() + relativedelta(months=-2)),
                ("date_end", "<=", fields.Date.today() ),
            ],
            order="date_end",
        )
        if not contract_ids:
            raise UserError(_("No Contract Details Found"))
        for contract_id in contract_ids:
            row += 1
            sheet1.write(row, col, contract_id.employee_id.registration_number or '', format_center)
            sheet1.write(row, col + 1, contract_id.employee_id.name or '', format_center)
            sheet1.write(row, col + 2, contract_id.employee_id.contract_id.analytic_account_id.display_name or '', format_center)
            sheet1.write(row, col + 3, contract_id.date_start or '', format_center_date)
            sheet1.write(row, col + 4, contract_id.date_end or '', format_center_date)

