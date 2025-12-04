from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    # state = fields.Selection(selection_add=[('draft', ),('on_hold', 'On Hold')])

    def _prepare_move_line_default_vals(self, write_off_line_vals=None, force_balance=False):
        vals = super()._prepare_move_line_default_vals(write_off_line_vals, force_balance)
        if self.payment_type == 'outbound':
            helpdesk_ticket = self.logistic_order_id.helpdesk_ticket_id
            if helpdesk_ticket:
                credit_account = helpdesk_ticket.service_type_ids[0].default_credit_account_id
                debit_account = helpdesk_ticket.service_type_ids[0].default_debit_account_id
            else:
                credit_account = self.env['account.account'].search(
                    [('account_type', '=', 'asset_current'), ('company_id', '=', self.env.company.id)], limit=1)
                debit_account = self.env['account.account'].search(
                    [('account_type', '=', 'expense'), ('company_id', '=', self.env.company.id)], limit=1)
            if self.logistic_order_id:
                if credit_account and debit_account:
                    # Use a different account for vendor outbound payments
                    vals[0]['account_id'] = credit_account.id
                    vals[1]['account_id'] = debit_account.id
                else:
                    raise ValidationError("Please configure the default credit and debit"
                                          " accounts for the service type %s" %
                                          helpdesk_ticket.service_type_ids[0].name)
            else:
                pass
        return vals

    def on_hold_process(self):
        self.ensure_one()
        return {
            'name': 'On Hold Reason',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'operation.on.hold.ticket.reason',
            'target': 'new',
        }


class AccountMove(models.Model):
    _inherit = 'account.move'
    
    state = fields.Selection(selection_add=[('draft',), ('on_hold', 'On Hold')],ondelete={'on_hold':'set draft'})
