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
import calendar
from datetime import datetime
from odoo import fields, models, _
from odoo.exceptions import UserError


class HrPayrollReport2(models.Model):
    _name = "hr.payroll.report2"
    _description = 'Hr Payroll Report2'

    employee_id = fields.Many2one('hr.employee', string='Employee')
    salary_rule_id = fields.Many2one('hr.salary.rule')  # ARCHIVED
    salary_rule_name = fields.Char(string='Rule')
    amount = fields.Float(string='Amount')
    amount_org = fields.Float("Amount Original")
    amount_scheduled = fields.Float(string='Scheduled Amount')
    slip_id = fields.Many2one('hr.payslip', string='Pay Slip')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Project')
    department_id = fields.Many2one('hr.department', string='Department')


    # def init(self):
    #     query = """
    #         SELECT
    #             p.id as id,
    #             e.id as employee_id
    #         FROM
    #             (SELECT * FROM hr_payslip) p
    #                 left join hr_employee e on (p.employee_id = e.id)
    #
    #         """
    #     #
    #     # print(122)
    #     tools.drop_view_if_exists(self.env.cr, self._table)
    #     self.env.cr.execute(sql.SQL("CREATE or REPLACE VIEW {} as ({})").format(sql.Identifier(self._table), sql.SQL(query)))


class HrPayrollReportWizard(models.TransientModel):
    _name = "hr.payroll.report2.wizard"
    _description = 'Hr Payroll Report2 Wizard'

    def _get_default_vals(self):
        today = datetime.now().date()
        return {
            'date_from': today.replace(day=1),
            'date_to': today.replace(day=calendar.monthrange(today.year, today.month)[1]),
        }

    date_from = fields.Date(string='From', default=lambda self: self._get_default_vals()['date_from'])
    date_to = fields.Date(string='To', default=lambda self: self._get_default_vals()['date_to'])
    payslip_run_id = fields.Many2one('hr.payslip.run', string='Batch')

    def button_open_report(self):
        action = self.env.ref('hr_payroll_report.payroll_report_action2').read()[0]
        self.sudo().setup_report()
        return action

    def setup_report(self):
        _table = self.env['hr.payroll.report2']._table

        self._cr.execute("DELETE FROM {};".format(_table))
        if self.payslip_run_id:
            self._cr.execute("SELECT p.id,p.employee_id,c.analytic_account_id, p.department_id FROM hr_payslip p, hr_contract c where p.contract_id=c.id and p.state!=%s and p.payslip_run_id=%s",['cancel',self.payslip_run_id.id])
        else:
            if not self.date_from or not self.date_to:
                raise UserError(_('Please select date from and date To!'))
            self._cr.execute(
                "SELECT p.id,p.employee_id,c.analytic_account_id, p.department_id FROM hr_payslip p, hr_contract c where p.contract_id=c.id and p.state!=%s and p.date_from>=%s and p.date_to<=%s",
                ['cancel', self.date_from, self.date_to])

        for slip in self._cr.fetchall():
            slip_id = slip[0]
            employee_id = slip[1]
            analytic_account_id = slip[2]
            department_id = slip[3]
            # date_from = slip[2]
            # date_to = slip[3]
            # state = slip[3]

            # if state in ['cancel']:
            #     continue
            #
            # if all([
            #     date_from < self.date_from,
            #     date_to < self.date_from,
            # ]):
            #     continue
            #
            # if all([
            #     date_from > self.date_to,
            #     date_to > self.date_to,
            # ]):
            #     continue

            # self._cr.execute("SELECT id,salary_rule_id,total,amount FROM hr_payslip_line WHERE slip_id={};".format(slip_id))
            self._cr.execute("SELECT id,salary_rule_id,total,amount,amount_org FROM hr_payslip_line WHERE slip_id={};".format(slip_id))
            for line in self._cr.fetchall():
                line_id, salary_rule_id, amount, amount_scheduled, amount_org = line

                salary_rule_name = self.env['hr.salary.rule'].browse(salary_rule_id).name

                query = "INSERT INTO {}(slip_id,employee_id,salary_rule_name,amount,amount_scheduled, analytic_account_id, department_id, amount_org) VALUES ({},{},\'{}\',{}, {}, {}, {}, {});".format(_table, slip_id, employee_id, salary_rule_name, amount, amount_scheduled or 0, analytic_account_id or 'Null', department_id or "Null", amount_org or 0)
                # print(query)
                self._cr.execute(query)


