from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class RejectionReasonWizard(models.TransientModel):
    _inherit = 'rejection.reason.wizard'

    def action_reject(self):
        active_record = self.env[self._context.get('active_model')].browse(self._context.get('active_id'))
        if active_record and self._context.get('active_model') == 'helpdesk.ticket':
            operation_manager_rejected = self.env["helpdesk.stage"].search(
                [("is_operation_manager_reject", "=", True)], limit=1
            )
            if not operation_manager_rejected:
                raise ValidationError(
                    _("Please configure 'Operation Manager Rejected' stage in helpdesk settings")
                )
            active_record.write({
                'stage_id': operation_manager_rejected.id,
            })
            active_record.activity_schedule(
                'mail.mail_activity_data_todo',
                note='the Ticket %s has been rejected for the following reason %s' % (
                    active_record.name, self.rejection_reason),
                user_id=active_record.user_id.id)
        return super(RejectionReasonWizard,self).action_reject()
