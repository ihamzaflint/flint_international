from odoo import fields, models, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _name = 'account.move'
    _inherit = ['account.move', 'dynamic.approval.mixin']
    _not_matched_action_xml_id = 'account_move_dynamic_approval.confirm_account_move_wizard_action'

    state = fields.Selection(
        selection_add=[('under_approval', 'Under Approval'), ('approved', 'Approved'), ('posted',)],
        ondelete={'under_approval': 'set default', 'approved': 'cascade'},
        )
    appear_recall_button = fields.Boolean(
        compute='_compute_appear_recall_button',
    )

    partner_id = fields.Many2one(
        string='Customer Name')
    approval_history_ids = fields.One2many(
        'account.move.approval.history',
        'account_id', )

    def action_draft(self):
        res = super(AccountMove, self).button_draft()
        self.remove_approval_requests()
        return res

    def action_cancel(self):
        res = super(AccountMove, self).button_cancel()
        self.mapped('dynamic_approve_request_ids').write({
            'status': 'rejected',
            'approve_date': False,
            'approved_by': False,
        })
        return res

    def _approval_allowed(self):
        """Returns whether the order qualifies to be approved by the current user"""
        self.ensure_one()
        return (
            self.company_id.po_double_validation == 'one_step'
            or (self.company_id.po_double_validation == 'two_step'
                and self.amount_total < self.env.company.currency_id._convert(
                    self.company_id.po_double_validation_amount, self.currency_id, self.company_id,
                    self.date or fields.Date.today()))
            or self.user_has_groups('account.group_account_manager'))

    def button_approve(self, force=False):
        self = self.filtered(lambda order: order._approval_allowed())
        self.write({'state': 'posted', 'approval_history_ids': [(0, 0, {
            'status': 'approved',
            'user_id': self.env.user.id,
            'action_date': fields.Datetime.now(),

        })]})
        return {}

    def button_confirm(self):
        """ override to restrict user to confirm if there is workflow """
        for move in self:
            if move.state not in ['draft', '', 'approved']:
                continue
            if move._approval_allowed():
                move.button_approve()
            else:
                move.write({'state': 'under_approval'})
            if move.partner_id not in move.message_partner_ids:
                move.message_subscribe([move.partner_id.id])
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
        res = super(AccountMove, self).action_dynamic_approval_request()
        for record in self:
            if record.line_ids:
                if not record.line_ids:
                    raise UserError(_('Please add product in order to request approval'))
                if not record.amount_total:
                    raise UserError(_('Please add selling price in order lines'))
            elif record.invoice_line_ids:
                if not record.invoice_line_ids:
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

    def _get_email_subject_name(self):
        for record in self:
            if record.move_type == 'out_invoice':
                return _('Customer Invoice')
            elif record.move_type == 'in_invoice':
                return _('Vendor Bill')
            elif record.move_type == 'out_refund':
                return _('Customer Credit Note')
            elif record.move_type == 'in_refund':
                return _('Vendor Credit Note')