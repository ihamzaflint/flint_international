from odoo import _, models, fields, api
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class HrContractHistory(models.Model):
    _inherit = "hr.contract.history"

    @api.model
    def _search(
        self,
        args,
        offset=0,
        limit=None,
        order=None,
        access_rights_uid=None,
    ):
        if self.env.user.analytic_account_ids:
            args = args or []
            analytic_accounts = self.env["account.analytic.account"].search(
                [("id", "child_of", self.env.user.analytic_account_ids.ids)]
            )
            args.append(
                (
                    "analytic_account_id",
                    "not in",
                    analytic_accounts.ids,
                )
            )
        return super(HrContractHistory, self)._search(
            args, offset, limit, order, access_rights_uid=access_rights_uid
        )


class HrContract(models.Model):
    _inherit = "hr.contract"

    def _compute_total_gross(self):
        for rec in self:
            rec.total_gross_wage = (
                rec.wage
                + rec.l10n_sa_housing_allowance
                + rec.l10n_sa_transportation_allowance
                + rec.l10n_sa_other_allowances
                + rec.phone_allowance
                + rec.tools_allowance
                + rec.tickets_allowance
                + rec.annual_leave_vacation_amount_allowance
                + rec.gosi_comp_onbehalf
                + rec.tech_allowance
                + rec.kids_allowance
                + rec.granted_monthly_bonus
                + rec.special_allowance
                + rec.niche_skill_allowance
                + rec.shift_allowance
                + rec.car_allowance
                + rec.gas_allowance
                + rec.oc_rec_allowance
                + rec.project_allowance
                + rec.food_allowance
                + rec.edu_allowance
            )

    total_gross_wage = fields.Float(
        string="Total Gross Wage", compute="_compute_total_gross"
    )

    def get_contract_expiry(self):
        contract_ids = self.search(
            [
                ("date_end", ">=", fields.Date.today()),
                ("date_end", "<=", fields.Date.today() + relativedelta(months=+3)),
            ],
            order="date_end",
        )
        if not contract_ids:
            raise UserError(_("No Contract Details Found"))
        return self.env.ref(
            "scs_hr_payroll.report_action_report_contract_expiry"
        ).report_action(contract_ids)

    @api.model
    def _search(
        self,
        args,
        offset=0,
        limit=None,
        order=None,
        access_rights_uid=None,
    ):
        if self.env.user.analytic_account_ids:
            args = args or []
            analytic_accounts = self.env["account.analytic.account"].search(
                [("id", "child_of", self.env.user.analytic_account_ids.ids)]
            )
            args.append(
                (
                    "analytic_account_id",
                    "not in",
                    analytic_accounts.ids,
                )
            )
        return super(HrContract, self)._search(
            args, offset, limit, order, access_rights_uid=access_rights_uid
        )

    def get_formview_action(self, access_uid=None):
        if self.env.user.analytic_account_ids:
            analytic_accounts = self.env["account.analytic.account"].search(
                [("id", "child_of", self.env.user.analytic_account_ids.ids)]
            )
            if self.analytic_account_id.id in analytic_accounts.ids:
                raise UserError(
                    _(
                        "Due to security restrictions, you are not allowed to access.\n"
                        "Contact your administrator to request access"
                    )
                )
        return super(HrContract, self).get_formview_action(access_uid)

    def write(self, vals):
        res = super().write(vals)
        allowances = [
            "wage",
            "l10n_sa_housing_allowance",
            "l10n_sa_transportation_allowance",
            "l10n_sa_other_allowances",
            "phone_allowance",
            "tools_allowance",
            "tickets_allowance",
            "annual_leave_vacation_amount_allowance",
            "gosi_comp_onbehalf",
            "tech_allowance",
            "kids_allowance",
            "granted_monthly_bonus",
            "special_allowance",
            "niche_skill_allowance",
            "shift_allowance",
            "car_allowance",
            "gas_allowance",
            "oc_rec_allowance",
            "project_allowance",
            "food_allowance",
            "edu_allowance",
        ]

        for rec in self:
            if (
                vals
                and rec.state == "open"
                and not self.env.user.has_group(
                    "scs_hr_payroll.group_contract_update_access"
                )
                and (set(allowances) & set(vals.keys()))
            ):
                raise UserError(
                    _(
                        "You are not allowed to update running contract. Please contact administrator"
                    )
                )

        return res
