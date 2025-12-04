# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import UserError


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    amount_select = fields.Selection(selection_add=[('parameter', 'Parameter')],
                                     ondelete={'parameter': 'cascade'})
    parameter_id = fields.Many2one('hr.salary.parameter', string='Salary Parameter', ondelete='restrict')

    def _compute_rule(self, localdict):
        precision = self.env['decimal.precision'].precision_get('Payroll')
        self.ensure_one()
        res = super(HrSalaryRule, self)._compute_rule(localdict)
        local_payslip = localdict.get('payslip')
        contract = local_payslip.contract_id
        localdict[self.code+'_AMT'] = res[0]
        # if self.code == 'HOUSEALW':
        #     localdict['HOUSEALW_AMT'] = res[0]
        if self.code == 'BASIC':
            localdict['BASIC_AMT'] = contract.wage
        # if self.code == 'GOSI':
        #     amount = localdict.get('BASIC_AMT',0) + localdict.get('HOUSEALW_AMT',0)
        #     res = (amount, res[1], res[2])

        if self.amount_select == 'parameter':
            parameter = self.parameter_id

            month_days = 30
            month_res = {'days': month_days}
            if contract.resource_calendar_id:
                # month_days =contract.resource_calendar_id.get_month_days()
                month_res = contract.resource_calendar_id.get_month_days_and_hours_calendar(local_payslip.date_to)
                month_days = month_res.get('days',30)
            date_to = local_payslip.date_to


            if local_payslip.payslip_run_id and local_payslip.payslip_run_id.final_settlement_batch:
                date_to = local_payslip.contract_id.date_end
            payslip_days = (date_to - local_payslip.date_from).days + 1
            if contract.resource_calendar_id.no_of_days_in_month == 'no_of_working_days':
                payslip_days = month_res.get('days',payslip_days)

            if contract.resource_calendar_id.no_of_days_in_month == 'standard_30':
                payslip_days = 30

            # if emp joined in middle
            date_start = local_payslip.date_from
            date_end = local_payslip.date_to
            contract_start = contract.date_start
            contract_end = contract.date_end
            update_rate = False
            if contract_start > date_start:
                date_start = contract_start
                update_rate = True
            if contract_end and contract_end < date_end:
                date_end = contract_end
                update_rate = True
            if update_rate:
                payslip_days = (date_end - date_start).days + 1
                if contract.resource_calendar_id.no_of_days_in_month == 'standard_30' and not update_rate:  # bcz payslip runs for 31st
                    payslip_days -= 1
            amount = getattr(contract, parameter.field_id.name)
            amount = (amount / month_days) * payslip_days
            res = (amount, res[1], res[2])

            # if payroll running for past month, and increment is happened for next months
            # take old values from increment lines
            increment_lines = self.env['hr.salary.increment.line'].search([
                ('increment_field_id', '=', parameter.id),
                ('is_changed', '=', True),
                ('increment_id.state', '=', 'approved'),
                ('increment_id.contract_id', '=', contract.id),
                ('increment_id.effective_date', '>=', local_payslip.date_to),
            ], order='id desc')

            if increment_lines:
                amount = increment_lines[0].old_value
                amount = (amount / month_days) * payslip_days
                res = (amount, res[1], res[2])
            else:
                ### Check if increment line exist
                increment_lines = self.env['hr.salary.increment.line'].search([
                    ('increment_field_id','=',parameter.id),
                    ('is_changed','=',True),
                    ('increment_id.state','=','approved'),
                    # ('increment_id.salary_structure_updated','=',True),
                    ('increment_id.contract_id','=',contract.id),
                    ('increment_id.effective_date','>=',local_payslip.date_from),
                    ('increment_id.effective_date','<=',local_payslip.date_to),
                ])

                if increment_lines:
                    if not increment_lines[0].increment_id.salary_structure_updated:
                        raise UserError(_('Please run Salary Increment cron first!'))

                    effective_date = increment_lines[0].increment_id.effective_date
                    days = int(effective_date.strftime("%d")) - 1
                    if days <= 30:
                        new_value = ((30 - days) * increment_lines[0].new_value) / month_days
                        old_value = (days * increment_lines[0].old_value) / month_days
                        amount = old_value + new_value
                        amount = (amount / month_days) * payslip_days
                        res = (amount, res[1], res[2])

        # rate = self._get_rate(localdict, res[2])
        res = (round(res[0], precision), res[1], res[2])
        # res = (round(res[0], precision), res[1], rate)
        return res

    def _get_rate(self, localdict, rate):
        if self.code in ['EOSB','GOSI']:
            return rate
        # if self.code in ['EOSB','GROSS','NET','GOSI','GOSICC','SIC']:
        #     return rate
        payslip = localdict.get('payslip')
        contract = payslip.contract_id
        month_days = contract.resource_calendar_id.get_month_days()

        contract_start = contract.date_start
        contract_end = contract.date_end

        date_start = payslip.date_from
        date_end = payslip.date_to
        update_rate = False
        if contract_start > date_start:
            date_start = contract_start
            update_rate = True
        if contract_end and contract_end < date_end:
            date_end = contract_end
            update_rate = True

        if update_rate:
            payslip_days = (date_end - date_start).days + 1
            rate = (payslip_days / month_days) * 100
        return rate