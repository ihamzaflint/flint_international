from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import re


class PurchaseApprovalConfig(models.Model):
    _name = 'purchase.approval.config'
    _description = 'Hierarchy'
    _rec_name = 'name'
    _order = 'id desc'

    name = fields.Char('Hierarchy Name')
    code = fields.Char('Code')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
    ],
        default='draft', string='Status')
    product_ids = fields.Many2many('product.template', string='Allowed Products')

    purchase_approval_line_ids = fields.One2many(
        'purchase.approval.line',
        'purchase_approval_config_id',
        string='Purchase Approval Line'
    )

    @api.onchange('name')
    def _onchange_name(self):
        for rec in self:
            if not rec.code:
                rec.code = re.sub(r'[^a-zA-Z0-9]', '_', rec.name).lower() if rec.name else ''

    def button_confirm(self):
        """
        Activate record for use.
        """
        for rec in self:
            if self.env['purchase.approval.config'].search_count(
                    [('code', '=', rec.code), ('state', '=', 'confirm')]) == 0:
                rec.write({'state': 'confirm'})
            else:
                raise ValidationError(
                    _('Another record with the same code already exists. Please choose a unique code.'))

    def button_draft(self):
        """
        Draft record to stop use.
        """
        for rec in self:
            rec.state = 'draft'


class PurchaseApprovalLine(models.Model):
    _name = 'purchase.approval.line'
    _description = 'Purchase Approval Line'

    purchase_approval_config_id = fields.Many2one('purchase.approval.config',
                                                  string='Purchase Approval Config')
    approver_id = fields.Many2one('res.users', string="Approver")
