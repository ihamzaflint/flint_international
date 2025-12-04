# -*- coding: utf-8 -*-
from odoo import models, api


class AccountReconciliation(models.AbstractModel):
    _inherit = "account.reconciliation.widget"

    def _str_domain_for_mv_line(self, search_str):
        return ["|", ("move_id.internal_ref", "ilike", search_str)] + super(
            AccountReconciliation, self
        )._str_domain_for_mv_line(search_str)

    @api.model
    def _prepare_js_reconciliation_widget_move_line(
        self, statement_line, line, recs_count=0
    ):
        js_vals = super(
            AccountReconciliation, self
        )._prepare_js_reconciliation_widget_move_line(statement_line, line, recs_count)

        js_vals.update({"internal_ref": line.move_id.internal_ref or ""})

        return js_vals
