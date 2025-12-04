from odoo import api, fields, models


class PostAttachmentWizard(models.TransientModel):
    _name = 'post.attachment.wizard'
    _description = 'Post Attachment Wizard'

    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')

    def action_post_attachment(self):
        self.ensure_one()
        res_obj = self.env['government.payment.line'].browse(self._context.get('line_id'))
        
        # Update attachments to link them to the government.payment.line
        self.attachment_ids.write({
            'res_model': 'government.payment.line',
            'res_id': res_obj.id,
        })
        
        res_obj.write({
            'operation_order_attachment': [(4, attachment.id) for attachment in self.attachment_ids]
        })