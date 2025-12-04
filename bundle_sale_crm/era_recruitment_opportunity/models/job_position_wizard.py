# -*- coding: utf-8 -*-

from odoo import fields, models, api
import ast


class jobPositionWizard(models.TransientModel):
    _name = "job.position.wizard"
    _inherit = ["mail.alias.mixin", "mail.thread"]
    _description = " Create Job Position"

    def _alias_get_creation_values(self):
        values = super(jobPositionWizard, self)._alias_get_creation_values()
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

    name = fields.Char()
    # change field type by shailesh
    recruitment_process = fields.Selection([
        ('full_recruitment', 'Full Recruitment'),
        ('direct_recruitment', 'Direct Recruitment')], required=True)
    lead_id = fields.Many2one('crm.lead')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    address_id = fields.Many2one(
        'res.partner', "Job Location", default=_default_address_id,
        domain=lambda self: self._address_id_domain(),
        help="Select the location where the applicant will work. Addresses listed here are defined on the company's contact information.")
    department_id = fields.Many2one('hr.department', string='Department', check_company=True)
    alias_id = fields.Many2one(
        help="Email alias for this job position. New emails will automatically create new applicants for this job position.")
    contract_type_id = fields.Many2one('hr.contract.type', string='Employment Type', required=True)
    no_of_recruitment = fields.Integer(string='Target', copy=False,
                                       help='Number of new employees you expect to recruit.', default=1)
    interviewer_ids = fields.Many2many('res.users', string='Interviewers',
                                       domain="[('share', '=', False), ('company_ids', 'in', company_id)]",
                                       help="The Interviewers set on the job position can see all Applicants in it. They have access to the information, the attachments, the meeting management and they can refuse him. You don't need to have Recruitment rights to be set as an interviewer.")
    user_id = fields.Many2one('res.users', "Recruiter",
                              domain="[('share', '=', False), ('company_ids', 'in', company_id)]", tracking=True,
                              help="The Recruiter will be the default value for all Applicants Recruiter's field in this job position. The Recruiter is automatically added to all meetings with the Applicant.")
    # only change in string parameter by shailesh
    description = fields.Html(string='Detailed Job Description', sanitize_attributes=False,
                              default="Perform assigned responsibilities, collaborate with team members, and adhere to company policies. Strong communication, problem-solving, and work ethic required. Adaptability, initiative, and willingness to learn are valued.")
    # add below fields by shailesh
    client_name = fields.Many2one("res.partner", related='lead_id.partner_id', string='Client / Project Name')
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
    job_location = fields.Char(string='Job Location', required=True)
    onsite_remote = fields.Selection([
        ('onsite', 'Onsite'),
        ('remote', 'Remote')], string='Onsite / Remote', required=True)
    permanent_contract = fields.Selection([
        ('permanent', 'Permanent Role'),
        ('contract', 'Contract through Flint')], string='Permanent Role / Contract through Flint', required=True)
    bidding_stage = fields.Selection([
        ('bidding', 'Bidding Stage'),
        ('live', 'Live Requirement')], string='Bidding Stage or Live Requirement', required=True)
    # fields for applicant information by shailesh.

    applicant_name = fields.Char(string='Applicant Name')
    applicant_email = fields.Char(string='Email')
    applicant_phone = fields.Char(string='Contact #')
    applicant_nationality = fields.Char(string='Nationality')
    applicant_current_location = fields.Char(string='Current Location')
    applicant_experience = fields.Char(string='Experience')
    applicant_qualification = fields.Char(string='Qualification')
    applicant_current_company = fields.Char(string='Current Company')
    applicant_position = fields.Char(string='Position')
    applicant_notice_period = fields.Char(string='Notice Period')
    applicant_salary_expectation = fields.Float(string='Salary Expected in SAR per month (Including Gosi if Saudi)')
    applicant_dependent = fields.Char(string='Dependents (Wife + Kids)')
    applicant_profession = fields.Char(string='Profession on iqama')
    applicant_number_iqama = fields.Char(string='Number of Iqama Transfers')
    applicant_current_salary = fields.Float(string='Current Salary')
    applicant_resume = fields.Binary(string='Resume')
    job_description = fields.Html(string='Job Description', translate=True, required=True)

    def action_create_job(self):
        recruitment_order = self.env['recruitment.order']
        for rec in self:
            if rec.recruitment_process == 'direct_recruitment':
                vals = {
                    'name': rec.name,
                    'description': rec.description,
                    'partner_name': rec.applicant_name,
                    'email_from': rec.applicant_email,
                    'partner_phone': rec.applicant_phone,
                    'interviewer_ids': rec.interviewer_ids.ids if rec.interviewer_ids else False,
                    'user_id': rec.user_id.id if rec.user_id else False,
                    'job_id': rec.lead_id.job_id.id,
                    'department_id': rec.department_id.id if rec.department_id else False,
                    'salary_expected': rec.applicant_salary_expectation,
                    'salary_proposed': rec.lead_id.net_monthly_salary,
                    'nationality': rec.applicant_nationality,
                    'current_location': rec.applicant_current_location,
                    'experience': rec.applicant_experience,
                    'qualification': rec.applicant_qualification,
                    'current_company': rec.applicant_current_company,
                    'position': rec.applicant_position,
                    'notice_period': rec.applicant_notice_period,
                    'dependent': rec.applicant_dependent,
                    'profession': rec.applicant_profession,
                    'number_iqama': rec.applicant_number_iqama,
                    'current_salary': rec.applicant_current_salary,
                    'partner_id': rec.client_name.id,
                    'lead_id': rec.lead_id.id,
                    # 'recruitment_order_id': rec.recruitment_order_id.id,
                    'resume': rec.applicant_resume,
                    'is_direct_hiring': True,
                    'job_description': rec.job_description
                }
                return self.env['hr.applicant'].sudo().create(vals)
            else:
                values = {
                    'name': rec.name,
                    'lead_id': rec.lead_id.id if rec.lead_id else False,
                    'active': rec.active,
                    'description': rec.description,
                    'client_name': rec.client_name.id,
                    'position_title': rec.position_title,
                    'experience_level': rec.experience_level,
                    'preferred_industry': rec.preferred_industry,
                    'nationality_requirement': rec.nationality_requirement,
                    'salary_range': rec.salary_range,
                    'job_location': rec.job_location,
                    'onsite_remote': rec.onsite_remote,
                    'permanent_contract': rec.permanent_contract,
                    'bidding_stage': rec.bidding_stage,
                    # For Below fields needs to discussed with muneeb.
                    'company_id': rec.company_id.id if rec.company_id else False,
                    'address_id': rec.address_id.id if rec.address_id else False,
                    'department_id': rec.department_id.id if rec.department_id else False,
                    'alias_id': rec.alias_id.id if rec.alias_id else False,
                    'contract_type_id': rec.contract_type_id.id if rec.contract_type_id else False,
                    'no_of_recruitment': rec.no_of_recruitment,
                    'interviewer_ids': rec.interviewer_ids.ids if rec.interviewer_ids else False,
                    'user_id': rec.user_id.id if rec.user_id else False,
                    'recruitment_process': rec.recruitment_process,
                    'job_description': rec.job_description
                }
                recruitment_order.create(values)
