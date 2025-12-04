from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RequisitionForm(models.Model):
    _name = "requisition.form"
    _description = "Requisition Form"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'sequence'
    _order = 'id desc'

    sequence = fields.Char(string='Request Loan Sequence', copy=False, readonly=True, default='New')

    vendor_id = fields.Many2one(
        'res.partner',
        string='Vendor',
        default=lambda self: self.env.ref(
            'requisition_form.demo_vendor_partner',
            raise_if_not_found=False
        )
    )
    description = fields.Char(string='Description')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approval', 'Approval'),
        ('approved', 'Approved'),
        ('confirm', 'Confirm'),
        ('rejected', 'Rejected'),
    ], default='draft')
    requisition_form_line_ids = fields.One2many(
        'requisition.form.line',
        'requisition_form_id',
        string='Products'
    )
    approval_line_ids = fields.One2many(
        'requisition.approval.line',
        'requisition_form_id',
        string='Approval Lines'
    )
    purchase_order_id = fields.Many2one('purchase.order', string="Purchase Order", copy=False)
    purchase_approval_config_id = fields.Many2one('purchase.approval.config', string="Approval Config", copy=False)

    def create(self, vals):
        if vals.get('sequence', _('New')) == _('New'):
            vals['sequence'] = self.env['ir.sequence'].next_by_code('requisition.form') or _('New')
        res = super(RequisitionForm, self).create(vals)
        return res

    def button_draft(self):
        for rec in self:
            rec.state = 'draft'
            rec.approval_line_ids.unlink()

    def _create_activity(self, user):
        """Schedule To-Do activity for given user"""
        self.activity_schedule(
            'mail.mail_activity_data_todo',
            user_id=user.id,
            note=f"Please approve requisition: {self.description or self.id}"
        )

    def button_request_approval(self):
        """Request approval: auto-create requisition if not selected"""
        for rec in self:
            # Fetch the latest active approval configuration from configuration
            latest_approval_config = self.env['purchase.approval.config'].search([('state', '=', 'confirm')],
                                                                                 order='id desc', limit=1)

            if not latest_approval_config:
                rec.write({
                    'state': 'approval',
                })
                pass
                # raise UserError(
                #     "No active approval configuration selected / found. Please ask your admin to create one!")

            allowed_products = latest_approval_config.product_ids
            line_products = rec.requisition_form_line_ids.mapped('product_id')
            mismatched_products = line_products - allowed_products

            if mismatched_products:
                # Prepare names for display
                product_names = ", ".join(mismatched_products.mapped('display_name'))
                allowed_names = ", ".join(allowed_products.mapped('display_name'))

                raise ValidationError(_(
                    "The following products are not allowed:\n%s\n\n"
                    "Allowed products:\n%s\n\n"
                    "Please ask your admin to allow your products for requisition!"
                ) % (product_names, allowed_names))

            approver_lines = []
            current_user_employee = self.env.user.employee_id
            if current_user_employee.parent_id:
                approver_lines.append((0, 0, {
                    'approver_id': current_user_employee.parent_id.user_id.id,
                    'is_approved': False,
                }))

            for line in latest_approval_config.purchase_approval_line_ids:
                approver_lines.append((0, 0, {
                    'approver_id': line.approver_id.id,
                    'is_approved': False,

                }))
            if approver_lines:
                rec.approval_line_ids = [(5, 0, 0)]  # Clear existing approval lines (Good Practice Only, however no need)
                rec.approval_line_ids = approver_lines  # Assign approver lines to the purchase order

                # # Schedule activity for next approver (first unapproved line)
                first_line = rec.approval_line_ids[0]
                if first_line:
                    rec._create_activity(first_line.approver_id)

            rec.write({
                'purchase_approval_config_id': latest_approval_config.id,
                'state': 'approval',
            })

    def button_approve(self):
        """Approve only current user's line and schedule next"""
        for rec in self:
            current_user = self.env.user
            pending_lines = rec.approval_line_ids.filtered(lambda l: not l.is_approved).sorted('sequence')

            if not pending_lines:
                raise UserError("All approval lines are already approved!")

            # Current user must be next approver
            next_line = pending_lines[0]
            if next_line.approver_id != current_user:
                raise UserError("You are not the current approver!")

            # Approve line
            next_line.is_approved = True

            # Complete activity
            rec.activity_ids.filtered(lambda a: a.user_id == current_user and a.active).action_done()

            # Schedule next approver
            remaining_lines = rec.approval_line_ids.filtered(lambda l: not l.is_approved).sorted('sequence')
            if remaining_lines:
                rec._create_activity(remaining_lines[0].approver_id)
            else:
                # All approved → state confirm
                rec.state = 'approved'

    def button_confirm(self):
        """Create Purchase Order after all approvals"""
        for rec in self:
            if rec.state != 'approved':
                raise UserError("Requisition not fully approved yet!")

            po_lines = []
            for line in rec.requisition_form_line_ids:
                po_lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'name': line.remarks or line.product_id.name,
                    'product_qty': line.qty,
                    'price_unit': line.product_id.list_price,
                    'taxes_id': [(6, 0, line.tax_ids.ids)],
                }))

            po_vals = {
                'partner_id': rec.vendor_id.id,
                'order_line': po_lines,
                'requisition_form_id': rec.id,
            }
            purchase_order = self.env['purchase.order'].create(po_vals)

            if purchase_order:
                rec.purchase_order_id = purchase_order.id
                rec.state = 'confirm'

    def button_reject(self):
        for rec in self:
            rec.state = 'rejected'

    def open_purchase_order(self):
        for rec in self:
            if not rec.purchase_order_id:
                raise UserError(_('No Purchase Order Exists!'))

            else:
                return {
                    'name': _('Purchase Order'),
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'purchase.order',
                    'res_id': self.purchase_order_id.id,
                    'target': 'current',
                }


class RequisitionFormLine(models.Model):
    _name = "requisition.form.line"
    _description = "Inventory Management Lines"

    requisition_form_id = fields.Many2one('requisition.form', string='Requisition Form')
    product_id = fields.Many2one('product.template', string='Product')
    tax_ids = fields.Many2many('account.tax', string='Taxes', related='product_id.supplier_taxes_id')
    qty = fields.Float(string='Qty')
    remarks = fields.Char(string='Remarks')


class RequisitionApprovalLine(models.Model):
    _name = "requisition.approval.line"
    _description = "Requisition Approval Line"

    requisition_form_id = fields.Many2one('requisition.form', string='Requisition Form', ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=1)
    approver_id = fields.Many2one('res.users', string='Approver', required=True)
    is_approved = fields.Boolean(string='Approved', default=False)
