from odoo import api, models, fields
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
from odoo.tools import date_utils
from datetime import datetime


class PayslipSendMail(models.TransientModel):
    _name = "payslip.send.mail"
    _description = "send mail using date and filtered"

    analytic_account_id = fields.Many2one("account.analytic.account", required=True)
    employee_ids = fields.Many2many(
        "hr.employee",
        "hr_employee_send_mail_rel",
        "payslip_id",
        "employee_id",
        "Employees",
        required=True,
        compute="_compute_employee_ids",
        store=True,
        readonly=False,
    )

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

    def _default_year(self):
        today_date = fields.Date.context_today(self)
        company = self.env.company
        if company.account_tax_periodicity == "trimester":
            this_quarter = date_utils.get_quarter(today_date)
            if (
                this_quarter
                and this_quarter[0].month == today_date.month
                and today_date.day <= 10
            ):
                return (
                    fields.Date.context_today(self)
                    - relativedelta(months=3)
                ).strftime("%Y")

        if today_date.day <= 10 and company.account_tax_periodicity == "monthly":
            return (
                fields.Date.context_today(self) - relativedelta(months=1)
            ).strftime("%Y")
        return today_date.strftime("%Y")

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

    @api.depends("analytic_account_id")
    def _compute_employee_ids(self):
        hr_employees = self.env["hr.employee"]

        for wizard in self.filtered(lambda w: w.analytic_account_id):
            analytic_accounts = self.env["account.analytic.account"].search(
                [("id", "child_of", self.analytic_account_id.id)]
            )

            domain = [
                ("contract_id.analytic_account_id", "in", analytic_accounts.ids),
                ("contract_id.state", "=", "open"),
            ]
            domain += [
                "|",
                ("departure_reason_id.exclude_from_batch", "!=", True),
                ("departure_reason_id", "=", False),
            ]

            hr_employees |= self.env["hr.employee"].search(domain)

            wizard.employee_ids = hr_employees

    def send_mail_to_employee(self):
        selected_month = self.month
        selected_year = int(self.year)
        start_date = datetime(selected_year, int(selected_month), 1)
        end_date = start_date + relativedelta(day=31)
        if not self.employee_ids:
            raise UserError(
                "No employee for the project %s" % self.analytic_account_id.name
            )
        domain = [
            ("employee_id", "in", self.employee_ids.ids),
            ("date_from", ">=", start_date),
            ("date_to", "<=", end_date),
        ]
        payslips = self.env["hr.payslip"].search(domain)
        template = self.env.ref("hr_payslip_send_mail.payslip_email_template")
        if not payslips:
            month_name = dict(self._fields["month"].selection).get(self.month, False)
            raise UserError("No payslip for month %s" % month_name)

        for payslip in payslips.filtered(lambda l: l.employee_id):
            email_to_send = payslip.employee_id.personal_email or payslip.employee_id.work_email
            if email_to_send:
                template.send_mail(payslip.id, force_send=True, email_values={'email_to': email_to_send})
                # payslip.message_post_with_template(template_id=template.id,)
        return {"type": "ir.actions.act_window_close"}