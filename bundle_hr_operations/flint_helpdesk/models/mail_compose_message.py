from odoo import models, _

class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    def action_send_mail(self):
        result = super(MailComposeMessage, self).action_send_mail()
        # Check if this is a ticket closure email
        if self._context.get('close_ticket') and self.model == 'helpdesk.ticket':
            # Use active_ids from context to ensure we get the correct record(s)
            active_ids = self._context.get('active_ids', [])
            tickets = self.env['helpdesk.ticket'].browse(active_ids)
            close_stage = self.env["helpdesk.stage"].search([("is_closed", "=", True)], limit=1)
            if tickets and close_stage:
                tickets.write({'stage_id': close_stage.id})
                for ticket in tickets:
                    ticket.message_post(body=_("Ticket is closed by %s" % self.env.user.name))
        return result
