""" inherit purchase.order """
from odoo import _, models, fields
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _name = 'purchase.order'
    _inherit = ['purchase.order', 'dynamic.approval.mixin']
    _not_matched_action_xml_id = 'purchase_dynamic_approval.confirm_purchase_order_wizard_action'

    # ToDo: remove readonly from field state. it used to allow import historical data only
    state = fields.Selection(
        selection_add=[('under_approval', 'Under Approval'), ('approved', 'Approved'), ('purchase',)],
        ondelete={'under_approval': 'set default', 'approved': 'set default', 'purchase': 'set default'},
        readonly=False,
    )
    appear_recall_button = fields.Boolean(
        compute='_compute_appear_recall_button',
    )

    partner_id = fields.Many2one(
        string='Customer Name',)
    approval_history_ids = fields.One2many(
        'purchase.order.approval.history',
        'purchase_id',)
    
    def action_draft(self):
        res = super(PurchaseOrder, self).button_draft()
        self.remove_approval_requests()
        return res

    def action_cancel(self):
        res = super(PurchaseOrder, self).button_cancel()
        self.mapped('dynamic_approve_request_ids').write({
            'status': 'rejected',
            'approve_date': False,
            'approved_by': False,
        })
        return res

    def button_confirm(self):
        """ override to restrict user to confirm if there is workflow """
        for order in self:
            if order.state not in ['draft', 'sent','approved']:
                continue
            order.order_line._validate_analytic_distribution()
            order._add_supplier_to_product()
            # Deal with double validation process
            if order._approval_allowed():
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
        if self.mapped('dynamic_approve_request_ids') and \
                self.mapped('dynamic_approve_request_ids').filtered(lambda request: request.status != 'approved'):
            raise UserError(
                _('You can not confirm order, There are pending approval.'))
        for record in self:
            activity = record._get_user_approval_activities()
            if activity:
                activity.action_feedback()

    def action_dynamic_approval_request(self):
        """" override to restrict request approval """
        res = super(PurchaseOrder, self).action_dynamic_approval_request()
        for record in self:
            if not record.order_line:
                raise UserError(_('Please add product in order to request approval'))
            if not record.amount_total:
                raise UserError(_('Please add selling price in order lines'))
        return res

    def _compute_appear_recall_button(self):
        """ appear recall button based on user """
        current_user = self.env.user
        for record in self:
            appear_recall_button = False
            if record.user_id and record.user_id == current_user:
                appear_recall_button = True
            if record.create_uid and record.create_uid == current_user:
                appear_recall_button = True
            record.appear_recall_button = appear_recall_button
