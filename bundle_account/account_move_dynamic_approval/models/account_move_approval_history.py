from odoo import fields, models


class PurchaseOrder(models.Model):
    _name = 'account.move.approval.history'
    _description = 'Purchase Order Approval History'

    user_id = fields.Many2one('res.users', string='User')
    status = fields.Selection(
        [('request_approval', 'Request Approval'), ('approved', 'Approved'), ('rejected', 'Rejected'),
         ('recall', 'Recall'), ],
        string='Status', )
    action_date = fields.Date(string='Action Date')
    account_id = fields.Many2one('account.move', string='Account Move')
    account_move_status = fields.Selection(
        selection=lambda self: self.env['account.move']._fields['state'].selection, string='Status')
