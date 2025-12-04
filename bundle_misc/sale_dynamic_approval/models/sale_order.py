""" inherit sale.order """
from odoo import _, models, fields
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['sale.order', 'dynamic.approval.mixin']
    _not_matched_action_xml_id = 'sale_dynamic_approval.confirm_sale_order_wizard_action'

    # ToDo: remove readonly from field state. it used to allow import historical data only
    state = fields.Selection(
        selection_add=[('under_approval', 'Under Approval'), ('approved', 'Approved'), ('sale',)],
        ondelete={'under_approval': 'set default', 'approved': 'set default', 'sale': 'set default'},
        readonly=False,
    )
    appear_recall_button = fields.Boolean(
        compute='_compute_appear_recall_button',
    )

    partner_id = fields.Many2one(
        string='Customer Name',
        )

    def action_draft(self):
        res = super(SaleOrder, self).action_draft()
        self.remove_approval_requests()
        return res

    def action_cancel(self):
        res = super(SaleOrder, self).action_cancel()
        self.mapped('dynamic_approve_request_ids').write({
            'status': 'rejected',
            'approve_date': False,
            'approved_by': False,
        })
        return res

    def action_confirm(self):
        """ override to restrict user to confirm if there is workflow """
        res = super(SaleOrder, self).action_confirm()
        if self.mapped('dynamic_approve_request_ids') and \
                self.mapped('dynamic_approve_request_ids').filtered(lambda request: request.status != 'approved'):
            raise UserError(
                _('You can not confirm order, There are pending approval.'))
        for record in self:
            activity = record._get_user_approval_activities()
            if activity:
                activity.action_feedback()
        return res

    def action_dynamic_approval_request(self):
        """" override to restrict request approval """
        res = super(SaleOrder, self).action_dynamic_approval_request()
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
