from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    requisition_form_id = fields.Many2one(
        'requisition.form',
        string='Requisition Form',
        ondelete='set null'
    )
