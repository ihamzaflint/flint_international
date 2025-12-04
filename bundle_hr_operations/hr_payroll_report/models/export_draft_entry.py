# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from collections import defaultdict

from markupsafe import Markup
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero, plaintext2html


class ExportDraftEntryXlsx(models.AbstractModel):
    _name = 'report.hr_payroll_report.export_draft_entry_report'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Export Draft Entry Report'

    def generate_xlsx_report(self, workbook, data, records):
        sheet = workbook.add_worksheet('Sheet1')
        precision = self.env['decimal.precision'].precision_get('Payroll')
        batch = self.env['hr.payslip.run'].browse(data['batch_id'])
        payslips = self.env['hr.payslip'].search([('payslip_run_id','=',batch.id)])

        payslips_to_post = payslips.filtered(lambda slip: not slip.payslip_run_id)

        # Adding pay slips from a batch and deleting pay slips with a batch that is not ready for validation.
        payslip_runs = (payslips - payslips_to_post).mapped('payslip_run_id')
        for run in payslip_runs:
            # if run._are_payslips_ready():
            payslips_to_post |= run.slip_ids

        # A payslip need to have a done state and not an accounting move.
        # payslips_to_post = payslips_to_post.filtered(lambda slip: slip.state == 'done' and not slip.move_id)
        payslips_to_post = payslips_to_post.filtered(lambda slip: slip.state == 'verify')

        # Check that a journal exists on all the structures
        if any(not payslip.struct_id for payslip in payslips_to_post):
            raise ValidationError(_('One of the contract for these payslips has no structure type.'))
        if any(not structure.journal_id for structure in payslips_to_post.mapped('struct_id')):
            raise ValidationError(_('One of the payroll structures has no account journal defined on it.'))

        # Map all payslips by structure journal and pay slips month.
        # {'journal_id': {'month': [slip_ids]}}
        slip_mapped_data = defaultdict(lambda: defaultdict(lambda: self.env['hr.payslip']))
        for slip in payslips_to_post:
            slip_mapped_data[slip.struct_id.journal_id.id][fields.Date().end_of(slip.date_to, 'month')] |= slip

        line_ids = []
        for journal_id in slip_mapped_data: # For each journal_id.
            for slip_date in slip_mapped_data[journal_id]: # For each month.
                line_ids = []
                debit_sum = 0.0
                credit_sum = 0.0
                date = slip_date
                move_dict = {
                    'narration': '',
                    'ref': date.strftime('%B %Y'),
                    'journal_id': journal_id,
                    'date': date,
                }

                for slip in slip_mapped_data[journal_id][slip_date]:
                    move_dict['narration'] += plaintext2html(slip.number or '' + ' - ' + slip.employee_id.name or '')
                    move_dict['narration'] += Markup('<br/>')
                    for line in slip.line_ids.filtered(lambda line: line.category_id):
                        amount = line.total
                        if line.code == 'NET': # Check if the line is the 'Net Salary'.
                            for tmp_line in slip.line_ids.filtered(lambda line: line.category_id):
                                if tmp_line.salary_rule_id.not_computed_in_net: # Check if the rule must be computed in the 'Net Salary' or not.
                                    if amount > 0:
                                        amount -= abs(tmp_line.total)
                                    elif amount < 0:
                                        amount += abs(tmp_line.total)
                        if float_is_zero(amount, precision_digits=precision):
                            continue
                        debit_account_id = line.salary_rule_id.account_debit.id
                        credit_account_id = line.salary_rule_id.account_credit.id

                        if debit_account_id: # If the rule has a debit account.
                            debit = amount if amount > 0.0 else 0.0
                            credit = -amount if amount < 0.0 else 0.0

                            debit_line = slip._get_existing_lines(
                                line_ids, line, debit_account_id, debit, credit)

                            if not debit_line:
                                debit_line = slip._prepare_line_values(line, debit_account_id, date, debit, credit)
                                line_ids.append(debit_line)
                            else:
                                debit_line['debit'] += debit
                                debit_line['credit'] += credit

                        if credit_account_id: # If the rule has a credit account.
                            debit = -amount if amount < 0.0 else 0.0
                            credit = amount if amount > 0.0 else 0.0
                            credit_line = slip._get_existing_lines(
                                line_ids, line, credit_account_id, debit, credit)

                            if not credit_line:
                                credit_line = slip._prepare_line_values(line, credit_account_id, date, debit, credit)
                                line_ids.append(credit_line)
                            else:
                                credit_line['debit'] += debit
                                credit_line['credit'] += credit

                for line_id in line_ids: # Get the debit and credit sum.
                    debit_sum += line_id['debit']
                    credit_sum += line_id['credit']

                print("debit_sum: ",debit_sum)
                print("credit_sum: ",credit_sum)
                # The code below is called if there is an error in the balance between credit and debit sum.
                acc_id = slip.sudo().journal_id.default_account_id.id
                if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
                    if not acc_id:
                        raise UserError(_('The Expense Journal "%s" has not properly configured the Credit Account! \n Debit=%s, Credit=%s') % (slip.journal_id.name,round(debit_sum,2),round(credit_sum,2)))
                    existing_adjustment_line = (
                        line_id for line_id in line_ids if line_id['name'] == _('Adjustment Entry')
                    )
                    adjust_credit = next(existing_adjustment_line, False)

                    if not adjust_credit:
                        adjust_credit = {
                            'name': _('Adjustment Entry'),
                            'partner_id': False,
                            'account_id': acc_id,
                            'journal_id': slip.journal_id.id,
                            'date': date,
                            'debit': 0.0,
                            'credit': debit_sum - credit_sum,
                        }
                        line_ids.append(adjust_credit)
                    else:
                        adjust_credit['credit'] = debit_sum - credit_sum

                elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
                    if not acc_id:
                        raise UserError(_('The Expense Journal "%s" has not properly configured the Debit Account!! \n Debit=%s, Credit=%s') % (slip.journal_id.name,debit_sum,credit_sum))
                    existing_adjustment_line = (
                        line_id for line_id in line_ids if line_id['name'] == _('Adjustment Entry')
                    )
                    adjust_debit = next(existing_adjustment_line, False)

                    if not adjust_debit:
                        adjust_debit = {
                            'name': _('Adjustment Entry'),
                            'partner_id': False,
                            'account_id': acc_id,
                            'journal_id': slip.journal_id.id,
                            'date': date,
                            'debit': credit_sum - debit_sum,
                            'credit': 0.0,
                        }
                        line_ids.append(adjust_debit)
                    else:
                        adjust_debit['debit'] = credit_sum - debit_sum

                # Add accounting lines in the move
                print("line_idsssssss: ",line_ids)
                # stop
                # move_dict['line_ids'] = [(0, 0, line_vals) for line_vals in line_ids]

        Account = self.env['account.account']
        Partner = self.env['res.partner']
        AnalyticAccount = self.env['account.analytic.account']
        if line_ids:
            format_head = workbook.add_format({'bold': False, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'bg_color': '#bfbfbf', 'border': 1})
            format_cell_center = workbook.add_format({'bold': False, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'bg_color': 'white', 'border': 1, })
            format_cell_left = workbook.add_format({'bold': False, 'font_color': 'black', 'align': 'left', 'valign': 'vcenter', 'bg_color': 'white', 'border': 1, })
            format_cell_right = workbook.add_format({'bold': False, 'font_color': 'black', 'align': 'right', 'valign': 'vcenter', 'bg_color': 'white', 'border': 1, })
            format_cell_center_date = workbook.add_format({'bold': False, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'bg_color': 'white', 'border': 1, 'num_format': 'dd/mm/yyyy'})
            format_center = workbook.add_format({'bold': False, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'bg_color': 'white', 'border': 1})
            format_signature = workbook.add_format({'bold': True, 'underline': True, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'bg_color': 'white', 'border': 1, })

            row = 1

            sheet.merge_range(row, 0, row, 1, 'Period', format_head)
            row += 1
            sheet.merge_range(row, 0, row, 1, '%s - %s' % (
            fields.Date.from_string(data['date_start']).strftime('%d %B %Y'),
            fields.Date.from_string(data['date_end']).strftime('%d %B %Y')), format_center)

            row += 1
            sheet.merge_range(row, 0, row, 1, 'Project Name', format_head)
            row += 1
            sheet.merge_range(row, 0, row, 1, batch.name, format_center)
            row += 1

            col_name = 0
            col_partner = 1
            col_account = 2
            col_analytic_account = 3
            col_debit = 4
            col_credit = 5
            sheet.set_column(col_name, col_name, 30)
            sheet.set_column(col_partner, col_partner, 15)
            sheet.set_column(col_account, col_account, 30)
            sheet.set_column(col_analytic_account, col_analytic_account, 30)
            sheet.set_column(col_debit, col_debit, 15)
            sheet.set_column(col_credit, col_credit, 15)

            sheet.write(row, col_name, "Name", format_head)
            sheet.write(row, col_partner, "Partner", format_head)
            sheet.write(row, col_account, "Account", format_head)
            sheet.write(row, col_analytic_account, "Analytic Account(Project)", format_head)
            sheet.write(row, col_debit, "Debit", format_head)
            sheet.write(row, col_credit, "Credit", format_head)
            row += 1

            for line in line_ids:
                account = Account.browse(int(line.get('account_id'))).name
                partner_name=''
                partner_id = line.get('partner_id',False)
                if partner_id:
                    partner_name = Partner.browse(int(partner_id)).name

                analytic_name=''
                analytic_account_id = line.get('analytic_account_id',False)
                if analytic_account_id:
                    analytic_name = AnalyticAccount.browse(int(analytic_account_id)).name

                sheet.write(row, col_name, line.get('name'), format_cell_left)
                sheet.write(row, col_partner, partner_name, format_cell_left)
                sheet.write(row, col_account, account, format_cell_left)
                sheet.write(row, col_analytic_account, analytic_name, format_cell_left)
                sheet.write(row, col_debit, line.get('debit',0), format_cell_left)
                sheet.write(row, col_credit, line.get('credit',0), format_cell_left)
                row += 1

        return True
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
        for sal_rule in list(set([x[col_sal_rule] for x in fetched])):
            self._cr.execute("SELECT sequence,code FROM hr_salary_rule where name=%s;", [sal_rule])
            sal_rule_data = self._cr.fetchall()
            code = sal_rule_data[0][1] if sal_rule_data else False
            if code and code=='GOSI':   # no need to show GOSI Total Salary in export
                continue
            sequence_data[sal_rule] = sal_rule_data[0][0] if sal_rule_data else self.env['hr.salary.rule'].search([('name', '=', sal_rule)])[0].sequence
            if not sequence_data[sal_rule]:
                raise UserWarning("Cannot find salary rule details. %s" % sal_rule)

            # print(sequence_data[sal_rule])

        sal_rules = [x[0] for x in sorted(sequence_data.items(), key=lambda x: x[1])]

        employee_ids = batch_id.slip_ids.mapped('employee_id')

        col_employee_code = 0
        col_employee_name = 1
        col_employee_iqama = 2
        col_contract_start_date = 3
        col_contract_end_date = 4
        col_project = 5
        col_department = 6

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
        sheet.merge_range(row, 0, row, 1, '%s - %s' % (fields.Date.from_string(data['date_start']).strftime('%d %B %Y'), fields.Date.from_string(data['date_end']).strftime('%d %B %Y')), format_center)

        row += 1
        sheet.merge_range(row, 0, row, 1, 'Project Name', format_head)
        row += 1
        sheet.merge_range(row, 0, row, 1, batch_id.name, format_center)

        row += 2
        sheet.set_column(col_employee_code, col_employee_code, 15)
        sheet.set_column(col_employee_name, col_employee_name, 40)
        sheet.set_column(col_employee_iqama, col_employee_iqama, 15)
        sheet.set_column(col_contract_start_date, col_contract_start_date, 12)
        sheet.set_column(col_contract_end_date, col_contract_end_date, 12)
        sheet.set_column(col_project, col_project, 30)
        sheet.set_column(col_department, col_department, 30)

        sheet.write(row, col_employee_code, "Emp_Code", format_head)
        sheet.write(row, col_employee_name, "Name", format_head)
        sheet.write(row, col_employee_iqama, "Iqama Number", format_head)
        sheet.write(row, col_contract_start_date, "Start Date", format_head)
        sheet.write(row, col_contract_end_date, "End Date", format_head)
        sheet.write(row, col_project, "Project", format_head)
        sheet.write(row, col_department, "Department", format_head)

        col = col_department
        for sal_rule in sal_rules:
            col += 1
            sheet.set_column(col, col, 30)
            sheet.write(row, col, sal_rule, format_head)

        col += 1
        sheet.set_column(col, col, 15)
        sheet.write(row, col, "Working Days", format_head)

        for sal_rule in sal_rules:
            col += 1
            sheet.set_column(col, col, 30)
            sheet.write(row, col, "Actual - " + sal_rule, format_head)

        for employee_id in employee_ids:
            row += 1

            sheet.write(row, col_employee_code, employee_id.registration_number or "", format_cell_center)
            sheet.write(row, col_employee_name, employee_id.name or "", format_cell_center)
            sheet.write(row, col_employee_iqama, employee_id.visa_no or "", format_cell_center)
            sheet.write(row, col_contract_start_date, employee_id.contract_id.date_start or "", format_cell_center_date)
            sheet.write(row, col_contract_end_date, employee_id.contract_id.date_end or "", format_cell_center_date)
            sheet.write(row, col_project, employee_id.contract_id.analytic_account_id.name or "", format_cell_center)
            sheet.write(row, col_department, employee_id.department_id.name or "", format_cell_center)

            grouped_by_employee = group_by(fetched, col=col_employee)

            col = col_department
            for sal_rule in sal_rules:
                col += 1
                cell_data = [x for x in grouped_by_employee[employee_id.id] if x[col_sal_rule] == sal_rule]
                amount_scheduled = sum([x[col_amount_scheduled] for x in cell_data])
                sheet.write(row, col, format(amount_scheduled, '.2f'), format_cell_right)

            col += 1
            sheet.write(row, col, self.get_working_days(employee_id=employee_id, batch_id=batch_id), format_cell_center)

            for sal_rule in sal_rules:
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

        payslip_days = (date_end - date_start).days + 1

        update_rate = False
        if contract_start > date_start:
            date_start = contract_start
            update_rate = True
        if contract_end and contract_end < date_end:
            date_end = contract_end
            update_rate = True

        if update_rate:
            payslip_days = (date_end - date_start).days + 1

        return payslip_days - self._get_absent_days(payslip)

    def _get_absent_days(self, payslip):
        absent_days = 0
        hours = sum(payslip.worked_days_line_ids.filtered(lambda l: l.work_entry_type_id.code=='ABSDED').mapped('number_of_hours'))
        if hours:
            absent_days = int(hours / payslip.contract_id.resource_calendar_id.hours_per_day)
        return absent_days
