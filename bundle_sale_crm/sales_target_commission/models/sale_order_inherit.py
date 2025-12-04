from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import calendar


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(SaleOrderInherit, self).action_confirm()
        for rec in self:
            self.env['sales.team.target'].is_valid_target('confirmed_sale',
                                                      rec.date_order.date(),
                                                      rec.user_id,
                                                      rec)
        return res

    def action_cancel(self):
        res = super(SaleOrderInherit, self).action_cancel()
        self.env['sales.team.target'].is_not_valid_target('confirmed_sale', self.order_line)
        return res
