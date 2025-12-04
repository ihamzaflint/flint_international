from odoo import models, fields, api


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    def _set_default_values(self):
        """Set default values for existing records"""
        tickets_without_email = self.search([('partner_email', '=', False)])
        for ticket in tickets_without_email:
            if ticket.partner_id and ticket.partner_id.email:
                ticket.partner_email = ticket.partner_id.email
            else:
                ticket.partner_email = 'default@example.com'

    @api.model
    def _handle_null_values(self):
        """Handle null values in tickets"""
        # Find tickets with null email
        tickets_with_null = self.search([('partner_email', '=', False)])
        
        for ticket in tickets_with_null:
            if not ticket.partner_email and ticket.partner_id:
                # Set email from partner if available
                ticket.partner_email = ticket.partner_id.email or 'default@example.com'

    def init(self):
        """Initialize module - runs during install/upgrade"""
        super(HelpdeskTicket, self).init()
        self._handle_null_values()
