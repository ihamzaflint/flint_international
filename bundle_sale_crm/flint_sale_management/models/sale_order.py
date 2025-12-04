from odoo import api, fields, models
from lxml import etree


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    state = fields.Selection(selection_add=[('draft',), ('recruitment_process', 'Recruitment Process')], ondelete={'draft': 'set default', 'recruitment_process': 'set default'})

    def action_add_service(self):
        self.ensure_one()
        return {
            'name': 'Add Service',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.line',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_order_id': self.id,
                'default_order_partner_id': self.partner_id.id,
                'default_product_uom': self.env.ref('uom.product_uom_unit').id,
                'default_product_uom_qty': 1,
            },
        }

    def add_line_control(self):
        self.ensure_one()
        return {
            'name': 'Add Service',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.service.line',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_order_id': self.id,
            },
        }