# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import time
import datetime


class OtherHrPayslipType(models.Model):
    _name = 'other.hr.payslip.type'
    _description = "Other HR Payslip Type"

    name = fields.Char(string="Type Name", required=True)
    mode = fields.Selection([('add', 'Add'), ('deduct', 'Deduct')], string="Mode", required=True)
    rule_id = fields.Many2one('hr.salary.rule', required=True, domain=[('amount_select', '=', 'adjustment')])
    active = fields.Boolean(related="rule_id.active", readonly=True)
    struct_ids = fields.Many2many('hr.payroll.structure', string='Availability in Structure',
        help='This input will be only available in those structure. If empty, it will be available in all payslip.')


class OtherHrPayslip(models.Model):
    _name = 'other.hr.payslip'
    _inherit = ['mail.thread']
    _description = "Other HR Payslip"

    name = fields.Char(required=True, translate=True, string='Name')
    amount = fields.Float('Amount')
    no_of_days = fields.Float('No of Days')
    operation_type = fields.Selection([('allowance', 'Allowance'), ('deduction', 'Deduction')],
                                      string='Mode', default='allowance', required=True)
    adjustment_type_id = fields.Many2one('other.hr.payslip.type', string='Type', required=True)
    calc_type = fields.Selection([('amount', 'By Amount'), ('days', 'By Days'), ('hours', 'By Hours'), ('percentage', 'By Percentage')],
                                 string='Calculation Type', required=True, default='amount')
    country_id = fields.Many2one('res.country', 'Country')
    no_of_hours = fields.Float(string='No of Hours')
    percentage = fields.Float(string='Percentage')
    date = fields.Date('Date', required=True, default=lambda *a: time.strftime('%Y-%m-%d'))
    description = fields.Text('Description')
    approved_date = fields.Date('Approved On', readonly=True, copy=False)
    approved_uid = fields.Many2one('res.users', string='Approved By', readonly=True, copy=False)
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True)
    payslip_line_id = fields.Many2one('hr.payslip.line', readonly=True, string='Payslip Line', copy=False)
    payslip_id = fields.Many2one('hr.payslip', related='payslip_line_id.slip_id', string="Payslip", readonly=True)
    department_id = fields.Many2one('hr.department', readonly=True, string='Department')
    struct_id = fields.Many2one('hr.payroll.structure', readonly=True, string='Structure')
    daily_wage = fields.Monetary('Daily Wage')
    hourly_wage = fields.Monetary('Hourly Wage')
    wage = fields.Monetary('Wage')
    state = fields.Selection([('draft', 'Draft'),
                              ('done', 'Done')], string='State', default='draft', tracking=True)
    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one(string="Currency", related='company_id.currency_id', readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Project')

    # @api.multi
    def unlink(self):
        """
            To remove the record, which is not in 'done' states
        """
        for line in self:
            if line.state in ['done']:
                raise UserError(_('You cannot remove the record which is in %s state!') % line.state)
        return super(OtherHrPayslip, self).unlink()

    @api.onchange('calc_type', 'date')
    def _onchange_calc_type(self):
        self.amount = 0.0
        contract = self.employee_id.sudo()._get_contracts(self.date, self.date, states=['open'])[:1]

        # no_of_days_in_month = contract.resource_calendar_id and contract.resource_calendar_id.get_month_days()
        # consider full month alwasy, so taking last day of month
        target_date = self.date
        next_month = target_date.replace(day=28) + datetime.timedelta(days=4)
        target_date = next_month - datetime.timedelta(days=next_month.day)
        month_res = contract.resource_calendar_id.get_month_days_and_hours_calendar(target_date)
        no_of_days_in_month = month_res.get('days', 30)

        wage = contract.wage + contract.l10n_sa_housing_allowance + contract.l10n_sa_transportation_allowance + contract.l10n_sa_other_allowances + contract.phone_allowance + contract.tools_allowance + contract.tickets_allowance + contract.eos_payment_allowance + contract.annual_leave_vacation_amount_allowance + contract.tech_allowance + contract.kids_allowance + contract.granted_monthly_bonus + contract.special_allowance + contract.niche_skill_allowance + contract.shift_allowance + contract.car_allowance + contract.gas_allowance + contract.oc_rec_allowance + contract.project_allowance + contract.food_allowance + contract.edu_allowance
        if self.calc_type == 'days':
            self.daily_wage = wage / no_of_days_in_month
            self.no_of_days = 0
            
        elif self.calc_type == 'hours':
            self.hourly_wage = wage / no_of_days_in_month / contract.resource_calendar_id.hours_per_day
            self.no_of_hours = 0

        elif self.calc_type == 'percentage':
            self.wage = wage
            self.percentage = 0

    @api.onchange('daily_wage','no_of_days')
    def _onchange_wage_daily(self):
        self.amount = self.daily_wage * self.no_of_days

    @api.onchange('hourly_wage', 'no_of_hours')
    def _onchange_wage_hourly(self):
        self.amount = self.hourly_wage * self.no_of_hours

    @api.onchange('wage', 'percentage')
    def _onchange_wage_percentage(self):
        self.amount = self.wage * self.percentage / 100.0

    @api.onchange('employee_id','date')
    def onchange_employee(self):
        """
            onchange the value based on selected employee
            department and company
        """
        self.department_id = False
        self.struct_id = False
        if self.employee_id:
            self.department_id = self.employee_id.department_id.id
            contracts = self.employee_id._get_contracts(self.date, self.date)
            if contracts:
                self.struct_id = contracts[0].structure_type_id.default_struct_id
                self.company_id = self.employee_id.company_id.id

    @api.onchange('adjustment_type_id')
    def onchange_adjustment(self):
        self.operation_type = {'deduct': 'deduction',
                               'add': 'allowance',
                               }.get(self.adjustment_type_id.mode)

    @api.model
    def create(self, vals_list):
        """
            Create a new record
            :return: Newly created record ID
        """
        if vals_list.get('employee_id'):
            employee = self.env['hr.employee'].browse(vals_list['employee_id'])
            vals_list.update({'department_id': employee.department_id.id})
        return super(OtherHrPayslip, self).create(vals_list)

    def write(self, vals):
        """
            Update an existing record.
            :param values: updated values
            :return: Current update record ID
        """
        if vals.get('employee_id'):
            employee = self.env['hr.employee'].browse(vals['employee_id'])
            vals.update({'department_id': employee.department_id.id})
        return super(OtherHrPayslip, self).write(vals)

    # @api.multi
    def other_hr_payslip_done(self):
        """
            sent the status of other allowance/deduction request in Done state
        """
        for rec in self:
            if rec.state != "draft":
                raise UserError("The selected record \'%s\' is not in draft state !!" % rec.name)

            rec.state = 'done'
            rec.approved_uid = self._uid
            rec.approved_date = fields.Date.today()

    # @api.multi
    def set_draft(self):
        """
            sent the status of other allowance/deduction request in Set to Draft state
        """
        if self.filtered(lambda adjustment: adjustment.payslip_id):
            raise UserError(_("Cannot move to draft if payslip is linked to adjustment."))
        self.write({
            'state': 'draft',
            'approved_uid': False,
            'approved_date': False,
        })


