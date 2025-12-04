from odoo import api, models, fields
from dateutil.relativedelta import relativedelta
from odoo.osv import expression
from datetime import datetime



class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    analytic_account_ids = fields.Many2many('account.analytic.account', 'analytic_account_payslip_employees_rel', 'analytic_account_id', 'payslip_employees_id', string='Projects')

    def _default_month(self):
        today_date = default_date = fields.Date.context_today(self)
        if today_date.day <= 10:
            default_date = fields.Date.context_today(
                self
            ) - relativedelta(months=1)
        return default_date.strftime("%m")

    month = fields.Selection(
        [
            ("01", "January"),
            ("02", "February"),
            ("03", "March"),
            ("04", "April"),
            ("05", "May"),
            ("06", "June"),
            ("07", "July"),
            ("08", "August"),
            ("09", "September"),
            ("10", "October"),
            ("11", "November"),
            ("12", "December"),
        ],
        required=True,
        default=_default_month,
    )

    year = fields.Selection(
        string="Year",
        selection="_selection_year",
        required=True,
        default=lambda self: str(fields.Date.context_today(self).year),
    )

    def _selection_year(self):
        current_year = fields.Date.context_today(self).year
        year_options = []
        for year in range(current_year - 20, current_year + 1):
            year_options.append((str(year), str(year)))
        return year_options

    @api.depends('analytic_account_ids')
    def _compute_employee_ids(self):
        emp = super()._compute_employee_ids()
        hr_employees = self.env["hr.employee"]

        for wizard in self.filtered(lambda w: w.analytic_account_ids):
            analytic_accounts = self.env['account.analytic.account'].search([('id','child_of',self.analytic_account_ids.ids)])

            domain = [
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

        return emp

    def compute_sheet(self):
        if self.analytic_account_ids:
            selected_month = self.month
            selected_year = int(self.year)
            start_date = datetime(selected_year, int(selected_month), 1)
            end_date = start_date + relativedelta(day=31)
            res = super(HrPayslipEmployees, self.with_context(default_date_start=start_date, default_date_end=end_date)).compute_sheet()
            payslip_run = self.env['hr.payslip.run'].search([] ,order='id desc', limit=1)
            name =','.join([p.name for p in self.analytic_account_ids])
            payslip_run.write({"name":name +' '+payslip_run.name})
        else:
            res = super().compute_sheet()
        return res