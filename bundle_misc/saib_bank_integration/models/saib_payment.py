from odoo import models, fields, api
from odoo.exceptions import UserError

class SaibPayment(models.Model):
    _name = 'saib.payment'
    _inherit = ['mail.thread']
    _description = 'SAIB Payment Transaction'

    name = fields.Char('Reference', required=True, copy=False, readonly=True, default='New')
    payment_type = fields.Selection([
        ('single', 'Single Payment'),
        ('bulk', 'Bulk Payment')
    ], required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent to Bank'),
        ('confirmed', 'Confirmed'),
        ('failed', 'Failed')
    ], default='draft', tracking=True)
    
    partner_id = fields.Many2one('res.partner', string='Partner')
    amount = fields.Monetary('Amount', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True)
    execution_date = fields.Date('Execution Date', required=True)
    
    debtor_account = fields.Char('Debtor Account', required=True)
    creditor_account = fields.Char('Creditor Account', required=True)
    bank_reference = fields.Char('Bank Reference', readonly=True)

    # [sanjay-techvoot] Auto-generate sequence for new payments if name is 'New'.
    # Ensures each payment gets a unique reference on create.
    @api.model
    def create(self, vals_list):
        if vals_list.get('name', 'New') == 'New':
            vals_list['name'] = self.env['ir.sequence'].next_by_code('saib.payment')
        return super().create(vals_list)
    
    # [sanjay-techvoot] Build payment payload and send to SAIB API; update state based on response.
    # Calls SAIB API via saib.api and marks payment confirmed or failed.
    def action_send_to_bank(self):
        self.ensure_one()
        try:
            api = self.env['saib.api']
            
            payment_data = {
                'instructionID': self.name,
                'CreationDateTime': fields.Datetime.now().isoformat(),
                'Currency': self.currency_id.name,
                'DebtorAccount': {
                    'AccountNumber': self.debtor_account,
                    'DebtorName': self.env.company.name,
                },
                'CreditorAccount': {
                    'AccountNumber': self.creditor_account,
                    'CreditorName': self.partner_id.name,
                },
                'ExecutionDate': self.execution_date.isoformat(),
                'Amount': str(self.amount),
            }
            
            endpoint = '/b2b-rest-payment-service/b2b/payment/single' if self.payment_type == 'single' else '/b2b-rest-bulk-payment-service/b2b/payment/bulk'
            
            response = api._make_request('POST', endpoint, payment_data)
            
            if response.get('Data', {}).get('Status') == 'SUCCESS':
                self.write({
                    'state': 'confirmed',
                    'bank_reference': response.get('Data', {}).get('BankReference')
                })
            else:
                self.write({'state': 'failed'})
                raise UserError(response.get('Data', {}).get('StatusReason', 'Payment Failed'))
                
        except Exception as e:
            self.write({'state': 'failed'})
            raise UserError(str(e))
