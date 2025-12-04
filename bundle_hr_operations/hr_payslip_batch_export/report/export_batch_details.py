from odoo import api, fields, models
import calendar

class ExportBatchXlsx(models.AbstractModel):
    _name = 'report.hr_payslip_batch_export.export_payslip_batch'
    _inherit = 'report.report_xlsx.abstract'
    _description = "Export Batch Xlsx"

    def generate_xlsx_report(self, workbook, data, records):
        sheet = workbook.add_worksheet('Sheet1')



        #Set the column widths
        sheet.set_column(0, 0, 14)
        sheet.set_column(1, 1, 40)
        sheet.set_column(2, 2, 40)
        sheet.set_column(3, 3, 40)
        sheet.set_column(4, 4, 18)
        sheet.set_column(5, 5, 18)
        sheet.set_column(6, 6, 40)
        sheet.set_column(7, 7, 40)
        sheet.set_column(8, 8, 18)
        sheet.set_column(9, 9, 18)
        sheet.set_column(10, 10, 14)
        sheet.set_column(11, 11, 14)
        sheet.set_column(12, 12, 16)

        format_head = workbook.add_format({'bold': False, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'bg_color': '#3497d9', 'border': 1})
        format_center = workbook.add_format({'bold': False, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'bg_color': 'white', 'border': 1})
        format_left = workbook.add_format({'bold': False, 'font_color': 'black', 'align': 'left', 'valign': 'vcenter', 'bg_color': 'white', 'border': 1})
        format_signature = workbook.add_format({'bold': True, 'underline': True, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'bg_color': 'white', 'border': 1, })

        # row = 4
        #
        # sheet.merge_range(row, 0, row, 1, 'EMPLOYEE PAY SLIP FOR THE MONTH', format_center)
        # row += 2
        # sheet.merge_range(row, 0, row, 1, 'Period', format_head)
        # row += 1
        # sheet.merge_range(row, 0, row, 1, '%s - %s' % (fields.Date.from_string(data['date_start']).strftime('%d %B %Y'), fields.Date.from_string(data['date_end']).strftime('%d %B %Y')), format_center)
        #
        # row += 1
        # sheet.merge_range(row, 0, row, 1, 'Project Name', format_head)
        # row += 1
        # sheet.merge_range(row, 0, row, 1, '', format_center)

        # row += 2

        row = 0
        sheet.write(row, 0, 'Net Salary', format_head)
        sheet.write(row, 1, 'Beneficiary Account', format_head)
        sheet.write(row, 2, 'Beneficiary Name', format_head)
        sheet.write(row, 3, 'Beneficiary Address 1', format_head)
        sheet.write(row, 4, 'Beneficiary Address 2', format_head)
        sheet.write(row, 5, 'Beneficiary Address 3', format_head)
        sheet.write(row, 6, 'Beneficiary Bank', format_head)
        sheet.write(row, 7, 'Payment Description (Optional)', format_head)
        sheet.write(row, 8, 'Basic Salary', format_head)
        sheet.write(row, 9, 'Housing Allowance', format_head)
        sheet.write(row, 10, 'Other Earnings', format_head)
        sheet.write(row, 11, 'Deductions', format_head)
        sheet.write(row, 12, 'Beneficiary ID', format_head)
        col = 0

        rule_categories = self.env['hr.salary.rule.category'].search([])
        ded_categories = rule_categories.filtered(lambda r: r.code == 'DED').ids
        net_categories = rule_categories.filtered(lambda r: r.code == 'NET').ids
        gross_categories = rule_categories.filtered(lambda r: r.code == 'GROSS').ids

        for payslip in self.env['hr.payslip'].search([('payslip_run_id','=',data.get('batch_id'))]):
            row += 1

            lines = payslip.line_ids
            basic = payslip.contract_id.wage
            housing = payslip.contract_id.l10n_sa_housing_allowance

            other_earning = sum(lines.filtered(lambda l: l.salary_rule_id.category_id.id in gross_categories and l.salary_rule_id.amount_select != 'adjustment').mapped('total'))
            other_earning -= (basic + housing)

            deductions = abs(sum(lines.filtered(lambda l: l.salary_rule_id.category_id.id in ded_categories).mapped('total')))
            net = sum(lines.filtered(lambda l: l.salary_rule_id.category_id.id in net_categories and l.salary_rule_id.amount_select != 'adjustment').mapped('total'))

            employee = payslip.employee_id
            payment_desc = "Salary for %s %s" %(calendar.month_name[payslip.date_to.month], payslip.date_to.year) or " "
            # bank account
            bank = employee.bank_account_id or False
            acc_number, bank_name = '', ''
            if bank:
                acc_number = employee.bank_account_id.acc_number or ''
                bank_name = employee.bank_account_id.bank_id and employee.bank_account_id.bank_id.bic or 'N/A'
            sheet.write(row, col+0, net or '', format_center)
            sheet.write(row, col+1, acc_number or '', format_center)
            holder_name = ""
            if employee.bank_account_id.partner_id.name:
                for name in employee.bank_account_id.partner_id.name.split():
                    if len(holder_name) + len(name) > 35:
                        break
                    holder_name += name + " "
                holder_name = holder_name.strip()
            else: holder_name = employee.bank_account_id.acc_holder_name
            sheet.write(row, col+2, holder_name or "", format_center)
            sheet.write(row, col+3, employee.address_id.street or " ", format_center)
            sheet.write(row, col+4, employee.address_id.street2 or " ", format_center)
            sheet.write(row, col+5, employee.registration_number or " ", format_center)
            sheet.write(row, col+6, bank_name, format_center)
            sheet.write(row, col+7, payment_desc, format_center)
            sheet.write(row, col+8, basic or '0', format_center)
            sheet.write(row, col+9, housing or '0', format_center)
            sheet.write(row, col+10, other_earning or '0', format_center)
            sheet.write(row, col+11, deductions or '0', format_center)
            sheet.write(row, col+12, employee.visa_no or '', format_center)

            # sheet.write(row, col+0, employee.registration_number or "", format_center)
            # sheet.write(row, col+1, employee.name or "", format_center)

            # sheet.write(row, col+2, acc_number, format_center)
            # sheet.write(row, col+3, bank_name, format_center)
            # sheet.write(row, col+4, employee.permit_no or "", format_center)
            # sheet.write(row, col+5, payslip.number or '', format_center)
            # sheet.write(row, col+6, payslip.name or '', format_center)
            # sheet.write(row, col+7, basic or '', format_center)
            # sheet.write(row, col+8, housing or '', format_center)
            # sheet.write(row, col+9, other_earning or '', format_center)
            # sheet.write(row, col+10, deductions or '', format_center)
            # sheet.write(row, col+11, net or '', format_center)

        # row += 3

        # sheet.write(row, col + 1, "Payroll Officer", format_signature)
        # sheet.write(row, col + 3, "HR Manager", format_signature)
        # sheet.write(row, col + 5, "HR Director", format_signature)

        #####################################################################
        # from odoo.modules.module import get_module_resource
        # from io import BytesIO
        #
        # file = open(get_module_resource('hr_payslip_batch_export', 'static/img', 'flintlogo.png'), 'rb')
        # data = BytesIO(file.read())
        # file.close()
        #
        # x_scale = 0.3
        # y_scale = 0.3
        #
        # sheet.insert_image('A2', 'foo', {'image_data': data, 'x_scale': x_scale, 'y_scale': y_scale})
        #####################################################################
