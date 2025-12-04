from datetime import datetime
import logging
from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DynamicApprovalMixin(models.AbstractModel):
    _name = 'dynamic.approval.mixin'
    _description = 'Advanced Approval Mixin'
    _state_under_approval = 'under_approval'  # to convert to it based on function 'action_dynamic_approval_request'
    _state_to = 'approved'  # to convert to it when no pending approval
    _state_from = ["draft"]  # to check that this stage is source that need to convert from it
    _state_field = "state"  # to update field with status, you need to override in your module to add selection_add
    _company_field = "company_id"  # to search for matched advanced approval based on company
    _not_matched_action_xml_id = False  # if no matched condition applied appear wizard to add custom action or restrict
    _reset_user = 'approve_requester_id'  # allow to appear request approve button to user

    dynamic_approve_request_ids = fields.One2many(
        comodel_name='dynamic.approval.request',
        inverse_name='res_id',
        auto_join=True,
        copy=False,
        domain=lambda self: [('res_model', '=', self._name)]
    )
    dynamic_approve_pending_group = fields.Boolean(
        compute='_compute_dynamic_approve_pending_group',
    )
    approve_requester_id = fields.Many2one(
        comodel_name='res.users',
        copy=False,
    )
    dynamic_approval_id = fields.Many2one(
        comodel_name='dynamic.approval',
        copy=False,
    )
    is_dynamic_approval_requester = fields.Boolean(
        compute='compute_is_dynamic_approval_requester')
    state_from_name = fields.Char(
        copy=False,
        readonly=True,
    )

    # helper functions
    def compute_is_dynamic_approval_requester(self):
        """ return true if current user is who submit approval """
        current_user = self.env.user
        for record in self:
            is_dynamic_approval_requester = False
            if record.approve_requester_id and current_user == record.approve_requester_id:
                is_dynamic_approval_requester = True
            elif not record.dynamic_approve_request_ids:
                is_dynamic_approval_requester = True
            elif getattr(record, self._reset_user) == current_user:
                is_dynamic_approval_requester = True
            elif self.env.user.has_group('base_dynamic_approval.dynamic_approval_user_group'):
                is_dynamic_approval_requester = True
            record.is_dynamic_approval_requester = is_dynamic_approval_requester

    def _compute_dynamic_approve_pending_group(self):
        for record in self:
            dynamic_approve_pending_group = False
            pend_approve_requests = record.dynamic_approve_request_ids.filtered(
                lambda approver: approver.status == 'pending')
            if pend_approve_requests:
                if self.env.user.has_group('base_dynamic_approval.dynamic_approval_user_group'):
                    dynamic_approve_pending_group = True
                else:
                    if self.env.user in pend_approve_requests.get_approve_user():
                        dynamic_approve_pending_group = True
            record.dynamic_approve_pending_group = dynamic_approve_pending_group

    def _notify_next_approval_request(self, matched_approval, user):
        """ notify next approval """
        self.ensure_one()
        if matched_approval.need_create_activity_to_approve:
            self._create_approve_activity(user)
        if matched_approval.email_template_to_approve_id and user != self.env.user:
            email_values = {'email_to': user.email, 'email_from': self.env.user.email}
            self.dynamic_approval_id.email_template_to_approve_id.with_context(
                name_to=user.name, user_lang=user.lang).send_mail(
                self.id, email_values=email_values, force_send=True)

    def _create_approve_activity(self, user):
        """ create activity based on next user """
        activity_type = self.env.ref('base_dynamic_approval.mail_activity_type_waiting_approval',
                                     raise_if_not_found=False)
        if activity_type:
            for record in self:
                try:
                    record.with_context(mail_activity_quick_update=True).activity_schedule(
                        activity_type_id=activity_type.id,
                        summary=_('Approval needed for %s', record.display_name),
                        user_id=user.id,
                    )
                except Exception as error_message:
                    _logger.exception(
                        'Cannot create activity for user %s. error: %s' % (user.name or '', error_message))

    def _create_done_approve_activity(self, user):
        """ create activity based on user """
        activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        if activity_type:
            for record in self:
                try:
                    record.with_context(mail_activity_quick_update=True).activity_schedule(
                        activity_type_id=activity_type.id,
                        summary=_('Approval done for %s', record.display_name),
                        user_id=user.id,
                    )
                except Exception as error_message:
                    _logger.exception(
                        'Cannot create activity for user %s. error: %s' % (user.name or '', error_message))

    def _create_reject_activity(self, user):
        """ create activity based on _reset_user """
        activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        if activity_type:
            for record in self:
                try:
                    record.with_context(mail_activity_quick_update=True).activity_schedule(
                        activity_type_id=activity_type.id,
                        summary=_('%s approval request rejected', record.display_name),
                        user_id=user.id,
                    )
                except Exception as error_message:
                    _logger.exception(
                        'Cannot create activity for user %s. error: %s' % (user.name or '', error_message))

    def _create_recall_activity(self, user):
        """ create activity based on _reset_user """
        activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        if activity_type:
            for record in self:
                try:
                    record.with_context(mail_activity_quick_update=True).activity_schedule(
                        activity_type_id=activity_type.id,
                        summary=_('%s approval request recalled', record.display_name),
                        user_id=user.id,
                    )
                except Exception as error_message:
                    _logger.exception(
                        'Cannot create activity for user %s. error: %s' % (user.name or '', error_message))

    def _run_final_approve_function(self):
        """ this method should be override to add custom function based on model"""
        return True

    def _action_final_approve(self):
        """ mark order as approved """
        self.ensure_one()
        self._run_final_approve_function()
        self.write({
            self._state_field: self._state_to,
        })
        # create activity based on setting
        if self.dynamic_approval_id and self.dynamic_approval_id.default_notify_user_field_after_final_approve_id:
            self._create_done_approve_activity(
                getattr(self, self.dynamic_approval_id.default_notify_user_field_after_final_approve_id.name))
        # send email to users
        if self.dynamic_approval_id and self.dynamic_approval_id.notify_user_field_after_final_approve_ids and \
                self.dynamic_approval_id.email_template_after_final_approve_id:
            users_to_send = self.env['res.users']
            for user_field in self.dynamic_approval_id.notify_user_field_rejection_ids:
                users_to_send |= getattr(self, user_field.name)
            # not send email for same user twice
            users_to_send = self.env['res.users'].browse(users_to_send.mapped('id'))
            for user in users_to_send:
                if user != self.env.user and user.email:
                    email_values = {'email_to': user.email, 'email_from': self.env.user.email}
                    self.dynamic_approval_id.email_template_after_final_approve_id.with_context(
                        name_to=user.name, user_lang=user.lang).send_mail(self.id, email_values=email_values,
                                                                          force_send=True)
        if self.dynamic_approval_id and self.dynamic_approval_id.after_final_approve_server_action_id:
            action = self.dynamic_approval_id.after_final_approve_server_action_id.with_context(
                active_model=self._name,
                active_ids=[self.id],
                active_id=self.id,
            )
            try:
                action.run()
            except Exception as e:
                _logger.warning('Approval Rejection: record <%s> model <%s> encountered server action issue %s',
                                self.id, self._name, str(e), exc_info=True)

    def _get_user_approval_activities(self, users=False):
        """ return users activities that need to mark done or cancel """
        domain = [
            ('res_model', '=', self._name),
            ('res_id', 'in', self.ids),
            '|',
            ('activity_type_id', '=', self.env.ref('base_dynamic_approval.mail_activity_type_waiting_approval').id),
            ('activity_type_id', '=', self.env.ref('mail.mail_activity_data_todo').id),
        ]
        if users:
            domain += [('user_id', 'in', users.ids)]
        return self.env['mail.activity'].search(domain)

    def unlink(self):
        """ remove approval requests when delete so """
        self.remove_approval_requests()
        return super(DynamicApprovalMixin, self).unlink()

    def remove_approval_requests(self):
        """ remove approval requests """
        self.mapped('dynamic_approve_request_ids').sudo().unlink()

    def _get_pending_approvals(self, user):
        """ return list of approval requests that need to approve """
        self.ensure_one()
        pending_approval_ids = []
        for request in self.dynamic_approve_request_ids.filtered(
                lambda request_approve: request_approve.status in ['pending', 'new']):
            if user in request.get_approve_user():
                pending_approval_ids.append(request.id)
            else:
                break
        return pending_approval_ids

    def _action_reset_original_state(self, reason='', attachments=[], reset_type='reject'):
        """
        set record to original state and notify user or approvers
        :param reason: reason for reset
        :param reset_type: reject / recall
        :param notify_approver: notify users who approved before
        """
        for record in self:
            pending_approve_requests = \
                record.dynamic_approve_request_ids.filtered(lambda approver: approver.status == 'pending')
            approved_requests = \
                record.dynamic_approve_request_ids.filtered(lambda approver: approver.status == 'approved')
            activity = record._get_user_approval_activities()
            if reset_type == 'reject':
                if activity:
                    activity.action_feedback(feedback=_('Rejected, Reason ') + reason, attachment_ids=attachments.ids)
                else:
                    record.message_post(body=_('Rejected, Reason ') + reason,
                                        attachments=attachments)
                #  update approval request status
                pending_approve_requests.write({
                    'status': 'rejected',
                    'approve_date': False,
                    'approved_by': False,
                    'reject_reason': reason,
                    'attachment_ids': attachments,
                    'reject_date': datetime.now(),
                })

                if pending_approve_requests.status == 'rejected':
                    val = {}
                    if self._context.get('active_model') == 'purchase.order':
                        val = {'user_id': self.env.uid,
                               'status': 'reject',
                               'action_date': datetime.now(),
                               'purchase_id': self.id,
                               'purchase_order_status': self.state,
                               }
                    elif self._context.get('active_model') == 'sale.order':
                        val = {'user_id': self.env.uid,
                               'status': 'reject',
                               'action_date': datetime.now(),
                               'sale_id': self.id,
                               'sale_order_status': self.state,
                               }
                    self.approval_history_ids.create(val)
                # create activity for user based on approval configuration
                if record.dynamic_approval_id and record.dynamic_approval_id.default_notify_user_field_rejection_id:
                    activity_user = \
                        getattr(record, record.dynamic_approval_id.default_notify_user_field_rejection_id.name)
                    if activity_user != self.env.user:
                        record._create_reject_activity(activity_user)
                # send email template to users that need to know if record is rejected
                if record.dynamic_approval_id and record.dynamic_approval_id.notify_user_field_rejection_ids and \
                        record.dynamic_approval_id.rejection_email_template_id:
                    users_to_send = self.env['res.users']
                    for user_field in record.dynamic_approval_id.notify_user_field_rejection_ids:
                        users_to_send |= getattr(record, user_field.name)
                    # not send email for same user twice
                    users_to_send = self.env['res.users'].browse(users_to_send.mapped('id'))
                    for user in users_to_send:
                        if user != self.env.user and user.email:
                            email_values = {'email_to': user.email, 'email_from': self.env.user.email}
                            record.dynamic_approval_id.rejection_email_template_id.with_context(
                                name_to=user.name, user_lang=user.lang, reject_reason=reason,
                                attachment_ids=attachments).send_mail(
                                record.id, email_values=email_values, force_send=True)
                # send email template to users who approved to record before about rejection
                if record.dynamic_approval_id and record.dynamic_approval_id.need_notify_rejection_approved_user and \
                        record.dynamic_approval_id.rejection_email_template_id:
                    approved_users = approved_requests.mapped('approved_by')
                    for approved_user in approved_users:
                        if approved_user != self.env.user and approved_user.email:
                            email_values = {'email_to': approved_user.email, 'email_from': self.env.user.email}
                            record.dynamic_approval_id.rejection_email_template_id.with_context(
                                name_to=approved_user.name, user_lang=user.lang, reject_reason=reason). \
                                send_mail(record.id, email_values=email_values, force_send=True)
                # run server action
                if record.dynamic_approval_id and record.dynamic_approval_id.rejection_server_action_id:
                    action = self.dynamic_approval_id.rejection_server_action_id.with_context(
                        active_model=self._name,
                        active_ids=[record.id],
                        active_id=record.id,
                    )
                    try:
                        action.run()
                    except Exception as e:
                        _logger.warning('Approval Rejection: record <%s> model <%s> encountered server action issue %s',
                                        record.id, record._name, str(e), exc_info=True)

            if reset_type == 'recall':
                if activity:
                    activity.unlink()
                pending_approve_requests.write({'status': 'recall'})
                approved_requests.write({'status': 'recall'})
                record.message_post(body=_('Recalled, Reason ') + reason)

                if pending_approve_requests.status == 'recall':
                    val = {}
                    if self._context.get('active_model') == 'purchase.order':
                        val = {'user_id': self.env.uid,
                               'status': 'recall',
                               'action_date': datetime.now(),
                               'purchase_id': self.id,
                               'purchase_order_status': self.state,
                               }
                    elif self._context.get('active_model') == 'sale.order':
                        val = {'user_id': self.env.uid,
                               'status': 'reject',
                               'action_date': datetime.now(),
                               'sale_id': self.id,
                               'sale_order_status': self.state,
                               }
                    self.approval_history_ids.create(val)

                # create activity for user based on approval configuration
                if record.dynamic_approval_id and record.dynamic_approval_id.default_notify_user_field_recall_id:
                    activity_user = getattr(record, record.dynamic_approval_id.default_notify_user_field_recall_id.name)
                    if activity_user != self.env.user:
                        record._create_recall_activity(activity_user)
                # send email template to users that need to know if record is recalled
                if record.dynamic_approval_id and record.dynamic_approval_id.notify_user_field_recall_ids and \
                        record.dynamic_approval_id.recall_email_template_id:
                    users_to_send = self.env['res.users']
                    for user_field in record.dynamic_approval_id.notify_user_field_recall_ids:
                        users_to_send |= getattr(record, user_field.name)
                    # not send email for same user twice
                    users_to_send = self.env['res.users'].browse(users_to_send.mapped('id'))
                    for user in users_to_send:
                        if user != self.env.user and user.email:
                            email_values = {'email_to': user.email, 'email_from': self.env.user.email}
                            record.dynamic_approval_id.recall_email_template_id.with_context(
                                name_to=user.name, user_lang=user.lang, recall_reason=reason).send_mail(
                                record.id, email_values=email_values, force_send=True)
                # send email template to users who approved to record before about recall
                if record.dynamic_approval_id and record.dynamic_approval_id.need_notify_recall_approved_user and \
                        record.dynamic_approval_id.recall_email_template_id:
                    approved_users = approved_requests.mapped('approved_by')
                    for approved_user in approved_users:
                        if approved_user != self.env.user and approved_user.email:
                            email_values = {'email_to': approved_user.email, 'email_from': self.env.user.email}
                            record.dynamic_approval_id.recall_email_template_id.with_context(
                                name_to=approved_user.name, user_lang=user.lang, recall_reason=reason). \
                                send_mail(record.id, email_values=email_values, force_send=True)

                # run server action
                if record.dynamic_approval_id and record.dynamic_approval_id.recall_server_action_id:
                    action = self.dynamic_approval_id.recall_server_action_id.with_context(
                        active_model=self._name,
                        active_ids=[record.id],
                        active_id=record.id,
                    )
                    try:
                        action.run()
                    except Exception as e:
                        _logger.warning(
                            'Approval Recall: record <%s> model <%s> encountered server action issue %s',
                            record.id, record._name, str(e), exc_info=True)

            record.write({
                record._state_field: record.state_from_name or record._state_from[0]
            })

    # actions workflow
    def action_dynamic_approval_request(self):
        """
        search for advanced approvals that match current record and add approvals
        if record does not match then appear wizard to confirm order without approval
        """
        for record in self:
            company = getattr(record, self._company_field)
            if getattr(record, record._state_field) in self._state_from:
                if record.dynamic_approve_request_ids:
                    record.remove_approval_requests()
                    # mark any old activity as done to allow create new activity
                    activity = record._get_user_approval_activities()
                    if activity:
                        activity.action_feedback()
                matched_approval = self.env['dynamic.approval'].action_set_approver(model=self._name, res=record,
                                                                                    company=company)
                if matched_approval:
                    record.write({
                        self._state_field: self._state_under_approval,
                        'approve_requester_id': self.env.user.id,
                        'dynamic_approval_id': matched_approval.id,
                        'state_from_name': getattr(record, record._state_field),
                    })
                    next_waiting_approval = record.dynamic_approve_request_ids.sorted(lambda x: (x.sequence, x.id))[0]
                    next_waiting_approval.status = 'pending'
                    if next_waiting_approval.get_approve_user():
                        user = next_waiting_approval.get_approve_user()[0]
                        record._notify_next_approval_request(matched_approval, user)

                    if next_waiting_approval and self.approve_requester_id:
                        val = {}
                        if self._context.get('active_model') == 'purchase.order':
                            val = {'user_id': self.env.uid,
                                   'status': 'request_approval',
                                   'action_date': datetime.now(),
                                   'purchase_id': self.id,
                                   'purchase_order_status': self.state,
                                   }
                        elif self._context.get('active_model') == 'sale.order':
                            val = {'user_id': self.env.uid,
                                   'status': 'reject',
                                   'action_date': datetime.now(),
                                   'sale_id': self.id,
                                   'sale_order_status': self.state,
                                   }
                        self.approval_history_ids.create(val)
                else:
                    if self._not_matched_action_xml_id:
                        action_id = self._not_matched_action_xml_id
                        action = self.env["ir.actions.actions"]._for_xml_id(action_id)
                        return action
            else:
                raise UserError(_('This status is not allowed to request approval'))

    def action_under_approval(self, note=''):
        """
        change status of approval request to approved and trigger next approval level or change status to be approved
        :param note: approval notes that user will add and store it in approval requests and add it as activity feedback
        """
        for record in self:
            user = self.env.user
            if self.env.user.has_group('base_dynamic_approval.dynamic_approval_user_group'):
                pending_approval = record.dynamic_approve_request_ids.filtered(
                    lambda request_approve: request_approve.status == 'pending')
                if pending_approval:
                    allowed_users = pending_approval.get_approve_user()
                    if allowed_users:
                        user = allowed_users[0]
            pending_approve_request_ids = record._get_pending_approvals(user)
            pending_approve_requests = self.env['dynamic.approval.request'].browse(pending_approve_request_ids)
            if pending_approve_requests:
                pending_approve_requests.write({
                    'approve_date': datetime.now(),
                    'approved_by': self.env.user.id,
                    'status': 'approved',
                })
                pending_approve_requests[-1].write({'approve_note': note})

            activity = record._get_user_approval_activities()
            if activity:
                activity.action_feedback(feedback=note)
            else:
                msg = _('Approved')
                if note:
                    msg += ' ' + note
                record.message_post(body=msg)
            if record.dynamic_approval_id.to_approve_server_action_id:
                action = record.dynamic_approval_id.to_approve_server_action_id.with_context(
                    active_model=self._name,
                    active_ids=[record.id],
                    active_id=record.id,
                )
                try:
                    action.run()
                except Exception as e:
                    _logger.warning(
                        'Approval Recall: record <%s> model <%s> encountered server action issue %s',
                        record.id, record._name, str(e), exc_info=True)
            new_approve_requests = \
                record.dynamic_approve_request_ids.filtered(lambda approver: approver.status == 'new')
            if new_approve_requests:
                next_waiting_approval = new_approve_requests.sorted(lambda x: (x.sequence, x.id))[0]
                next_waiting_approval.status = 'pending'
                if next_waiting_approval.get_approve_user():
                    user = next_waiting_approval.get_approve_user()[0]
                    record._notify_next_approval_request(record.dynamic_approval_id, user)
            else:
                record._action_final_approve()

            if pending_approve_requests:
                for rec in pending_approve_requests:
                    if rec.status == 'approved':
                        val = {}
                        if self._context.get('active_model') == 'purchase.order':
                            val = {'user_id': self.env.uid,
                                   'status': 'approved',
                                   'action_date': datetime.now(),
                                   'purchase_id': self.id,
                                   'purchase_order_status': self.state,
                                   }
                        elif self._context.get('active_model') == 'sale.order':
                            val = {'user_id': self.env.uid,
                                   'status': 'reject',
                                   'action_date': datetime.now(),
                                   'sale_id': self.id,
                                   'sale_order_status': self.state,
                                   }
                        self.approval_history_ids.create(val)
