# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.tools.float_utils import float_round
from odoo.tools import clean_context



class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

    nationality = fields.Char(string='Nationality')
    current_location = fields.Char(string='Current Location')
    experience = fields.Char(string='Experience')
    qualification = fields.Char(string='Qualification')
    current_company = fields.Char(string='Current Company')
    position = fields.Char(string='Position')
    notice_period = fields.Char(string='Notice Period')
    dependent = fields.Char(string='Dependents (Wife + Kids)')
    profession = fields.Char(string='Profession on iqama')
    number_iqama = fields.Char(string='Number of Iqama Transfers')
    current_salary = fields.Float(string='Current Salary')
    resume = fields.Binary(string='Resume')
    recruitment_order_id = fields.Many2one('recruitment.order', string='Recruitment Order')
    recruitment_order_count = fields.Integer(string='Recruitment Order', compute='_compute_recruitment_order_count')
    lead_id = fields.Many2one("crm.lead")
    is_direct_hiring = fields.Boolean(string="Direct Hiring")
    available_stage_ids = fields.Many2many(
        'hr.recruitment.stage',
        compute='_compute_available_stages'
    )
    stage_id = fields.Many2one('hr.recruitment.stage', 'Stage', ondelete='restrict', tracking=True,
                               compute='_compute_stage', store=True, readonly=False,
                               domain="['|', ('job_ids', '=', False), ('job_ids', '=', job_id),"
                                      "('id', 'in', available_stage_ids)]",
                               copy=False, index=True,
                               group_expand='_read_group_stage_ids')


    @api.depends('job_id', 'is_direct_hiring')
    def _compute_stage(self):
        for applicant in self:
            if applicant.is_direct_hiring:
                # Only allow "Contract Proposal" and "Contract Signed"
                stage_ids = self.env['hr.recruitment.stage'].search([
                    ('name', 'in', ['Contract Proposal', 'Contract Signed'])
                ], order='sequence asc', limit=1).ids
                applicant.stage_id = stage_ids[0] if stage_ids else False
            elif applicant.job_id:
                if not applicant.stage_id:
                    stage_ids = self.env['hr.recruitment.stage'].search([
                        '|',
                        ('job_ids', '=', False),
                        ('job_ids', '=', applicant.job_id.id),
                        ('fold', '=', False)
                    ], order='sequence asc', limit=1).ids
                    applicant.stage_id = stage_ids[0] if stage_ids else False
            else:
                applicant.stage_id = False

    @api.depends('is_direct_hiring')
    def _compute_available_stages(self):
        for rec in self:
            if rec.is_direct_hiring:
                rec.available_stage_ids = self.env['hr.recruitment.stage'].search([
                    ('name', 'in', ['Contract Proposal', 'Contract Signed'])
                ])
            else:
                rec.available_stage_ids = self.env['hr.recruitment.stage'].search([])


    def _compute_recruitment_order_count(self):
        for rec in self:
            rec.recruitment_order_count = self.env['recruitment.order'].search_count([('id', '=', rec.recruitment_order_id.id)])

    def action_open_recruitment(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Recruitment Orders'),
            'res_model': 'recruitment.order',
            'view_mode': 'form',
            'target': 'current',
            'views': [[False, 'form']],
            'res_id': self.recruitment_order_id.id,
        }

    # def write(self, vals):
    #     if 'stage_id' in vals:
    #         hired_stage = self.env['hr.recruitment.stage'].search([('hired_stage', '=', True)], limit=1)
    #         if vals.get('stage_id') == hired_stage.id and self.recruitment_order_id or self.lead_id:
    #             sale = self.create_sale_order()
    #             if sale:
    #                 self.create_cost_analysis(sale)
    #         if not self.recruitment_order_id.state == 'done':
    #             self.recruitment_order_id.action_done()
    #     contract_proposal = self.env['hr.recruitment.stage'].search([('name', '=', 'Contract Proposal')], limit=1)
    #     if 'stage_id' in vals and vals.get('stage_id') == contract_proposal.id and (self.recruitment_order_id or self.lead_id):
    #         self.action_send_proposal()
    #     return super(HrApplicant, self).write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        contract_proposal = self.env['hr.recruitment.stage'].search([('name', '=', 'Contract Proposal')], limit=1)
        applicant = super(HrApplicant, self).create(vals_list)
        for rec in applicant:
            if rec.stage_id.id == contract_proposal.id and rec.lead_id:
                rec.action_send_proposal()
        return applicant

    # def _get_employee_create_vals_with_partner(self, partner_id):
    #     self.ensure_one()
    #     address_id = partner_id.id
    #     address_sudo = self.env['res.partner'].sudo().browse(address_id)
    #     return {
    #         'name': self.partner_name or self.partner_id.display_name,
    #         'work_contact_id': self.partner_id.id,
    #         'job_id': self.job_id.id,
    #         'job_title': self.job_id.name,
    #         'private_street': address_sudo.street,
    #         'private_street2': address_sudo.street2,
    #         'private_city': address_sudo.city,
    #         'private_state_id': address_sudo.state_id.id,
    #         'private_zip': address_sudo.zip,
    #         'private_country_id': address_sudo.country_id.id,
    #         'private_phone': address_sudo.phone,
    #         'private_email': address_sudo.email,
    #         'lang': address_sudo.lang,
    #         'department_id': self.department_id.id,
    #         'address_id': self.company_id.partner_id.id,
    #         'work_email': self.department_id.company_id.email or self.email_from, # To have a valid email address by default
    #         'work_phone': self.department_id.company_id.phone,
    #         'applicant_id': self.ids,
    #         'private_phone': self.partner_phone or self.partner_mobile
    #     }

    # def write(self, vals):
    #     if 'stage_id' in vals:
    #         hired_stage = self.env['hr.recruitment.stage'].search([('hired_stage', '=', True)], limit=1)
    #         if vals.get('stage_id') == hired_stage.id and self.recruitment_order_id or self.lead_id:
                
    #             if self.email_from:
    #                 employee_ids = self.env['hr.employee'].sudo().search(
    #                     ['|', ('active', '=', True), ('active', '=', False),
    #                      ('work_email', '!=', False),
    #                      ('work_email', '=', self.email_from)])
    #                 if not employee_ids:
    #                     if not self.partner_name:
    #                         raise UserError(_('Please provide an applicant name.'))
    #                     new_partner = self.env['res.partner'].with_context(clean_context(self.env.context)).create({
    #                         'is_company': False,
    #                         'name': self.partner_name,
    #                         'email': self.email_from,
    #                     })
    #                     employee = self.env['hr.employee'].with_context(clean_context(self.env.context)).create(self._get_employee_create_vals_with_partner(new_partner))
    #     res = super(HrApplicant, self).write(vals)
    #     return res

    def _get_employee_create_vals_with_partner(self, partner):
        """Return employee vals using the provided partner record (partner must be a record)."""
        self.ensure_one()
        partner = partner if hasattr(partner, 'id') else self.env['res.partner'].browse(partner)
        address_id = partner.id
        address_sudo = self.env['res.partner'].sudo().browse(address_id)
        return {
            # Force applicant name (prefer applicant partner_name)
            'name': self.partner_name or partner.display_name or self.name,
            # link to the partner we just created/passed
            'work_contact_id': partner.id,
            'job_id': self.job_id.id,
            'job_title': (self.job_id.name or False),
            'private_street': address_sudo.street,
            'private_street2': address_sudo.street2,
            'private_city': address_sudo.city,
            'private_state_id': address_sudo.state_id.id,
            'private_zip': address_sudo.zip,
            'private_country_id': address_sudo.country_id.id,
            'private_phone': address_sudo.phone,
            'private_email': address_sudo.email,
            'lang': address_sudo.lang,
            'department_id': self.department_id.id,
            'address_id': (self.company_id.partner_id.id if self.company_id and self.company_id.partner_id else False),
            # IMPORTANT: prefer applicant email first to avoid using company email that may conflict
            'work_email': (partner.email or self.email_from) or False,
            'work_phone': (self.department_id.company_id.phone if self.department_id and self.department_id.company_id else False),
            'applicant_id': self.ids,
            'private_phone': self.partner_phone or self.partner_mobile
        }

    def write(self, vals):
        """
        Safe write: when moving to hired/contract-signed, create/link employee safely:
        - Create partner first (if needed), create employee with partner as contact,
        - Force employee work_email = applicant email (if exists),
        - Set vals['emp_id'] and call super() once.
        """
        # find hired stage (use hired_stage boolean or specific stage name if you prefer)
        hired_stage = self.env['hr.recruitment.stage'].search([('hired_stage', '=', True)], limit=1)
        contract_signed_stage = self.env['hr.recruitment.stage'].search([('name', '=', 'Contract Signed')], limit=1)
        # decide trigger (either hired_stage flag or explicit "Contract Signed")
        trigger_stage_id = contract_signed_stage.id if contract_signed_stage else (hired_stage.id if hired_stage else False)

        # If stage going to trigger and applicant is linked to recruitment/lead
        if 'stage_id' in vals and vals.get('stage_id') == trigger_stage_id and (self.recruitment_order_id or self.lead_id):
            # Only act when no emp_id yet
            if not self.emp_id:
                applicant_name = (self.partner_name or self.name or "").strip()
                applicant_email = (self.email_from or "").strip()

                # First check if an employee exists with same email
                existing_emp = False
                if applicant_email:
                    existing_emp = self.env['hr.employee'].sudo().search([('work_email', '=', applicant_email)], limit=1)

                if existing_emp:
                    # If name matches, safe to link; otherwise raise to avoid wrong mapping
                    if existing_emp.name and existing_emp.name.strip().lower() == applicant_name.lower():
                        vals['emp_id'] = existing_emp.id
                    else:
                        raise ValidationError(_("An employee with email %s already exists (%s). Resolve this before hiring.") % (applicant_email, existing_emp.name))
                else:
                    # create partner first (use applicant name + email)
                    if not self.partner_id:
                        if not self.partner_name:
                            raise UserError(_('Please provide an applicant name.'))
                        new_partner = self.env['res.partner'].with_context(clean_context(self.env.context)).create({
                            'is_company': False,
                            'name': self.partner_name,
                            'email': self.email_from or False,
                        })
                    else:
                        # use existing partner but ensure email preference
                        # optionally update partner email if missing
                        if self.partner_id and not self.partner_id.email and self.email_from:
                            self.partner_id.sudo().write({'email': self.email_from})
                        new_partner = self.partner_id

                    # Build employee vals from partner and force correct fields
                    employee_vals = self._get_employee_create_vals_with_partner(new_partner)
                    # ensure employee name forced to applicant
                    employee_vals['name'] = applicant_name or employee_vals.get('name')
                    # ensure work_email set to applicant email if present
                    if applicant_email:
                        employee_vals['work_email'] = applicant_email

                    # create employee with sudo & proper context
                    employee = self.env['hr.employee'].sudo().with_context(create_employee=True).create(employee_vals)
                    # set emp_id into vals (so super write handles linking & update)
                    vals['emp_id'] = employee.id

        # Keep contract proposal behavior (if needed)
        contract_proposal = self.env['hr.recruitment.stage'].search([('name', '=', 'Contract Proposal')], limit=1)
        if 'stage_id' in vals and vals.get('stage_id') == (contract_proposal.id if contract_proposal else False) and (self.recruitment_order_id or self.lead_id):
            self.action_send_proposal()

        # Finally call super once
        return super(HrApplicant, self).write(vals)




    # def write(self, vals):
    #     if 'stage_id' in vals:
    #         hired_stage = self.env['hr.recruitment.stage'].search([('hired_stage', '=', True)], limit=1)
    #         if vals.get('stage_id') == hired_stage.id and self.recruitment_order_id or self.lead_id:
    #             sale = self.with_context(create_employee=True).create_employee_from_applicant()
    #         #     if sale:
    #         #         self.create_cost_analysis(sale)
    #         # if not self.recruitment_order_id.state == 'done':
    #         #     self.recruitment_order_id.action_done()
    #     contract_proposal = self.env['hr.recruitment.stage'].search([('name', '=', 'Contract Proposal')], limit=1)
    #     if 'stage_id' in vals and vals.get('stage_id') == contract_proposal.id and (self.recruitment_order_id or self.lead_id):
    #         self.action_send_proposal()
    #     return super(HrApplicant, self).write(vals)

    # @api.model_create_multi
    # def create(self, vals_list):
    #     contract_proposal = self.env['hr.recruitment.stage'].search([('name', '=', 'Contract Proposal')], limit=1)
    #     applicant = super(HrApplicant, self).create(vals_list)
    #     for rec in applicant:
    #         if rec.stage_id.id == contract_proposal.id and rec.lead_id:
    #             rec.action_send_proposal()
    #     return applicant

    def action_send_proposal(self):
        template = self.env.ref('era_recruitment_opportunity.email_template_data_applicant_send_proposal')
        email_values = {}
        if template:
            email_values['email_to'] = self.email_from
            email_values['recipient_ids'] = []
            template.send_mail(self.id, force_send=True, email_values=email_values)

    def create_sale_order(self):
        sale_order = self.env['sale.order']
        recruitement_service_product = self.env.ref('era_recruitment_opportunity.recruitment_service_product')
        for rec in self:
            values = {
                'partner_id': rec.partner_id.id,
                'applicant_name': rec.partner_name,
                'applicant_email': rec.email_from,
                'applicant_phone': rec.partner_phone,
                'applicant_nationality': rec.nationality,
                'applicant_current_location': rec.current_location,
                'applicant_experience': rec.experience,
                'applicant_qualification': rec.qualification,
                'applicant_current_company': rec.current_company,
                'applicant_position': rec.position,
                'applicant_notice_period': rec.notice_period,
                'applicant_dependent': rec.dependent,
                'applicant_profession': rec.profession,
                'applicant_number_iqama': rec.number_iqama,
                'applicant_current_salary': rec.current_salary,
                'applicant_resume': rec.resume,
                'applicant_salary_expectation': rec.salary_expected,
                'is_create_from_applicant': True,
                'hr_applicant_id': rec.id,
                'opportunity_id': rec.recruitment_order_id.lead_id.id if rec.recruitment_order_id else rec.lead_id.id,
                'campaign_id': rec.recruitment_order_id.lead_id.campaign_id.id if rec.recruitment_order_id else rec.lead_id.campaign_id.id,
                'medium_id': rec.recruitment_order_id.lead_id.medium_id.id if rec.recruitment_order_id else rec.lead_id.medium_id.id,
                'origin': rec.recruitment_order_id.lead_id.name if rec.recruitment_order_id else rec.lead_id.name,
                'source_id': rec.recruitment_order_id.lead_id.source_id.id if rec.recruitment_order_id else rec.lead_id.source_id.id,
                'company_id': rec.recruitment_order_id.lead_id.company_id.id or self.env.company.id if rec.recruitment_order_id else rec.lead_id.company_id.id or self.env.company.id,
                'tag_ids': [(6, 0, rec.recruitment_order_id.lead_id.tag_ids.ids if rec.recruitment_order_id else rec.lead_id.tag_ids.ids)],
                'order_line': [
                    (0, 0, {
                        'name': recruitement_service_product.name,
                        'product_id': recruitement_service_product.id,
                        'product_uom_qty': 1.0,
                        'product_uom': recruitement_service_product.uom_id.id,
                    })],
            }
            return sale_order.create(values)


    def create_cost_analysis(self, sale_order):
        cost_analysis = self.env['sale.order.service.line']
        saudi_id = self.env['res.country'].search([('name', '=', 'Saudi Arabia')], limit=1)
        for rec in self:
            # here some of the fields required to be added in the cost analysis so i added some dummy values like 1.0
            values = {
                'order_line_id' : sale_order.order_line[0].id,
                'package': rec.salary_proposed,
                'basic': float_round(rec.salary_proposed * 0.65, precision_digits=2),
                'housing': float_round(rec.salary_proposed * 0.25, precision_digits=2),
                'transportation': float_round(rec.salary_proposed * 0.10, precision_digits=2),
                'candidate_type': 'saudi_local',
                'contract_type': 'permanent',
                'gosi': 1.0,
                'hr_job_id': rec.job_id.id,
                'invoice_period': 12.0,
                'iqama_fees': 1.0,
                'iqama_transfer_fees': 1.0,
                'marital': 'single',
                'mobilization_cost': 1.0,
                'name': rec.partner_name,
                'partner_id': rec.recruitment_order_id.client_name.id if rec.recruitment_order_id else rec.lead_id.partner_id.id,
                'nationality_id': saudi_id.id,
                'net_monthly_salary': rec.salary_proposed,
                'total_monthly_cost': rec.salary_proposed,
                'yearly_employee_cost': rec.salary_proposed,
                'end_of_service': 1.0,
                'saudization': 1.0,
                'vac_salary': 1.0,
                'employee_annual_flight_ticket': 1.0,
                'wife_annual_flight_ticket': 1.0,
                'child_flight_ticket': 1.0,
                'employee_health': 1.0,
                'spouse_health_insurance': 1.0,
                'kids_health_insurance': 1.0,
            }
            return cost_analysis.create(values)