from odoo import _, api, models
from odoo.tools.misc import format_date


class OtherHrPayslip(models.Model):
    _inherit = "other.hr.payslip"

    @api.onchange("employee_id", "date")
    def onchange_employee(self):
        super().onchange_employee()
        self.analytic_account_id = False
        if self.employee_id:
            contracts = self.employee_id._get_contracts(self.date, self.date)
            if contracts:
                self.analytic_account_id = contracts[0].analytic_account_id

    @api.onchange("employee_id", "adjustment_type_id")
    def _onchange_check_adjustment(self):
        if self.employee_id and (
            self.adjustment_type_id.name
            in [
                "Flight Ticket Deduction",
                "Flight Ticket Addition",
                "Vacation Salary/leave Pay Addition",
                "Vacation Salary/leave Deduction",
            ]
        ):
            adjustment_id = self.search(
                [
                    ("adjustment_type_id", "=", self.adjustment_type_id.id),
                    ("id", "!=", self._origin.id),
                ],
                limit=1,
                order="id desc",
            )

            if adjustment_id:
                message = _(
                    "Previous %s is on date %s"
                    % (
                        adjustment_id.adjustment_type_id.name,
                        format_date(self.env, adjustment_id.date),
                    )
                )
                return {
                    "warning": {"title": _("Warning"), "message": message},
                }
