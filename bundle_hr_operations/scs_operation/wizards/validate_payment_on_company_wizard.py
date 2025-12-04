from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ValidatePaymentOnCompanyWizard(models.TransientModel):
    _name = 'validate.payment.on.company.wizard'
    _description = 'Validate Payment On Company Wizard'

    government_payment_id = fields.Many2one('government.payment', string='Government Payment', required=True)
    partner_id = fields.Many2one('res.partner', string='Customer', domain=[('customer_rank', '>', 0)])
    is_flint_payment = fields.Boolean(string='Pay through Flint')

    @api.constrains('partner_id', 'is_flint_payment')
    def _check_selection(self):
        for record in self:
            if not record.is_flint_payment and not record.partner_id:
                raise ValidationError(_('Please select a customer or choose to pay through Flint.'))
            if record.is_flint_payment and record.partner_id:
                raise ValidationError(_('Please select only one option: customer or Flint payment.'))

    def validate_payment(self):
        self.ensure_one()
        active_obj = self.env[self._context.get('active_model')].browse(self._context.get('active_id'))
        ctx = {
            'partner_id': self.partner_id.id if self.partner_id else False,
            'government_payment_id': active_obj.id
        }
        if self.is_flint_payment:
            ctx.update({'is_flint_payment': True})
        if active_obj.state == 'draft':
            active_obj.write({'state': 'submit',
                              'is_flint_payment': self.is_flint_payment,
                              'wizard_partner_id': self.partner_id.id})
            users = self.env.ref("scs_operation.group_operation_admin").users
            note = _("Hello Mr. Mofleh kindly Approve payment request %s") % active_obj.name
            for user in users:
                active_obj.activity_schedule(
                    user_id=user.id,
                    note=note,
                )
            return {'type': 'ir.actions.act_window_close'}
        payment = self.government_payment_id.with_context(**ctx).create_payment()
        if payment:
            self.government_payment_id.write({
                'state': 'validate',
                'payment_reference_ids': [(4, payment.id, 0)]
            })
        return {'type': 'ir.actions.act_window_close'}
