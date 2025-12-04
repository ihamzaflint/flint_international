from datetime import datetime
from odoo import models, fields, _


class RejectDynamicApprovalWizard(models.TransientModel):
    _name = 'reject.dynamic.approval.wizard'
    _description = 'Reject Advanced Approval Wizard'

    name = fields.Char('Reason')
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')

    def action_reject_order(self):
        active_ids = self._context.get('active_ids')
        active_model = self._context.get('active_model')
        record = self.env[active_model].browse(active_ids)
        if getattr(record, record._state_field) == record._state_under_approval:
            reject_reason = self.name or ''
            attachment_ids = self.attachment_ids or []
            record._action_reset_original_state(reason=reject_reason,attachments=attachment_ids, reset_type='reject')
