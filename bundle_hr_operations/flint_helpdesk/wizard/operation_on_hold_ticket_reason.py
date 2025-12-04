from odoo import fields, models


class OperationOnHoldTicketReason(models.TransientModel):
    _name = 'operation.on.hold.ticket.reason'
    _description = 'Operation On Hold Ticket Reason'
    on_hold_reason = fields.Text(string='On Hold Reason', required=True)

    def action_on_hold(self):
        active_record = self.env[self._context.get('active_model')].browse(self._context.get('active_id'))
        on_hold_stage_id = self.env['helpdesk.stage'].search([('is_on_hold', '=', True)], limit=1)
        if active_record and self._context.get('active_model') == 'government.payment':
            ticket = self.env['helpdesk.ticket'].search([('government_payment_id', '=', active_record.id)], limit=1)
            if ticket:
                ticket.write({'stage_id': on_hold_stage_id.id})
                ticket.activity_schedule(
                    'mail.mail_activity_data_todo',
                    note='the Ticket %s has been put on hold for the following reason %s' % (
                        ticket.name, self.on_hold_reason),
                    user_id=ticket.user_id.id)
                active_record.change_activity_state()
                ticket.write({'stage_id': on_hold_stage_id.id})
            active_record.state = 'on_hold'
        elif active_record and self._context.get('active_model') == 'account.payment':
            operation_process_id = active_record.government_payment_ref_id
            if operation_process_id:
                ticket = self.env['helpdesk.ticket'].search([('government_payment_id', '=', operation_process_id.id)], limit=1)
                if ticket:
                    ticket.write({'stage_id': on_hold_stage_id.id})
                    ticket.activity_schedule(
                        'mail.mail_activity_data_todo',
                        note='the Ticket %s has been put on hold for the following reason %s' % (
                            ticket.name, self.on_hold_reason),
                        user_id=ticket.user_id.id)
                operation_process_id.with_context({'on_hold':1,
                                                'pass_hold':1,
                                                'rejection_reason':self.on_hold_reason}).change_state()
                operation_process_id.activity_schedule(
                    'mail.mail_activity_data_todo',
                    note='the Operation Process %s has been put on hold for the following reason %s' % (
                        operation_process_id.name, self.on_hold_reason),
                    user_id=operation_process_id.create_uid.id)
            active_record.state = 'on_hold'
        return {'type': 'ir.actions.act_window_close'}
