from odoo import fields, models, api, _
from odoo.osv import expression
from collections import defaultdict
from odoo.exceptions import UserError



class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    # employee_ids = fields.Many2many(compute='_compute_employee_ids', store=True, readonly=False)
    # employee_ids = fields.Many2many('hr.employee', 'hr_employee_group_rel', 'payslip_id', 'employee_id', 'Employees',
    #                                 default=lambda self: self._get_employees(), required=True,
    #                                 compute='_compute_employee_ids', store=True, readonly=False)
    # department_id = fields.Many2one('hr.department')
    analytic_account_id = fields.Many2one('account.analytic.account')
    employee_ids = fields.Many2many('hr.employee', 'hr_employee_group_rel', 'payslip_id', 'employee_id', 'Employees',
                                    default=lambda self: self._get_employees(), required=True,
                                    compute='_compute_employee_ids', store=True, readonly=False,
                                    # domain=['|',('active','=',True),('active','!=',True)],
                                    context={'active_test': False})
    filtered_analytic_account_ids = fields.Many2many('account.analytic.account', readonly=True, string="Filtered Projects (Analytic Accounts)")

    @api.depends('department_id','analytic_account_id')
    def _compute_employee_ids(self):
        hr_employees = self.env['hr.employee']
        for wizard in self.filtered(lambda w: w.department_id):
            hr_employees |= self.env['hr.employee'].search(expression.AND([
                wizard._get_available_contracts_domain(),
                [('department_id', 'ilike', self.department_id.name)]
            ]))
            
        for wizard in self.filtered(lambda w: w.analytic_account_id):
            analytic_accounts = self.env['account.analytic.account'].search([('id','child_of',self.analytic_account_id.id)])

            domain = [
                    # ('contract_id.analytic_account_id', 'child_of', self.analytic_account_id.id),
                    # ('contract_id.analytic_account_id', '=', self.analytic_account_id.id),
                    ('contract_id.analytic_account_id', 'in', analytic_accounts.ids),
                ]

            if self.env['hr.payslip.run'].browse(self._context.get('active_id')).final_settlement_batch:
                domain += [('contract_id.state', '=', 'close'),('active', '!=', True)]
            else:
                domain += [('contract_id.state', '=', 'open')]
            domain += ['|',('departure_reason_id.exclude_from_batch','!=',True),('departure_reason_id','=',False)]

            hr_employees |= self.env['hr.employee'].search(expression.AND([
                wizard._get_available_contracts_domain(), domain
            ]))
            
            wizard.employee_ids = hr_employees
            wizard.filtered_analytic_account_ids = analytic_accounts.ids

    def _check_undefined_slots(self, work_entries, payslip_run):
        # return True
        """
        overritten to re-generate the work-entries
        Check if a time slot in the contract's calendar is not covered by a work entry
        """
        missing_structures = []
        contracts = self.env['hr.contract']
        work_entries_by_contract = defaultdict(lambda: self.env['hr.work.entry'])
        for work_entry in work_entries:
            contracts |= work_entry.contract_id
            work_entries_by_contract[work_entry.contract_id] |= work_entry
            if not work_entry.contract_id.structure_type_id:
                missing_structures.append(work_entry.contract_id.name)
        if missing_structures:
            raise UserError(_("Salary structure missing for: %s") % (list(set(missing_structures))))

        duplicate_payslips = self.env['hr.payslip'].search([
                ('date_from','=',payslip_run.date_start),
                ('date_to', '=', payslip_run.date_end),
                ('contract_id','in',contracts.ids)
                  ])
        if duplicate_payslips:
            contracts = duplicate_payslips.mapped('contract_id')
            raise UserError(_("You are tying to run duplicate payroll. Please check for: %s") % (contracts.mapped('name')))


        return True

        # for contract, work_entries in work_entries_by_contract.items():
        #     calendar_start = pytz.utc.localize(datetime.combine(max(contract.date_start, payslip_run.date_start), time.min))
        #     calendar_end = pytz.utc.localize(datetime.combine(min(contract.date_end or date.max, payslip_run.date_end), time.max))
        #     outside = contract.resource_calendar_id._attendance_intervals_batch(calendar_start, calendar_end)[False] - work_entries._to_intervals()
        #     if outside:# custom code
        #         # contract.sudo()._remove_work_entries()
        #         contract.sudo()._cancel_work_entries()
        #         # contract._generate_work_entries(payslip_run.date_start, payslip_run.date_end)
        #         contract._recompute_work_entries(calendar_start, calendar_end)
        #         work_entries = self.env['hr.work.entry'].search([
        #             ('date_start', '<=', payslip_run.date_end),
        #             ('date_stop', '>=', payslip_run.date_start),
        #             ('employee_id', '=', contract.employee_id.id),
        #         ])
        #         outside = contract.resource_calendar_id._attendance_intervals_batch(calendar_start, calendar_end)[False] - work_entries._to_intervals()
        #         if outside:
        #             time_intervals_str = "\n - ".join(['', *["%s -> %s" % (s[0], s[1]) for s in outside._items]])
        #             raise UserError(_("Some part of %s's calendar is not covered by any work entry. Please complete the schedule. Time intervals to look for:%s") % (contract.employee_id.name, time_intervals_str))
