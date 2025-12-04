from odoo import fields, models, _
from .browsable_object import BrowsableObject, InputLine, WorkedDays, Payslips

from odoo.tools import float_compare, float_is_zero, plaintext2html
from markupsafe import Markup
from collections import defaultdict
from odoo.exceptions import UserError, ValidationError


class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    def get_all_rules(self, payslip, localdict):
        return self.rule_ids, localdict


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def _prepare_payslip_line_vals(self, contract, rule, amount, qty, rate, localdict):
        precision = self.env['decimal.precision'].precision_get('Payroll')

        rule_codes = self._context.get('rule_codes',[])
        localdict = self._context.get('localdict',{})
        amt_dict = self._context.get('amt_dict', {})
        amt = amt_dict.get(rule.code + '_AMT', 0)
        if rule.amount_select == 'adjustment':  #its adjustment rule
            amt = amount
            amt_dict[rule.code + '_AMT'] = amount

        if rule.code == 'GOSI':
            amt = amt_dict.get('BASIC_AMT', 0) + amt_dict.get('HOUSEALW_AMT', 0)
            amt = min(amt, 45000)
            amt_dict['gosi_salary'] = amt
            amount = min(amt,amount)

        if rule.code in ('GROSS', 'NET'):
            amt = 0
            for rule_code in rule_codes:
                if rule_code in localdict.keys() and not rule_code in ('GOSI', 'GROSS', 'NET', 'BASIC', 'HOUSEALW'):
                    # print("rule_code: ",rule_code)
                    # print("amttt: ",amt_dict.get(rule_code+'_AMT', 0))
                    amt += amt_dict.get(rule_code+'_AMT', 0) or 0
            # amt += amt_dict.get('gosi_salary', 0)
            amt += (amt_dict.get('BASIC_AMT', 0) or 0) + (amt_dict.get('HOUSEALW_AMT', 0) or 0)

            # amount -= (amt_dict.get('BASIC_AMT') + amt_dict.get('HOUSEALW_AMT'))
            # amount += amt_dict.get('gosi_salary', 0)
        if rule.code == 'SIC':    # Social insurance contribution(GOSI)
            # amt = amt_dict.get('gosi_salary',amount) * -0.0975
            amt = (amt_dict.get('BASIC_AMT', 0) + amt_dict.get('HOUSEALW_AMT', 0)) * -0.0975
        if rule.code == 'GOSICC':
            # amt = amt_dict.get('gosi_salary',amount)
            amt = amt_dict.get('BASIC_AMT', 0) + amt_dict.get('HOUSEALW_AMT', 0)
            if contract.employee_id.country_id.code == 'SA':
                amt = amt * 0.1175
            else:
                amt = amt * 0.02

        return {
            'sequence': rule.sequence,
            'code': rule.code,
            'name': rule.name,
            'salary_rule_id': rule.id,
            'contract_id': contract.id,
            'employee_id': contract.employee_id.id,
            'amount_org': float(round(amt or 0,precision)),
            'amount': float(round(amount,precision)),
            'quantity': qty,
            'rate': rate,
            'slip_id': self.id,
            'total': float(round(amount * qty * rate / 100.0, precision)),
        }

    def _get_payslip_lines(self):
        precision = self.env['decimal.precision'].precision_get('Payroll')

        def _sum_salary_rule_category(localdict, category, amount):
            if category.parent_id:
                localdict = _sum_salary_rule_category(localdict, category.parent_id, amount)
            localdict['categories'].dict[category.code] = localdict['categories'].dict.get(category.code, 0) + amount
            return localdict

        all_results = []
        for payslip in self:
            result = {}
            rules_dict = {}
            worked_days_dict = {line.code: line for line in payslip.worked_days_line_ids if line.code}
            inputs_dict = {line.code: line for line in payslip.input_line_ids if line.code}

            employee = payslip.employee_id
            contract = payslip.contract_id
            amt_dict = {
                'gosi_salary': 0
            }

            localdict = {
                **payslip._get_base_local_dict(),
                **{
                    'categories': BrowsableObject(employee.id, {}, self.env),
                    'rules': BrowsableObject(employee.id, rules_dict, self.env),
                    'payslip': Payslips(employee.id, payslip, self.env),
                    'worked_days': WorkedDays(employee.id, worked_days_dict, self.env),
                    'inputs': InputLine(employee.id, inputs_dict, self.env),
                    'employee': employee,
                    'contract': contract
                }
            }

            rules, localdict = payslip.struct_id.get_all_rules(payslip, localdict)
            rule_codes = [rule.code for rule in rules]
            basic_rate = 100.0
            for rule in sorted(rules, key=lambda x: x.sequence):
                localdict.update({
                    'result': None,
                    'result_qty': 1.0,
                    'result_rate': 100
                })
                if rule._satisfy_condition(localdict):
                    amount, qty, rate = rule._compute_rule(localdict)
                    org_amount = localdict.get(rule.code + '_AMT')
                    previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
                    tot_rule = amount * qty * rate / 100.0
                    localdict[rule.code] = float(round(tot_rule, precision))
                    rules_dict[rule.code] = rule
                    localdict = _sum_salary_rule_category(localdict, rule.category_id, tot_rule - previous_amount)
                    if rule.code in ('HOUSEALW', 'BASIC'):
                        amt_dict['gosi_salary'] += (org_amount or 0)
                        amt_dict['gosi_salary'] = min(amt_dict['gosi_salary'], 45000)
                    amt_dict[rule.code + '_AMT'] = org_amount

                    payslip = payslip.with_context(
                        {'amt_dict': amt_dict, 'rule_codes': rule_codes, 'localdict': localdict,
                         'basic_rate': basic_rate})
                    result[rule.code] = payslip._prepare_payslip_line_vals(contract, rule, amount, qty, rate, localdict)

            all_results.extend(result.values())

        return all_results

    # inherited to Make Rounding of debit and credit

class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'

    amount_org = fields.Monetary(string='Amount Orginal', readonly=True, help='Orignal amount as per contract, for full month')
