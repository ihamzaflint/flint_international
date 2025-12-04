from odoo import models, fields


class ConfirmPurchaseOrderWizard(models.TransientModel):
    _name = 'confirm.purchase.order.wizard'
    _description = 'Confirm Purchase Order Without Approval Wizard'

    name = fields.Char(
        default='There is no approval workflow found, Are you sure to confirm order without approvals cycle?',
    )

    def action_confirm_order(self):
        if self._context.get('active_model') == 'purchase.order':
            order = self.env['purchase.order'].browse(self._context.get('active_id'))
            order.button_confirm()
