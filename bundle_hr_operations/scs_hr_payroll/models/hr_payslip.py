from odoo import api, models


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    @api.model
    def _search(
        self,
        domain,
        offset=0,
        limit=None,
        order=None,
        access_rights_uid=None,
        count=False,
    ):
        if self.env.user.analytic_account_ids:
            domain = domain or []
            analytic_accounts = self.env["account.analytic.account"].search(
                [("id", "child_of", self.env.user.analytic_account_ids.ids)]
            )
            domain.append(
                (
                    "contract_id.analytic_account_id",
                    "not in",
                    analytic_accounts.ids,
                )
            )
        return super(HrPayslip, self)._search(
            domain, offset, limit, order, access_rights_uid=access_rights_uid,
        )

    def _is_invalid(self):
        return False
