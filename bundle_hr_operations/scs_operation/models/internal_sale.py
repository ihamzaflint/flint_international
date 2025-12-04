from odoo import _, models, fields, api
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round


class InternalSale(models.Model):
    _name = "internal.sale"
    _description = "Internal Sale"
    _rec_name = "partner_id"

    _inherit = ["mail.thread", "mail.activity.mixin"]

    partner_id = fields.Many2one("res.partner", string="Customer", required=True)

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submit", "Submit"),
            ("validate", "Validate"),
            ("reject", "Reject"),
            ("cancel", " Cancel"),
        ],
        default="draft",
        tracking=True,
    )

    internal_sale_line_ids = fields.One2many("internal.sale.line", "internal_sale_id")

    def _create_activity(self, note=None, users=None):
        for user in users:
            activity = self.activity_schedule(
                "mail.mail_activity_data_todo",
                note=note,
                user_id=user.id,
            )

    def change_activity_state(self):
        self.ensure_one()
        self.activity_unlink(["mail.mail_activity_data_todo"])

    def change_state(self):
        ctx = self._context
        if ctx.get("submit"):
            self.state = "submit"
            group_id = self.env.ref("scs_operation.group_internal_sale_admin")
            note = _("Request for Internal Sale Validate")
            self._create_activity(note=note, users=group_id.users)
        elif ctx.get("validate"):
            self.state = "validate"
            self.change_activity_state()
        elif ctx.get("reject"):
            self.state = "reject"
            self.change_activity_state()
        elif ctx.get("cancel"):
            self.state = "cancel"
        elif ctx.get("draft"):
            self.change_activity_state()
            self.state = "draft"

    def unlink(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("You can only delete draft record"))
        return super().unlink()


class InternalSaleLine(models.Model):
    _name = "internal.sale.line"
    _description = "Internal Sale Line"

    internal_sale_id = fields.Many2one("internal.sale", ondelete="cascade")
    candidate_type = fields.Selection(
        [("saudi_local", "Saudi Local"), ("no_saudi", "Non-Saudi")],
        required=True,
        default="saudi_local"
    )
    roles = fields.Char()
    nationality_id = fields.Many2one("res.country")
    name = fields.Char("Candidate Names")
    exp_year = fields.Float()
    marital = fields.Selection(
        [
            ("single", "Single"),
            ("married", "Married"),
            ("cohabitant", "Legal Cohabitant"),
            ("widower", "Widower"),
            ("divorced", "Divorced"),
        ],
        string="Marital Status",
        default="single",
    )
    invoice_period = fields.Float("Invoice Period (No. of months)")
    package = fields.Float()
    basic = fields.Float()
    housing = fields.Float()
    trans = fields.Float('Transportation')
    profile_fees = fields.Float("Profile Fees (One-time)")

    @api.depends("basic", "housing", "trans")
    def _compute_net_monthly(self):
        for rec in self:
            rec.net_monthly_salary = rec.basic + rec.housing + rec.trans
            rec.end_of_service = (
                float_round(
                    rec.net_monthly_salary and rec.net_monthly_salary / 24,
                    precision_digits=2,
                )
            ) or 0
            if rec.candidate_type == "no_saudi":
                rec.gosi = float_round(
                    ((rec.basic + rec.housing) * 0.02), precision_digits=2
                )
                rec.iqama_fees = float_round(((9700 + 650) / 12), precision_digits=2)
                rec.iqama_transfer_fees = 6000 / 12
                rec.ajeer = float_round((420 / 12), precision_digits=2)
                rec.exit_reentry = float_round(((200 * 4) / 12), precision_digits=2)
            else:
                rec.gosi = float_round(
                    ((rec.basic + rec.housing) * 0.1175), precision_digits=2
                )
                if rec.invoice_period and rec.net_monthly_salary:
                    rec.profile_fees = float_round(
                        (rec.net_monthly_salary / 12),
                        precision_digits=2,
                    )

            

    @api.depends("exit_reentry", "saudization", "gosi", "mobilization_cost", 'profile_fees')
    def _compute_total_monthly_cost(self):
        for rec in self:
            if rec.candidate_type == "no_saudi":
                rec.total_monthly_cost = rec.monthly_po_without_margin = (
                    rec.net_monthly_salary
                    + rec.vac_salary
                    + rec.end_of_service
                    + rec.employee_annual_flight_ticket
                    + rec.wife_annual_flight_ticket
                    + rec.child_flight_ticket
                    + rec.employee_health
                    + rec.spouse_health_insurance
                    + rec.kids_health_insurance
                    + rec.gosi
                    + rec.saudization
                    + rec.iqama_fees
                    + rec.iqama_transfer_fees
                    + rec.mobilization_cost
                    + rec.ajeer
                    + rec.exit_reentry
                )
            else:
                rec.total_monthly_cost = (
                    rec.net_monthly_salary
                    + rec.vac_salary
                    + rec.end_of_service
                    + rec.employee_health
                    + rec.spouse_health_insurance
                    + rec.kids_health_insurance
                    + rec.gosi
                    + rec.profile_fees
                )
                if rec.total_monthly_cost and rec.invoice_period:
                    rec.monthly_po_without_margin = float_round(
                ((rec.total_monthly_cost * 12) / rec.invoice_period), precision_digits=2)

            rec.twelve_months_cost = float_round(
                (rec.total_monthly_cost * 12), precision_digits=2
            )

            rec.monthly_flint_margin = float_round(
                (rec.monthly_po_without_margin * 0.15), precision_digits=2
            )
            rec.monthly_po_sar_without_vat = float_round(
                rec.monthly_flint_margin + rec.monthly_po_without_margin,
                precision_digits=2,
            )

            rec.monthly_po_sar_with_vat = (
                float_round(rec.monthly_po_sar_without_vat * 0.15, precision_digits=2)
            ) + rec.monthly_po_sar_without_vat

    net_monthly_salary = fields.Float(compute="_compute_net_monthly", store=True)
    vac_salary = fields.Float("Vac Salary 12 months PO")
    end_of_service = fields.Float()
    employee_annual_flight_ticket = fields.Float()
    wife_annual_flight_ticket = fields.Float()
    child_flight_ticket = fields.Float("2 Child Annual Flight Ticket")
    employee_health = fields.Float("Employee Health Insurance (Categories)")
    spouse_health_insurance = fields.Float("Spouse Health Insurance")
    kids_health_insurance = fields.Float("2 Kids  Health Insurance")
    gosi = fields.Float()
    saudization = fields.Float()
    iqama_fees = fields.Float()
    iqama_transfer_fees = fields.Float()
    mobilization_cost = fields.Float()
    ajeer = fields.Float()
    exit_reentry = fields.Float()
    total_monthly_cost = fields.Float(
        compute="_compute_total_monthly_cost",
        store=True,
    )
    twelve_months_cost = fields.Float(
        compute="_compute_total_monthly_cost",
        store=True,
    )
    monthly_po_without_margin = fields.Float()
    monthly_flint_margin = fields.Float()
    monthly_po_sar_without_vat = fields.Float()
    monthly_po_sar_with_vat = fields.Float()

    @api.onchange("package")
    def _onchange_package(self):
        if self.package:
            self.basic = float_round(self.package * 0.65, precision_digits=2)
            self.housing = float_round(self.package * 0.25, precision_digits=2)
            self.trans = float_round(self.package * 0.10, precision_digits=2)
            if self.candidate_type == 'no_saudi':
                self.employee_health = float_round(6000 / 12, precision_digits=2)
                self.spouse_health_insurance = float_round(10000 / 12, precision_digits=2)
                self.kids_health_insurance = float_round(
                    (6000 * 2) / 12, precision_digits=2
                )
