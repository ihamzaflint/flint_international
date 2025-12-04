import pytz
from datetime import datetime, timedelta

from odoo import api, models, fields


class DynamicApprovalRequest(models.Model):
    _name = 'dynamic.approval.request'
    _description = 'Approval Request'
    _order = 'sequence, id'

    res_model = fields.Char(
        string='Related Document Model',
        required=True,
    )
    res_id = fields.Many2oneReference(
        string='Related Document ID',
        index=True,
        required=True,
        model_field='res_model'
    )
    res_name = fields.Char(
        string='Document Name',
        compute='_compute_res_name',
        compute_sudo=True,
        store=True,
        help="Display name of the related document.",
    )
    sequence = fields.Integer(
        string='Sequence',
        default=1,
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Approver User',
    )
    group_id = fields.Many2one(
        comodel_name='res.groups',
        string='Approver Group',
    )
    approve_date = fields.Datetime(
        string='Approved Date',
    )
    status = fields.Selection(
        selection=[
            ('new', 'New'),
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('recall', 'recall')
        ],
        default="new",
    )
    approved_by = fields.Many2one(
        comodel_name='res.users',
    )
    reject_date = fields.Datetime(
        string='Reject Date',
    )
    reject_reason = fields.Char()
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    approve_note = fields.Char()
    dynamic_approval_id = fields.Many2one(
        comodel_name='dynamic.approval',
        copy=False,
    )
    dynamic_approve_level_id = fields.Many2one(
        comodel_name='dynamic.approval.level',
        copy=False,
    )
    last_reminder_date = fields.Datetime()
    employee_quo = fields.Many2one('hr.employee')
    team_leader_quo = fields.Many2one('hr.employee')
    manager_quo = fields.Many2one('hr.employee')


    @api.depends('res_model', 'res_id')
    def _compute_res_name(self):
        """ appear display name of related document """
        for record in self:
            record.res_name = record.res_model and self.env[record.res_model].browse(record.res_id).display_name

    def get_approve_user(self):
        """ :return users that need to approve """
        users = self.env['res.users']
        for record in self:
            if record.user_id:
                users |= record.user_id
            if record.group_id:
                users |= record.group_id.users
        return users

    def action_send_reminder_email(self):
        """ send email to user for each request """

        cal_obj = self.env['resource.calendar']
        calendar_id = self.env['ir.config_parameter'].sudo().get_param('base_dynamic_approval.email_resource_calendar_id', 0)
        calendar_id =cal_obj.search([('id', '=', calendar_id)])
        for record in self:
            if record.dynamic_approval_id and record.dynamic_approval_id.reminder_pending_approver_email_template_id:
                for user in record.get_approve_user():
                    timezone = False
                    if calendar_id and calendar_id.tz:
                        timezone = pytz.timezone(calendar_id.tz)
                    usertime = datetime.now(timezone) if timezone else datetime.now()
                    intersect = calendar_id._time_within(usertime)
                    if not intersect:
                        continue
                    email_values = {'email_to': user.email, 'email_from': self.env.user.email}
                    record.dynamic_approval_id.reminder_pending_approver_email_template_id.with_context(
                        name_to=user.name, user_lang=user.lang).send_mail(
                        self.res_id, email_values=email_values, force_send=True)

    @api.model
    def _cron_send_reminder_to_approve(self):
        """ cron job used to send email template to approve """
        approve_requests = self.search([
            ('status', '=', 'pending'),
            ('dynamic_approval_id.reminder_pending_approver_email_template_id', '!=', False),
        ])
        now = fields.Datetime.now()
        for approve_request in approve_requests:
            if approve_request.dynamic_approval_id.reminder_period_to_approve:
                delay_period = approve_request.dynamic_approval_id.reminder_period_to_approve
                request_end_date = approve_request.last_reminder_date or approve_request.write_date
                deadline_date = request_end_date + timedelta(hours=delay_period)
                if deadline_date <= now:
                    approve_request.action_send_reminder_email()
                    approve_request.last_reminder_date = now
