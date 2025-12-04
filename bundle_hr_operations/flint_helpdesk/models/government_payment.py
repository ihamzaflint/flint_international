from odoo import fields, models,_
from odoo.exceptions import ValidationError


class GovernmentPayment(models.Model):
    _inherit = "government.payment"

    ticket_count = fields.Integer(compute='_compute_ticket_count', string='Ticket Count')
    muqeem_attachment_ids = fields.Many2many('ir.attachment', 'muqeem_attachment_rel', 'muqeem_id', 'attachment_id',
                                                string='Muqeem Attachments')
    previous_state = fields.Char(string='Previous State', help='Stores the state before putting the payment on hold')

    def validate_hold_ticket(self):
        self.ensure_one()
        # Find the associated helpdesk ticket
        ticket = self.env['helpdesk.ticket'].search([('government_payment_id', '=', self.id)], limit=1)
        if ticket:
            # Get the default stage (not on hold)
            default_stage = self.env['helpdesk.stage'].search([('is_on_hold', '=', False)], limit=1)
            if default_stage:
                ticket.write({'stage_id': default_stage.id})
                # Add a note in the chatter
                ticket.message_post(body=_('Ticket validated and removed from hold status.'))
            else:
                raise ValidationError(_('No default stage found for the helpdesk ticket.'))
        else:
            raise ValidationError(_('No helpdesk ticket found for this government payment.'))
        
        # Change the state to validate
        self.write({'state': 'validate'})
    def _validate_payments(self):
        if self.payment_type == 'individual':
            for line in self.payment_line_ids:
                # Get attachments and ensure proper access rights
                attachments = self.env['ir.attachment'].sudo().search([
                    ('id', 'in', line.operation_order_attachment.ids)
                ])

                # Create copies of attachments with proper access rights for helpdesk users
                helpdesk_attachments = []
                for attachment in attachments:
                    new_attachment = attachment.sudo().copy({
                        'res_model': 'helpdesk.ticket',
                        'res_id': line.helpdesk_ticket_id.id,
                        'name': attachment.name,
                        # Grant read access to helpdesk users
                        'public': True  # or configure specific group access as needed
                    })
                    helpdesk_attachments.append(new_attachment.id)

                if line.payment_state == 'paid' and (
                        'not_paid' in self.payment_line_ids.mapped('payment_state') or
                        'not_paid' not in self.payment_line_ids.mapped('payment_state')
                ):
                    line.helpdesk_ticket_id.activity_schedule(
                        summary=_('Government Payment Done'),
                        note=_('Please Close your Ticket %s') % line.helpdesk_ticket_id.name,
                        user_id=line.helpdesk_ticket_id.user_id.id,
                        attachment_ids=[(4, attachment_id) for attachment_id in helpdesk_attachments]
                    )
        elif self.payment_type == 'no_payment':
            if not self.muqeem_attachment_ids:
                raise ValidationError(_("Please attach the muqeem file"))
            else:
                # get copy of attachments with proper access rights for helpdesk users
                helpdesk_attachments = []
                ticket = self.env['helpdesk.ticket'].search([('government_payment_id', '=', self.id)], limit=1)
                for attachment in self.muqeem_attachment_ids:
                    new_attachment = attachment.sudo().copy({
                        'res_model': 'helpdesk.ticket',
                        'res_id': ticket.id,
                        'name': attachment.name,
                        # Grant read access to helpdesk users
                        'public': True  # or configure specific group access as needed
                    })
                    helpdesk_attachments.append(new_attachment.id)
                ticket.activity_schedule(
                    summary=_('Muqeem File Attached'),
                    note=_('Please check the attached muqeem file'),
                    user_id=ticket.user_id.id,
                    attachment_ids=[(4, attachment_id) for attachment_id in helpdesk_attachments]
                )
        return super(GovernmentPayment, self)._validate_payments()

    def show_ticket(self):
        self.ensure_one()
        ticket = self.env['helpdesk.ticket'].search([('government_payment_id', '=', self.id)], limit=1)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Helpdesk Ticket',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'tree,form',
            'res_id': ticket.id,
            'domain': [('id', '=', ticket.id)],
            'target': 'current',
            'context': {'create': False, 'edit': False, 'delete': False,'open':False}
        }

    def _compute_ticket_count(self):
        for rec in self:
            rec.ticket_count = self.env['helpdesk.ticket'].search_count([('government_payment_id', '=', rec.id)])

    def change_state(self):
        res = super(GovernmentPayment, self).change_state()
        ctx = self._context
        if ctx.get("on_hold") and not ctx.get('pass_hold'):
            ticket = self.env['helpdesk.ticket'].search([('government_payment_id','=',self.id)],limit=1)
            if ticket:
                return {
                    'name': _('Operation On Hold Ticket Reason'),
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'operation.on.hold.ticket.reason',
                    'target': 'new',
                }
        elif ctx.get('on_hold') and ctx.get('pass_hold'):
            # Store the current state before changing to on_hold
            self.write({
                'previous_state': self.state,
                'state': 'on_hold',
                'rejection_reason': ctx.get('rejection_reason')
            })
        elif ctx.get('draft'):
            ticket = self.env['helpdesk.ticket'].search([('government_payment_id', '=', self.id)], limit=1)
            if ticket:
                self.state = "draft"
                ticket.write({'stage_id': self.env['helpdesk.stage'].search([('is_draft', '=', True)], limit=1).id})
                self.activity_schedule('mail.mail_activity_data_todo',
                                       note="%s Your Ticket has been set to draft" % self.create_uid.name,
                                       user_id=ticket.user_id.id)
            else:
                self.state = "draft"
        return res
