from odoo import api, fields, models, _
import base64
import logging

_logger = logging.getLogger(__name__)


class LogisticOrderSendSelection(models.TransientModel):
    _name = 'logistic.order.send.selection'
    _description = 'Send Selection Wizard'

    @api.model
    def default_get(self, fields):
        result = super().default_get(fields)
        logistic_order_id = self.env.context.get('active_id')
        if logistic_order_id:
            logistic_order = self.env['logistic.order'].browse(logistic_order_id)
            result['logistic_order_id'] = logistic_order.id
            result['subject'] = _('Selection Request: %s') % logistic_order.name
        return result

    logistic_order_id = fields.Many2one('logistic.order', string='Logistic Order', required=True)
    subject = fields.Char('Subject', required=True)
    template_id = fields.Many2one(
        'mail.template', string='Email Template',
        domain=[('model', '=', 'logistic.order')],
        default=lambda self: self.env.ref('scs_operation.email_template_flight_selection', raise_if_not_found=False)
    )

    def action_send_selection(self):
        self.ensure_one()
        if self.template_id:
            # Update the state before sending email
            self.logistic_order_id.write({'state': 'selection'})
            self.logistic_order_id.activity_update()
            
            # Generate PDF report
            if self.logistic_order_id.order_type == 'flight':
                try:
                    report = self.env.ref('scs_operation.action_report_flight_logistics')
                    pdf_content, _ = report._render_qweb_pdf(self.logistic_order_id.id)
                    
                    # Create attachment
                    attachment = self.env['ir.attachment'].create({
                        'name': f'Flight Logistics Order - {self.logistic_order_id.name}.pdf',
                        'type': 'binary',
                        'datas': base64.b64encode(pdf_content),
                        'res_model': self.logistic_order_id._name,
                        'res_id': self.logistic_order_id.id,
                        'mimetype': 'application/pdf'
                    })
                    
                    # Send email with attachment
                    self.template_id.attachment_ids = [(6, 0, [attachment.id])]
                    self.template_id.send_mail(
                        self.logistic_order_id.id,
                        force_send=True,
                        email_values={'subject': self.subject}
                    )
                    self.template_id.attachment_ids = [(5, 0, 0)]  # Clear attachments
                except Exception as e:
                    _logger.error("Error generating flight logistics report: %s", str(e))

            # Create activity for operation manager
            operation_manager = self.env.ref('scs_operation.group_operation_admin').users[:1]
            if operation_manager:
                self.logistic_order_id.activity_schedule(
                    'mail.mail_activity_data_todo',
                    user_id=operation_manager.id,
                    note=_("Dear %s, Logistic Order %s is ready for your review") % (
                        operation_manager.name, self.logistic_order_id.name),
                )

        return {'type': 'ir.actions.act_window_close'}
