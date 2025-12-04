from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    saddad_no = fields.Char("Saddad No", copy=False, index=True)
    service_type = fields.Many2one("service.type", string="Service Type")
    service_name = fields.Char("Service Name")
    project_id = fields.Many2one("client.project", string="Project")
    analytic_account_id = fields.Many2one("account.analytic.account", string="Analytic Account")
    government_payment_ref_id = fields.Many2one("government.payment", string="Government Payment Ref", readonly=True)
    government_payment_line_ref_id = fields.Many2one("government.payment.line", string="Government Payment Ref",
                                                     readonly=True)
    logistic_order_id = fields.Many2one('logistic.order', string="Logistic Order")
    order_type = fields.Selection(related='logistic_order_id.order_type', string="Order Type")
    employee_id = fields.Many2one("hr.employee", string="Employee")
    employee_iqama_no = fields.Char("Employee Iqama No")
    file_no = fields.Char("File No")

    @api.constrains('saddad_no')
    def _check_saddad_no(self):
        for record in self:
            if record.saddad_no and not record.saddad_no.isdigit():
                raise ValidationError("Saddad Number must contain only numbers.")

    # send email to government payment requester when payment is done
    def action_post(self):
        res = super(AccountPayment, self).action_post()
        if self.government_payment_ref_id:
            self.government_payment_ref_id.sudo().activity_schedule(
                'mail.mail_activity_data_todo', user_id=self.government_payment_ref_id.create_uid.id,
                note='Payment Done for the request %s' % self.government_payment_ref_id.name)
            self.government_payment_line_ref_id.sudo().write(
                {'payment_state':
                     'paid'}
            )
        return res

    def _prepare_move_line_default_vals(self, write_off_line_vals=None, force_balance=False):
        self.ensure_one()
        # Only handle outbound payments, for other cases use the standard implementation
        if self.payment_type != 'outbound':
            return super()._prepare_move_line_default_vals(write_off_line_vals=write_off_line_vals, force_balance=force_balance)
                
        if self.payment_type == 'outbound' and self.saddad_no or self.employee_iqama_no:   
            line_vals_list = []
            related_payment_line = self.government_payment_line_ref_id
            if related_payment_line and related_payment_line.service_type_ids:
                credit_account = related_payment_line.service_type_ids[0].default_credit_account_id
                debit_account = related_payment_line.service_type_ids[0].default_debit_account_id
            else:
                related_payment_line = self.env['government.payment.line'].search(
                    [('saddad_no', '=', self.saddad_no)], limit=1)
                if related_payment_line and related_payment_line.service_type_ids:
                    credit_account = related_payment_line.service_type_ids[0].default_credit_account_id
                    debit_account = related_payment_line.service_type_ids[0].default_debit_account_id
                else:
                    credit_account = self.government_payment_ref_id.service_type_id.default_credit_account_id
                    debit_account = self.government_payment_ref_id.service_type_id.default_debit_account_id
                    # credit_account = self.env['account.account'].search(
                    #     [('code', '=', '101003')], limit=1)
                    # debit_account = self.env['account.account'].search(
                    #     [('code', '=', '201002')], limit=1)

            if not credit_account or not debit_account:
                if self.government_payment_line_ref_id and self.government_payment_line_ref_id.service_type_ids:
                    raise ValidationError(_(
                        "Please configure the default credit and debit accounts for the service type %s") % 
                        self.government_payment_line_ref_id.service_type_ids[0].name)
                else:
                    raise ValidationError(_(
                        "Could not determine the payment accounts. Please configure default accounts or specify a service type."))

            line_vals_list.extend([
                {
                    'name': self.ref or '/',
                    'account_id': credit_account.id,
                    'partner_id': self.partner_id.id,
                    'currency_id': self.currency_id.id,
                    'amount_currency': -self.amount,
                    'debit': 0.0,
                    'credit': self.amount,
                },
                {
                    'name': self.ref or '/',
                    'account_id': debit_account.id,
                    'partner_id': self.partner_id.id,
                    'currency_id': self.currency_id.id,
                    'amount_currency': self.amount,
                    'debit': self.amount,
                    'credit': 0.0,
                }
            ])

            if force_balance:
                # Apply force_balance adjustments if needed
                total_balance = sum(line['debit'] - line['credit'] for line in line_vals_list)
                if not self.currency_id.is_zero(total_balance):
                    if total_balance > 0:
                        line_vals_list[0]['credit'] += total_balance
                    else:
                        line_vals_list[1]['debit'] += -total_balance

            return line_vals_list
        else:
            return super()._prepare_move_line_default_vals(write_off_line_vals=write_off_line_vals, force_balance=force_balance)