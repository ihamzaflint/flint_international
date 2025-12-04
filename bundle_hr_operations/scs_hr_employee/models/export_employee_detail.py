from odoo import models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def export_employee_detail_xlsx(self):
        data = {
            'employee_id': self.id,
        }
        return self.env.ref('scs_hr_employee.action_employee_detail_export').report_action(self, data=data)


class ExportEmployeeDetailXlsx(models.AbstractModel):
    _name = 'report.scs_hr_employee.export_employee_detail_report'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Export Employee Detail Report'

    def generate_xlsx_report(self, workbook, data, records):
        sheet = workbook.add_worksheet('Sheet1')

        format_head = workbook.add_format({'bold': True, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'bg_color': '#bfbfbf', 'border': 1, 'text_wrap': True,})
        format_cell_center = workbook.add_format({'bold': False, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'bg_color': 'white', 'border': 1, 'text_wrap': True,})
        format_cell_center_date = workbook.add_format({'bold': False, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'bg_color': 'white', 'border': 1, 'text_wrap': True, 'num_format': 'dd/mm/yyyy'})

        row = 0
        col = 0
        col1 = 0

        sheet.set_column(col, col, 15)
        sheet.set_column(col + 1, col + 1, 15)
        sheet.set_column(col + 2, col + 2, 15)
        sheet.set_column(col + 3, col + 3, 15)
        sheet.set_column(col + 4, col + 4, 15)
        sheet.set_column(col + 5, col + 5, 30)
        sheet.set_column(col + 6, col + 6, 30)
        sheet.set_column(col + 7, col + 7, 30)
        sheet.set_column(col + 8, col + 8, 30)
        sheet.set_column(col + 9, col + 9, 30)
        sheet.set_column(col + 10, col + 10, 15)
        sheet.set_column(col + 11, col + 11, 15)
        sheet.set_column(col + 12, col + 12, 10)
        sheet.set_column(col + 13, col + 13, 10)
        sheet.set_column(col + 14, col + 14, 10)
        sheet.set_column(col + 15, col + 15, 10)
        sheet.set_column(col + 16, col + 16, 10)
        sheet.set_column(col + 17, col + 17, 10)
        sheet.set_column(col + 18, col + 18, 10)
        sheet.set_column(col + 19, col + 19, 10)
        sheet.set_column(col + 20, col + 20, 10)
        sheet.set_column(col + 21, col + 21, 10)
        sheet.set_column(col + 22, col + 22, 10)
        sheet.set_column(col + 23, col + 23, 10)
        sheet.set_column(col + 24, col + 24, 10)
        sheet.set_column(col + 25, col + 25, 20)
        sheet.set_column(col + 26, col + 26, 20)
        sheet.set_column(col + 27, col + 27, 20)
        sheet.set_column(col + 28, col + 28, 30)
        sheet.set_column(col + 29, col + 29, 30)
        sheet.set_column(col + 30, col + 30, 30)
        sheet.set_column(col + 31, col + 31, 30)
        sheet.set_column(col + 32, col + 32, 30)
        sheet.set_column(col + 33, col + 33, 30)
        sheet.set_column(col + 34, col + 34, 30)
        sheet.set_column(col + 35, col + 35, 30)
        sheet.set_column(col + 36, col + 36, 30)
        sheet.set_column(col + 37, col + 37, 30)
        sheet.set_column(col + 38, col + 38, 30)
        sheet.set_column(col + 39, col + 39, 30)
        sheet.set_column(col + 40, col + 40, 30)
        sheet.set_column(col + 41, col + 41, 30)
        sheet.set_column(col + 42, col + 42, 30)
        sheet.set_column(col + 43, col + 43, 30)
        sheet.set_column(col + 44, col + 44, 30)
        sheet.set_column(col + 45, col + 45, 30)
        sheet.set_column(col + 46, col + 46, 30)
        sheet.set_column(col + 47, col + 47, 30)
        sheet.set_column(col + 48, col + 47, 30)
        sheet.set_column(col + 49, col + 47, 30)
        sheet.set_column(col + 50, col + 47, 30)
        sheet.set_row(row, 50)

        sheet.write(row, col, "Related User/Name", format_head)
        sheet.write(row, col + 1, "Flint EMP.ID", format_head)
        sheet.write(row, col + 2, "Client Employee ID", format_head)
        sheet.write(row, col + 3, "Client Type", format_head)
        sheet.write(row, col + 4, "Client", format_head)
        sheet.write(row, col + 5, "Client Project ", format_head)
        sheet.write(row, col + 6, "Analytic Accounts", format_head)
        sheet.write(row, col + 7, "Name", format_head)
        sheet.write(row, col + 8, "Job Position in project", format_head)
        sheet.write(row, col + 9, "Contract Start Date", format_head)
        sheet.write(row, col + 10, "Contract End Date", format_head)
        sheet.write(row, col + 11, "Status", format_head)
        sheet.write(row, col + 12, "Salary Structure Type", format_head) 
        sheet.write(row, col + 13, "Wage Type", format_head)
        sheet.write(row, col + 14, "Basic Salary", format_head)
        sheet.write(row, col + 15, "Housing Allowance", format_head)
        sheet.write(row, col + 16, "Transport Allowance", format_head)
        sheet.write(row, col + 17, "Mobile Allowance", format_head)
        # sheet.write(row, col + 18, "Internet Allowance", format_head)
        sheet.write(row, col + 18, "On Call Recurring", format_head)
        sheet.write(row, col + 19, "Other Allowances", format_head)
        sheet.write(row, col + 20, "Technical Allowance", format_head)
        sheet.write(row, col + 21, "Car Allowance", format_head)
        sheet.write(row, col + 22, "Ticket Allowance", format_head)
        sheet.write(row, col + 23, "Lap Top & Tools Allowances", format_head)
        sheet.write(row, col + 24, "Project Allowance", format_head)
        sheet.write(row, col + 25, "Niche Skill Allowance", format_head)
        sheet.write(row, col + 26, "Educational Allowance", format_head)    
        sheet.write(row, col + 27, "Guaranteed Monthly Bonus", format_head)
        sheet.write(row, col + 28, "Special Allowance", format_head)
        sheet.write(row, col + 29, "EOS Payment", format_head)
        sheet.write(row, col + 30, "EOS Provision Accural", format_head)
        sheet.write(row, col + 31, "Annual Leave Vacation Amount", format_head)
        sheet.write(row, col + 32, "GOSI OnBehalf", format_head)
        sheet.write(row, col + 33, "Kids Allowance", format_head)
        sheet.write(row, col + 34, "Shift Allowance", format_head)
        sheet.write(row, col + 35, "Gas Allowance", format_head)
        sheet.write(row, col + 36, "Food Allowance", format_head)
        sheet.write(row, col + 37, "Total Gross", format_head)
        sheet.write(row, col + 38, "Bank Account Number/IBAN Number", format_head)
        sheet.write(row, col + 39, "Bank Name", format_head)
        sheet.write(row, col + 40, "Iqama Number", format_head)
        sheet.write(row, col + 41, "Iqama Expiry Date", format_head)
        sheet.write(row, col + 42, "Passport No", format_head)
        sheet.write(row, col + 43, "Passport Expiry Date", format_head)
        sheet.write(row, col + 44, "Name As per Muqeem", format_head)
        sheet.write(row, col + 45, "Nationality (Country) In English", format_head)
        sheet.write(row, col + 46, "Sponsor Number", format_head)
        sheet.write(row, col + 47, "Sponsor Name", format_head)
        sheet.write(row, col + 48, "Profession as per Muqeem in arabic", format_head)
        sheet.write(row, col + 49, "Profession in Iqama", format_head)
        sheet.write(row, col + 50, "Country of Birth", format_head)
        sheet.write(row, col + 51, "Date of Birth", format_head)
        sheet.write(row, col + 52, "Gender", format_head)
        sheet.write(row, col + 53, "Date of Entry", format_head)
        sheet.write(row, col + 54, "Marital Status", format_head)
        sheet.write(row, col + 55, "Number of Children", format_head)
        sheet.write(row, col + 56, "Personal Email", format_head)
        sheet.write(row, col + 57, "Mobile", format_head)
        sheet.write(row, col + 58, "Emergency Contact", format_head)
        sheet.write(row, col + 59, "Degree", format_head)
        sheet.write(row, col + 60, "Education Level", format_head)
        sheet.write(row, col + 61, "Field of Study", format_head)

        counter = 0
        for employee_id in records:
            contract_id = self.env['hr.contract'].search([('employee_id', '=', employee_id.id),
                                                          ('state', '=', 'open')], limit=1)
            
            wage_type = dict(contract_id.structure_type_id._fields["wage_type"].selection).get(contract_id.structure_type_id.wage_type, False)

            row += 1
            sheet.set_row(row, 30)
            counter += 1
            emp_gender = contract_status = education_level = ''

            marital = dict(employee_id._fields["marital"].selection).get(employee_id.marital, False)
            if employee_id.gender:
                emp_gender = dict(employee_id.fields_get(allfields=['gender']
                                                         )['gender']['selection']
                                                         )[employee_id.gender]
            if employee_id.certificate:
                education_level = dict(employee_id.fields_get(allfields=['certificate']
                                                         )['certificate']['selection']
                                                         )[employee_id.certificate]
            if contract_id:
                contract_status = dict(contract_id.fields_get(allfields=['state'])['state']['selection'])[contract_id.state]
            
            sheet.write(row, col, employee_id.user_id.name  or '', format_cell_center)
            sheet.write(row, col + 1, employee_id.registration_number or  '', format_cell_center)
            sheet.write(row, col + 2, employee_id.client_employee_id or '', format_cell_center)
            sheet.write(row, col + 3, employee_id.client_type_id.name or '', format_cell_center)
            sheet.write(row, col + 4, employee_id.client_id.name or '', format_cell_center)
            sheet.write(row, col + 5, employee_id.project_id.name or '', format_cell_center)
            sheet.write(row, col + 6, contract_id.analytic_account_id.name or '', format_cell_center)
            sheet.write(row, col + 7, employee_id.name or '', format_cell_center)
            sheet.write(row, col + 8, employee_id.job_id.name or '', format_cell_center)
            sheet.write(row, col + 9, contract_id.date_start or '', format_cell_center_date)
            sheet.write(row, col + 10, contract_id.date_end or '', format_cell_center_date)
            sheet.write(row, col + 11, contract_status or '', format_cell_center_date)
            sheet.write(row, col + 12, contract_id.structure_type_id.name or '', format_cell_center)
            sheet.write(row, col + 13, format(wage_type or ''), format_cell_center)
            sheet.write(row, col + 14, format(contract_id.wage or 0.0, '.2f'), format_cell_center)
            sheet.write(row, col + 15, format(contract_id.l10n_sa_housing_allowance or 0.0, '.2f'), format_cell_center)
            sheet.write(row, col + 16, format(contract_id.l10n_sa_transportation_allowance or 0.0, '.2f'), format_cell_center)
            sheet.write(row, col + 17, format(contract_id.phone_allowance or 0.0, '.2f'), format_cell_center)
            # sheet.write(row, col + 18, 0.0, format_cell_center)
            sheet.write(row, col + 18, format(contract_id.oc_rec_allowance or 0.0, '.2f'), format_cell_center)
            sheet.write(row, col + 19, format(contract_id.l10n_sa_other_allowances or 0.0, '.2f'), format_cell_center)
            sheet.write(row, col + 20, format(contract_id.tech_allowance or 0.0, '.2f'), format_cell_center)
            sheet.write(row, col + 21, format(contract_id.car_allowance or 0.0, '.2f'), format_cell_center)
            sheet.write(row, col + 22, format(contract_id.tickets_allowance or 0.0, '.2f'), format_cell_center)
            sheet.write(row, col + 23, 0.0, format_cell_center)
            sheet.write(row, col + 24, format(contract_id.project_allowance or 0.0, '.2f'), format_cell_center)
            sheet.write(row, col + 25, format(contract_id.niche_skill_allowance or 0.0, '.2f'), format_cell_center)
            sheet.write(row, col + 26, format(contract_id.edu_allowance or 0.0, '.2f'), format_cell_center)
            sheet.write(row, col + 27, format(contract_id.granted_monthly_bonus or 0.0, '.2f'), format_cell_center)
            sheet.write(row, col + 28, format(contract_id.special_allowance or 0.0, '.2f'), format_cell_center)
            sheet.write(row, col + 29, format(contract_id.eos_payment_allowance or 0.0, '.2f'), format_cell_center)
            sheet.write(row, col + 30, format(contract_id.eos_provision_accural_allowance or 0.0, '.2f'), format_cell_center)
            sheet.write(row, col + 31, format(contract_id.annual_leave_vacation_amount_allowance or 0.0, '.2f'), format_cell_center)
            sheet.write(row, col + 32, format(contract_id.gosi_comp_onbehalf or 0.0, '.2f'), format_cell_center)
            sheet.write(row, col + 33, format(contract_id.kids_allowance or 0.0, '.2f'), format_cell_center)
            sheet.write(row, col + 34, format(contract_id.shift_allowance or 0.0, '.2f'), format_cell_center)
            sheet.write(row, col + 35, format(contract_id.gas_allowance or 0.0, '.2f'), format_cell_center)
            sheet.write(row, col + 36, format(contract_id.food_allowance or 0.0, '.2f'), format_cell_center)
            sheet.write(row, col + 37, format(contract_id.total_gross_wage or 0.0, '.2f'), format_cell_center)
            sheet.write(row, col + 38, employee_id.bank_account_id.acc_number or '', format_cell_center)
            sheet.write(row, col + 39, employee_id.bank_account_id.bank_id.name or '', format_cell_center)
            sheet.write(row, col + 40, employee_id.visa_no or '', format_cell_center)
            sheet.write(row, col + 41, employee_id.visa_expire or '', format_cell_center_date)
            sheet.write(row, col + 42, employee_id.passport_id or '', format_cell_center)
            sheet.write(row, col + 43, employee_id.passport_expiry_date or '', format_cell_center_date)
            sheet.write(row, col + 44, employee_id.muqeem_name or '', format_cell_center)
            sheet.write(row, col + 45, employee_id.country_id.name or '', format_cell_center)
            sheet.write(row, col + 46, contract_id.sponsor_id.code or '', format_cell_center)
            sheet.write(row, col + 47, contract_id.sponsor_id.name or '', format_cell_center)
            sheet.write(row, col + 48, employee_id.muqeem_profession or '', format_cell_center)
            sheet.write(row, col + 49, employee_id.profession_id.name or '', format_cell_center)
            sheet.write(row, col + 50, employee_id.country_of_birth.name or '', format_cell_center_date)
            sheet.write(row, col + 51, employee_id.birthday or '', format_cell_center_date)
            sheet.write(row, col + 52, emp_gender or '', format_cell_center)
            sheet.write(row, col + 53, employee_id.date_of_entry or '', format_cell_center)
            sheet.write(row, col + 54, marital or '', format_cell_center)
            sheet.write(row, col + 55, employee_id.children or '', format_cell_center)
            sheet.write(row, col + 56, employee_id.personal_email or '', format_cell_center)
            sheet.write(row, col + 57, employee_id.work_phone or '', format_cell_center)
            sheet.write(row, col + 58, employee_id.emergency_contact or '', format_cell_center)
            sheet.write(row, col + 59, employee_id.emp_degree_id.name or '', format_cell_center)
            sheet.write(row, col + 60, education_level or '', format_cell_center)
            sheet.write(row, col + 61, employee_id.study_field or '', format_cell_center)

