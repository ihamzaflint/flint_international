from odoo import api, fields, models, _


class SalesTeamTargetCommissions(models.Model):
    _name = 'sales.team.target.commissions'
    _rec_name = 'name'
    _description = 'Sales Team Target Commissions'

    target_commission_id = fields.Many2one('sales.team.target', string="Target Commissions", ondelete="cascade")
    sales_commission_line_id = fields.Many2one('sales.commission.lines', string="Sales Commissions", ondelete="cascade")
    name = fields.Char(string="Source Document")
    product_id = fields.Many2one('product.product', string="Product Name", ondelete="set null", index=True)
    product_desc = fields.Char(string="Product Description")
    uom_id = fields.Many2one('uom.uom', string="Unit Of Measure")
    price_subtotal = fields.Float(string="Price Subtotal")
    quantity = fields.Float(string="Quantity", index=True)
    price = fields.Float(string="Unit Price", index=True)
    sale_order_line_id = fields.Many2one('sale.order.line', string="Order Line", index=True)
    account_move_line_id = fields.Many2one('account.move.line', string="Move Line", index=True)
    target_achievement = fields.Selection(selection=[('confirmed_sale', 'Confirmed Sales Order')])
    sale_id = fields.Many2one('sale.order', string="Sale Order")
    is_commission = fields.Boolean(string="Commissioned")
