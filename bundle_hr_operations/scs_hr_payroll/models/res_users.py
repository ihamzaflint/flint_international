from odoo import models, fields


class ResUsers(models.Model):
    _inherit = "res.users"

    analytic_account_ids = fields.Many2many(
        "account.analytic.account",
        "res_user_account_analytic_project_rel",
        "user_id",
        "analytic_id",

        string="Payroll Project Not Allowed",
    )
