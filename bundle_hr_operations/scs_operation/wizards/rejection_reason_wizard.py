from odoo import fields, models


class RejectionReasonWizard(models.TransientModel):
    _name = 'rejection.reason.wizard'
    _description = 'Rejection Reason Wizard'
    rejection_reason = fields.Text(string='Rejection Reason', required=True)

    def action_reject(self):
        active_record = self.env[self._context.get('active_model')].browse(self._context.get('active_id'))
        if active_record and self._context.get('active_model') == 'logistic.order':
            # Handle the case where notes might be False or empty
            current_notes = active_record.notes or ''
            new_notes = current_notes + '\n\nRejection Reason: ' + self.rejection_reason if current_notes else 'Rejection Reason: ' + self.rejection_reason
            
            active_record.write({
                'state': 'rejected',
                'notes': new_notes
            })
            for user in self.env.ref('scs_operation.group_insurance_user').users:
                active_record.activity_schedule(
                    'mail.mail_activity_data_todo',
                    note='the Order %s has been rejected for the following reason %s' % (
                        active_record.name, self.rejection_reason),
                    user_id=user.id)
        elif active_record and self._context.get('active_model') == 'government.payment':
            active_record.write({'rejection_reason': self.rejection_reason,
                                 'state': 'reject'})
            active_record.send_notify("%s Your Ticket has been rejected for the following reason %s" % ( active_record.create_uid.name, self.rejection_reason))
            active_record.change_activity_state()
        return {'type': 'ir.actions.act_window_close'}
