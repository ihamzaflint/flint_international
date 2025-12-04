import time
from datetime import datetime

import babel
from dateutil import relativedelta
from odoo import api, fields, models, _
from odoo import tools
import logging

_logger = logging.getLogger(__name__)


class HrPayslipAttendance(models.Model):
    _name = 'hr.payslip.attendance'
    _description = 'Payslip Attendance'
    _order = 'payslip_id, sequence'

    name = fields.Char(string='Description', required=True)
    payslip_id = fields.Many2one('hr.payslip', string='Pay Slip', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(required=True, index=True, default=10)
    code = fields.Char(required=True, help="The code that can be used in the salary rules")
    number_of_days = fields.Float(string='Number of Days')
    number_of_hours = fields.Float(string='Number of Worked Hours')
    number_of_ot_hours = fields.Float(string='Number of Overtime Hours')
    number_of_ded_hours = fields.Float(string='Number of Deduction Hours')
    contract_id = fields.Many2one('hr.contract', string='Contract', required=True,
                                  help="The contract for which applied this input")


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    date_start = fields.Date(string='Date From', required=True, readonly=True,
                             default=lambda self: self.env['hr.payslip']._get_contract_date_from())
    date_end = fields.Date(string='Date To', required=True, readonly=True,
                           default=lambda self: self.env['hr.payslip']._get_contract_date_to())
    journal_id = fields.Many2one('account.journal', 'Salary Journal',
                                 readonly=True,
                                 required=True,
                                 default=lambda self: self.env['account.journal'].search([('name', 'ilike', 'salary')],
                                                                                         limit=1))


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    # @api.multi
    # def compute_sheet(self):
    #     for payslip in self:
    #         attendance_summaries = self.env['hr.attendance.summary'].search([
    #             ('employee_id', '=', payslip.employee_id.id),
    #             ('date_from', '>=', payslip.date_from),
    #             ('check_date', '<=', payslip.date_to),
    #             ('state','=','draft')
    #         ])
    #         payslip.attendance_summary_ids = [(6, 0, attendance_summaries.ids)]
    #         payslip.update_worked_days_lines()
    #
    #     res = super(HrPayslip, self).compute_sheet()
    #     return res

    # @api.depends('employee_id', 'contract_id', 'struct_id', 'date_from', 'date_to')
    # def _compute_worked_days_line_ids(self):
    #     if self.env.context.get('salary_simulation'):
    #         return
    #     valid_slips = self.filtered(lambda p: p.employee_id and p.date_from and p.date_to and p.contract_id and p.struct_id)
    #     # Make sure to reset invalid payslip's worked days line
    #     invalid_slips = self - valid_slips
    #     invalid_slips.worked_days_line_ids = [(5, False, False)]
    #     # Ensure work entries are generated for all contracts
    #     generate_from = min(p.date_from for p in self)
    #     current_month_end = date_utils.end_of(fields.Date.today(), 'month')
    #     generate_to = max(min(fields.Date.to_date(p.date_to), current_month_end) for p in self)
    #     self.mapped('contract_id')._generate_work_entries(generate_from, generate_to)
    #
    #     for slip in valid_slips:
    #         t = {'sequence': 25, 'work_entry_type_id': 1, 'number_of_days': 23.0, 'number_of_hours': 184.0}
    #         lines = slip._get_new_worked_days_lines()
    #         lines += t
    #         print("lines: ",lines)
    #
    #         slip.write({'worked_days_line_ids': lines})

    # @api.depends('employee_id', 'contract_id', 'struct_id', 'date_from', 'date_to')
    # def _compute_worked_days_line_ids(self):
    #     res = super(HrPayslip, self)._compute_worked_days_line_ids()
    #     print("ressss: ",res)
    #     print("self.worked_days_line_ids: ",self.worked_days_line_ids)
    #     return res

    # onchagne commented in 15
    # @api.onchange('employee_id', 'struct_id', 'contract_id', 'date_from', 'date_to')
    # def _onchange_employee(self):
    #     # res = super(HrPayslip, self)._onchange_employee()
    #     for payslip in self:
    #         attendance_summaries = self.env['hr.attendance.summary'].search([
    #             ('employee_id', '=', payslip.employee_id.id),
    #             ('date_from', '>=', payslip.date_from),
    #             ('check_date', '<=', payslip.date_to),
    #             ('state', '=', 'draft')
    #         ])
    #         payslip.attendance_summary_ids = [(6, 0, attendance_summaries.ids)]
    #         payslip.update_worked_days_lines()
    #
    #     return {}

    def update_worked_days_lines(self):
        precision = self.env['decimal.precision'].precision_get('Payroll')
        self.ensure_one()

        if not self.contract_id:
            return

        attendance_summaries = self.attendance_summary_ids
        # weekdays_overtime_hours = sum(attendance_summaries.mapped('weekdays_overtime_hours'))
        # weekend_overtime_hours = sum(attendance_summaries.mapped('weekend_overtime_hours'))
        # public_holiday_overtime_hours = sum(attendance_summaries.mapped('public_holiday_overtime_hours'))

        # weekdays_ot_work_entry = self.env.ref('hr_payroll_attendance.hr_work_entry_type_weekdays_overtime')
        # weekend_ot_work_entry = self.env.ref('hr_payroll_attendance.hr_work_entry_type_weekend_overtime')
        # public_holiday_ot_work_entry = self.env.ref('hr_payroll_attendance.hr_work_entry_type_public_holiday_overtime')

        # Remove Existing
        for summary in attendance_summaries:
            for line in summary.manual_line_ids:
                existing = self.worked_days_line_ids.filtered(
                    lambda x: x.work_entry_type_id.id == line.work_entry_type_id.id)
                existing.unlink()

        # Insert New
        lines = []
        for summary in attendance_summaries:
            for line in summary.manual_line_ids:
                lines.append({
                    'sequence': line.work_entry_type_id.sequence,
                    'work_entry_type_id': line.work_entry_type_id.id,
                    'number_of_days': 0,
                    'number_of_hours': line.no_of_hours,
                    'calc_rate': float(
                        round((line.work_entry_type_id.is_calculation and line.work_entry_type_id.calc_rate or 0),
                              precision)),
                })

        self.write({'worked_days_line_ids': [(0, 0, x) for x in lines]})

    # @api.multi
    # def refresh_payslip(self):
    #     # print "refresh_payslip claled ***********************"
    #     old_input_lines = self.env['hr.payslip'].browse(self.id).input_line_ids
    #     old_values = {}
    #     for old_input_line in old_input_lines:
    #         old_values[old_input_line.code] = old_input_line.amount
    #
    #     self.onchange_employee()
    #
    #     for input_line in self.input_line_ids:
    #         input_line.write({'amount': old_values.get(input_line.code,0.0) })
    #
    #     return True

    def _get_payslip_days(self):
        company_id = self.env.user.company_id.id
        # ir_values = self.env['ir.values']
        # payslip_day_from = ir_values.get_default('hr.payroll.config.settings', 'payslip_day_from_setting', company_id=company_id)
        # payslip_day_to = ir_values.get_default('hr.payroll.config.settings', 'payslip_day_to_setting', company_id=company_id)
    
        payslip_day_from = self.env['ir.config_parameter'].sudo().get_param('payslip_day_from_setting')
        payslip_day_to = self.env['ir.config_parameter'].sudo().get_param('payslip_day_to_setting')
    
        return payslip_day_from, payslip_day_to

    def _get_contract_date_from(self):
        user_obj = self.env['res.users']
        date_from = time.strftime('%Y-%m-01')
    
        payslip_day_from, payslip_day_to = self._get_payslip_days()
        if payslip_day_from and payslip_day_to:
            if int(payslip_day_from) < int(payslip_day_to):
                date_from = time.strftime('%Y-%m-' + str(payslip_day_from))
            else:
                date_from = str(datetime.now() + relativedelta.relativedelta(months=-1, day=int(payslip_day_from)))[:10]
        return date_from
    
    def _get_contract_date_to(self):
        user_obj = self.env['res.users']
        date_to = str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10]
    
        payslip_day_from, payslip_day_to = self._get_payslip_days()
        if payslip_day_from and payslip_day_to:
            date_to = time.strftime('%Y-%m-' + str(payslip_day_to))
    
        return date_to

    # date_from = fields.Date(string='Date From', readonly=True, required=True,
    #                         default=_get_contract_date_from)
    # date_to = fields.Date(string='Date To', readonly=True, required=True,
    #                       default=_get_contract_date_to,
    #                       )
    attendance_line_ids = fields.One2many('hr.payslip.attendance', 'payslip_id',
                                          string='Payslip Attendance', copy=True, readonly=True,
                                          )
    journal_id = fields.Many2one('account.journal', 'Salary Journal', readonly=True, required=True,
                                 default=lambda self: self.env['account.journal'].search([('name', 'ilike', 'salary')],
                                                                                         limit=1))
    attendance_summary_ids = fields.One2many('hr.attendance.summary', 'payslip_id', string='Attendance Summary',
                                             copy=False)

    def _get_worked_day_lines(self, domain=None, check_out_of_contract=True):
        res = super(HrPayslip, self)._get_worked_day_lines(domain=None, check_out_of_contract=True)
        precision = self.env['decimal.precision'].precision_get('Payroll')
        if self.contract_id:
            attendance_summaries = self.attendance_summary_ids
            if not attendance_summaries:
                attendance_summaries = self.env['hr.attendance.summary'].search([
                    ('employee_id', '=', self.contract_id.employee_id.id),
                    ('date_from', '>=', self.date_from),
                    ('check_date', '<=', self.date_to),
                    ('state', '=', 'draft')
                ])
            if attendance_summaries:
                worked_days = sum(attendance_summaries.mapped('worked_days'))
                worked_hours_total_compute = sum(attendance_summaries.mapped('worked_hours_total_compute'))
                absent_days = sum(attendance_summaries.mapped('absent_days'))
                # overtime_hours_compute = sum(attendance_summaries.mapped('overtime_hours_compute'))
                # deduction_hours_compute = sum(attendance_summaries.mapped('deduction_hours_compute'))

                overtime_hours_compute = deduction_hours_compute = 0
                special_ot_hours_compute = mol_ot_hours_compute = 0
                for sl in attendance_summaries:
                    overtime_hours_compute += sum(
                        sl.manual_line_ids.filtered(lambda l: l.work_entry_type_id.code == 'OT').mapped('no_of_hours'))
                    deduction_hours_compute += sum(
                        sl.manual_line_ids.filtered(lambda l: l.work_entry_type_id.code == 'ABSDED').mapped(
                            'no_of_hours'))

                    special_ot_hours_compute += sum(
                        sl.manual_line_ids.filtered(lambda l: l.work_entry_type_id.code == 'SPCLOT').mapped(
                            'no_of_hours'))
                    mol_ot_hours_compute += sum(
                        sl.manual_line_ids.filtered(lambda l: l.work_entry_type_id.code == 'MOLOT').mapped(
                            'no_of_hours'))

                    if overtime_hours_compute:
                        wo_type_id, calc_rate = False, 0.0
                        wo_type_ids = sl.manual_line_ids.filtered(lambda l: l.work_entry_type_id.code == 'OT').mapped(
                            'work_entry_type_id')
                        if wo_type_ids:
                            wo_type_id = wo_type_ids[0].id
                            calc_rate = float(
                                round((wo_type_ids[0].is_calculation and wo_type_ids[0].calc_rate or 0), precision))
                        attendances = {
                            'name': _("Overtime Hours"),
                            'sequence': 10,
                            'code': 'OT',
                            'number_of_days': 0.0,
                            'number_of_hours': overtime_hours_compute,
                            'work_entry_type_id': wo_type_id,
                            'calc_rate': calc_rate,
                        }
                        res.append(attendances)

                    if special_ot_hours_compute:
                        wo_type_id, calc_rate = False, 0.0
                        wo_type_ids = sl.manual_line_ids.filtered(
                            lambda l: l.work_entry_type_id.code == 'SPCLOT').mapped('work_entry_type_id')
                        if wo_type_ids:
                            wo_type_id = wo_type_ids[0].id
                            calc_rate = float(
                                round((wo_type_ids[0].is_calculation and wo_type_ids[0].calc_rate or 0), precision))
                        attendances = {
                            'name': _("Special Overtime Hours"),
                            'sequence': 10,
                            'code': 'SPCLOT',
                            'number_of_days': 0.0,
                            'number_of_hours': special_ot_hours_compute,
                            'work_entry_type_id': wo_type_id,
                            'calc_rate': calc_rate,
                        }
                        res.append(attendances)

                    if mol_ot_hours_compute:
                        wo_type_id, calc_rate = False, 0.0
                        wo_type_ids = sl.manual_line_ids.filtered(
                            lambda l: l.work_entry_type_id.code == 'MOLOT').mapped('work_entry_type_id')
                        if wo_type_ids:
                            wo_type_id = wo_type_ids[0].id
                            calc_rate = float(
                                round((wo_type_ids[0].is_calculation and wo_type_ids[0].calc_rate or 0), precision))
                        attendances = {
                            'name': _("MOL Overtime Hours"),
                            'sequence': 10,
                            'code': 'MOLOT',
                            'number_of_days': 0.0,
                            'number_of_hours': mol_ot_hours_compute,
                            'work_entry_type_id': wo_type_id,
                            'calc_rate': calc_rate,
                        }
                        res.append(attendances)

                    if deduction_hours_compute:
                        wo_type_id = False
                        wo_type_ids = sl.manual_line_ids.filtered(
                            lambda l: l.work_entry_type_id.code == 'ABSDED').mapped('work_entry_type_id')
                        if wo_type_ids:
                            wo_type_id = wo_type_ids[0].id
                        attendances = {
                            'name': _("Absent/Deduction Hours"),
                            'sequence': 15,
                            'code': 'ABSDED',
                            'number_of_days': 0.0,
                            'number_of_hours': deduction_hours_compute,
                            'work_entry_type_id': wo_type_id,
                        }
                        res.append(attendances)

        return res
        res = super(HrPayslip, self)._get_worked_day_lines(contract_ids, date_from, date_to)
        
        def _get_attendance_summaries(contract):
            summaries = self.attendance_summary_ids
            if not summaries:
                summaries = self.env['hr.attendance.summary'].search([
                    ('employee_id', '=', contract.employee_id.id),
                    ('date_from', '>=', date_from),
                    ('check_date', '<=', date_to),
                    ('state', '=', 'draft')
                ])
            return summaries
            
        def _create_work_entry(name, code, days, hours, contract_id, sequence):
            return {
                'name': name,
                'sequence': sequence,
                'code': code,
                'number_of_days': days,
                'number_of_hours': hours,
                'contract_id': contract_id,
            }

        for contract in self.env['hr.contract'].browse(contract_ids).filtered(lambda contract: contract.working_hours):
            attendance_summaries = _get_attendance_summaries(contract)
            
            # Handle case when no attendance summaries found
            if not attendance_summaries and contract.attendance_mode != 'na':
                res.append(_create_work_entry(
                    _("Absent Days"), 'ABSENT', 
                    contract.calc_days, 0.0, 
                    contract.id, 5
                ))
                continue
                
            # Calculate summary totals
            worked_days = sum(attendance_summaries.mapped('worked_days'))
            worked_hours = sum(attendance_summaries.mapped('worked_hours_total_compute'))
            absent_days = sum(attendance_summaries.mapped('absent_days'))
            overtime_hours = sum(attendance_summaries.mapped('overtime_hours_compute'))
            deduction_hours = sum(attendance_summaries.mapped('deduction_hours_compute'))
            
            # Update existing worked days entry
            if worked_days:
                for work_entry in res:
                    if work_entry['code'] == 'WORK100':
                        work_entry.update({
                            'name': 'Worked Days',
                            'number_of_days': worked_days,
                            'number_of_hours': worked_hours
                        })
                        break
            
            # Add additional entries if needed
            if absent_days:
                res.append(_create_work_entry(
                    _("Absent Days"), 'ABSENT',
                    absent_days, 0.0,
                    contract.id, 5
                ))
                
            if overtime_hours:
                res.append(_create_work_entry(
                    _("Overtime Hours"), 'OT',
                    0.0, overtime_hours,
                    contract.id, 10
                ))
                
            if deduction_hours:
                res.append(_create_work_entry(
                    _("Deduction Hours"), 'DED',
                    0.0, deduction_hours,
                    contract.id, 15
                ))

        return res

    def action_payslip_done(self):
        attendance_summaries = self.mapped('attendance_summary_ids')
        holidays = attendance_summaries.mapped('summary_lines').mapped('holiday_id')
        holidays.write({'holiday_status_id': True})
        attendance_summaries.write({'state': 'validated'})
        return super(HrPayslip, self).action_payslip_done()

    # @api.multi
    def unlink(self):
        attendance_summaries = self.mapped('attendance_summary_ids')
        holidays = attendance_summaries.mapped('summary_lines').mapped('holiday_id')
        holidays.write({'holiday_status_id': False})
        attendance_summaries.write({'state': 'draft'})
        return super(HrPayslip, self).unlink()

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        ttyme = datetime.fromtimestamp(time.mktime(time.strptime(str(self.date_to), "%Y-%m-%d")))
        # employee = self.env['hr.employee'].browse(self.employee_id)
        locale = self.env.context.get('lang') or 'en_US'

        self.update({
            'name': _('Salary Slip of %s for %s') % (
                self.employee_id.name, str(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale))),
        })


class HrPayslipWorkedDays(models.Model):
    _inherit = 'hr.payslip.worked_days'

    calc_rate = fields.Float(string="Overtime Rate")

    @api.depends('is_paid', 'number_of_hours', 'payslip_id', 'payslip_id.basic_wage', 'payslip_id.sum_worked_hours')
    def _compute_amount(self):
        for worked_days in self.filtered(lambda wd: not wd.payslip_id.edited):
            payslip = worked_days.payslip_id
            final_settlement = payslip.payslip_run_id.final_settlement_batch or False
            if not worked_days.contract_id or worked_days.code == 'OUT':
                worked_days.amount = 0
                continue
            contract = worked_days.contract_id
            if worked_days.payslip_id.wage_type == "hourly":
                worked_days.amount = contract.hourly_wage * worked_days.number_of_hours if worked_days.is_paid else 0
            else:
                if final_settlement or (contract.date_start > payslip.date_from):
                    hours_per_day = contract.resource_calendar_id.hours_per_day
                    # payslip_hours = ((contract.date_end - payslip.date_from).days + 1) * hours_per_day
                    # payslip_hours = contract.total_hours # passing full as we are passing rate based on no of working days

                    month_res = contract.resource_calendar_id.get_month_days_and_hours_calendar(payslip.date_to)
                    total_hours = month_res.get('hours',240)
                    # worked_days.amount = payslip.normal_wage * payslip_hours / (total_hours or 1) if worked_days.is_paid else 0
                    worked_days.amount = payslip.basic_wage * total_hours / (total_hours or 1) if worked_days.is_paid else 0
                else:
                    worked_days.amount = payslip.basic_wage * worked_days.number_of_hours / (payslip.sum_worked_hours or 1) if worked_days.is_paid else 0
