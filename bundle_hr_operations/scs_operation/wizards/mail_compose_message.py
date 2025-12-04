from odoo import models


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    def action_send_mail(self):
        """Override to handle the logistic order state change"""
        context = self.env.context
        result = super(MailComposeMessage, self).action_send_mail()
        
        # Update logistic order state to 'done' after sending the email
        if context.get('mark_logistic_done') and context.get('default_model') == 'logistic.order' and context.get('default_res_ids'):
            logistic_orders = self.env['logistic.order'].browse(context.get('default_res_ids'))
            logistic_orders.write({'state': 'done'})
            # Log the state change
            for order in logistic_orders:
                order.message_post(
                    body=f"Order marked as done after sending completion email.",
                    message_type='notification'
                )
                
        return result

    def cancel_mail(self):
        """Called when the wizard is discarded"""
        # No need to do anything special, just close the wizard
        return {'type': 'ir.actions.act_window_close'}
