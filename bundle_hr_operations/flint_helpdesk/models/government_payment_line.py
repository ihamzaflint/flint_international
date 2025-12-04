from odoo import api, fields, models


class GovernmentPaymentLine(models.Model):
    _inherit = "government.payment.line"


    helpdesk_ticket_id = fields.Many2one('helpdesk.ticket', string="Helpdesk Ticket")


    def open_post_attachment_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Attachment Wizard',
            'res_model': 'post.attachment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'line_id': self.id}
        }
