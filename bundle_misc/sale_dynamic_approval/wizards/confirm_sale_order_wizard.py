from odoo import models, fields


class ConfirmSaleOrderWizard(models.TransientModel):
    _name = 'confirm.sale.order.wizard'
    _description = 'Confirm Sale Order Without Approval Wizard'

    name = fields.Char(
        default='There is no approval workflow found, Are you sure to confirm order without approvals cycle?',
    )


    def action_confirm_order(self):
        if self._context.get('active_model') == 'sale.order':
            order = self.env['sale.order'].browse(self._context.get('active_id'))
            order.action_confirm()
