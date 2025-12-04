from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    sale_order_service_line_ids = fields.One2many('sale.order.service.line', 'order_line_id', string='Service Line', )
    order_partner_id = fields.Many2one('res.partner', string='Client', store=True, readonly=True,
                                       related='order_id.partner_id')
    is_recruitment_service = fields.Boolean(string='Is Recruitment Service',
                                            related='product_id.is_recruitment_service',
                                            store=True, readonly=True)

    def edit_line_control(self):
        return {
            'name': 'Edit Service',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.line',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id,
            'context': {
                'create': False,
                'edit': True,
                'default_partner_id': self.order_partner_id.id,
            },
        }

    def write(self, values):
        # Call the super method to perform the write operation
        res = super(SaleOrderLine, self).write(values)

        # Check if product_id was updated in the write operation
        if 'product_id' in values:
            for record in self:
                # Check if the product associated with the record is not a recruitment service
                product = self.env['product.product'].browse(values['product_id'])
                if not product.is_recruitment_service:
                    # Unlink sale order service lines if they exist
                    record.sale_order_service_line_ids.unlink()
                    record.price_unit = record.product_id.lst_price
        return res
