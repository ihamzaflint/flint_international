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
from odoo import _, fields, models
import json
from dateutil import relativedelta
import logging
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    def export_payslips_xlsx(self):

        data = {
            'batch_id': self.id,
            'date_start': self.date_start,
            'date_end': self.date_end,
        }
        return self.env.ref('hr_payroll_report.action_payslips_export').report_action(self, data=data)

    def export_draft_entry(self):

        data = {
            'batch_id': self.id,
            'date_start': self.date_start,
            'date_end': self.date_end,
        }
        return self.env.ref('hr_payroll_report.action_export_draft_entry').report_action(self, data=data)

#     def action_open_payslip_report(self):
#         self.ensure_one()
#         action = self.env.ref('hr_payroll_report.payroll_report_action2_wizard').read()[0]
#         action['context'] = "{'default_payslip_run_id':%s}" % self.id
#         return action
#
#


class ExportPayslipXlsx(models.AbstractModel):
    _name = 'report.hr_payroll_report.export_payslips_report'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Export payslips Report'

    def generate_xlsx_report(self, workbook, data, records):
        sal_rules = []
        sheet = workbook.add_worksheet('Sheet1')
        batch_id = self.env['hr.payslip.run'].browse(data['batch_id'])

        self.env['hr.payroll.report2.wizard'].create({
            'date_from': batch_id.date_start,
            'date_to': batch_id.date_end,
            'payslip_run_id': batch_id.id,
        }).sudo().setup_report()

        table = self.env['hr.payroll.report2']._table

        self._cr.execute("SELECT analytic_account_id,department_id,employee_id,salary_rule_name,amount,amount_scheduled,amount_org FROM {};".format(table))
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
        col_amount_org = 6

        sequence_data = {}
        rule_info = {}
        for sal_rule in set(x[col_sal_rule] for x in fetched):
            try:
                self.env.cr.execute("""
                    SELECT id, sequence, code, amount_select, category_id
                    FROM hr_salary_rule
                    WHERE name->>'en_US' = %s AND active = TRUE
                    ORDER BY sequence
                """, (sal_rule,))
                sal_rule_data = self.env.cr.fetchone()

                if not sal_rule_data:
                    # Fallback to search if not found directly
                    rule = self.env['hr.salary.rule'].search([('name', '=', sal_rule), ('active', '=', True)], limit=1)
                    if not rule:
                        raise UserError(_("Cannot find salary rule details for %s") % sal_rule)
                    sal_rule_data = (rule.id, rule.sequence, rule.code, rule.amount_select, rule.category_id.id)

                rule_id, sequence, code, amount_select, category_id = sal_rule_data

                if code == 'GOSI':  # no need to show GOSI Total Salary in export
                    continue

                # Fetch the complete rule object
                rule = self.env['hr.salary.rule'].browse(rule_id)

                # Get the JSON representation of the rule
                rule_dict = rule.read(['id', 'name', 'sequence', 'code', 'amount_select', 'category_id'])[0]

                sequence_data[sal_rule] = sequence
                rule_info[sal_rule] = {
                    'sequence': sequence,
                    'code': code,
                    'amount_select': amount_select,
                    'category_id': category_id,
                    'rule_id': rule_id,
                    'rule': rule_dict
                }

                print(rule_dict)

            except Exception as e:
                _logger.error("Error processing salary rule %s: %s", sal_rule, str(e))
                continue
            sal_rules = [x[0] for x in sorted(sequence_data.items(), key=lambda x: x[1])]

        employee_ids = batch_id.slip_ids.mapped('employee_id')

        col_employee_code = 0
        col_employee_client = 1
        col_employee_name = 2
        col_employee_iqama = 3
        col_contract_start_date = 4
        col_contract_end_date = 5
        col_project = 6
        col_department = 7
        col_employee_iban = 8

        format_head = workbook.add_format({'bold': False, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'bg_color': '#bfbfbf', 'border': 1})
        format_cell_center = workbook.add_format({'bold': False, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'bg_color': 'white', 'border': 1, })
        format_cell_right = workbook.add_format({'bold': False, 'font_color': 'black', 'align': 'right', 'valign': 'vcenter', 'bg_color': 'white', 'border': 1, })
        format_cell_center_date = workbook.add_format({'bold': False, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'bg_color': 'white', 'border': 1, 'num_format': 'dd/mm/yyyy'})
        format_center = workbook.add_format({'bold': False, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'bg_color': 'white', 'border': 1})
        format_signature = workbook.add_format({'bold': True, 'underline': True, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'bg_color': 'white', 'border': 1, })

        row = 4
        # sheet.merge_range(row, 0, row, 1, 'EMPLOYEE PAY SLIP FOR THE MONTH', format_center)
        # sheet.merge_range(row, 0, row, 1, batch_id.name, format_center)
        # row += 2
        sheet.merge_range(row, 0, row, 1, 'Period', format_head)
        row += 1
        date_start = fields.Date.from_string(data['date_start']) if data['date_start'] else None
        date_end = fields.Date.from_string(data['date_end']) if data['date_end'] else None

        if date_start and date_end:
            sheet.merge_range(row, 0, row, 1, '%s - %s' % (date_start.strftime('%d %B %Y'), date_end.strftime('%d %B %Y')), format_center)
        else:
            sheet.merge_range(row, 0, row, 1, 'Date not available', format_center)

        row += 1
        sheet.merge_range(row, 0, row, 1, 'Project Name', format_head)
        row += 1
        sheet.merge_range(row, 0, row, 1, batch_id.name, format_center)

        row += 2
        sheet.set_column(col_employee_code, col_employee_code, 15)
        sheet.set_column(col_employee_client, col_employee_client, 15)
        sheet.set_column(col_employee_name, col_employee_name, 40)
        sheet.set_column(col_employee_iqama, col_employee_iqama, 15)
        sheet.set_column(col_contract_start_date, col_contract_start_date, 12)
        sheet.set_column(col_contract_end_date, col_contract_end_date, 12)
        sheet.set_column(col_project, col_project, 30)
        sheet.set_column(col_department, col_department, 30)
        sheet.set_column(col_employee_iban, col_employee_iban, 20)

        sheet.write(row, col_employee_code, "Emp_Code", format_head)
        sheet.write(row, col_employee_client, "Emp Client Id", format_head)
        sheet.write(row, col_employee_name, "Name", format_head)
        sheet.write(row, col_employee_iqama, "Iqama Number", format_head)
        sheet.write(row, col_contract_start_date, "Start Date", format_head)
        sheet.write(row, col_contract_end_date, "End Date", format_head)
        sheet.write(row, col_project, "Project", format_head)
        sheet.write(row, col_department, "Department", format_head)
        sheet.write(row, col_employee_iban, "IBAN", format_head)


        def filter_rules(rules, section):
            res = []
            for sal_rule in rules:
                sal_rule = str(sal_rule).strip()
                sal_rule = sal_rule.replace("'", "''")
                rule_data = rule_info[sal_rule]

                if section == "first_section":
                    if rule_data['amount_select'] == 'adjustment' or rule_data['code'] in ('SIC', 'NET', 'EOSP', 'GOSICC', 'EOSBFULL','EOSDIFF'):
                        continue
                    res.append(sal_rule)

                if section == "actual_allowances":
                    # if rule_data['sequence'] <= 100 and rule_data['amount_select'] != 'adjustment':

                    # category_code = self.env['hr.salary.rule.category'].browse(rule_data['category_id']).code

                    if rule_data['category_id'] in [self.env.ref('hr_payroll.COMP').id]:
                        continue
                    # if category_code == "COMP":
                    #     continue

                    if rule_data['category_id'] in [self.env.ref('hr_payroll.BASIC').id, self.env.ref('hr_payroll.ALW').id] and rule_data['amount_select'] != 'adjustment':
                        res.append(sal_rule)

                if section == "actual_deduction":
                    if rule_data['category_id'] in [self.env.ref('hr_payroll.DED').id] and rule_data['amount_select'] != 'adjustment':
                        res.append(sal_rule)

                if section == "actual_adjustment_addition":

                    if (rule_data['category_id'] == self.env.ref('hr_payroll.ALW').id and rule_data['amount_select'] == 'adjustment') or rule_data['code'] in ('OT,MOLOT'):
                        res.append(sal_rule)

                if section == "actual_adjustment_deduction":
                    # if rule_data['sequence'] >= 100 and rule_data['amount_select'] == 'adjustment':
                    if rule_data['category_id'] == self.env.ref('hr_payroll.DED').id and rule_data['amount_select'] == 'adjustment':
                        res.append(sal_rule)

                if section == "actual_net":
                    if rule_data['category_id'] in [self.env.ref('hr_payroll.NET').id] and rule_data['amount_select'] != 'adjustment':
                        res.append(sal_rule)

                if section == "company_contributions":

                    # category_code = self.env['hr.salary.rule.category'].browse(rule_data['category_id']).code
                    # if category_code == "COMP":
                    #     continue

                    if rule_data['category_id'] in [self.env.ref('hr_payroll.COMP').id] and rule_data['amount_select'] != 'adjustment':
                        res.append(sal_rule)

                if section == "eosb_full":
                    eosb_rule_categ = self.env['hr.salary.rule.category'].search([('code','=','EOSBFULL')])
                    # if rule_data['category_id'] == self.env.ref('hr_payroll.EOSBFULL').id:
                    if rule_data['category_id'] in eosb_rule_categ.ids:
                        res.append(sal_rule)

                if section == "eos_diff":
                    eos_diff_categ = self.env['hr.salary.rule.category'].search([('code','=','EOSDIFF')])
                    # if rule_data['category_id'] == self.env.ref('hr_payroll.EOSDIFF').id:
                    if rule_data['category_id'] in eos_diff_categ.ids:
                        res.append(sal_rule)

            return res

        col = col_department
        for sal_rule in filter_rules(sal_rules, "first_section"):
            col += 1
            sheet.set_column(col, col, 30)
            sheet.write(row, col, sal_rule, format_head)

        # for sal_rule in sal_rules:
        #     rule_data = rule_info[sal_rule]
        #     if rule_data['amount_select'] == 'adjustment' or rule_data['code'] in ('SIC','NET','EOSP','GOSICC'):
        #         continue
        #     col += 1
        #     sheet.set_column(col, col, 30)
        #     sheet.write(row, col, sal_rule, format_head)

        col += 1
        sheet.set_column(col, col, 15)
        sheet.write(row, col, "Working Days", format_head)

        for sal_rule in filter_rules(sal_rules, "actual_allowances"):
            col += 1
            sheet.set_column(col, col, 30)
            sheet.write(row, col, "Actual - " + sal_rule, format_head)

        # for sal_rule in sal_rules:
        #     col += 1
        #     sheet.set_column(col, col, 30)
        #     sheet.write(row, col, "Actual - " + sal_rule, format_head)

        for sal_rule in filter_rules(sal_rules, "actual_adjustment_addition"):
            col += 1
            sheet.set_column(col, col, 30)
            sheet.write(row, col, "Actual - " + sal_rule, format_head)

        col += 1
        sheet.set_column(col, col, 30)
        sheet.write(row, col, "Total Addition", format_head)

        for sal_rule in filter_rules(sal_rules, "actual_deduction"):
            col += 1
            sheet.set_column(col, col, 30)
            sheet.write(row, col, "Actual - " + sal_rule, format_head)

        for sal_rule in filter_rules(sal_rules, "actual_adjustment_deduction"):
            col += 1
            sheet.set_column(col, col, 30)
            sheet.write(row, col, "Actual - " + sal_rule, format_head)

        col += 1
        sheet.set_column(col, col, 30)
        sheet.write(row, col, "Total Deduction", format_head)

        for sal_rule in filter_rules(sal_rules, "actual_net"):
            col += 1
            sheet.set_column(col, col, 30)
            sheet.write(row, col, "Actual - " + sal_rule, format_head)

        for sal_rule in filter_rules(sal_rules, "company_contributions"):
            col += 1
            sheet.set_column(col, col, 30)
            sheet.write(row, col, sal_rule, format_head)

        col += 1
        sheet.set_column(col, col, 30)
        sheet.write(row, col, "Service Period Year", format_head)
        col += 1
        sheet.set_column(col, col, 30)
        sheet.write(row, col, "Service Period Months", format_head)
        col += 1
        sheet.set_column(col, col, 30)
        sheet.write(row, col, "Service Period Days", format_head)
        col += 1
        sheet.set_column(col, col, 30)
        sheet.write(row, col, "Total End of Service Benefit", format_head)
        col += 1
        sheet.set_column(col, col, 30)
        sheet.write(row, col, "EOS Difference", format_head)

        for employee_id in employee_ids:
            row += 1

            sheet.write(row, col_employee_code, employee_id.registration_number or "", format_cell_center)
            sheet.write(row, col_employee_client, employee_id.client_employee_id or "", format_cell_center)
            sheet.write(row, col_employee_name, employee_id.name or "", format_cell_center)
            sheet.write(row, col_employee_iqama, employee_id.visa_no or "", format_cell_center)
            sheet.write(row, col_contract_start_date, employee_id.contract_id.date_start or "", format_cell_center_date)
            sheet.write(row, col_contract_end_date, employee_id.contract_id.date_end or "", format_cell_center_date)
            sheet.write(row, col_project, employee_id.contract_id.analytic_account_id.name or "", format_cell_center)
            sheet.write(row, col_department, employee_id.department_id.name or "", format_cell_center)
            iban = employee_id.bank_account_id.acc_number if employee_id.bank_account_id else 'N/A'
            sheet.write(row, col_employee_iban, iban, format_cell_center)

            grouped_by_employee = group_by(fetched, col=col_employee)

            col = col_department
            for sal_rule in filter_rules(sal_rules, "first_section"):
                col += 1
                cell_data = [x for x in grouped_by_employee[employee_id.id] if x[col_sal_rule] == sal_rule]
                amount_scheduled = sum([x[col_amount_org] for x in cell_data])
                sheet.write(row, col, format(amount_scheduled, '.2f'), format_cell_right)

            #     for sal_rule in sal_rules:
            #         rule_data = rule_info[sal_rule]
            #         if rule_data['amount_select'] == 'adjustment' or rule_data['code'] in ('SIC', 'NET', 'EOSP', 'GOSICC'):
            #             continue
            #
            #         col += 1
            #         cell_data = [x for x in grouped_by_employee[employee_id.id] if x[col_sal_rule] == sal_rule]
            #         amount_scheduled = sum([x[col_amount_scheduled] for x in cell_data])
            #         sheet.write(row, col, format(amount_scheduled, '.2f'), format_cell_right)
            #
            col += 1
            sheet.write(row, col, self.get_working_days(employee_id=employee_id, batch_id=batch_id), format_cell_center)

            #     for sal_rule in sal_rules:
            #         col += 1
            #         cell_data = [x for x in grouped_by_employee[employee_id.id] if x[col_sal_rule] == sal_rule]
            #         amount = sum([x[col_amount] for x in cell_data])
            #         sheet.write(row, col, format(amount, '.2f'), format_cell_right)
            for sal_rule in filter_rules(sal_rules, "actual_allowances"):
                col += 1
                cell_data = [x for x in grouped_by_employee[employee_id.id] if x[col_sal_rule] == sal_rule]
                amount = sum([x[col_amount] for x in cell_data])
                sheet.write(row, col, format(amount, '.2f'), format_cell_right)

            total_adjustment_add = 0
            for sal_rule in filter_rules(sal_rules, "actual_adjustment_addition"):
                col += 1
                cell_data = [x for x in grouped_by_employee[employee_id.id] if x[col_sal_rule] == sal_rule]
                amount = sum([x[col_amount] for x in cell_data])
                total_adjustment_add += amount
                sheet.write(row, col, format(amount, '.2f'), format_cell_right)

            col += 1
            sheet.write(row, col, format(total_adjustment_add, '.2f'), format_cell_right)

            total_adjustment_ded = 0

            for sal_rule in filter_rules(sal_rules, "actual_deduction"):
                col += 1
                cell_data = [x for x in grouped_by_employee[employee_id.id] if x[col_sal_rule] == sal_rule]
                amount = sum([x[col_amount] for x in cell_data])
                total_adjustment_ded += amount
                sheet.write(row, col, format(amount, '.2f'), format_cell_right)

            for sal_rule in filter_rules(sal_rules, "actual_adjustment_deduction"):
                col += 1
                cell_data = [x for x in grouped_by_employee[employee_id.id] if x[col_sal_rule] == sal_rule]
                amount = sum([x[col_amount] for x in cell_data])
                total_adjustment_ded += amount
                sheet.write(row, col, format(amount, '.2f'), format_cell_right)

            col += 1
            sheet.write(row, col, format(total_adjustment_ded, '.2f'), format_cell_right)

            for sal_rule in filter_rules(sal_rules, "actual_net"):
                col += 1
                cell_data = [x for x in grouped_by_employee[employee_id.id] if x[col_sal_rule] == sal_rule]
                amount = sum([x[col_amount] for x in cell_data])
                sheet.write(row, col, format(amount, '.2f'), format_cell_right)

            for sal_rule in filter_rules(sal_rules, "company_contributions"):
                col += 1
                cell_data = [x for x in grouped_by_employee[employee_id.id] if x[col_sal_rule] == sal_rule]
                amount = sum([x[col_amount] for x in cell_data])
                sheet.write(row, col, format(amount, '.2f'), format_cell_right)

            ## insert Service period data
            col += 1
            service_period_res = self.get_service_period(employee_id=employee_id, batch_id=batch_id)
            sheet.write(row, col, service_period_res['years'], format_cell_right)
            col += 1
            sheet.write(row, col, service_period_res['months'], format_cell_right)
            col += 1
            sheet.write(row, col, service_period_res['days'], format_cell_right)

            for sal_rule in filter_rules(sal_rules, "eosb_full"):
                col += 1
                cell_data = [x for x in grouped_by_employee[employee_id.id] if x[col_sal_rule] == sal_rule]
                amount = sum([x[col_amount] for x in cell_data])
                sheet.write(row, col, format(amount, '.2f'), format_cell_right)
            for sal_rule in filter_rules(sal_rules, "eos_diff"):
                col += 1
                cell_data = [x for x in grouped_by_employee[employee_id.id] if x[col_sal_rule] == sal_rule]
                amount = sum([x[col_amount] for x in cell_data])
                sheet.write(row, col, format(amount, '.2f'), format_cell_right)

        row += 4

        sheet.write(row, 1, "Payroll Officer", format_signature)
        sheet.write(row, 3, "HR Manager", format_signature)
        sheet.write(row, 5, "HR Director", format_signature)
        sheet.write(row, 7, "CEO", format_signature)

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

    def get_service_period(self, employee_id, batch_id):
        contract = employee_id.contract_id
        payslip = batch_id.slip_ids.filtered(lambda x:x.employee_id.id == employee_id.id and x.state not in ('draft','cancel'))

        date_end = payslip.date_to
        start_date = contract.first_contract_date
        difference = relativedelta.relativedelta(date_end, start_date)
        res = {
            'years': difference.years,
            'months': difference.months,
            'days': int(difference.days),
        }
        return res


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
