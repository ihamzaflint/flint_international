from odoo import models, fields, api, _

class PayrollRejectionReasonWizard(models.TransientModel):
    _name = 'payroll.rejection.reason.wizard'
    _description = 'Payroll Rejection Reason Wizard'

    rejection_reason = fields.Text(string='Rejection Reason')

    def action_reject(self):
        current_object = self.env['hr.payslip.run'].browse(self.env.context.get('active_id'))
        self.ensure_one()
        current_object.write({'rejection_reason': self.rejection_reason, 'state': self.env.context.get('rejection_department')})
        current_object._send_rejection_notification(self.env.context.get('rejection_department'))
        return {'type': 'ir.actions.act_window_close'}