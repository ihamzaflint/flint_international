from odoo import models, fields


class ConfirmPurchaseOrderWizard(models.TransientModel):
    _name = 'confirm.account.move.wizard'
    _description = 'Account Move Order Without Approval Wizard'

    name = fields.Char(
        default='There is no approval workflow found, Are you sure to confirm order without approvals cycle?',
    )

    def action_post(self):
        self.env[self._context.get('active_model')].browse(self._context.get('active_id')).action_post()
        return True
