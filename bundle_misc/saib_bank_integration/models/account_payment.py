from odoo import models, fields

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    saib_payment_id = fields.Many2one('saib.payment', string='SAIB Payment', readonly=True)
    saib_reference = fields.Char('SAIB Reference', readonly=True)
    saib_status = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent to Bank'),
        ('processing', 'Processing'),
        ('done', 'Done'),
        ('failed', 'Failed')
    ], string='SAIB Status', related='saib_payment_id.state', readonly=True)
