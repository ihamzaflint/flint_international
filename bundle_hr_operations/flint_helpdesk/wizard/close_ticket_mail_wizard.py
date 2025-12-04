from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class CloseTicketMailWizard(models.TransientModel):
    _name = 'close.ticket.mail.wizard'
    _description = 'Close Ticket Mail Wizard'

    ticket_id = fields.Many2one('helpdesk.ticket', string='Ticket', required=True)
    template_id = fields.Many2one('mail.template', string='Email Template', required=True,
                                default=lambda self: self.env.ref('flint_helpdesk.solved_ticket_request_email_template_inherited'))
    subject = fields.Char('Subject', required=True)
    body = fields.Html('Body', required=True, sanitize=False)
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')

    @api.onchange('template_id')
    def onchange_template_id(self):
        if self.template_id:
            self.subject = self.template_id._render_template(
                self.template_id.subject,
                self.ticket_id._name,
                self.ticket_id.id
            )
            self.body = self.template_id._render_template(
                self.template_id.body_html,
                self.ticket_id._name,
                self.ticket_id.id
            )
            # Get attachments from chatter
            self.attachment_ids = [(6, 0, self.ticket_id.message_ids.mapped('attachment_ids').ids)]

    def action_send_mail(self):
        self.ensure_one()
        # Send mail
        mail_values = {
            'email_from': self.template_id.email_from,
            'email_to': self.ticket_id.employee_id.work_email,
            'subject': self.subject,
            'body_html': self.body,
            'attachment_ids': [(6, 0, self.attachment_ids.ids)],
            'model': self.ticket_id._name,
            'res_id': self.ticket_id.id,
        }
        mail = self.env['mail.mail'].create(mail_values)
        mail.send()
        
        # Close the ticket
        close_stage = self.env['helpdesk.stage'].search(
            [("is_closed", "=", True)], limit=1
        )
        if not close_stage:
            raise ValidationError(_("Please configure 'Close' stage in helpdesk settings"))
        self.ticket_id.write({'stage_id': close_stage.id})
        return {'type': 'ir.actions.act_window_close'}
