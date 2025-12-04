from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _name = 'purchase.order.approval.history'
    _description = 'Purchase Order Approval History'

    user_id = fields.Many2one('res.users', string='User')
    status = fields.Selection(
        [('request_approval', 'Request Approval'), ('approved', 'Approved'), ('rejected', 'Rejected'),
         ('recall', 'Recall'), ],
        string='Status', )
    action_date = fields.Date(string='Action Date')
    purchase_id = fields.Many2one('purchase.order', string='Purchase Order')
    purchase_order_status = fields.Selection(
        selection=lambda self: self.env['purchase.order']._fields['state'].selection, string='Status')
