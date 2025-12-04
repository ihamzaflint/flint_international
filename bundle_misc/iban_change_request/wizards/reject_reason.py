from odoo import fields, models


class RejectReasonWizard(models.TransientModel):
    _name = 'reject.reason.wizard'
    _description = 'Rejection Reason Wizard'


    rejection_reason = fields.Text(string='Rejection Reason', required=True)

    def action_reject(self):
        active_record = self.env[self._context.get('active_model')].browse(self._context.get('active_id'))
        if active_record and self._context.get('active_model') == 'iban.change.request':
            active_record.write({
                'state': 'reject',
                'rejection_reason': self.rejection_reason
            })
        return {'type': 'ir.actions.act_window_close'}
