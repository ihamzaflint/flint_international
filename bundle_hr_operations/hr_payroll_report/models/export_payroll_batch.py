# -*- coding: utf-8 -*-
###################################################################################
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
from odoo import _, api, fields, models
from collections import defaultdict
from dateutil import relativedelta

from odoo.exceptions import UserError

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    def export_payslips_batch_xlsx(self):

        data = {
            'batch_id': self.id,
            'date_start': self.date_start,
            'date_end': self.date_end,
        }
        return self.env.ref('hr_payroll_report.action_payslips_batch_export').report_action(self, data=data)


class ExportPayslipBatchXlsx(models.AbstractModel):
    _name = 'report.hr_payroll_report.export_payslips_batch_report'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Export Payslips Batch Report'

    # def generate_xlsx_report_old(self, workbook, data, records):
    #     sheet = workbook.add_worksheet('Sheet1')
    #     batch_id = self.env['hr.payslip.run'].browse(data['batch_id'])
    #
    #     self.env['hr.payroll.report2.wizard'].create({
    #         'date_from': batch_id.date_start,
    #         'date_to': batch_id.date_end,
    #         'payslip_run_id': batch_id.id,
    #     }).sudo().setup_report()
    #
    #     table = self.env['hr.payroll.report2']._table
    #
    #     self._cr.execute("SELECT analytic_account_id,department_id,employee_id,salary_rule_name,amount FROM {};".format(table))
    #     fetched = self._cr.fetchall()
    #
    #     def group_by(data, col, label=None):
    #         result = {}
    #         for o in data:
    #             val = o[col]
    #             if label and val:
    #                 val = label + str(val)
    #
    #             if val in result:
    #                 result[val].append(o)
    #             else:
    #                 result[val] = [o]
    #         return result
    #
    #     col_analytic = 0
    #     col_department = 1
    #     col_employee = 2
    #     col_sal_rule = 3
    #     col_amount = 4
    #
    #     grouped_by_analytic = group_by(fetched, col=col_analytic)
    #
    #     ###################################################################
    #
    #     result = []
    #
    #     for analytic in grouped_by_analytic:
    #
    #         grouped_by_department = group_by(grouped_by_analytic[analytic], col=col_department)
    #
    #         dep = []
    #         for department in grouped_by_department:
    #             grouped_by_employee = group_by(grouped_by_department[department], col=col_employee)
    #
    #             emp = []
    #             for employee in grouped_by_employee:
    #                 emp.append({
    #                     'employee_id': employee,
    #                     'data': grouped_by_employee[employee],
    #                 })
    #
    #             dep.append({
    #                 'department_id': department,
    #                 'data': emp,
    #             })
    #         result.append({
    #             'analytic_id': analytic,
    #             'data': dep,
    #         })
    #
    #     ###################################################################
    #     # Find all Salary Rules
    #     # sal_rules = list(set([x[col_sal_rule] for x in fetched]))
    #
    #     sequence_data = {}
    #     for sal_rule in list(set([x[col_sal_rule] for x in fetched])):
    #         self._cr.execute("SELECT sequence FROM hr_salary_rule where name=%s;", [sal_rule])
    #         sal_rule_data = self._cr.fetchall()
    #         # if not sal_rule_data:
    #         #     self.env['hr.salary.rule'].search([('name', '=', sal_rule)])[0].sequence
    #         #     raise UserWarning("Cannot find salary rule details. %s" % sal_rule)
    #
    #         if sal_rule_data:
    #             sequence_data[sal_rule] = sal_rule_data[0][0]
    #         else:
    #             sequence_data[sal_rule] = self.env['hr.salary.rule'].search([('name', '=', sal_rule)])[0].sequence
    #
    #         if not sequence_data[sal_rule]:
    #             raise UserWarning("Cannot find salary rule details. %s" % sal_rule)
    #
    #     sal_rules = [x[0] for x in sorted(sequence_data.items(), key=lambda x: x[1])]
    #
    #     # sal_rules = sorted(sal_rules, key=lambda x: sequence_data[])
    #
    #     ###################################################################
    #     # Export
    #
    #     sheet.set_column(0, 0, 30)
    #
    #     format_head = workbook.add_format({'bold': False, 'font_color': 'black', 'align': 'left', 'valign': 'vcenter', 'bg_color': '#bfbfbf', 'border': 1})
    #     format_cell = workbook.add_format({'bold': False, 'font_color': 'black', 'align': 'right', 'valign': 'vcenter', 'bg_color': 'white', 'border': 1})
    #
    #     row = 0
    #     sheet.write(row, 0, ' ', format_head)
    #
    #     col = 0
    #     for sal_rule in sal_rules:
    #         col += 1
    #         sheet.set_column(row+1, col, 15)
    #         sheet.write(row, col, sal_rule, format_head)
    #
    #     row += 1
    #     sheet.write(row, 0, "Total", format_head)
    #
    #     all_ana_data = []
    #     space = " "
    #     for analytic in result:
    #         row += 1
    #
    #         analytic_row = row
    #
    #         analytic_name = self.env['account.analytic.account'].browse(analytic['analytic_id']).name or "Undefined"
    #         sheet.write(row, 0, 5*space + analytic_name, format_head)
    #         ana_data = {}
    #         for department in analytic['data']:
    #             row += 1
    #             department_row = row
    #             department_name = self.env['hr.department'].browse(department['department_id']).name or "Undefined"
    #             sheet.write(row, 0, 10*space + department_name, format_head)
    #
    #             dep_data = {}
    #
    #             for employee in department['data']:
    #                 row += 1
    #                 employee_name = self.env['hr.employee'].browse(employee['employee_id']).name or "Undefined"
    #                 sheet.write(row, 0, 15*space + employee_name, format_head)
    #
    #                 col = 0
    #                 for sal_rule in sal_rules:
    #                     col += 1
    #                     data = [x for x in employee['data'] if x[col_sal_rule] == sal_rule]
    #                     amount = sum([x[col_amount] for x in data])
    #                     sheet.write(row, col, format(amount, '.2f'), format_cell)
    #
    #                     if sal_rule in dep_data:
    #                         dep_data[sal_rule] += amount
    #                     else:
    #                         dep_data[sal_rule] = amount
    #
    #                     if sal_rule in ana_data:
    #                         ana_data[sal_rule] += amount
    #                     else:
    #                         ana_data[sal_rule] = amount
    #
    #             col = 0
    #             for sal_rule in sal_rules:
    #                 col += 1
    #                 sheet.write(department_row, col, format(dep_data[sal_rule], '.2f'), format_cell)
    #
    #         col = 0
    #         for sal_rule in sal_rules:
    #             col += 1
    #             sheet.write(analytic_row, col, format(ana_data[sal_rule], '.2f'), format_cell)
    #
    #         all_ana_data.append(ana_data)
    #
    #     col = 0
    #     for sal_rule in sal_rules:
    #         col += 1
    #         sheet.write(1, col, format(sum([x[sal_rule] for x in all_ana_data]), '.2f'), format_cell)

    def generate_xlsx_report(self, workbook, data, records):
        sheet = workbook.add_worksheet('Sheet1')
        batch_id = self.env['hr.payslip.run'].browse(data['batch_id'])

        self.env['hr.payroll.report2.wizard'].create({
            'date_from': batch_id.date_start,
            'date_to': batch_id.date_end,
            'payslip_run_id': batch_id.id,
        }).sudo().setup_report()

        table = self.env['hr.payroll.report2']._table

        self._cr.execute("SELECT analytic_account_id,department_id,employee_id,salary_rule_name,amount,amount_scheduled FROM {};".format(table))
        fetched = self._cr.fetchall()

        def group_by(data, col, label=None):
            result = {}
            for o in data:
                val = o[col]
                if label and val:
                    val = label + str(val)

                if val in result:
                    result[val].append(o)
                else:
                    result[val] = [o]
            return result

        col_employee = 2
        col_sal_rule = 3
        col_amount = 4
        col_amount_scheduled = 5

        sequence_data = {}
        rule_info = {}
        for sal_rule in list(set([x[col_sal_rule] for x in fetched])):
            self._cr.execute("""
                                SELECT sequence, code, amount_select, category_id, id
                                FROM hr_salary_rule
                                WHERE name->>'en_US' = %s AND active = TRUE
                                ORDER BY sequence ASC;
                            """, [sal_rule])
            sal_rule_data = self._cr.fetchall()
            code = sal_rule_data[0][1] if sal_rule_data else False
            if code and code=='GOSI':   # no need to show GOSI Total Salary in export
                continue
            sequence_data[sal_rule] = sal_rule_data[0][0] if sal_rule_data else self.env['hr.salary.rule'].search([('name', '=', sal_rule)])[0].sequence
            if not sequence_data[sal_rule]:
                raise UserWarning("Cannot find salary rule details. %s" % sal_rule)
            rule_info[sal_rule] = {
                'sequence':sal_rule_data[0][0],
                'code':sal_rule_data[0][1],
                'amount_select':sal_rule_data[0][2],
                'category_id':sal_rule_data[0][3],
                'rule_id':sal_rule_data[0][4],
            }

            # print(sequence_data[sal_rule])
        sal_rules = [x[0] for x in sorted(sequence_data.items(), key=lambda x: x[1])]

        employee_ids = batch_id.slip_ids.mapped('employee_id')

        format_head = workbook.add_format({'bold': False, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'bg_color': '#bfbfbf', 'border': 1, 'text_wrap': True,})
        format_cell_center = workbook.add_format({'bold': False, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'bg_color': 'white', 'border': 1, 'text_wrap': True,})
        format_cell_right = workbook.add_format({'bold': False, 'font_color': 'black', 'align': 'right', 'valign': 'vcenter', 'bg_color': 'white', 'border': 1, })
        format_cell_center_date = workbook.add_format({'bold': False, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'bg_color': 'white', 'border': 1, 'text_wrap': True, 'num_format': 'dd/mm/yyyy'})
        format_center = workbook.add_format({'bold': False, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'bg_color': 'white', 'border': 1})
        format_signature = workbook.add_format({'bold': True, 'underline': True, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'bg_color': 'white', 'border': 1, })
        format_signature_1 = workbook.add_format({'bold': True, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'bg_color': 'white', 'border': 1, })
        format_cell_right_1 = workbook.add_format({'bold': True, 'font_color': 'black', 'align': 'right', 'valign': 'vcenter', 'bg_color': 'white', 'border': 1, })

        row = 4
        # sheet.merge_range(row, 0, row, 1, 'EMPLOYEE PAY SLIP FOR THE MONTH', format_center)
        # sheet.merge_range(row, 0, row, 1, batch_id.name, format_center)
        # row += 2
        sheet.merge_range(row, 0, row, 1, 'Period', format_head)
        row += 1
        sheet.merge_range(row, 0, row, 1, '%s - %s' % (fields.Date.from_string(data['date_start']).strftime('%d %B %Y'), fields.Date.from_string(data['date_end']).strftime('%d %B %Y')), format_center)

        row += 1
        sheet.merge_range(row, 0, row, 1, 'Project Name', format_head)
        row += 1
        sheet.merge_range(row, 0, row, 1, batch_id.name, format_center)

        row += 2
        col = 0
        sheet.set_column(col, col, 15)
        sheet.set_column(col + 1, col + 1, 40)
        sheet.set_column(col + 2, col + 2, 30)
        sheet.set_column(col + 3, col + 3, 15)
        sheet.set_column(col + 4, col + 4, 15)
        sheet.set_column(col + 5, col + 5, 15)
        sheet.set_column(col + 6, col + 6, 15)
        sheet.set_column(col + 7, col + 7, 15)
        sheet.set_column(col + 8, col + 8, 15)
        sheet.set_column(col + 9, col + 9, 15)
        sheet.set_column(col + 10, col + 10, 15)
        sheet.set_column(col + 11, col + 11, 15)
        sheet.set_column(col + 12, col + 12, 15)
        sheet.set_column(col + 13, col + 13, 15)
        sheet.set_column(col + 14, col + 14, 15)
        sheet.set_column(col + 15, col + 15, 15)
        sheet.set_column(col + 16, col + 16, 15)
        sheet.set_column(col + 17, col + 17, 15)
        sheet.set_column(col + 18, col + 18, 15)
        sheet.set_column(col + 19, col + 19, 15)
        sheet.set_column(col + 20, col + 20, 15)
        sheet.set_column(col + 21, col + 20, 30)
        sheet.set_column(col + 22, col + 20, 30)
        sheet.set_column(col + 23, col + 20, 30)
        sheet.set_row(row, 50)
        sheet.write(row, col, "Emp_Code", format_head)
        sheet.write(row, col + 1, "Client Employee ID", format_head)
        sheet.write(row, col + 2, "Name", format_head)
        sheet.write(row, col + 3, "Iqama Number", format_head)
        sheet.write(row, col + 4, "Start Date", format_head)
        sheet.write(row, col + 5, "End Date", format_head)
        sheet.write(row, col + 6, "Basic Salary", format_head)
        sheet.write(row, col + 7, "Housing Allowance", format_head)
        sheet.write(row, col + 8, "Transportation Allowance", format_head)
        sheet.write(row, col + 9, "Phone Allowance", format_head)
        sheet.write(row, col + 10, "Tools Allowance", format_head)
        sheet.write(row, col + 11, "Project Allowance", format_head)
        sheet.write(row, col + 12, "Other Allowances", format_head)
        sheet.write(row, col + 13, "Gross", format_head)
        sheet.write(row, col + 14, "Working Days", format_head)
        sheet.write(row, col + 15, "Actual - Expenses Additions", format_head)
        sheet.write(row, col + 16, "Actual - Over Time Add", format_head)
        sheet.write(row, col + 17, "Total Addition", format_head)
        sheet.write(row, col + 18, "Actual - Medical Insurance Upgrade Deduction", format_head)
        sheet.write(row, col + 19, "GOSI Company Contribution_9.75% ", format_head)
        sheet.write(row, col + 20, "Total Deduction", format_head)
        sheet.write(row, col + 21, "Actual - Net Salary", format_head)
        sheet.write(row, col + 22, "Allowance Details", format_head)
        sheet.write(row, col + 23, "Deduction Details", format_head)



        row += 1

        tot_basic = tot_housing_alw = tot_transport_alw = tot_phone_alw =\
        tot_tools_alw = tot_project_alw = tot_other_alw = tot_gross =\
        tot_act_exp_add = tot_act_ot_add = fin_tot_add = tot_med_ins_ded =\
        tot_gosi_cont_ded = fin_tot_ded = tot_act_net_sal = 0
        for slip_id in batch_id.slip_ids:
            allowance = ''
            deduction = ''
            basic = housing_alw = transport_alw = phone_alw = tools_alw =\
                project_alw = other_alw = gross = act_exp_add =\
                act_ot_add = tot_add = med_ins_ded = gosi_cont_ded =\
                tot_ded = act_net_sal = 0.0
            sheet.write(row, col, slip_id.employee_id.registration_number or "", format_cell_center)
            sheet.write(row, col + 1, slip_id.employee_id.client_employee_id or "", format_cell_center)
            sheet.write(row, col + 2, slip_id.employee_id.name or "", format_cell_center)
            sheet.write(row, col + 3, slip_id.employee_id.visa_no or "", format_cell_center)
            sheet.write(row, col + 4, slip_id.employee_id.contract_id.date_start or "", format_cell_center_date)
            sheet.write(row, col + 5, slip_id.employee_id.contract_id.date_end or "", format_cell_center_date)
            for line_id in slip_id.line_ids:
                if line_id.category_id.code == 'BASIC':
                    basic += line_id.total
                    tot_basic += line_id.total
                if line_id.code == 'HOUSEALW':
                    housing_alw += line_id.total
                    tot_housing_alw += line_id.total
                if line_id.code == 'TRAALLOW':
                    transport_alw += line_id.total
                    tot_transport_alw += line_id.total
                if line_id.code == 'PHONEALLOW':
                    phone_alw += line_id.total
                    tot_phone_alw += line_id.total
                if line_id.code == 'TOOLSALLOW':
                    tools_alw += line_id.total
                    tot_tools_alw += line_id.total
                if line_id.code == 'PROJALLW':
                    project_alw += line_id.total
                    tot_project_alw += line_id.total
                if line_id.code == 'OTALLOW':
                    other_alw += line_id.total
                    tot_other_alw += line_id.total
                if line_id.code == 'GROSS':
                    gross += line_id.total
                    tot_gross += line_id.total
                    # act_net_sal += line_id.total
                    # tot_act_net_sal += line_id.total
                if line_id.code == 'EAP':
                    act_exp_add += line_id.total
                    tot_act_exp_add += line_id.total
                    # tot_add += line_id.total
                    # fin_tot_add += line_id.total
                    # act_net_sal += line_id.total
                    # tot_act_net_sal += line_id.total
                if line_id.code == 'OTADD':
                    act_ot_add += line_id.total
                    tot_act_ot_add += line_id.total
                    # tot_add += line_id.total
                    # fin_tot_add += line_id.total
                    # act_net_sal += line_id.total
                    # tot_act_net_sal += line_id.total
                if line_id.code in ['EAP', 'FTA', 'OTADD', 'OAP']:
                    tot_add += line_id.total
                    fin_tot_add += line_id.total
                if line_id.code == 'MIUD':
                    med_ins_ded += line_id.total
                    tot_med_ins_ded += line_id.total
                    # tot_ded += line_id.total
                    # fin_tot_ded += line_id.total
                    # act_net_sal -= line_id.total
                    # tot_act_net_sal -= line_id.total
                if line_id.code == 'GOSICC_':
                    gosi_cont_ded += line_id.total
                    tot_gosi_cont_ded += line_id.total
                    # tot_ded += line_id.total
                    # fin_tot_ded += line_id.total
                    # act_net_sal -= line_id.total
                    # tot_act_net_sal -= line_id.total
                if line_id.category_id and line_id.category_id.code == 'DED':
                    tot_ded += line_id.total
                    fin_tot_ded += line_id.total
                if line_id.category_id and line_id.category_id.code == 'NET':
                    act_net_sal += line_id.total
                    tot_act_net_sal += line_id.total
                for other_line in  line_id.other_hr_payslip_ids:
                    if other_line.operation_type == 'allowance':
                        allowance += other_line.name + "\n"
                    else:
                        deduction += other_line.name + "\n"

            sheet.write(row, col + 6, format(basic, '.2f'), format_cell_right)
            sheet.write(row, col + 7, format(housing_alw, '.2f'), format_cell_right)
            sheet.write(row, col + 8, format(transport_alw, '.2f'), format_cell_right)
            sheet.write(row, col + 9, format(phone_alw, '.2f'), format_cell_right)
            sheet.write(row, col + 10, format(tools_alw, '.2f'), format_cell_right)
            sheet.write(row, col + 11, format(project_alw, '.2f'), format_cell_right)
            sheet.write(row, col + 12, format(other_alw, '.2f'), format_cell_right)
            sheet.write(row, col + 13, format(gross, '.2f'), format_cell_right)
            sheet.write(row, col + 14, self.get_working_days(employee_id=slip_id.employee_id, batch_id=batch_id), format_cell_center)
            sheet.write(row, col + 15, format(act_exp_add, '.2f'), format_cell_right)
            sheet.write(row, col + 16, format(act_ot_add, '.2f'), format_cell_right)
            sheet.write(row, col + 17, format(tot_add, '.2f'), format_cell_right)
            sheet.write(row, col + 18, format(med_ins_ded, '.2f'), format_cell_right)
            sheet.write(row, col + 19, format(gosi_cont_ded, '.2f'), format_cell_right)
            sheet.write(row, col + 20, format(tot_ded, '.2f'), format_cell_right)
            sheet.write(row, col + 21, format(act_net_sal, '.2f'), format_cell_right)
            sheet.write(row, col + 22, allowance or '', format_cell_center)
            sheet.write(row, col + 23, deduction or '', format_cell_center)
            row += 1

        sheet.write(row, 4, "Total", format_signature_1)
        sheet.write(row, 5, " ", format_cell_right_1)
        col = 6
        sheet.write(row, col, format(tot_basic, '.2f'), format_cell_right_1)
        sheet.write(row, col + 1, format(tot_housing_alw, '.2f'), format_cell_right_1)
        sheet.write(row, col + 2, format(tot_transport_alw, '.2f'), format_cell_right_1)
        sheet.write(row, col + 3, format(tot_phone_alw, '.2f'), format_cell_right_1)
        sheet.write(row, col + 4, format(tot_tools_alw, '.2f'), format_cell_right_1)
        sheet.write(row, col + 5, format(tot_project_alw, '.2f'), format_cell_right_1)
        sheet.write(row, col + 6, format(tot_other_alw, '.2f'), format_cell_right_1)
        sheet.write(row, col + 7, format(tot_gross, '.2f'), format_cell_right_1)
        sheet.write(row, col + 8, " ", format_cell_right_1)
        sheet.write(row, col + 9, format(tot_act_exp_add, '.2f'), format_cell_right_1)
        sheet.write(row, col + 10, format(tot_act_ot_add, '.2f'), format_cell_right_1)
        sheet.write(row, col + 11, format(fin_tot_add, '.2f'), format_cell_right_1)
        sheet.write(row, col + 12, format(tot_med_ins_ded, '.2f'), format_cell_right_1)
        sheet.write(row, col + 13, format(tot_gosi_cont_ded, '.2f'), format_cell_right_1)
        sheet.write(row, col + 14, format(fin_tot_ded, '.2f'), format_cell_right_1)
        sheet.write(row, col + 15, format(tot_act_net_sal, '.2f'), format_cell_right_1)

        row += 3

        sheet.write(row, 1, "Payroll Officer", format_signature)
        sheet.write(row, 3, "CX", format_signature)
        sheet.write(row, 7, "HR Manager", format_signature)
        sheet.write(row, 11, "Finance", format_signature)
        sheet.write(row, 15, "HR Director", format_signature)
        # sheet.write(row, 7, "CEO", format_signature)

        ####################################################################
        from odoo.modules.module import get_module_resource
        from io import BytesIO

        file = open(get_module_resource('hr_payroll_report', 'static/img', 'flintlogo.png'), 'rb')
        data = BytesIO(file.read())
        file.close()

        x_scale = 0.3
        y_scale = 0.3

        sheet.insert_image('A2', 'IMG', {'image_data': data, 'x_scale': x_scale, 'y_scale': y_scale})
        ####################################################################

    def get_working_days(self, employee_id, batch_id):
        contract = employee_id.contract_id

        contract_start = contract.date_start
        contract_end = contract.date_end

        payslip = batch_id.slip_ids.filtered(lambda x:x.employee_id.id == employee_id.id and x.state not in ('draft','cancel'))

        if len(payslip) > 1:
            raise UserError(_('More than one payslip found for this employee. Please check the payslip dates.'))
        else: payslip = payslip[0]

        date_start = payslip.date_from
        date_end = payslip.date_to

        payslip_days = (date_end - date_start).days
        if contract.resource_calendar_id:
            month_res = contract.resource_calendar_id.get_month_days_and_hours_calendar(payslip.date_to)
            payslip_days = month_res.get('days', payslip_days)

            if contract.resource_calendar_id.no_of_days_in_month == 'standard_30' and payslip_days > 30:
                payslip_days = 30

        update_rate = False
        if contract_start > date_start:
            date_start = contract_start
            update_rate = True
        if contract_end and contract_end < date_end:
            date_end = contract_end
            update_rate = True

        if update_rate:
            payslip_days = (date_end - date_start).days + 1
            if contract.resource_calendar_id.no_of_days_in_month == 'standard_30' and not update_rate: #bcz payslip runs for 31st
                payslip_days -= 1

        return payslip_days - self._get_absent_days(payslip)

    def _get_absent_days(self, payslip):
        absent_days = 0
        hours = sum(payslip.worked_days_line_ids.filtered(lambda l: l.work_entry_type_id.code=='ABSDED').mapped('number_of_hours'))
        if hours:
            absent_days = int(round(hours,0) / payslip.contract_id.resource_calendar_id.hours_per_day)
        return absent_days
