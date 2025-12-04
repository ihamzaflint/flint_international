from odoo import fields, models, api, _


class LogisticOrder(models.Model):
    _inherit = 'logistic.order'

    helpdesk_ticket_id = fields.Many2one('helpdesk.ticket', string='Helpdesk Ticket', copy=False)
    payment_ref_id = fields.Many2one('account.move', string='Bill Reference', copy=False)
    insurance_membership_no = fields.Char(string='Insurance Membership No')

    def action_view_helpdesk(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Helpdesk Tickets',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'form',
            'res_id': self.helpdesk_ticket_id.id,
            'domain': [('logistic_order_id', '=', self.id)],
            'target': 'current',
        }

    def action_done(self):
        res = super(LogisticOrder, self).action_done()
        
        # Update ticket with specific order type data
        if self.order_type == 'flight' and self.flight_ticket and self.helpdesk_ticket_id:
            self.helpdesk_ticket_id.write({
                'flight_ticket': self.flight_ticket,
                'location_country_id': self.location_country_id.id,
                'destination_country_id': self.destination_country_id.id,
                'departure_date': self.departure_date,
                'return_date': self.return_date,
            })
        if self.order_type == 'insurance' and self.helpdesk_ticket_id:
            self.helpdesk_ticket_id.write({
                'insurance_membership_no': self.insurance_membership_no,
            })
        
        # Close the associated helpdesk ticket when logistic order is done
        if self.helpdesk_ticket_id and not self.helpdesk_ticket_id.is_closed:
            # Find the closed stage
            closed_stage = self.env['helpdesk.stage'].search([('is_closed', '=', True)], limit=1)
            if closed_stage:
                self.helpdesk_ticket_id.write({
                    'stage_id': closed_stage.id
                })
                # Log a message on the ticket about automatic closure
                self.helpdesk_ticket_id.message_post(
                    body=_("Ticket automatically closed because logistic order '%s' has been completed.") % self.name,
                    subject=_("Ticket Closed - Logistic Order Completed")
                )
        
        return res

    def action_show_payment(self):
        self.ensure_one()
        return {
            'name': 'Account Payment',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree',
            'target': 'current',
            'domain': [('logistic_order_id', '=', self.id)],
            'context': {'no_open': True, 'create': False, 'edit': False}
        }


