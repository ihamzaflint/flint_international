from odoo import models


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    def _action_send_mail(self, auto_commit=False):
        """ Override to mark logistic order email as sent """
        result = super()._action_send_mail(auto_commit=auto_commit)
        
        # Check if we need to mark the logistic order email as sent
        if self._context.get('mark_logistic_email_sent'):
            logistic_orders = self.env['logistic.order'].browse(self._context.get('default_res_ids', []))
            for order in logistic_orders:
                order.mark_email_sent()
        
        return result
