# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo import fields, models, api, _
import ast
import uuid
from odoo.tools.float_utils import float_round
import logging
import json
from odoo.exceptions import UserError
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)


# -----------------------
# Helper for 2-dec string
# -----------------------
def _fmt2(val):
    """Return a fixed 2-decimal string without changing field types."""
    return f"{float_round(val or 0.0, precision_digits=2):.2f}"


class RecruitmentRecruiter(models.Model):
    _name = "recruitment.recruiter"
    _description = "Recruiter (ordered list for auto-assignment)"
    _order = "sequence, id"

    sequence = fields.Integer(string='Sequence', default=10, help='Lower first in order')
    user_id = fields.Many2one('res.users', string='User', required=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    active = fields.Boolean(string='Active', default=True)
    order_count = fields.Integer(string='Recruitment Orders', compute='_compute_order_count', store=False)

    def _compute_order_count(self):
        if not self:
            return
        user_ids = self.mapped('user_id.id')
        if not user_ids:
            for rec in self:
                rec.order_count = 0
            return
        # Only count orders that are NOT done
        domain = [('user_id', 'in', user_ids), ('state', '!=', 'done')]
        groups = self.env['recruitment.order'].read_group(domain, ['user_id'], ['user_id'])
        counts = {g['user_id'][0]: g['user_id_count'] for g in groups if g.get('user_id')}
        for rec in self:
            rec.order_count = counts.get(rec.user_id.id, 0)

    def action_view_orders(self):
        self.ensure_one()
        action = self.env.ref('era_recruitment_opportunity.recruitment_order_act_window', False)
        if not action:
            action = {
                'type': 'ir.actions.act_window',
                'name': _('Recruitment Orders'),
                'res_model': 'recruitment.order',
                'view_mode': 'tree,form',
                'target': 'current',
            }
        domain = [('user_id', '=', self.user_id.id)]
        return dict(action if isinstance(action, dict) else action.read()[0], domain=domain)

    def action_view_orders_multi(self):
        user_ids = self.mapped('user_id.id')
        action = self.env.ref('era_recruitment_opportunity.recruitment_order_act_window', False)
        if not action:
            action = {
                'type': 'ir.actions.act_window',
                'name': _('Recruitment Orders'),
                'res_model': 'recruitment.order',
                'view_mode': 'tree,form',
                'target': 'current',
            }
        domain = [('user_id', 'in', user_ids)] if user_ids else [('id', '=', 0)]
        return dict(action if isinstance(action, dict) else action.read()[0], domain=domain)

class RecruitmentOrder(models.Model):
    _name = 'recruitment.order'
    _inherit = ["mail.thread", "mail.alias.mixin", "mail.activity.mixin"]
    _description = 'Recruitment Order'

    name = fields.Char()
    recruitment_process = fields.Selection([
        ('full_recruitment', 'Full Recruitment'),
        ('direct_recruitment', 'Direct Recruitment')], required=True)
    sequence = fields.Char(
        string='Recruitment Order',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        help="Sequence: RO/000001, assigned automatically"
    )
    recruitment_count = fields.Integer(string="Recruitment Count", compute="_compute_recruitment_count")
    job_description = fields.Html(string='Job Description', translate=True)
    has_sendable_applicants = fields.Boolean(
    compute="_compute_has_sendable_applicants", store=False)

    def _compute_has_sendable_applicants(self):
        for rec in self:
            rec.has_sendable_applicants = any(
                (l.state in ('draft', 'confirm')) and not l.sent_to_client
                for l in rec.applicant_line
            )
    # @api.model_create_multi
    # def create(self, vals_list):
    #     # assign sequence before creating records so it's available immediately on create
    #     seq_code = 'recruitment.order'
    #     for vals in vals_list:
    #         if not vals.get('sequence') or vals.get('sequence') == _('New'):
    #             # reserve/generate next sequence value
    #             vals['sequence'] = self.env['ir.sequence'].next_by_code(seq_code) or _('New')
    #     records = super(RecruitmentOrder, self).create(vals_list)
    #     return records

    # def name_get(self):
    #     """ Show sequence in many2one displays; falls back to name if sequence missing. """
    #     res = []
    #     for rec in self:
    #         display_name = rec.sequence or rec.name or _('New')
    #         res.append((rec.id, display_name))
    #     return res

    def _compute_recruitment_count(self):
        for rec in self:
            count = rec.no_of_recruitment - rec.applicant_ids_count
            if count < 0:
                count = 0
            rec.recruitment_count = count

    def _alias_get_creation_values(self):
        values = super(RecruitmentOrder, self)._alias_get_creation_values()
        values['alias_model_id'] = self.env['ir.model']._get('hr.applicant').id
        if self.id:
            values['alias_defaults'] = defaults = ast.literal_eval(self.alias_defaults or "{}")
            defaults.update({
                'job_id': self.id,
                'department_id': self.department_id.id,
                'company_id': self.department_id.company_id.id if self.department_id else self.company_id.id,
                'user_id': self.user_id.id,
            })
        return values

    @api.model
    def _default_address_id(self):
        last_used_address = self.env['hr.job'].search([('company_id', 'in', self.env.companies.ids)], order='id desc',
                                                      limit=1)
        if last_used_address:
            return last_used_address.address_id
        else:
            return self.env.company.partner_id

    def _address_id_domain(self):
        return ['|', '&', '&', ('type', '!=', 'contact'), ('type', '!=', 'private'),
                ('id', 'in', self.sudo().env.companies.partner_id.child_ids.ids),
                ('id', 'in', self.sudo().env.companies.partner_id.ids)]

    def return_to_draft(self):
        for rec in self:
            rec.write({
                'state': 'draft'
            })
            template = self.env.ref('era_recruitment_opportunity.email_template_to_draft')
            recruiter_id = self.env['res.users'].browse(rec.user_id.id)
            partner_id = recruiter_id.partner_id
            if template and partner_id:
                template.send_mail(
                    rec.id,
                    force_send=True,
                    email_values={'partner_ids': [partner_id.id]}
                )

    def action_head_hunting(self):
        for rec in self:
            rec.write({
                'state': 'head_hunting'
            })
            template = self.env.ref('era_recruitment_opportunity.email_template_draft_to_headhunting')
            recruiter_id = self.env['res.users'].browse(rec.user_id.id)
            partner_id = recruiter_id.partner_id
            if template and partner_id:
                template.send_mail(
                    rec.id,
                    force_send=True,
                    email_values={'partner_ids': [partner_id.id]}
                )

    def action_import_applicants(self):
        view_id = self.env.ref('era_recruitment_opportunity.import_applicants_wizard_form_view').id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Import Jobs'),
            'res_model': 'import.applicants.wizard',
            'target': 'new',
            'view_mode': 'form',
            'views': [[view_id, 'form']],
            'context': {'default_rec_id': self.id},
        }

    # def _get_resume_applicants(self):
    #     attachments = []
    #     attachments_ids = []
    #     for line in self.applicant_line:
    #         # resume_name = line.name + "_resume"
    #         resume_name = (line.name or "resume") + "_resume"
    #         if not line.resume:
    #             continue
    #         attachments.append((
    #             resume_name,
    #             line.resume
    #         ))
    #     for fname, data in attachments:
    #         attachment = self.env['ir.attachment'].create({
    #             'name': fname,
    #             'type': 'binary',
    #             'datas': data,
    #             'res_model': self._name,
    #             'res_id': self.id,
    #             'mimetype': 'application/octet-stream',
    #         })
    #         attachments_ids.append((attachment.id))
    #     return attachments_ids

    def _get_resume_applicants(self, lines=None):
        """Return attachment ids for resumes, optionally limited to given applicant lines."""
        attachments_ids = []
        iter_lines = lines or self.applicant_line  # if lines not given, use all lines
        for line in iter_lines:
            if not line.resume:
                continue
            resume_name = (line.name or "resume") + "_resume"
            attachment = self.env['ir.attachment'].create({
                'name': resume_name,
                'type': 'binary',
                'datas': line.resume,
                'res_model': self._name,
                'res_id': self.id,
                'mimetype': 'application/octet-stream',
            })
            attachments_ids.append(attachment.id)
        return attachments_ids

    # def action_client_select(self):
    #     self.ensure_one()
    #     base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
    #     self.selection_link = base_url + self.action_generate_portal_url()['url']
    #     # lang = self.env.context.get('lang')
    #     mail_template = self._find_mail_template()
    #     attachments = self._get_resume_applicants()
    #     # if mail_template and mail_template.lang:
    #     #     lang = mail_template._render_lang(self.ids)[self.id]
    #     ctx = {
    #         'default_model': 'recruitment.order',
    #         'default_res_ids': self.ids,
    #         'default_template_id': mail_template.id if mail_template else None,
    #         'default_composition_mode': 'comment',
    #         'mark_so_as_sent': True,
    #         'default_email_layout_xmlid': 'mail.mail_notification_layout_with_responsible_signature',
    #         'force_email': True,
    #         'selection_link': self.selection_link,
    #         'default_attachment_ids': [(6, 0, attachments)]
    #     }
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'view_mode': 'form',
    #         'res_model': 'mail.compose.message',
    #         'views': [(False, 'form')],
    #         'view_id': False,
    #         'target': 'new',
    #         'context': ctx,
    #     }
    def action_client_select(self):
        self.ensure_one()

        eligible_lines = self.applicant_line.filtered(
            lambda l: l.state in ('draft', 'confirm') and not l.sent_to_client
        )
        if not eligible_lines:
            raise UserError(_("No new applicants to send."))

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        self.selection_link = base_url + self.action_generate_portal_url()['url']

        mail_template = self._find_mail_template()
        attachments = self._get_resume_applicants(eligible_lines)  # <-- fixed

        ctx = {
            'default_model': 'recruitment.order',
            'default_res_ids': self.ids,
            'default_email_from': self.company_id.email_formatted,
            'default_author_id': self.company_id.partner_id.id,
            'default_template_id': mail_template.id if mail_template else None,
            'default_composition_mode': 'comment',
            'default_email_layout_xmlid': 'mail.mail_notification_layout_with_responsible_signature',
            'force_email': True,
            'mark_so_as_sent': True,
            'selection_link': self.selection_link,
            'default_attachment_ids': [(6, 0, attachments)],
            'line_ids_for_email': eligible_lines.ids,  # template me isi list ko render kar rahe
        }
        print("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF", ctx)
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'target': 'new',
            'context': ctx,
        }

    def action_generate_portal_url(self):
        self.ensure_one()
        if not self.access_token:
            self._generate_access_token()
        return {
            'type': 'ir.actions.act_url',
            'url': '/my/recruitment-order/%s?access_token=%s' % (self.id, self.access_token),
            'target': 'self',
        }

    def _generate_access_token(self):
        for record in self:
            record.access_token = uuid.uuid4().hex

    def _find_mail_template(self):
        self.ensure_one()
        return self.env.ref('era_recruitment_opportunity.email_template_client_selection', raise_if_not_found=False)

    def action_in_progress(self):
        for rec in self.sudo():
            rec.write({'state': 'in_progress'})
            template = self.env.ref('era_recruitment_opportunity.email_template_clientselection_to_inprogress')
            recruiter_id = self.env['res.users'].browse(rec.user_id.id)
            partner_id = recruiter_id.partner_id
            if template and partner_id:
                template.send_mail(
                    rec.id,
                    force_send=True,
                    email_values={'partner_ids': [partner_id.id]}
                )
        return True

    def action_done(self):
        for rec in self:
            rec.write({
                'state': 'done'
            })
            template = self.env.ref('era_recruitment_opportunity.email_template_inprogress_to_done')
            recruiter_id = self.env['res.users'].browse(rec.user_id.id)
            partner_id = recruiter_id.partner_id
            if template and partner_id:
                template.send_mail(
                    rec.id,
                    force_send=True,
                    email_values={'partner_ids': [partner_id.id]}
                )
        return True

    def create_recruitment_applicant(self):
        for rec in self:
            for line in rec.applicant_line.filtered(lambda x: x.id == self.env.context.get('app_id')):
                # --- find or create a partner for the candidate (do NOT use client_name) ---
                candidate_partner = False
                # prefer email to find/create contact
                if line.email:
                    # use same helper as hr.applicant._inverse_partner_email would use
                    candidate_partner = self.env['res.partner'].with_context(default_lang=self.env.lang).find_or_create(line.email)
                    # ensure name/phone present on the partner
                    vals_to_write = {}
                    if line.name and candidate_partner.name != line.name:
                        vals_to_write['name'] = line.name
                    if line.phone and not candidate_partner.phone:
                        vals_to_write['phone'] = line.phone
                    if vals_to_write:
                        candidate_partner.sudo().write(vals_to_write)
                else:
                    # no email — create contact specifically for this candidate (avoid touching client partner)
                    candidate_partner = self.env['res.partner'].sudo().create({
                        'is_company': False,
                        'name': line.name or _('Unknown Candidate'),
                        'phone': line.phone or False,
                        'email': False,
                    })

                vals = {
                    'name': line.recruitment_order_id.name,
                    'description': line.recruitment_order_id.description,
                    'partner_name': line.name,
                    'email_from': line.email,
                    'partner_phone': line.phone,
                    'interviewer_ids': line.recruitment_order_id.interviewer_ids.ids,
                    'user_id': line.recruitment_order_id.user_id.id,
                    'job_id': line.recruitment_order_id.lead_id.job_id[0].id if line.recruitment_order_id.lead_id.job_id else False,
                    'department_id': line.recruitment_order_id.department_id.id,
                    'salary_expected': line.salary_expectation,
                    'salary_proposed': getattr(line.recruitment_order_id, 'net_monthly_salary', 0.0),
                    'nationality': line.nationality,
                    'current_location': line.current_location,
                    'experience': line.experience,
                    'qualification': line.qualification,
                    'current_company': line.current_company,
                    'position': line.position,
                    'notice_period': line.notice_period,
                    'profession': line.profession,
                    'number_iqama': line.number_iqama,
                    'current_salary': line.current_salary,
                    'partner_id': candidate_partner.id if candidate_partner else False,
                    'recruitment_order_id': line.recruitment_order_id.id,
                    'resume': line.resume,
                }
                # create applicant as sudo (if required by your flows)
                return self.env['hr.applicant'].sudo().create(vals)
    # def create_recruitment_applicant(self):
    #     for rec in self:
    #         for line in rec.applicant_line.filtered(lambda x: x.id == self.env.context.get('app_id')):
    #             vals = {
    #                 'name': line.recruitment_order_id.name,
    #                 'description': line.recruitment_order_id.description,
    #                 'partner_name': line.name,
    #                 'email_from': line.email,
    #                 'partner_phone': line.phone,
    #                 'interviewer_ids': line.recruitment_order_id.interviewer_ids.ids,
    #                 'user_id': line.recruitment_order_id.user_id.id,
    #                 'job_id': line.recruitment_order_id.lead_id.job_id[
    #                     0].id if line.recruitment_order_id.lead_id.job_id else False,
    #                 'department_id': line.recruitment_order_id.department_id.id,
    #                 'salary_expected': line.salary_expectation,
    #                 'salary_proposed': getattr(line.recruitment_order_id, 'net_monthly_salary', 0.0),
    #                 'nationality': line.nationality,
    #                 'current_location': line.current_location,
    #                 'experience': line.experience,
    #                 'qualification': line.qualification,
    #                 'current_company': line.current_company,
    #                 'position': line.position,
    #                 'notice_period': line.notice_period,
    #                 # 'dependent': line.wife + line.kids,
    #                 'profession': line.profession,
    #                 'number_iqama': line.number_iqama,
    #                 'current_salary': line.current_salary,
    #                 'partner_id': line.recruitment_order_id.client_name.id,
    #                 'recruitment_order_id': line.recruitment_order_id.id,
    #                 'resume': line.resume,
    #             }
    #             return self.env['hr.applicant'].sudo().create(vals)

    department_id = fields.Many2one('hr.department', string='Department', check_company=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    active = fields.Boolean(default=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('head_hunting', 'Head hunting'),
        ('client_selection', 'Client selection'),
        ('in_progress', 'In progress'),
        ('done', 'Done')], default='draft', string='Status', tracking=True)
    contract_type_id = fields.Many2one('hr.contract.type', string='Employment Type', required=True)
    no_of_recruitment = fields.Integer(string='Quantity', copy=False,
                                       help='Number of new employees you expect to recruit.', default=1)
    interviewer_ids = fields.Many2many('res.users', string='Interviewers',
                                       domain="[('share', '=', False), ('company_ids', 'in', company_id)]",
                                       help="The Interviewers set on the job position can see all Applicants in it. They have access to the information, the attachments, the meeting management and they can refuse him. You don't need to have Recruitment rights to be set as an interviewer.")
    user_id = fields.Many2one('res.users', "Recruiter",
                              domain="[('share', '=', False), ('company_ids', 'in', company_id)]", tracking=True,
                              help="The Recruiter will be the default value for all Applicants Recruiter's field in this job position. The Recruiter is automatically added to all meetings with the Applicant.")

    alias_id = fields.Many2one(
        help="Email alias for this job position. New emails will automatically create new applicants for this job position.")
    address_id = fields.Many2one(
        'res.partner', "Job Location", default=_default_address_id,
        domain=lambda self: self._address_id_domain(), required=True,
        help="Select the location where the applicant will work. Addresses listed here are defined on the company's contact information.")
    recruitment_process = fields.Selection([
        ('full_recruitment', 'Full Recruitment'),
        ('direct_recruitment', 'Direct Recruitment')], required=True)
    lead_id = fields.Many2one('crm.lead')
    description = fields.Html(string='Detailed Job Description', sanitize_attributes=False,
                              default="Perform assigned responsibilities, collaborate with team members, and adhere to company policies. Strong communication, problem-solving, and work ethic required. Adaptability, initiative, and willingness to learn are valued.")
    client_name = fields.Many2one('res.partner', string='Client / Project Name')
    position_title = fields.Char(string='Position Title', required=True)
    experience_level = fields.Selection([
        ('entry', 'Entry Level'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior Level'),
        ('manager', 'Manager'),
        ('director', 'Director'),
        ('executive', 'Executive')], string='Experience Level', required=True)
    preferred_industry = fields.Char(string='Preferred Industry', required=True)
    nationality_requirement = fields.Char(string='Nationality Requirement')
    salary_range = fields.Char(string='Salary Range', required=True)
    job_location = fields.Char(string='Job Location')
    onsite_remote = fields.Selection([
        ('onsite', 'Onsite'),
        ('remote', 'Remote')], string='Onsite / Remote', required=True)
    permanent_contract = fields.Selection([
        ('permanent', 'Permanent Role'),
        ('contract', 'Contract through Flint')], string='Permanent Role / Contract through Flint', required=True)
    bidding_stage = fields.Selection([
        ('bidding', 'Bidding Stage'),
        ('live', 'Live Requirement')], string='Bidding Stage or Live Requirement', required=True)
    applicant_line = fields.One2many('applicant.line', 'recruitment_order_id', string='Order Lines')
    selection_link = fields.Char(string='Selection Link', readonly=True, copy=False,
                                 help='URL for accessing the selection page')
    access_token = fields.Char('Security Token', copy=False)
    applicant_ids_count = fields.Integer(string="Applicants", compute="_compute_applicant_count")
    last_stage_update = fields.Datetime(string="Last Stage Update", default=fields.Datetime.now)

    def _compute_applicant_count(self):
        for rec in self:
            rec.applicant_ids_count = 0
            created_applicant = self.env['hr.applicant'].search([('recruitment_order_id', '=', rec.id)])
            if created_applicant:
                rec.applicant_ids_count = len(created_applicant)

    def open_applicants(self):
        self.ensure_one()
        return {
            'name': _("Applicants Created from %s", self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.applicant',
            'domain': [('recruitment_order_id', '=', self.id)],
            'views': [(self.env.ref('hr_recruitment.crm_case_tree_view_job').id, 'tree'),
                      (False, 'form')],
        }

    # @api.returns('mail.message', lambda value: value.id)
    # def message_post(self, **kwargs):
    #     """ Override to handle the email sent state """
    #     message = super().message_post(**kwargs)
    #     if self.env.context.get('mark_so_as_sent'):
    #         self.write({'state': 'client_selection'})
    #         # Here already send email to recruiter so no need to send again but as of now we are sending email to recruiter.
    #         template = self.env.ref('era_recruitment_opportunity.email_template_headhunting_to_clientselection')
    #         recruiter_id = self.env['res.users'].browse(self.user_id.id)
    #         partner_id = recruiter_id.partner_id
    #         if template and partner_id:
    #             template.send_mail(
    #                 self.id,
    #                 force_send=True,
    #                 email_values={'partner_ids': [partner_id.id]}
    #             )
            # self.activity_update()
            # Create activity for operation manager
            # operation_manager = self.env.ref('scs_operation.group_operation_admin').users[:1]
            # if operation_manager:
            #     self.activity_schedule(
            #         'mail.mail_activity_data_todo',
            #         user_id=operation_manager.id,
            #         note="Dear %s, Logistic Order %s is ready for your review" % (
            #             operation_manager.name, self.name),
            #     )
        # elif self.env.context.get('mark_logistic_done'):
        #     self.write({'state': 'done'})
        #     # Generate vendor bill if vendor is selected
        #     if self.vendor_id and self.total_amount > 0:
        #         self.generate_vendor_bill()
        # return message

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        message = super().message_post(**kwargs)
        if self.env.context.get('mark_so_as_sent'):
            # move order to client_selection (as before)
            self.write({'state': 'client_selection'})

            line_ids = self.env.context.get('line_ids_for_email') or []
            lines_to_mark = self.applicant_line.filtered(
                lambda l: (not line_ids or l.id in line_ids)
                          and l.state in ('draft', 'confirm')
                          and not l.sent_to_client
            )
            if lines_to_mark:
                lines_to_mark.write({
                    'sent_to_client': True,
                    'client_sent_on': fields.Datetime.now(),
                })

            # (optional) recruiter notify — as you already do
            template = self.env.ref('era_recruitment_opportunity.email_template_headhunting_to_clientselection')
            recruiter_id = self.env['res.users'].browse(self.user_id.id)
            partner_id = recruiter_id.partner_id
            if template and partner_id:
                template.send_mail(
                    self.id,
                    force_send=True,
                    email_values={'partner_ids': [partner_id.id]}
                )
        return message

    @api.model
    def _get_available_recruiters(self, company_id=False):
        """Return recruitment.recruiter records for the company (active only)."""
        domain = [('active', '=', True)]
        if company_id:
            domain.append(('company_id', '=', company_id))
        return self.env['recruitment.recruiter'].search(domain, order='sequence, id')

    @api.model
    def _choose_recruiter_for_vals(self, vals):
        """
        Choose recruiter user_id for given vals.

        Priority:
        1) If vals contains lead_id and there exists any recruitment.order for that lead
           with user_id set, return that same user_id (lead-wise consistency).
        2) Otherwise select from recruitment.recruiter (active, company filtered)
           the user_id who has the least number of recruitment.order assigned.
           Ties broken by the order of recruitment.recruiter (sequence, id).
        """
        # 1) If lead_id present, keep same recruiter as existing orders for that lead
        lead_id = vals.get('lead_id') or False
        if lead_id:
            existing = self.search([('lead_id', '=', lead_id), ('user_id', '!=', False)], limit=1)
            if existing and existing.user_id:
                return existing.user_id.id

        # 2) Choose from recruitment.recruiter
        company_id = vals.get('company_id') or self.env.company.id
        recruiters = self._get_available_recruiters(company_id=company_id)
        if not recruiters:
            return False

        # list of user ids available via recruitment.recruiter (respect order by sequence)
        user_ids = recruiters.mapped('user_id.id')
        if not user_ids:
            return False

        # get counts of recruitment.order per user
        groups = self.env['recruitment.order'].read_group(
            [('user_id', 'in', user_ids)],
            ['user_id'],
            ['user_id']
        )
        counts = {g['user_id'][0]: g['user_id_count'] for g in groups if g.get('user_id')}
        # ensure every candidate user_id present with default 0
        for uid in user_ids:
            counts.setdefault(uid, 0)

        # find minimum and candidates
        min_count = min(counts.values()) if counts else 0
        candidates = [uid for uid, c in counts.items() if c == min_count]

        # prefer the first recruiter (by sequence) whose user_id in candidates
        for recruiter in recruiters:
            if recruiter.user_id and recruiter.user_id.id in candidates:
                return recruiter.user_id.id

        # fallback
        return candidates[0] if candidates else False

    def write(self, vals):
        if 'state' in vals:
            vals['last_stage_update'] = fields.Datetime.now()  # Update timestamp on stage change
        return super().write(vals)

    def _send_stage_stuck_notifications(self):
        """Cron job to check and notify recruiters about stuck recruitment orders."""

        policies = {policy.stage: policy.max_days for policy in self.env['recruitment.policy'].search([])}

        stuck_orders = []
        for order in self.search([('state', '!=', 'done')]):
            max_days = policies.get(order.state)
            if not max_days:
                continue  # Skip if no policy is set for this stage

            if order.last_stage_update and order.last_stage_update <= datetime.now() - timedelta(days=max_days):
                stuck_orders.append(order)

        template = self.env.ref('era_recruitment_opportunity.email_template_recruitment_stuck')

        for order in stuck_orders:
            if template and order.user_id:
                template.send_mail(
                    order.id,
                    force_send=True,
                    email_values={'partner_ids': [order.user_id.partner_id.id]}
                )

        return True

    @api.model_create_multi
    def create(self, vals_list):
        seq_code = 'recruitment.order'
        for vals in vals_list:
            if not vals.get('sequence') or vals.get('sequence') == _('New'):
                vals['sequence'] = self.env['ir.sequence'].next_by_code(seq_code) or _('New')
            if not vals.get('user_id'):
                try:
                    uid = self._choose_recruiter_for_vals(vals)
                    if uid:
                        vals['user_id'] = uid
                except Exception:
                    _logger.exception("Auto-assign recruiter failed for vals: %s", vals)

        records = super(RecruitmentOrder, self).create(vals_list)
        for rec in records:
            if rec.user_id:
                rec.message_post(body=_("Recruiter assigned: %s") % rec.user_id.display_name)
        return records

class ApplicantLine(models.Model):
    _name = 'applicant.line'
    _description = 'Applicant Information'

    recruitment_order_id = fields.Many2one('recruitment.order', string='Recruitment Order')
    sequence = fields.Char(default=lambda self: _('New'))
    name = fields.Char(string='Applicant Name')
    email = fields.Char(string='Email')
    phone = fields.Char(string='Contact #')
    nationality = fields.Char(string='Nationality')
    current_location = fields.Char(string='Current Location')
    experience = fields.Char(string='Experience')
    qualification = fields.Char(string='Qualification')
    current_company = fields.Char(string='Current Company')
    position = fields.Char(string='Position')
    notice_period = fields.Char(string='Notice Period')
    salary_expectation = fields.Float(string="Salary Expectation",
                                      help='Salary Expected in SAR per month (Including Gosi if Saudi)')
    show_salary_expectation = fields.Boolean(string="Don't Show Salary Expectation")
    wife = fields.Char(string='Dependents (Wife)')
    show_wife = fields.Boolean(string="Don't Show Wife")
    show_kids = fields.Boolean(string="Don't Show Kids")
    kids = fields.Char(string='Dependents (Kids)')
    profession = fields.Char(string='Profession on iqama')
    number_iqama = fields.Char(string='Number of Iqama Transfers')
    current_salary = fields.Float(string='Current Salary')
    show_current_salary = fields.Boolean(string="Don't Show Current Salary")
    resume = fields.Binary(string='Resume')
    # file_name = fields.Char('File Name', compute="_compute_file_name")
    file_name = fields.Char('File Name')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('reject', 'Rejected')
    ], string='Status', default='draft')
    rejection_reason = fields.Text(string="Rejection Reason")
    selection_link = fields.Char(string='Selection Link', readonly=True, copy=False,
                                 help='URL for accessing the selection page')
    access_token = fields.Char('Security Token', copy=False)
    rejection_date = fields.Datetime(string="Rejection Date", readonly=True)
    is_saved = fields.Boolean()
    sent_to_client = fields.Boolean(copy=False, default=False)
    client_sent_on = fields.Datetime(copy=False)

    def action_confirm(self):
        for record in self.sudo():
            target_recruitment_number = record.recruitment_order_id.no_of_recruitment
            total_confirmed_applicants = len(record.recruitment_order_id.applicant_line.filtered(lambda l: l.state == 'confirm'))
            if target_recruitment_number == total_confirmed_applicants or total_confirmed_applicants > target_recruitment_number:
                raise UserError(
                    _("You already fulfilled the recruitment target"))
            record.state = 'confirm'
        return True

    def action_reject(self):
        for record in self:
            if record.state == 'draft':
                record.state = 'reject'
                record.rejection_date = datetime.today()
        return True

    def action_draft(self):
        for record in self:
            if record.state != 'draft':
                record.state = 'draft'
        return True

    def write(self, vals):
        for record in self:
            if 'state' in vals:
                if vals.get('state') == 'confirm':
                    record.recruitment_order_id.sudo().with_context(app_id=record.id).create_recruitment_applicant()

                find_all_applicant = self.env['applicant.line'].sudo().search([
                    ('recruitment_order_id', '=', record.recruitment_order_id.id)
                ])
                expect_current_one = find_all_applicant.filtered(lambda x: x.id != record.id)

                if all(rec.state in ('confirm', 'reject') for rec in expect_current_one):
                    record.recruitment_order_id.sudo().action_in_progress()

        return super(ApplicantLine, self).write(vals)

    # comment this because it gives error while creating record for applicant line model.
    # @api.depends('name')
    # def _compute_file_name(self):
    #     for rec in self:
    #         rec.file_name = rec.name + "'s CV"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('sequence') or vals['sequence'] == _('New'):
                vals['sequence'] = self.env['ir.sequence'].next_by_code('applicant.sequence') or _('New')
            vals['is_saved'] = True
        ApplicantLine = super().create(vals_list)
        for rec in ApplicantLine:
            rec.selection_link = self.env['ir.config_parameter'].sudo().get_param('web.base.url') + \
                                 rec.action_generate_portal_url()['url']
        return ApplicantLine

    def action_generate_portal_url(self):
        self.ensure_one()
        if not self.access_token:
            self._generate_access_token()
        return {
            'type': 'ir.actions.act_url',
            'url': '/my/applicant-bidding/reject/%s?access_token=%s' % (self.id, self.access_token),
            'target': 'self',
        }

    def _generate_access_token(self):
        for record in self:
            record.access_token = uuid.uuid4().hex

    # Following code is for dynamic performance report

    date_from = fields.Datetime(string="Date From", help='Start date of report',
                                default=lambda self: fields.Datetime.to_string(datetime.now() - timedelta(days=365)))
    date_to = fields.Datetime(string="Date to", help='End date of report', default=fields.Date.context_today)
    report_type = fields.Selection([
        ('report_by_order', 'Report By Order'),
        ('report_by_order_detail', 'Report By Order Detail')], default='report_by_order',
        help='The order of the report')

    @api.model
    def recruitment_performance_report(self, option):
        """Function for getting datas for requests """
        report_values = self.env['applicant.line'].search(
            [('id', '=', option[0])])
        data = {
            'report_type': report_values.report_type,
            'model': self,
        }
        if report_values.date_from:
            data.update({
                'date_from': report_values.date_from,
            })
        if report_values.date_to:
            data.update({
                'date_to': report_values.date_to,
            })
        filters = self.get_filter(option)
        lines = self._get_report_values(data).get('PURCHASE')
        return {
            'name': "Performance Report",
            'type': 'ir.actions.client',
            'tag': 's_r',
            'orders': data,
            'filters': filters,
            'report_lines': lines,
        }

    def get_filter(self, option):
        """Function for get data according to order_by filter """
        data = self.get_filter_data(option)
        filters = {}
        if data.get('report_type') == 'report_by_order':
            filters['report_type'] = 'Report By Order'
        else:
            filters['report_type'] = 'Report By Order Detail'
        return filters

    def get_filter_data(self, option):
        """ Function for get filter data in report """
        record = self.env['applicant.line'].search([('id', '=', option[0])])
        default_filters = {}
        filter_dict = {
            'report_type': record.report_type,
        }
        filter_dict.update(default_filters)
        return filter_dict

    def _get_report_sub_lines(self, data):
        """ Function for get report value using sql query """
        report_sub_lines = []
        if data.get('report_type') == 'report_by_order':
            query = """ select sequence,name,rejection_reason,id
           from applicant_line where recruitment_order_id is not null and rejection_reason is not null
            """
            if data.get('date_from'):
                query += """and create_date >= '%s' """ % data.get('date_from')
            if data.get('date_to'):
                query += """ and create_date <= '%s' """ % data.get('date_to')
            # query += """group by l.user_id,res_users.partner_id,res_partner.name,
            #          l.partner_id,l.date_order,l.name,l.amount_total,l.notes,l.id"""
            try:
                self._cr.execute(query)
                # result = self._cr.fetchall()
                # Process result...
            except Exception as e:
                self._cr.rollback()  # Rollback the failed transaction
                raise e
            report_by_order = self._cr.dictfetchall()
            report_sub_lines.append(report_by_order)
        else:
            query = """ select l.sequence,l.name,l.rejection_reason,
                       from applicant_line as l Where
                        """
            if data.get('date_from'):
                query += """ l.date_order >= '%s' """ % data.get('date_from')
            if data.get('date_to'):
                query += """ and l.date_order <= '%s' """ % data.get('date_to')
            # query += """group by l.user_id,res_users.partner_id,res_partner.name,
            #          l.partner_id,l.date_order,l.name,l.amount_total,l.notes,l.id"""
            self._cr.execute(query)
            report_by_order = self._cr.dictfetchall()
            report_sub_lines.append(report_by_order)
        return report_sub_lines

    def _get_report_values(self, data):
        """ Get report values based on the provided data. """
        docs = data['model']
        if data.get('report_type'):
            report_res = \
                self._get_report_sub_lines(data)[0]
        else:
            report_res = self._get_report_sub_lines(data)
        return {
            'doc_ids': self.ids,
            'docs': docs,
            'PURCHASE': report_res,
        }

    # Cost Analysis
    # Cost analysis
    basic = fields.Float('Basic Salary')
    housing = fields.Float()
    transportation = fields.Float('Transportation')
    vac_salary = fields.Float("Vac Salary 12 months PO", required=True)
    end_of_service = fields.Float()
    employee_health = fields.Float("Employee Health Insurance", compute="_compute_monthly_health_insurance", store=True)
    spouse_health_insurance = fields.Float("Spouse Health Insurance")
    kids_health_insurance = fields.Float("Kids  Health Insurance")
    family_health_insurance = fields.Float("Family Health Insurance", compute="_compute_monthly_health_insurance", store=True)
    employee_annual_flight_ticket = fields.Float()
    employee_monthly_flight_ticket = fields.Float(string="Employee Monthly Flight Ticket",
                                                  compute="_compute_employee_monthly_flight")
    wife_annual_flight_ticket = fields.Float()
    wife_monthly_flight_ticket = fields.Float(string="Wife Monthly Flight Ticket",
                                              compute="_compute_wife_monthly_flight")
    child_flight_ticket = fields.Float("Child Annual Flight Ticket")
    child_monthly_flight_ticket = fields.Float(string="child Monthly Flight Ticket",
                                               compute="_compute_child_monthly_flight")

    family_annual_flight_ticket = fields.Float("Family Annual Flight Ticket")

    saudi_eng_council = fields.Float("Saudi Engineering Council", compute='_compute_net_monthly', readonly=False, store=True)
    hire_right_process = fields.Float("Hire Right Process", compute='_compute_net_monthly', readonly=False, store=True)
    employee_visa = fields.Float("Employee Visa Cost", compute='_compute_net_monthly', readonly=False, store=True)
    employee_visa_endorsement = fields.Float("Employee Visa Endorsement", compute='_compute_net_monthly',
                                             readonly=False, store=True)
    family_visa_cost = fields.Float("Family Visa Cost", compute='_compute_net_monthly', readonly=False, store=True)
    family_visa_endorsement = fields.Float("Family Visa Endorsement", compute='_compute_net_monthly', readonly=False, store=True)
    gosi = fields.Float(required=False)
    gosi_share = fields.Float(required=False)
    saudization = fields.Float(required=False)
    iqama_fees = fields.Float(required=False)
    iqama_transfer_fees = fields.Float(required=False)
    # iqama_transfer_percentage = fields.Float(required=False, help="Enter Amount For Iqama Transfer Fees")
    iqama_transfer_percentage = fields.Float(
    string="Iqama Transfers (count)",
    help="Enter number of transfers: 1, 2, or 3+")
    mobilization_cost = fields.Float(required=False)
    ajeer = fields.Float()
    exit_reentry = fields.Float()
    profile_fees = fields.Float("Profile Fees (One-time)")
    candidate_type = fields.Selection(
        [
            ("saudi_local", "Saudi Local"),
            ("no_saudi", "Non-Saudi"),
            ("remote", "Remote"),
        ],
        default="saudi_local",
    )
    expatriates_married_type = fields.Selection(
        [("married_status_new_visa", "Expatriates - Married Status New Visa"),
         ("married_status_iqama_transfer", "Expatriates - Married Status Iqama Transfer")]
    )
    expatriates_unmarried_type = fields.Selection(
        [("single_status_new_visa", "Expatriates - Single Status New Visa"),
         ("single_status_iqama_transfer", "Expatriates  - Single Status Iqama Transfer")]
    )
    marital_status = fields.Selection(
        [("married", "Married"), ("unmarried", "Un-Married")],
        required=True,
        default="unmarried",
    )
    candidate_class = fields.Selection(
        [("class_a", "A"),
         ("class_a_plus", "A+"),
         ("class_b", "B"),
         ("class_b_plus", "B+"),
         ("class_c", "C"),
         ("class_c_plus", "C+")],
        required=True,
        default="class_a",
    )
    package = fields.Float()
    misc = fields.Float("Miscellaneous")
    flint_fee = fields.Float()
    number_of_kids = fields.Integer("kids", default=0)
    number_of_spouses = fields.Integer("Spouses", default=0)
    invoice_period = fields.Float("Invoice Period (No. of months)", required=True)
    total_monthly_cost = fields.Float(
        compute="_compute_total_monthly_cost",
        store=True,
    )
    total_monthly_cost_usd = fields.Char(
        compute="_compute_total_monthly_cost",
        store=True,
    )
    total_annual_cost_usd = fields.Char(
        compute="_compute_total_monthly_cost",
        store=True,
    )
    percentage_amount = fields.Float("Percentage Amount", help="Enter Amount For Percentage Amount")

    per_25 = fields.Char(
        compute="_compute_total_monthly_cost",
        store=True,
    )
    percentage_amount_fifteen = fields.Float("Percentage Amount", help="Enter Amount For Percentage Amount")

    per_15 = fields.Char(
        compute="_compute_total_monthly_cost",
        store=True,
    )
    per_day_cost = fields.Char(
        compute="_compute_total_monthly_cost",
        store=True,
    )

    net_monthly_salary = fields.Float(string='Net Salary', compute="_compute_net_monthly", store=True)
    yearly_employee_cost = fields.Float(
        compute="_compute_yearly_cost",
        store=True,
    )
    # Validation fields
    is_create_job = fields.Boolean(string="Create Job", default=False)
    applicant_ids_count = fields.Integer(string="Applicants", compute="_compute_applicant_count")

    show_cost_case1 = fields.Boolean(string="Show Case 1 Fields", compute="_compute_show_cost_case1")
    show_cost_case2 = fields.Boolean(
        string="Show Cost Case 2",
        compute="_compute_show_cost_case2",
        store=True
    )
    show_cost_case3 = fields.Boolean(
        compute="_compute_show_cost_case3",
        store=False
    )
    show_cost_case4 = fields.Boolean(
        compute="_compute_show_cost_case4", store=True
    )
    show_cost_case5 = fields.Boolean(
        compute="_compute_show_cost_case5", store=True
    )

    # @api.onchange('iqama_transfer_percentage')
    # def _onchange_percentage_iqama_transfer(self):
    #     for rec in self:
    #         if rec.iqama_transfer_percentage > 0:
    #             per_iq_val = float(rec.iqama_transfer_fees or 0)
    #             perc_val = float(rec.iqama_transfer_percentage or 0)
    #             result = per_iq_val * perc_val
    #             rec.iqama_transfer_fees = result

    @api.onchange('iqama_transfer_percentage', 'invoice_period', 'candidate_type')
    def _onchange_percentage_iqama_transfer(self):
        """Iqama transfer count → annual ladder (2000/4000/6000) → monthly."""
        for rec in self:
            count = int(rec.iqama_transfer_percentage or 0)  # treat as COUNT: 1, 2, 3+
            yearly = 0.0
            if rec.candidate_type == 'no_saudi':
                if count == 1:
                    yearly = 2000.0
                elif count == 2:
                    yearly = 4000.0
                elif count >= 3:
                    yearly = 6000.0
            months = rec.invoice_period or 12.0
            rec.iqama_transfer_fees = float_round((yearly / months) if yearly else 0.0, precision_digits=2)

    @api.onchange('percentage_amount')
    def _onchange_percentage_amount(self):
        for rec in self:
            if rec.percentage_amount > 0:
                per_25_val = float(rec.per_day_cost or 0)
                perc_val = float(rec.percentage_amount or 0)
                result = per_25_val + ((per_25_val * perc_val) / 100)
                rec.per_25 = _fmt2(result)

    @api.onchange('percentage_amount_fifteen')
    def _onchange_percentage_amount_fifteen(self):
        for rec in self:
            if rec.percentage_amount_fifteen > 0:
                per_15_val = float(rec.per_25 or 0)
                perc_val = float(rec.percentage_amount_fifteen or 0)
                result = per_15_val + ((per_15_val * perc_val) / 100)
                rec.per_15 = _fmt2(result)

    @api.depends('candidate_type', 'marital_status', 'expatriates_married_type')
    def _compute_show_cost_case1(self):
        """
        Case 1:
        Candidate Type --> no_saudi
        Marital Status --> Married
        expatriates_married_type --> married_status_new_visa
        """
        for rec in self:
            rec.show_cost_case1 = (
                    rec.candidate_type == 'no_saudi'
                    and rec.marital_status == 'married'
                    and rec.expatriates_married_type == 'married_status_new_visa'
            )

    @api.depends('candidate_type', 'marital_status', 'expatriates_married_type')
    def _compute_show_cost_case2(self):
        for rec in self:
            rec.show_cost_case2 = (
                    rec.candidate_type == 'no_saudi'
                    and rec.marital_status == 'married'
                    and rec.expatriates_married_type == 'married_status_iqama_transfer'
            )
            # if rec.show_cost_case2:
            #     insurance_value = 5000
            #     print(">>>>22222222222222>>>>>>>>aaaaaaaa>>>>>>", insurance_value)
            #     rec.employee_health = insurance_value / 12
            rec._compute_monthly_health_insurance()

    @api.depends('candidate_type', 'marital_status', 'expatriates_unmarried_type')
    def _compute_show_cost_case3(self):
        for rec in self:
            rec.show_cost_case3 = (
                    rec.candidate_type == 'no_saudi'
                    and rec.marital_status == 'unmarried'
                    and rec.expatriates_unmarried_type == 'single_status_new_visa'
            )
            # if rec.show_cost_case3:
            if not rec.is_saved:
                rec.flint_fee = float_round((float(self.env['ir.config_parameter'].sudo().get_param(
                    'era_recruitment_opportunity.flint_fee'))), precision_digits=2)
            elif not rec.flint_fee:
                rec.flint_fee = 0.0

    @api.depends("candidate_type", "marital_status", "expatriates_unmarried_type")
    def _compute_show_cost_case4(self):
        for rec in self:
            rec.show_cost_case4 = (
                    rec.candidate_type == "no_saudi"
                    and rec.marital_status == "unmarried"
                    and rec.expatriates_unmarried_type == "single_status_iqama_transfer"
            )

    @api.depends("candidate_type", "marital_status")
    def _compute_show_cost_case5(self):
        for rec in self:
            rec.show_cost_case5 = (
                    rec.candidate_type == "saudi_local"
                    and rec.marital_status == "unmarried"
            )

    show_cost_case6 = fields.Boolean(
        compute="_compute_show_cost_case6", store=True
    )

    @api.depends("candidate_type", "marital_status")
    def _compute_show_cost_case6(self):
        for rec in self:
            rec.show_cost_case6 = (
                    rec.candidate_type == "saudi_local"
                    and rec.marital_status == "married"
            )

    show_cost_case7 = fields.Boolean(
        compute="_compute_show_cost_case7", store=True
    )

    @api.depends("candidate_type")
    def _compute_show_cost_case7(self):
        for rec in self:
            rec.show_cost_case7 = rec.candidate_type == "remote"

    @api.depends('employee_annual_flight_ticket')
    def _compute_employee_monthly_flight(self):
        for rec in self:
            rec.employee_monthly_flight_ticket = rec.employee_annual_flight_ticket / 12
            rec._compute_net_monthly()

    @api.depends('wife_annual_flight_ticket')
    def _compute_wife_monthly_flight(self):
        for rec in self:
            rec.wife_monthly_flight_ticket = rec.wife_annual_flight_ticket / 12

    @api.depends('child_flight_ticket', 'number_of_kids')
    def _compute_child_monthly_flight(self):
        for rec in self:
            rec.child_monthly_flight_ticket = (rec.child_flight_ticket * rec.number_of_kids) / 12

    def _compute_applicant_count(self):
        for rec in self:
            rec.applicant_ids_count = 0
            created_applicant = self.env['hr.applicant'].search([('lead_id', '=', rec.id)])
            if created_applicant:
                rec.applicant_ids_count = len(created_applicant)

    def open_applicants(self):
        self.ensure_one()
        return {
            'name': _("Applicants Created from %s", self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.applicant',
            'domain': [('lead_id', '=', self.id)],
            'views': [(self.env.ref('hr_recruitment.crm_case_tree_view_job').id, 'tree'),
                      (False, 'form')],
        }

    @api.depends("exit_reentry", "mobilization_cost", "profile_fees", "ajeer", "iqama_transfer_fees", "iqama_fees",
                 "saudization", "gosi", "employee_health", "spouse_health_insurance", "kids_health_insurance",
                 "child_flight_ticket", "wife_annual_flight_ticket", "employee_annual_flight_ticket",
                 "end_of_service", "misc", "saudi_eng_council", "hire_right_process", "employee_visa",
                 "employee_visa_endorsement", "family_visa_cost", "family_visa_endorsement",
                 "vac_salary", "total_monthly_cost", 'invoice_period', "percentage_amount", "percentage_amount_fifteen"
                 )
    def _compute_total_monthly_cost(self):
        for rec in self:
            if rec.candidate_type == "no_saudi":
                # rec.total_monthly_cost = 0
                if rec.show_cost_case1:
                    rec.total_monthly_cost = (
                                rec.net_monthly_salary + rec.gosi + rec.employee_annual_flight_ticket + rec.end_of_service +
                                rec.flint_fee + rec.iqama_transfer_fees + rec.iqama_fees + rec.employee_health + rec.family_health_insurance +
                                rec.family_annual_flight_ticket + rec.saudi_eng_council + rec.hire_right_process +
                                rec.employee_visa + rec.employee_visa_endorsement + rec.family_visa_cost +
                                rec.family_visa_endorsement + rec.misc
                                )
                elif rec.show_cost_case2:
                    rec.total_monthly_cost = (
                            rec.net_monthly_salary + rec.gosi + rec.employee_annual_flight_ticket + rec.end_of_service +
                            rec.flint_fee + rec.iqama_transfer_fees + rec.iqama_fees + rec.employee_health + rec.family_health_insurance +
                            rec.family_annual_flight_ticket + rec.saudi_eng_council + rec.hire_right_process +
                            rec.misc
                    )
                elif rec.show_cost_case3:
                    rec.total_monthly_cost = (
                            rec.net_monthly_salary + rec.gosi + rec.employee_annual_flight_ticket + rec.end_of_service +
                            rec.flint_fee + rec.iqama_transfer_fees + rec.iqama_fees + rec.employee_health + rec.saudi_eng_council + rec.hire_right_process +
                            rec.employee_visa + rec.employee_visa_endorsement + rec.misc
                    )
                elif rec.show_cost_case4:
                    rec.total_monthly_cost = (
                            rec.net_monthly_salary + rec.gosi + rec.employee_annual_flight_ticket + rec.end_of_service +
                            rec.flint_fee + rec.iqama_transfer_fees + rec.iqama_fees + rec.employee_health + rec.saudi_eng_council + rec.hire_right_process +
                            rec.misc
                    )
            elif rec.candidate_type == "saudi_local":
                if rec.show_cost_case5:
                    rec.total_monthly_cost = (
                            rec.net_monthly_salary + rec.gosi + rec.gosi_share + rec.end_of_service +
                            rec.employee_health +
                            rec.hire_right_process +
                            rec.misc
                    )
                elif rec.show_cost_case6:
                    rec.total_monthly_cost = (
                            rec.net_monthly_salary + rec.gosi + rec.gosi_share + rec.end_of_service +
                            rec.employee_health + rec.family_health_insurance +
                            rec.hire_right_process +
                            rec.misc
                    )
            else:
                rec.total_monthly_cost = (
                        rec.net_monthly_salary + rec.end_of_service +
                        rec.employee_visa_endorsement +
                        rec.misc
                )

            # ---- Values that are Char fields: format to 2-dec strings ----
            rec.total_monthly_cost_usd = _fmt2(rec.total_monthly_cost / 3.75)
            rec.total_annual_cost_usd = _fmt2((rec.total_monthly_cost / 3.75) * 12)

            per_day_usd = ((rec.total_monthly_cost / 3.75) * 12) / 228
            rec.per_day_cost = _fmt2(per_day_usd)

            # base_per25 = per_day_usd * 1.25
            # rec.per_25 = _fmt2(base_per25)
            # if rec.percentage_amount > 0:
            #     per_25_val = float(rec.per_25 or 0)
            #     perc_val = float(rec.percentage_amount or 0)
            #     result = per_25_val + ((per_25_val * perc_val) / 100)
            #     rec.per_25 = _fmt2(result)

            # base_per15 = per_day_usd * 1.25 * 1.15
            # rec.per_15 = _fmt2(base_per15)
            # if rec.percentage_amount_fifteen > 0:
            #     per_15_val = float(rec.per_15 or 0)
            #     perc_val = float(rec.percentage_amount_fifteen or 0)
            #     result = per_15_val + ((per_15_val * perc_val) / 100)
            #     rec.per_15 = _fmt2(result)
            # per_day_usd = ((rec.total_monthly_cost / 3.75) * 12) / 228
            # rec.per_day_cost = _fmt2(per_day_usd)

            if rec.percentage_amount and rec.percentage_amount > 0:
                base_per25 = per_day_usd * 1.0
                rec.per_25 = _fmt2(base_per25 + (base_per25 * rec.percentage_amount / 100.0))
            else:
                rec.per_25 = "0.00"

            if rec.percentage_amount_fifteen and rec.percentage_amount_fifteen > 0:
                base_per15 = float(rec.per_25) * 1.1
                rec.per_15 = _fmt2(base_per15)
            else:
                rec.per_15 = "0.00"

    # @api.depends('basic', 'housing', 'transportation', 'number_of_kids', 'number_of_spouses', 'marital_status',
    #              'candidate_type')
    # def _compute_net_monthly(self):
    #     for rec in self:
    #         ICP = self.env['ir.config_parameter'].sudo().get_param
    #         rec.net_monthly_salary = rec.basic + rec.housing + rec.transportation
    #         family_member = rec.number_of_kids + rec.number_of_spouses + 1

    #         if family_member > 3:
    #             family_member = 3
    #         if rec.candidate_type == "remote":
    #             gross = rec.basic + rec.housing + rec.transportation

    #             # EOSB
    #             rec.end_of_service = float_round((gross / 24.0) if gross else 0.0, precision_digits=2)

    #             # Visa endorsement (annual param ÷ 12)
    #             # endr_y = float(ICP('era_recruitment_opportunity.visa_endorsement') or 0.0)
    #             # rec.employee_visa_endorsement = float_round(endr_y / 12.0, precision_digits=2)

    #             # Misc (option 1: record pe manual input, option 2: system param)
    #             misc_val = rec.misc
    #             if not misc_val and rec.state == 'draft':
    #                 misc_val = float(ICP('era_recruitment_opportunity.remote_misc') or 0.0)  # system param se lo
    #                 rec.misc = misc_val  # default fill kar do
    #             else:
    #                 rec.misc = 0
    #             # reset other fields
    #             rec.gosi = rec.gosi_share = 0
    #             rec.iqama_fees = rec.iqama_transfer_fees = 0
    #             rec.saudi_eng_council = rec.hire_right_process = 0
    #             rec.employee_visa = rec.family_visa_cost = rec.family_visa_endorsement = 0
    #             rec.flint_fee = 0
    #             rec.employee_health = rec.family_health_insurance = 0

    #             # Net + Total
    #             rec.net_monthly_salary = float_round(rec.basic + rec.housing + rec.transportation, precision_digits=2)
    #             rec.total_monthly_cost = float_round(rec.net_monthly_salary + rec.end_of_service, precision_digits=2)
    #             if rec.state == 'draft':
    #                 rec.misc = float_round((float(self.env['ir.config_parameter'].sudo().get_param(
    #                     'era_recruitment_opportunity.misc'))), precision_digits=2)
    #             elif not rec.misc:
    #                 rec.misc = 0
    #             rec.employee_visa_endorsement = float_round((gross) * 0.05, precision_digits=2)

    #         if rec.marital_status == 'married' and rec.candidate_type == "no_saudi":
    #             if rec.state == 'draft':
    #                 rec.family_visa_endorsement = float_round(((float(self.env['ir.config_parameter'].sudo().get_param(
    #                     'era_recruitment_opportunity.family_visa_endorsement')) * (family_member - 1)) / 12),
    #                                                           precision_digits=2)
    #                 rec.family_visa_cost = float_round((float(self.env['ir.config_parameter'].sudo().get_param(
    #                     'era_recruitment_opportunity.family_visa_cost')) / 12), precision_digits=2)
    #             else:
    #                 if not rec.family_visa_endorsement:
    #                     rec.family_visa_endorsement = 0
    #                 if not rec.family_visa_cost:
    #                     rec.family_visa_cost = 0

    #         elif rec.marital_status == 'married' and rec.candidate_type == "saudi_local":
    #             rec.family_visa_endorsement = 0
    #             rec.family_visa_cost = 0

    #         elif rec.marital_status == 'unmarried':
    #             rec.number_of_kids = 0
    #             rec.number_of_spouses = 0
    #             family_member = rec.number_of_kids + rec.number_of_spouses + 1
    #             rec.family_visa_endorsement = 0
    #             rec.family_visa_cost = 0

    #         rec.end_of_service = (
    #                                  float_round(
    #                                      rec.net_monthly_salary and rec.net_monthly_salary / 24,
    #                                      precision_digits=2,
    #                                  )
    #                              ) or 0

    #         if rec.candidate_type == "no_saudi" and rec.marital_status == "married":
    #             if rec.state == 'draft':
    #                 rec.iqama_fees = float_round((float(self.env['ir.config_parameter'].sudo().get_param(
    #                     'era_recruitment_opportunity.iqama_fee')) / 12), precision_digits=2)
    #             elif not rec.iqama_fees:
    #                 rec.iqama_fees = 0

    #             new_iqama_annual_amount = 0
    #             if family_member == 1:
    #                 new_iqama_annual_amount = 2000
    #             elif family_member == 2:
    #                 new_iqama_annual_amount = 4000
    #             elif family_member >= 3:
    #                 new_iqama_annual_amount = 6000
    #             rec.iqama_transfer_fees = float_round((new_iqama_annual_amount / 12), precision_digits=2)
    #             if rec.iqama_transfer_percentage > 0:
    #                 per_iq_val = float(rec.iqama_transfer_fees or 0)
    #                 perc_val = float(rec.iqama_transfer_percentage or 0)
    #                 result = per_iq_val * perc_val
    #                 rec.iqama_transfer_fees = result

    #             spouse_health = float_round((float(self.env['ir.config_parameter'].sudo().get_param(
    #                 'era_recruitment_opportunity.spouse_health_insurance_a'))), precision_digits=2)
    #             kid_health = float_round((float(self.env['ir.config_parameter'].sudo().get_param(
    #                 'era_recruitment_opportunity.kids_health_insurance_a'))), precision_digits=2)
    #             if rec.state == 'draft':
    #                 rec.family_health_insurance = float_round(
    #                     ((spouse_health * rec.number_of_spouses + (kid_health * rec.number_of_kids)) / 12),
    #                     precision_digits=2)
    #             elif not rec.family_health_insurance:
    #                 rec.family_health_insurance = 0

    #             rec.gosi = float_round(
    #                 ((rec.basic + rec.housing) * 0.02), precision_digits=2
    #             )
    #             rec.gosi_share = 0

    #             rec.ajeer = float_round((420 / 12), precision_digits=2)
    #             rec.exit_reentry = float_round(((200 * 4) / 12), precision_digits=2)
    #             if rec.state == 'draft':
    #                 rec.saudi_eng_council = float_round((float(self.env['ir.config_parameter'].sudo().get_param(
    #                     'era_recruitment_opportunity.saudi_eng_council')) / 12), precision_digits=2)
    #             elif not rec.saudi_eng_council:
    #                 rec.saudi_eng_council = 0

    #             if rec.state == 'draft':
    #                 rec.hire_right_process = float_round(
    #                     float(self.env['ir.config_parameter'].sudo().get_param(
    #                         'era_recruitment_opportunity.hire_right_process')) / 12,
    #                     precision_digits=2
    #                 )
    #             elif not rec.hire_right_process:
    #                 rec.hire_right_process = 0

    #             if rec.state == 'draft':
    #                 rec.employee_visa = float_round(
    #                     float(self.env['ir.config_parameter'].sudo().get_param(
    #                         'era_recruitment_opportunity.visa_cost')) / 12,
    #                     precision_digits=2
    #                 )
    #             elif not rec.employee_visa:
    #                 rec.employee_visa = 0

    #             if rec.state == 'draft':
    #                 rec.employee_visa_endorsement = float_round(
    #                     float(self.env['ir.config_parameter'].sudo().get_param(
    #                         'era_recruitment_opportunity.visa_endorsement')) / 12,
    #                     precision_digits=2
    #                 )
    #             elif not rec.employee_visa_endorsement:
    #                 rec.employee_visa_endorsement = 0

    #             if rec.state == 'draft':
    #                 rec.flint_fee = float_round(
    #                     float(self.env['ir.config_parameter'].sudo().get_param(
    #                         'era_recruitment_opportunity.flint_fee')),
    #                     precision_digits=2
    #                 )
    #             elif not rec.flint_fee:
    #                 rec.flint_fee = 0

    #             if rec.state == 'draft':
    #                 rec.employee_annual_flight_ticket = float_round(
    #                     float(self.env['ir.config_parameter'].sudo().get_param(
    #                         'era_recruitment_opportunity.annual_ticket_serv')) / 12,
    #                     precision_digits=2
    #                 )
    #             elif not rec.employee_annual_flight_ticket:
    #                 rec.employee_annual_flight_ticket = 0

    #             spouse_annual_ticket_config = float_round((float(self.env['ir.config_parameter'].sudo().get_param(
    #                 'era_recruitment_opportunity.spouse_annual_ticket'))), precision_digits=2)
    #             kid_annual_ticket_config = float_round((float(self.env['ir.config_parameter'].sudo().get_param(
    #                 'era_recruitment_opportunity.kid_annual_ticket'))), precision_digits=2)
    #             if rec.state == 'draft':
    #                 rec.family_annual_flight_ticket = float_round(((
    #                                                                            spouse_annual_ticket_config * rec.number_of_spouses + (
    #                                                                                kid_annual_ticket_config * rec.number_of_kids)) / 12),
    #                                                               precision_digits=2)
    #             elif not rec.family_annual_flight_ticket:
    #                 rec.family_annual_flight_ticket = 0

    #             if rec.state == 'draft':
    #                 rec.misc = float_round((float(self.env['ir.config_parameter'].sudo().get_param(
    #                     'era_recruitment_opportunity.misc'))), precision_digits=2)
    #             elif not rec.misc:
    #                 rec.misc = 0


    #         elif rec.candidate_type == "no_saudi" and rec.marital_status == "unmarried":
    #             rec.gosi = float_round(
    #                 ((rec.basic + rec.housing) * 0.02), precision_digits=2
    #             )
    #             rec.gosi_share = 0
    #             if rec.state == 'draft':
    #                 rec.iqama_fees = float_round((float(self.env['ir.config_parameter'].sudo().get_param(
    #                     'era_recruitment_opportunity.iqama_fee')) / 12), precision_digits=2)
    #             elif not rec.iqama_fees:
    #                 rec.iqama_fees = 0

    #             new_iqama_annual_amount = 0
    #             if family_member == 1:
    #                 new_iqama_annual_amount = 2000
    #             elif family_member == 2:
    #                 new_iqama_annual_amount = 4000
    #             elif family_member >= 3:
    #                 new_iqama_annual_amount = 6000
    #             rec.iqama_transfer_fees = float_round((new_iqama_annual_amount / 12), precision_digits=2)
    #             if rec.iqama_transfer_percentage > 0:
    #                 per_iq_val = float(rec.iqama_transfer_fees or 0)
    #                 perc_val = float(rec.iqama_transfer_percentage or 0)
    #                 result = per_iq_val * perc_val
    #                 rec.iqama_transfer_fees = result

    #             if rec.state == 'draft':
    #                 rec.hire_right_process = float_round(
    #                     float(self.env['ir.config_parameter'].sudo().get_param(
    #                         'era_recruitment_opportunity.hire_right_process')) / 12,
    #                     precision_digits=2
    #                 )
    #             elif not rec.hire_right_process:
    #                 rec.hire_right_process = 0

    #             if rec.state == 'draft':
    #                 rec.saudi_eng_council = float_round(
    #                     float(self.env['ir.config_parameter'].sudo().get_param(
    #                         'era_recruitment_opportunity.saudi_eng_council')) / 12,
    #                     precision_digits=2
    #                 )
    #             elif not rec.saudi_eng_council:
    #                 rec.saudi_eng_council = 0

    #             if rec.state == 'draft':
    #                 rec.employee_visa = float_round(
    #                     float(self.env['ir.config_parameter'].sudo().get_param(
    #                         'era_recruitment_opportunity.visa_cost')) / 12,
    #                     precision_digits=2
    #                 )
    #             elif not rec.employee_visa:
    #                 rec.employee_visa = 0

    #             if rec.state == 'draft':
    #                 rec.employee_visa_endorsement = float_round(
    #                     float(self.env['ir.config_parameter'].sudo().get_param(
    #                         'era_recruitment_opportunity.visa_endorsement')) / 12,
    #                     precision_digits=2
    #                 )
    #             elif not rec.employee_visa_endorsement:
    #                 rec.employee_visa_endorsement = 0

    #             if rec.invoice_period and rec.net_monthly_salary:
    #                 rec.profile_fees = float_round(
    #                     (rec.net_monthly_salary / 12),
    #                     precision_digits=2,
    #                 )

    #             if rec.state == 'draft':
    #                 rec.flint_fee = float_round(
    #                     float(self.env['ir.config_parameter'].sudo().get_param(
    #                         'era_recruitment_opportunity.flint_fee')),
    #                     precision_digits=2
    #                 )
    #             elif not rec.flint_fee:
    #                 rec.flint_fee = 0

    #             if rec.state == 'draft':
    #                 rec.employee_annual_flight_ticket = float_round(
    #                     float(self.env['ir.config_parameter'].sudo().get_param(
    #                         'era_recruitment_opportunity.annual_ticket_serv')) / 12,
    #                     precision_digits=2
    #                 )
    #             elif not rec.employee_annual_flight_ticket:
    #                 rec.employee_annual_flight_ticket = 0

    #             if rec.state == 'draft':
    #                 rec.misc = float_round(
    #                     float(self.env['ir.config_parameter'].sudo().get_param(
    #                         'era_recruitment_opportunity.misc')),
    #                     precision_digits=2
    #                 )
    #             elif not rec.misc:
    #                 rec.misc = 0


    #         elif rec.candidate_type == "saudi_local" and rec.marital_status == "unmarried":
    #             rec.gosi = float_round(
    #                 ((rec.basic + rec.housing) * 0.12), precision_digits=2
    #             )
    #             rec.gosi_share = float_round(
    #                 ((rec.basic + rec.housing) * 0.1), precision_digits=2
    #             )
    #             rec.iqama_fees = 0
    #             rec.flint_fee = 0
    #             rec.iqama_transfer_fees = 0
    #             if rec.state == 'draft':
    #                 rec.hire_right_process = float_round(
    #                     float(self.env['ir.config_parameter'].sudo().get_param(
    #                         'era_recruitment_opportunity.hire_right_process')) / 12,
    #                     precision_digits=2
    #                 )
    #             elif not rec.hire_right_process:
    #                 rec.hire_right_process = 0
    #             rec.saudi_eng_council = 0
    #             rec.employee_visa = 0
    #             rec.employee_visa_endorsement = 0
    #             if rec.invoice_period and rec.net_monthly_salary:
    #                 rec.profile_fees = float_round(
    #                     (rec.net_monthly_salary / 12),
    #                     precision_digits=2,
    #                 )
    #         elif rec.candidate_type == "saudi_local" and rec.marital_status == "married":
    #             rec.iqama_fees = 0

    #             rec.iqama_transfer_fees = 0
    #             if rec.state == 'draft':
    #                 rec.hire_right_process = float_round(
    #                     float(self.env['ir.config_parameter'].sudo().get_param(
    #                         'era_recruitment_opportunity.hire_right_process')) / 12,
    #                     precision_digits=2
    #                 )
    #             elif not rec.hire_right_process:
    #                 rec.hire_right_process = 0
    #             rec.saudi_eng_council = 0
    #             rec.employee_visa = 0
    #             rec.employee_visa_endorsement = 0
    #             rec.gosi = float_round(
    #                 ((rec.basic + rec.housing) * 0.12), precision_digits=2
    #             )
    #             rec.gosi_share = float_round(
    #                 ((rec.basic + rec.housing) * 0.1), precision_digits=2
    #             )
    #             if rec.invoice_period and rec.net_monthly_salary:
    #                 rec.profile_fees = float_round(
    #                     (rec.net_monthly_salary / 12),
    #                     precision_digits=2,
    #                 )
    #             rec.flint_fee = 0
    #             # Misc
    #             if rec.state == 'draft':
    #                 rec.misc = float_round(
    #                     float(self.env['ir.config_parameter'].sudo().get_param(
    #                         'era_recruitment_opportunity.misc')) or 0.0,
    #                     precision_digits=2
    #                 )
    #             elif not rec.misc:
    #                 rec.misc = 0
    #         else:
    #             rec.iqama_fees = 0

    #             rec.iqama_transfer_fees = 0
    #             if rec.state == 'draft':
    #                 rec.hire_right_process = float_round(
    #                     float(self.env['ir.config_parameter'].sudo().get_param(
    #                         'era_recruitment_opportunity.hire_right_process')) / 12,
    #                     precision_digits=2
    #                 )
    #             elif not rec.hire_right_process:
    #                 rec.hire_right_process = 0
    #             rec.saudi_eng_council = 0
    #             rec.employee_visa = 0
    #             if not rec.candidate_type == "remote":
    #                 rec.employee_visa_endorsement = 0
    #             rec.gosi = float_round(
    #                 ((rec.basic + rec.housing) * 0.12), precision_digits=2
    #             )
    #             rec.gosi_share = float_round(
    #                 ((rec.basic + rec.housing) * 0.1), precision_digits=2
    #             )
    #             if rec.invoice_period and rec.net_monthly_salary:
    #                 rec.profile_fees = float_round(
    #                     (rec.net_monthly_salary / 12),
    #                     precision_digits=2,
    #                 )
    #             if rec.state == 'draft':
    #                 rec.flint_fee = float_round(
    #                     float(self.env['ir.config_parameter'].sudo().get_param(
    #                         'era_recruitment_opportunity.flint_fee')) / 12,
    #                     precision_digits=2
    #                 )
    #             elif not rec.flint_fee:
    #                 rec.flint_fee = 0

    @api.depends( 'basic', 'housing', 'transportation', 'number_of_kids', 'number_of_spouses', 'marital_status', 'candidate_type', 'iqama_transfer_percentage', 'invoice_period')
    def _compute_net_monthly(self):
        for rec in self:
            ICP = self.env['ir.config_parameter'].sudo().get_param
            rec.net_monthly_salary = rec.basic + rec.housing + rec.transportation
            family_member = rec.number_of_kids + rec.number_of_spouses + 1
            if family_member > 3:
                family_member = 3

            # -------- Remote case --------
            if rec.candidate_type == "remote":
                gross = rec.basic + rec.housing + rec.transportation
                rec.end_of_service = float_round((gross / 24.0) if gross else 0.0, precision_digits=2)

                misc_val = rec.misc
                if not misc_val and not rec.is_saved:
                    misc_val = float(ICP('era_recruitment_opportunity.remote_misc') or 0.0)
                    rec.misc = misc_val
                else:
                    rec.misc = 0

                rec.gosi = rec.gosi_share = 0
                rec.iqama_fees = rec.iqama_transfer_fees = 0
                rec.saudi_eng_council = rec.hire_right_process = 0
                rec.employee_visa = rec.family_visa_cost = rec.family_visa_endorsement = 0
                rec.flint_fee = 0
                rec.employee_health = rec.family_health_insurance = 0

                rec.net_monthly_salary = float_round(gross, precision_digits=2)
                rec.total_monthly_cost = float_round(rec.net_monthly_salary + rec.end_of_service, precision_digits=2)
                if not rec.is_saved:
                    rec.misc = float_round(float(ICP('era_recruitment_opportunity.misc') or 0.0), precision_digits=2)
                elif not rec.misc:
                    rec.misc = 0
                rec.employee_visa_endorsement = float_round(gross * 0.05, precision_digits=2)

            # -------- Family visa costs (common) --------
            if rec.marital_status == 'married' and rec.candidate_type == "no_saudi":
                if not rec.is_saved:
                    rec.family_visa_endorsement = float_round(
                        (float(ICP('era_recruitment_opportunity.family_visa_endorsement') or 0.0) * (family_member - 1)) / 12,
                        precision_digits=2
                    )
                    rec.family_visa_cost = float_round(
                        float(ICP('era_recruitment_opportunity.family_visa_cost') or 0.0) / 12,
                        precision_digits=2
                    )
                else:
                    rec.family_visa_endorsement = rec.family_visa_endorsement or 0
                    rec.family_visa_cost = rec.family_visa_cost or 0

            elif rec.marital_status == 'married' and rec.candidate_type == "saudi_local":
                rec.family_visa_endorsement = 0
                rec.family_visa_cost = 0

            elif rec.marital_status == 'unmarried':
                rec.number_of_kids = 0
                rec.number_of_spouses = 0
                family_member = 1
                rec.family_visa_endorsement = 0
                rec.family_visa_cost = 0

            # EOSB
            rec.end_of_service = float_round((rec.net_monthly_salary / 24) if rec.net_monthly_salary else 0.0, 2) or 0.0

            # -------- Non-Saudi + Married --------
            if rec.candidate_type == "no_saudi" and rec.marital_status == "married":
                if not rec.is_saved:
                    rec.iqama_fees = float_round(float(ICP('era_recruitment_opportunity.iqama_fee') or 0.0) / 12, 2)
                elif not rec.iqama_fees:
                    rec.iqama_fees = 0

                # Iqama transfer ladder (count-based)
                count = int(rec.iqama_transfer_percentage or 0)
                yearly = 0.0
                if count == 1:
                    yearly = 2000.0
                elif count == 2:
                    yearly = 4000.0
                elif count >= 3:
                    yearly = 6000.0
                months = rec.invoice_period or 12.0
                rec.iqama_transfer_fees = float_round((yearly / months) if yearly else 0.0, 2)

                spouse_health = float_round(float(ICP('era_recruitment_opportunity.spouse_health_insurance_a') or 0.0), 2)
                kid_health = float_round(float(ICP('era_recruitment_opportunity.kids_health_insurance_a') or 0.0), 2)
                if not rec.is_saved:
                    rec.family_health_insurance = float_round(
                        ((spouse_health * rec.number_of_spouses) + (kid_health * rec.number_of_kids)) / 12, 2)
                elif not rec.family_health_insurance:
                    rec.family_health_insurance = 0

                rec.gosi = float_round((rec.basic + rec.housing) * 0.02, 2)
                rec.gosi_share = 0
                rec.ajeer = float_round(420 / 12, 2)
                rec.exit_reentry = float_round((200 * 4) / 12, 2)

                if not rec.is_saved:
                    rec.saudi_eng_council = float_round(float(ICP('era_recruitment_opportunity.saudi_eng_council') or 0.0) / 12, 2)
                elif not rec.saudi_eng_council:
                    rec.saudi_eng_council = 0

                if not rec.is_saved:
                    rec.hire_right_process = float_round(float(ICP('era_recruitment_opportunity.hire_right_process') or 0.0) / 12, 2)
                elif not rec.hire_right_process:
                    rec.hire_right_process = 0

                if not rec.is_saved:
                    rec.employee_visa = float_round(float(ICP('era_recruitment_opportunity.visa_cost') or 0.0) / 12, 2)
                elif not rec.employee_visa:
                    rec.employee_visa = 0

                if not rec.is_saved:
                    rec.employee_visa_endorsement = float_round(float(ICP('era_recruitment_opportunity.visa_endorsement') or 0.0) / 12, 2)
                elif not rec.employee_visa_endorsement:
                    rec.employee_visa_endorsement = 0

                if not rec.is_saved:
                    rec.flint_fee = float_round(float(ICP('era_recruitment_opportunity.flint_fee') or 0.0), 2)
                elif not rec.flint_fee:
                    rec.flint_fee = 0

                if not rec.is_saved:
                    rec.employee_annual_flight_ticket = float_round(float(ICP('era_recruitment_opportunity.annual_ticket_serv') or 0.0) / 12, 2)
                elif not rec.employee_annual_flight_ticket:
                    rec.employee_annual_flight_ticket = 0

                spouse_ticket = float_round(float(ICP('era_recruitment_opportunity.spouse_annual_ticket') or 0.0), 2)
                kid_ticket = float_round(float(ICP('era_recruitment_opportunity.kid_annual_ticket') or 0.0), 2)
                if not rec.is_saved:
                    rec.family_annual_flight_ticket = float_round(
                        ((spouse_ticket * rec.number_of_spouses) + (kid_ticket * rec.number_of_kids)) / 12, 2)
                elif not rec.family_annual_flight_ticket:
                    rec.family_annual_flight_ticket = 0

                if not rec.is_saved:
                    rec.misc = float_round(float(ICP('era_recruitment_opportunity.misc') or 0.0), 2)
                elif not rec.misc:
                    rec.misc = 0

            # -------- Non-Saudi + Unmarried --------
            elif rec.candidate_type == "no_saudi" and rec.marital_status == "unmarried":
                rec.gosi = float_round((rec.basic + rec.housing) * 0.02, 2)
                rec.gosi_share = 0
                if not rec.is_saved:
                    rec.iqama_fees = float_round(float(ICP('era_recruitment_opportunity.iqama_fee') or 0.0) / 12, 2)
                elif not rec.iqama_fees:
                    rec.iqama_fees = 0

                # Iqama transfer ladder (same as above)
                count = int(rec.iqama_transfer_percentage or 0)
                yearly = 0.0
                if count == 1:
                    yearly = 2000.0
                elif count == 2:
                    yearly = 4000.0
                elif count >= 3:
                    yearly = 6000.0
                months = rec.invoice_period or 12.0
                rec.iqama_transfer_fees = float_round((yearly / months) if yearly else 0.0, 2)

                if not rec.is_saved:
                    rec.hire_right_process = float_round(float(ICP('era_recruitment_opportunity.hire_right_process') or 0.0) / 12, 2)
                elif not rec.hire_right_process:
                    rec.hire_right_process = 0

                if not rec.is_saved:
                    rec.saudi_eng_council = float_round(float(ICP('era_recruitment_opportunity.saudi_eng_council') or 0.0) / 12, 2)
                elif not rec.saudi_eng_council:
                    rec.saudi_eng_council = 0

                if not rec.is_saved:
                    rec.employee_visa = float_round(float(ICP('era_recruitment_opportunity.visa_cost') or 0.0) / 12, 2)
                elif not rec.employee_visa:
                    rec.employee_visa = 0

                if not rec.is_saved:
                    rec.employee_visa_endorsement = float_round(float(ICP('era_recruitment_opportunity.visa_endorsement') or 0.0) / 12, 2)
                elif not rec.employee_visa_endorsement:
                    rec.employee_visa_endorsement = 0

                if rec.invoice_period and rec.net_monthly_salary:
                    rec.profile_fees = float_round((rec.net_monthly_salary / 12), 2)

                if not rec.is_saved:
                    rec.flint_fee = float_round(float(ICP('era_recruitment_opportunity.flint_fee') or 0.0), 2)
                elif not rec.flint_fee:
                    rec.flint_fee = 0

                if not rec.is_saved:
                    rec.employee_annual_flight_ticket = float_round(float(ICP('era_recruitment_opportunity.annual_ticket_serv') or 0.0) / 12, 2)
                elif not rec.employee_annual_flight_ticket:
                    rec.employee_annual_flight_ticket = 0

                if not rec.is_saved:
                    rec.misc = float_round(float(ICP('era_recruitment_opportunity.misc') or 0.0), 2)
                elif not rec.misc:
                    rec.misc = 0

            # -------- Saudi Local (unmarried/married) --------
            elif rec.candidate_type == "saudi_local" and rec.marital_status == "unmarried":
                rec.gosi = float_round((rec.basic + rec.housing) * 0.12, 2)
                rec.gosi_share = float_round((rec.basic + rec.housing) * 0.10, 2)
                rec.iqama_fees = 0
                rec.flint_fee = 0
                rec.iqama_transfer_fees = 0
                if not rec.is_saved:
                    rec.hire_right_process = float_round(float(ICP('era_recruitment_opportunity.hire_right_process') or 0.0) / 12, 2)
                elif not rec.hire_right_process:
                    rec.hire_right_process = 0
                rec.saudi_eng_council = 0
                rec.employee_visa = 0
                rec.employee_visa_endorsement = 0
                if rec.invoice_period and rec.net_monthly_salary:
                    rec.profile_fees = float_round((rec.net_monthly_salary / 12), 2)

            elif rec.candidate_type == "saudi_local" and rec.marital_status == "married":
                rec.iqama_fees = 0
                rec.iqama_transfer_fees = 0
                if not rec.is_saved:
                    rec.hire_right_process = float_round(float(ICP('era_recruitment_opportunity.hire_right_process') or 0.0) / 12, 2)
                elif not rec.hire_right_process:
                    rec.hire_right_process = 0
                rec.saudi_eng_council = 0
                rec.employee_visa = 0
                rec.employee_visa_endorsement = 0
                rec.gosi = float_round((rec.basic + rec.housing) * 0.12, 2)
                rec.gosi_share = float_round((rec.basic + rec.housing) * 0.10, 2)
                if rec.invoice_period and rec.net_monthly_salary:
                    rec.profile_fees = float_round((rec.net_monthly_salary / 12), 2)
                rec.flint_fee = 0
                if not rec.is_saved:
                    rec.misc = float_round(float(ICP('era_recruitment_opportunity.misc') or 0.0), 2)
                elif not rec.misc:
                    rec.misc = 0

            # -------- Else (catch-all) --------
            else:
                rec.iqama_fees = 0
                rec.iqama_transfer_fees = 0
                if not rec.is_saved:
                    rec.hire_right_process = float_round(float(ICP('era_recruitment_opportunity.hire_right_process') or 0.0) / 12, 2)
                elif not rec.hire_right_process:
                    rec.hire_right_process = 0
                rec.saudi_eng_council = 0
                rec.employee_visa = 0
                if rec.candidate_type != "remote":
                    rec.employee_visa_endorsement = 0
                rec.gosi = float_round((rec.basic + rec.housing) * 0.12, 2)
                rec.gosi_share = float_round((rec.basic + rec.housing) * 0.10, 2)
                if rec.invoice_period and rec.net_monthly_salary:
                    rec.profile_fees = float_round((rec.net_monthly_salary / 12), 2)
                if not rec.is_saved:
                    rec.flint_fee = float_round(float(ICP('era_recruitment_opportunity.flint_fee') or 0.0) / 12, 2)
                elif not rec.flint_fee:
                    rec.flint_fee = 0

    @api.depends('candidate_class', 'number_of_kids', 'number_of_spouses', 'marital_status', 'candidate_type')
    def _compute_monthly_health_insurance(self):
        """
        Compute monthly health insurance values based on candidate_class, family members and marital status.
        Uses config parameters:
         - era_recruitment_opportunity.health_insurance_<suffix>
         - era_recruitment_opportunity.kids_health_insurance_<suffix>
         - era_recruitment_opportunity.spouse_health_insurance_<suffix>
        where suffix in: a, a_plus, b, b_plus, c, c_plus
        """
        ICP = self.env['ir.config_parameter'].sudo().get_param
        suffix_map = {
            'class_a': 'a',
            'class_a_plus': 'a_plus',
            'class_b': 'b',
            'class_b_plus': 'b_plus',
            'class_c': 'c',
            'class_c_plus': 'c_plus',
        }

        for rec in self:
            # default values
            insurance_value = 0.0
            kids_insurance_value = 0.0
            spouse_insurance_value = 0.0

            # remote candidates have no health insurance contribution
            if rec.candidate_type == 'remote':
                rec.employee_health = 0.0
                rec.spouse_health_insurance = 0.0
                rec.kids_health_insurance = 0.0
                rec.family_health_insurance = 0.0
                continue

            suffix = suffix_map.get(rec.candidate_class)
            if suffix:
                # safe param reading with fallback 0.0
                try:
                    insurance_value = float(ICP(f'era_recruitment_opportunity.health_insurance_{suffix}') or 0.0)
                except Exception:
                    insurance_value = 0.0
                try:
                    kids_insurance_value = float(ICP(f'era_recruitment_opportunity.kids_health_insurance_{suffix}') or 0.0)
                except Exception:
                    kids_insurance_value = 0.0
                try:
                    spouse_insurance_value = float(ICP(f'era_recruitment_opportunity.spouse_health_insurance_{suffix}') or 0.0)
                except Exception:
                    spouse_insurancesaudi_eng_council_value = 0.0

            # If unmarried => no family health
            if rec.marital_status == "unmarried":
                rec.family_health_insurance = 0.0
                # ensure spouse/kids zeroed
                rec.spouse_health_insurance = 0.0
                rec.kids_health_insurance = 0.0
            else:
                # compute family health insurance monthly (divide annual values by 12)
                rec.spouse_health_insurance = float_round(spouse_insurance_value, precision_digits=2) if spouse_insurance_value else 0.0
                rec.kids_health_insurance = float_round(kids_insurance_value, precision_digits=2) if kids_insurance_value else 0.0
                # family_health_insurance is based on number of spouses/kids and monthly basis
                rec.family_health_insurance = float_round(((spouse_insurance_value * rec.number_of_spouses + (kids_insurance_value * rec.number_of_kids)) / 12.0) if (spouse_insurance_value or kids_insurance_value) else 0.0, precision_digits=2)

            # employee health monthly (assumes configured value is annual, same pattern as original)
            # Original code divided insurance_value by 12
            if not rec.is_saved:
                rec.employee_health = float_round((insurance_value / 12.0) if insurance_value else 0.0, precision_digits=2)
            else:
                # if not draft and empty, keep 0
                rec.employee_health = rec.employee_health or 0.0

    # @api.depends('candidate_class', 'number_of_kids', 'number_of_spouses', 'marital_status')
    # def _compute_monthly_health_insurance(self):
    #     for rec in self:
    #         insurance_value = 0
    #         kids_insurance_value = 0
    #         spouse_insurance_value = 0
    #         if rec.candidate_class == 'class_a':
    #             insurance_value = float(self.env['ir.config_parameter'].sudo().get_param(
    #                 'era_recruitment_opportunity.health_insurance_a'))
    #             kids_insurance_value = float(self.env['ir.config_parameter'].sudo().get_param(
    #                 'era_recruitment_opportunity.kids_health_insurance_a'))
    #             spouse_insurance_value = float(self.env['ir.config_parameter'].sudo().get_param(
    #                 'era_recruitment_opportunity.spouse_health_insurance_a'))

    #         if rec.candidate_class == 'class_a_plus':
    #             insurance_value = float(self.env['ir.config_parameter'].sudo().get_param(
    #                 'era_recruitment_opportunity.health_insurance_a_plus'))
    #             kids_insurance_value = float(self.env['ir.config_parameter'].sudo().get_param(
    #                 'era_recruitment_opportunity.kids_health_insurance_a_plus'))
    #             spouse_insurance_value = float(self.env['ir.config_parameter'].sudo().get_param(
    #                 'era_recruitment_opportunity.spousehealth_insurance_a_plus'))

    #         if rec.candidate_class == 'class_b':
    #             insurance_value = float(self.env['ir.config_parameter'].sudo().get_param(
    #                 'era_recruitment_opportunity.health_insurance_b'))
    #             kids_insurance_value = float(self.env['ir.config_parameter'].sudo().get_param(
    #                 'era_recruitment_opportunity.kids_health_insurance_b'))
    #             spouse_insurance_value = float(self.env['ir.config_parameter'].sudo().get_param(
    #                 'era_recruitment_opportunity.spouse_health_insurance_b'))

    #         if rec.candidate_class == 'class_b_plus':
    #             insurance_value = float(self.env['ir.config_parameter'].sudo().get_param(
    #                 'era_recruitment_opportunity.health_insurance_b_plus'))
    #             kids_insurance_value = float(self.env['ir.config_parameter'].sudo().get_param(
    #                 'era_recruitment_opportunity.kids_health_insurance_b_plus'))
    #             spouse_insurance_value = float(self.env['ir.config_parameter'].sudo().get_param(
    #                 'era_recruitment_opportunity.spouse_health_insurance_b_plus'))

    #         if rec.candidate_class == 'class_c':
    #             insurance_value = float(self.env['ir.config_parameter'].sudo().get_param(
    #                 'era_recruitment_opportunity.health_insurance_c'))
    #             kids_insurance_value = float(self.env['ir.config_parameter'].sudo().get_param(
    #                 'era_recruitment_opportunity.kids_health_insurance_c'))
    #             spouse_insurance_value = float(self.env['ir.config_parameter'].sudo().get_param(
    #                 'era_recruitment_opportunity.spouse_health_insurance_c'))

    #         if rec.candidate_class == 'class_c_plus':
    #             insurance_value = float(self.env['ir.config_parameter'].sudo().get_param(
    #                 'era_recruitment_opportunity.health_insurance_c_plus'))
    #             kids_insurance_value = float(self.env['ir.config_parameter'].sudo().get_param(
    #                 'era_recruitment_opportunity.health_insurance_c_plus'))
    #             spouse_insurance_value = float(self.env['ir.config_parameter'].sudo().get_param(
    #                 'era_recruitment_opportunity.health_insurance_c_plus'))

    #         if rec.marital_status == "unmarried":
    #             rec.family_health_insurance = 0
    #         if rec.candidate_type == 'remote':
    #             rec.employee_health = 0.0
    #             rec.spouse_health_insurance = 0.0
    #             rec.kids_health_insurance = 0.0
    #             rec.family_health_insurance = 0.0
    #         else:
    #             if rec.state == 'draft':
    #                 rec.family_health_insurance = float_round(((spouse_insurance_value * rec.number_of_spouses + (
    #                             kids_insurance_value * rec.number_of_kids)) / 12), precision_digits=2)
    #             elif not rec.family_health_insurance:
    #                 rec.family_health_insurance = 0.0

    #         if rec.show_cost_case2:
    #             insurance_value = 5000
    #         if rec.state == 'draft':
    #             rec.employee_health = insurance_value / 12
    #         elif not rec.employee_health:
    #             rec.employee_health = 0

    @api.depends("total_monthly_cost")
    def _compute_yearly_cost(self):
        for rec in self:
            rec.yearly_employee_cost = float_round(
                rec.total_monthly_cost * rec.invoice_period, precision_digits=2)

    @api.onchange("package")
    def _onchange_package(self):
        # if self.package:
        self.basic = float_round(self.package * 0.65, precision_digits=2)
        self.housing = float_round(self.package * 0.25, precision_digits=2)
        self.transportation = float_round(self.package * 0.10, precision_digits=2)
        # if self.candidate_type == "no_saudi":
        #     self.employee_health = float_round(6000 / 12, precision_digits=2)
        #     self.spouse_health_insurance = float_round(
        #         10000 / 12, precision_digits=2
        #     )
        #     self.kids_health_insurance = float_round(
        #         (6000 * 2) / 12, precision_digits=2)

    @api.onchange('candidate_type')
    def _onchange_candidate_type(self):
        for rec in self:
            for field_name in ['gosi', 'saudization', 'iqama_fees', 'iqama_transfer_fees', 'mobilization_cost',
                               'ajeer', 'housing', 'transportation', 'basic', 'profile_fees', 'package',
                               'vac_salary',
                               'end_of_service', 'employee_annual_flight_ticket', 'wife_annual_flight_ticket',
                               'child_flight_ticket', 'employee_health', 'spouse_health_insurance',
                               'kids_health_insurance', 'exit_reentry', 'invoice_period', 'total_monthly_cost',
                               'yearly_employee_cost', 'flint_fee']:
                rec[field_name] = 0.0
