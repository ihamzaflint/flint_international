from odoo import api, models, fields


class CrmLead(models.Model):
    _inherit = "crm.lead"

    contract_number = fields.Integer(string="Contract Number", default=1)
    contract_period = fields.Selection(
        [("1", "Months"), ("12", "Years")],
        string="Number of Months in a Period",
        default="12",
    )

    contract_type = fields.Selection(
        [("renewal", "Renewal"), ("nonrenewal", "Non-renewal")],
        string="Contract Type",
    )
    margin_percentage = fields.Float("Margin Percentage")
    margin_amount = fields.Float("Margin Amount")

    usd_currency_id = fields.Many2one(
        "res.currency",
        string="Currency In USD",
        compute="usd_company_currency",
        readonly=True,
    )
    convert_amount = fields.Float(
        compute="_convert_amount",
        currency_field="usd_currency_id",
        store=True,
        string="Total Revenue in USD",
    )
    expected_revenue = fields.Monetary(
        "Total Revenue",
        currency_field="company_currency",
        tracking=True,
    )

    @api.onchange("margin_percentage")
    def _onchange_margin_percentage(self):
        self.margin_amount = 0
        if self.margin_percentage and self.expected_revenue:
            self.margin_amount = (self.expected_revenue * self.margin_percentage) / 100

    @api.onchange("margin_amount")
    def _onchange_margin_amount(self):
        self.margin_percentage = 0
        if self.margin_amount and self.expected_revenue:
            self.margin_percentage = (self.margin_amount / self.expected_revenue) * 100

    @api.depends(
        lambda self: ["stage_id", "team_id", "expected_revenue"]
        + self._pls_get_safe_fields()
    )
    def _compute_probabilities(self):
        super()._compute_probabilities()
        for rec in self:
            if rec.stage_id.probability_per and rec.expected_revenue:
                rec.probability = rec.stage_id.probability_per
            else:
                rec.probability = rec.stage_id.probability_per

    @api.depends("expected_revenue")
    def _convert_amount(self):
        for rec in self:
            convert_amount = 0
            if rec.expected_revenue and rec.usd_currency_id:
                convert_amount = rec.company_currency._convert(
                    rec.expected_revenue,
                    rec.usd_currency_id,
                    self.company_id,
                    fields.Date.today(),
                )
            rec.convert_amount = convert_amount

    @api.depends("margin_amount")
    def _convert_margin_amount(self):
        for rec in self:
            convert_amount = 0
            if rec.margin_amount and rec.usd_currency_id:
                convert_amount = rec.company_currency._convert(
                    rec.margin_amount,
                    rec.usd_currency_id,
                    self.company_id,
                    fields.Date.today(),
                )
            rec.usd_margin_amount = convert_amount

    def usd_company_currency(self):
        usd_currency_id = self.env["res.currency"].search([("name", "=", "USD")])
        for lead in self:
            lead.usd_currency_id = usd_currency_id
