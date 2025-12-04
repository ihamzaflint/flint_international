from odoo import api, fields, models, _

class TicketCloseMailComposer(models.TransientModel):
    _name = 'ticket.close.mail.composer'
    _inherit = 'mail.compose.message'
    _description = 'Ticket Close Mail Composer'

    # Override attachment_ids to use a different table
    attachment_ids = fields.Many2many(
        'ir.attachment', 'ticket_close_mail_composer_attachment_rel',
        'wizard_id', 'attachment_id', string='Attachments'
    )

    # Override partner_ids to use a different table
    partner_ids = fields.Many2many(
        'res.partner', 'ticket_close_mail_composer_partner_rel',
        'wizard_id', 'partner_id', string='Recipients'
    )

    @api.model
    def default_get(self, fields):
        res = super(TicketCloseMailComposer, self).default_get(fields)
        ticket_id = self.env.context.get('active_id')
        if ticket_id:
            ticket = self.env['helpdesk.ticket'].browse(ticket_id)
            template = self.env.ref('flint_helpdesk.email_template_helpdesk_ticket_close', raise_if_not_found=False)
            if template:
                res.update({
                    'template_id': template.id,
                    'model': 'helpdesk.ticket',
                    'res_id': ticket_id,
                    'partner_ids': [(6, 0, [ticket.employee_id.address_id.id])],
                })
        return res

    def action_send_mail(self):
        self.ensure_one()
        # Send the email
        super(TicketCloseMailComposer, self).send_mail()
        
        # Get the ticket and close stage
        ticket = self.env['helpdesk.ticket'].browse(self.res_id)
        close_stage = self.env["helpdesk.stage"].search([("is_closed", "=", True)], limit=1)
        
        # Update ticket stage and post message
        if ticket and close_stage:
            ticket.write({'stage_id': close_stage.id})
            ticket.message_post(body=_("Ticket is closed by %s" % self.env.user.name))
        
        return {'type': 'ir.actions.act_window_close'}
