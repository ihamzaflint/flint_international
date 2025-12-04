# -*- coding: utf-8 -*-
import re
from odoo import fields, models, api, _
from odoo.tools.float_utils import float_round
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    job_ids = fields.Many2many('recruitment.order', compute="_compute_job_count")
    job_ids_count = fields.Integer(string="Jobs", compute="_compute_job_count")
    job_id = fields.Many2many('hr.job', string="Job")
    crm_recruitment_count = fields.Integer(string="Total Recruitment", compute="_compute_crm_recruitment_count")
    job_desc = fields.Html(string='Job Description', translate=True, compute="_compute_job_desc")
    # jobs_id = fields.Many2many('hr.job', string="Job")
    # # cost analysis fields
    # basic = fields.Float('Basic Salary')
    # housing = fields.Float()
    # transportation = fields.Float('Transportation')
    # vac_salary = fields.Float("Vac Salary 12 months PO", required=True)
    # end_of_service = fields.Float()
    # employee_health = fields.Float("Employee Health Insurance (Categories)")
    # spouse_health_insurance = fields.Float("Spouse Health Insurance")
    # kids_health_insurance = fields.Float("Kids  Health Insurance")
    # employee_annual_flight_ticket = fields.Float()
    # wife_annual_flight_ticket = fields.Float()
    # child_flight_ticket = fields.Float("Child Annual Flight Ticket")
    # gosi = fields.Float(required=True)
    # saudization = fields.Float(required=True)
    # iqama_fees = fields.Float(required=True)
    # iqama_transfer_fees = fields.Float(required=True)
    # mobilization_cost = fields.Float(required=True)
    # ajeer = fields.Float()
    # exit_reentry = fields.Float()
    # profile_fees = fields.Float("Profile Fees (One-time)")
    # candidate_type = fields.Selection(
    #     [("saudi_local", "Saudi Local"), ("no_saudi", "Non-Saudi")],
    #     required=True,
    #     default="saudi_local",
    # )
    # package = fields.Float()
    # invoice_period = fields.Float("Invoice Period (No. of months)", required=True)
    # total_monthly_cost = fields.Float(
    #     compute="_compute_total_monthly_cost",
    #     store=True,
    # )
    # net_monthly_salary = fields.Float(string='Net Salary', compute="_compute_net_monthly", store=True)
    # yearly_employee_cost = fields.Float(
    #     compute="_compute_yearly_cost",
    #     store=True,
    # )
    # Validation fields
    is_create_job = fields.Boolean(string="Create Job", default=False)
    applicant_ids_count = fields.Integer(string="Applicants", compute="_compute_applicant_count")
    crm_applicant_line_ids = fields.One2many('crm.applicant.line', 'crm_lead_id')
    costing_summary_line_ids = fields.One2many(
        'crm.costing.summary.line',
        'lead_id',
        string='Costing Summary',
    )

    def _compute_job_desc(self):
        for rec in self:
            rec.job_desc = ''  # Always reset to avoid accumulation
            jobs = self.env['recruitment.order'].search([('lead_id', '=', rec.id)])

            if not jobs:
                rec.job_desc = '<p><em>No job descriptions available.</em></p>'
                continue

            descriptions = []
            for index, job in enumerate(jobs, start=1):
                title = f"Job description for {job.name}"
                desc = job.job_description or "<em>No description</em>"
                descriptions.append(f"""
                    <div style="margin-bottom: 20px;">
                        <p><strong>{title}</strong></p>
                        <div>{desc}</div>
                    </div>
                """)

            rec.job_desc = "<br>".join(descriptions)
        
    def _compute_crm_recruitment_count(self):
        for rec in self:
            jobs = self.env['recruitment.order'].search([('lead_id', '=', rec.id)])
            counter = 0
            for each_job in jobs:
                counter += each_job.recruitment_count

            rec.crm_recruitment_count = counter

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

    # @api.depends("exit_reentry", "mobilization_cost", "profile_fees", "ajeer", "iqama_transfer_fees", "iqama_fees",
    #              "saudization", "gosi", "employee_health", "spouse_health_insurance", "kids_health_insurance",
    #              "child_flight_ticket", "wife_annual_flight_ticket", "employee_annual_flight_ticket", "end_of_service",
    #              "vac_salary", "total_monthly_cost", 'invoice_period',
    #              )
    # def _compute_total_monthly_cost(self):
    #     for rec in self:
    #         if rec.candidate_type == "no_saudi":
    #             rec.total_monthly_cost = (
    #                                              rec.net_monthly_salary
    #                                              + rec.vac_salary
    #                                              + rec.end_of_service
    #                                              + rec.employee_annual_flight_ticket
    #                                              + rec.wife_annual_flight_ticket
    #                                              + rec.child_flight_ticket
    #                                              + rec.employee_health
    #                                              + rec.spouse_health_insurance
    #                                              + rec.kids_health_insurance
    #                                              + rec.gosi
    #                                              + rec.saudization
    #                                              + rec.iqama_fees
    #                                              + rec.iqama_transfer_fees
    #                                              + rec.mobilization_cost
    #                                              + rec.ajeer
    #                                              + rec.exit_reentry
    #                                      ) / rec.invoice_period if rec.invoice_period else 0
    #         else:
    #             rec.total_monthly_cost = (
    #                                              rec.net_monthly_salary
    #                                              + rec.vac_salary
    #                                              + rec.end_of_service
    #                                              + rec.employee_health
    #                                              + rec.spouse_health_insurance
    #                                              + rec.kids_health_insurance
    #                                              + rec.gosi
    #                                              + rec.employee_annual_flight_ticket
    #                                              + rec.wife_annual_flight_ticket
    #                                              + rec.child_flight_ticket
    #                                              + rec.profile_fees
    #                                      ) / rec.invoice_period if rec.invoice_period else 0

    # @api.depends('basic', 'housing', 'transportation')
    # def _compute_net_monthly(self):
    #     for rec in self:
    #         rec.net_monthly_salary = rec.basic + rec.housing + rec.transportation
    #         rec.end_of_service = (
    #                                  float_round(
    #                                      rec.net_monthly_salary and rec.net_monthly_salary / 24,
    #                                      precision_digits=2,
    #                                  )
    #                              ) or 0
    #         if rec.candidate_type == "no_saudi":
    #             rec.gosi = float_round(
    #                 ((rec.basic + rec.housing) * 0.02), precision_digits=2
    #             )
    #             rec.iqama_fees = float_round(((9700 + 650) / 12), precision_digits=2)
    #             rec.iqama_transfer_fees = 6000 / 12
    #             rec.ajeer = float_round((420 / 12), precision_digits=2)
    #             rec.exit_reentry = float_round(((200 * 4) / 12), precision_digits=2)
    #         else:
    #             rec.gosi = float_round(
    #                 ((rec.basic + rec.housing) * 0.1175), precision_digits=2
    #             )
    #             if rec.invoice_period and rec.net_monthly_salary:
    #                 rec.profile_fees = float_round(
    #                     (rec.net_monthly_salary / 12),
    #                     precision_digits=2,
    #                 )

    # @api.depends("total_monthly_cost")
    # def _compute_yearly_cost(self):
    #     for rec in self:
    #         rec.yearly_employee_cost = float_round(
    #             rec.total_monthly_cost * rec.invoice_period, precision_digits=2)

    @api.onchange("package")
    def _onchange_package(self):
        if self.package:
            self.basic = float_round(self.package * 0.65, precision_digits=2)
            self.housing = float_round(self.package * 0.25, precision_digits=2)
            self.transportation = float_round(self.package * 0.10, precision_digits=2)
            if self.candidate_type == "no_saudi":
                self.employee_health = float_round(6000 / 12, precision_digits=2)
                self.spouse_health_insurance = float_round(
                    10000 / 12, precision_digits=2
                )
                self.kids_health_insurance = float_round(
                    (6000 * 2) / 12, precision_digits=2)

    @api.onchange('candidate_type')
    def _onchange_candidate_type(self):
        for rec in self:
            for field_name in ['gosi', 'saudization', 'iqama_fees', 'iqama_transfer_fees', 'mobilization_cost',
                               'ajeer', 'housing', 'transportation', 'basic', 'profile_fees', 'package', 'vac_salary',
                               'end_of_service', 'employee_annual_flight_ticket', 'wife_annual_flight_ticket',
                               'child_flight_ticket', 'employee_health', 'spouse_health_insurance',
                               'kids_health_insurance', 'exit_reentry', 'invoice_period', 'total_monthly_cost',
                               'yearly_employee_cost']:
                rec[field_name] = 0.0

    def action_open_jobs(self):
        self.ensure_one()
        return {
            'name': _("Jobs Created from %s", self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'recruitment.order',
            'domain': [('lead_id', '=', self.id)],
            'views': [(self.env.ref('era_recruitment_opportunity.recruitment_order_tree_view').id, 'tree'),
                      (False, 'form')],

        }

    @api.model
    def _compute_job_count(self):
        for rec in self:
            rec.job_ids = False
            rec.job_ids_count = 0
            jobs = self.env['recruitment.order'].search([('lead_id', '=', rec.id)])
            if jobs:
                rec.job_ids = jobs.ids
                rec.job_ids_count = len(jobs)

    def action_create_job(self):
        if not self.partner_id:
            raise UserError(_("Please select a customer for the lead."))
        if not self.job_id:
            raise UserError(_("Please select a Job for the lead."))
        view_id = self.env.ref('era_recruitment_opportunity.job_position_wizard_form_view').id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create a Job'),
            'res_model': 'job.position.wizard',
            'target': 'new',
            'view_mode': 'form',
            'views': [[view_id, 'form']],
            'context': {'default_lead_id': self.id},
        }

    def action_import_jobs(self):
        if not self.partner_id:
            raise UserError(_("Please select a customer for the lead."))
        if not self.job_id:
            raise UserError(_("Please select a Job for the lead."))
        view_id = self.env.ref('era_recruitment_opportunity.import_job_wizard_form_view').id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Import Jobs'),
            'res_model': 'import.jobs.wizard',
            'target': 'new',
            'view_mode': 'form',
            'views': [[view_id, 'form']],
            'context': {'default_lead_id': self.id},
        }

    def button_update_crm_applicant_lines(self):
        self.ensure_one()

        recruitment_order_ids = self.job_ids

        if recruitment_order_ids:
            crm_applicant_lines = []

            # get allowed keys for candidate_type selection
            cand_type_selection = self.env['crm.applicant.line'].fields_get(['candidate_type'])['candidate_type'][
                                      'selection'] or []
            allowed_cand_types = [key for key, label in cand_type_selection]

            for order in recruitment_order_ids:
                for line in order.applicant_line.filtered(lambda l: l.state == 'confirm'):
                    # safe candidate_type (only use if it's allowed, otherwise False)
                    cand_type_value = line.candidate_type
                    if cand_type_value not in allowed_cand_types:
                        # optional: map known external values to allowed keys here
                        # e.g. if cand_type_value == 'remote': cand_type_value = 'external'
                        cand_type_value = False

                    crm_applicant_lines.append((0, 0, {
                        'recruitment_order_id': line.recruitment_order_id.id,
                        'sequence': line.sequence,
                        'name': line.name,
                        'email': line.email,
                        'phone': line.phone,
                        'nationality': line.nationality or False,
                        'current_location': line.current_location,
                        'experience': line.experience,
                        'qualification': line.qualification,
                        'current_company': line.current_company,
                        'position': line.position,
                        'notice_period': line.notice_period,
                        'salary_expectation': line.salary_expectation,
                        'show_salary_expectation': line.show_salary_expectation,
                        'wife': line.wife,
                        'show_wife': line.show_wife,
                        'show_kids': line.show_kids,
                        'kids': line.kids,
                        'profession': line.profession,
                        'number_iqama': line.number_iqama,
                        'current_salary': line.current_salary,
                        'show_current_salary': line.show_current_salary,
                        'resume': line.resume,
                        'file_name': line.file_name,
                        'state': line.state,
                        'rejection_reason': line.rejection_reason,
                        'selection_link': line.selection_link,
                        'access_token': line.access_token,
                        'rejection_date': line.rejection_date,
                        'basic': line.basic,
                        'housing': line.housing,
                        'transportation': line.transportation,
                        'vac_salary': line.vac_salary,
                        'end_of_service': line.end_of_service,
                        'employee_health': line.employee_health,
                        'spouse_health_insurance': line.spouse_health_insurance,
                        'kids_health_insurance': line.kids_health_insurance,
                        'family_health_insurance': line.family_health_insurance,
                        'employee_annual_flight_ticket': line.employee_annual_flight_ticket,
                        'employee_monthly_flight_ticket': line.employee_monthly_flight_ticket,
                        'wife_annual_flight_ticket': line.wife_annual_flight_ticket,
                        'wife_monthly_flight_ticket': line.wife_monthly_flight_ticket,
                        'child_flight_ticket': line.child_flight_ticket,
                        'child_monthly_flight_ticket': line.child_monthly_flight_ticket,
                        'saudi_eng_council': line.saudi_eng_council,
                        'hire_right_process': line.hire_right_process,
                        'employee_visa': line.employee_visa,
                        'employee_visa_endorsement': line.employee_visa_endorsement,
                        'family_visa_cost': line.family_visa_cost,
                        'family_visa_endorsement': line.family_visa_endorsement,
                        'gosi': line.gosi,
                        'gosi_share': line.gosi_share,
                        'saudization': line.saudization,
                        'iqama_transfer_fees': line.iqama_transfer_fees,
                        'mobilization_cost': line.mobilization_cost,
                        'ajeer': line.ajeer,
                        'exit_reentry': line.exit_reentry,
                        'profile_fees': line.profile_fees,
                        'candidate_type': cand_type_value,
                        'marital_status': line.marital_status,
                        'candidate_class': line.candidate_class,
                        'package': line.package,
                        'misc': line.misc,
                        'flint_fee': line.flint_fee,
                        'number_of_kids': line.number_of_kids,
                        'number_of_spouses': line.number_of_spouses,
                        'invoice_period': line.invoice_period,
                        'total_monthly_cost': line.total_monthly_cost,
                        'total_monthly_cost_usd': line.total_monthly_cost_usd,
                        'total_annual_cost_usd': line.total_annual_cost_usd,
                        'per_25': line.per_25,
                        'per_15': line.per_15,
                        'per_day_cost': line.per_day_cost,
                        'net_monthly_salary': line.net_monthly_salary,
                        'yearly_employee_cost': line.yearly_employee_cost,
                    }))

            self.crm_applicant_line_ids = [(5, 0, 0)]
            self.crm_applicant_line_ids = crm_applicant_lines

        else:
            raise ValidationError(_('No applicants found!'))
            # def button_update_crm_applicant_lines(self):
    #     self.ensure_one()

    #     recruitment_order_ids = self.job_ids

    #     if recruitment_order_ids:
    #         crm_applicant_lines = []
    #         for order in recruitment_order_ids:
    #             for line in order.applicant_line.filtered(lambda l: l.state == 'confirm'):
    #                 crm_applicant_lines.append((0, 0, {
    #                     'recruitment_order_id': line.recruitment_order_id.id,
    #                     'sequence': line.sequence,
    #                     'name': line.name,
    #                     'email': line.email,
    #                     'phone': line.phone,
    #                     'nationality': line.nationality or False,
    #                     'current_location': line.current_location,
    #                     'experience': line.experience,
    #                     'qualification': line.qualification,
    #                     'current_company': line.current_company,
    #                     'position': line.position,
    #                     'notice_period': line.notice_period,
    #                     'salary_expectation': line.salary_expectation,
    #                     'show_salary_expectation': line.show_salary_expectation,
    #                     'wife': line.wife,
    #                     'show_wife': line.show_wife,
    #                     'show_kids': line.show_kids,
    #                     'kids': line.kids,
    #                     'profession': line.profession,
    #                     'number_iqama': line.number_iqama,
    #                     'current_salary': line.current_salary,
    #                     'show_current_salary': line.show_current_salary,
    #                     'resume': line.resume,
    #                     'file_name': line.file_name,
    #                     'state': line.state,
    #                     'rejection_reason': line.rejection_reason,
    #                     'selection_link': line.selection_link,
    #                     'access_token': line.access_token,
    #                     'rejection_date': line.rejection_date,
    #                     'basic': line.basic,
    #                     'housing': line.housing,
    #                     'transportation': line.transportation,
    #                     'vac_salary': line.vac_salary,
    #                     'end_of_service': line.end_of_service,
    #                     'employee_health': line.employee_health,
    #                     'spouse_health_insurance': line.spouse_health_insurance,
    #                     'kids_health_insurance': line.kids_health_insurance,
    #                     'family_health_insurance': line.family_health_insurance,
    #                     'employee_annual_flight_ticket': line.employee_annual_flight_ticket,
    #                     'employee_monthly_flight_ticket': line.employee_monthly_flight_ticket,
    #                     'wife_annual_flight_ticket': line.wife_annual_flight_ticket,
    #                     'wife_monthly_flight_ticket': line.wife_monthly_flight_ticket,
    #                     'child_flight_ticket': line.child_flight_ticket,
    #                     'child_monthly_flight_ticket': line.child_monthly_flight_ticket,
    #                     'saudi_eng_council': line.saudi_eng_council,
    #                     'hire_right_process': line.hire_right_process,
    #                     'employee_visa': line.employee_visa,
    #                     'employee_visa_endorsement': line.employee_visa_endorsement,
    #                     'family_visa_cost': line.family_visa_cost,
    #                     'family_visa_endorsement': line.family_visa_endorsement,
    #                     'gosi': line.gosi,
    #                     'gosi_share': line.gosi_share,
    #                     'saudization': line.saudization,
    #                     'iqama_transfer_fees': line.iqama_transfer_fees,
    #                     'mobilization_cost': line.mobilization_cost,
    #                     'ajeer': line.ajeer,
    #                     'exit_reentry': line.exit_reentry,
    #                     'profile_fees': line.profile_fees,
    #                     'candidate_type': line.candidate_type,
    #                     'marital_status': line.marital_status,
    #                     'candidate_class': line.candidate_class,
    #                     'package': line.package,
    #                     'misc': line.misc,
    #                     'flint_fee': line.flint_fee,
    #                     'number_of_kids': line.number_of_kids,
    #                     'number_of_spouses': line.number_of_spouses,
    #                     'invoice_period': line.invoice_period,
    #                     'total_monthly_cost': line.total_monthly_cost,
    #                     'total_monthly_cost_usd': line.total_monthly_cost_usd,
    #                     'total_annual_cost_usd': line.total_annual_cost_usd,
    #                     'per_25': line.per_25,
    #                     'per_15': line.per_15,
    #                     'per_day_cost': line.per_day_cost,
    #                     'net_monthly_salary': line.net_monthly_salary,
    #                     'yearly_employee_cost': line.yearly_employee_cost,
    #                 }))

    #         self.crm_applicant_line_ids = [(5, 0, 0)]
    #         self.crm_applicant_line_ids = crm_applicant_lines

    #     else:
    #         raise ValidationError(_('No applicants found!'))

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        help="Currency used for profitability amounts"
    )

    total_untaxed = fields.Monetary(
        string="Invoices Untaxed",
        currency_field='currency_id',
        compute="_compute_profitability",
        readonly=True
    )
    total_taxed = fields.Monetary(
        string="Invoices After Tax / Total",
        currency_field='currency_id',
        compute="_compute_profitability",
        readonly=True
    )
    total_payroll_net = fields.Monetary(
        string="Payroll Net",
        currency_field='currency_id',
        compute="_compute_profitability",
        readonly=True
    )
    profitability = fields.Monetary(
        string="Profit (Total - Payroll)",
        currency_field='currency_id',
        compute="_compute_profitability",
        readonly=True
    )

    @api.model
    def _get_currency_precision(self, currency):
        try:
            return currency.decimal_places
        except Exception:
            return 2

    def _compute_profitability(self):
        for lead in self:
            total_untaxed = 0.0
            total_taxed = 0.0
            payroll_total = 0.0
            sale_order_obj = self.env['sale.order']
            possible_lead_fields = ['opportunity_id', 'lead_id', 'crm_lead_id']
            found_field = None
            for fname in possible_lead_fields:
                if fname in sale_order_obj._fields:
                    found_field = fname
                    break

            sale_orders = self.env['sale.order'].browse()
            try:
                if found_field:
                    sale_orders = sale_order_obj.search([(found_field, '=', lead.id)])
                else:
                    if lead.partner_id:
                        sale_orders = sale_order_obj.search([('partner_id', '=', lead.partner_id.id)], limit=200)
                        if not sale_orders:
                            sale_orders = sale_order_obj.search([('origin', 'ilike', lead.name)], limit=200)
                    else:
                        sale_orders = sale_order_obj.search([('origin', 'ilike', lead.name)], limit=200)
            except Exception as e:
                _logger.exception("Error searching sale.order for lead %s: %s", lead.id, e)
                sale_orders = self.env['sale.order'].browse()

            invoices = self.env['account.move'].browse()
            if sale_orders:
                inv_domain = [
                    ('move_type', '=', 'out_invoice'),
                    ('state', '=', 'posted'),
                ]
                try:
                    rel = ('invoice_line_ids.sale_line_ids.order_id', 'in', sale_orders.ids)
                    self.env['account.move'].search_count(inv_domain + [rel])
                    inv_domain.append(rel)
                    invoices = self.env['account.move'].search(inv_domain)
                except Exception:
                    order_names = sale_orders.mapped('name')
                    if order_names:
                        inv_domain.append(('invoice_origin', 'in', order_names))
                        invoices = self.env['account.move'].search(inv_domain)
                    else:
                        invoices = self.env['account.move'].browse()
            else:
                invoices = self.env['account.move'].browse()
            try:
                if invoices:
                    company_currency = self.env.company.currency_id
                    unique_currencies = invoices.mapped('currency_id')
                    if len(unique_currencies) <= 1 or all((c == company_currency for c in unique_currencies)):
                        total_untaxed = sum(invoices.mapped('amount_untaxed') or [0.0])
                        total_taxed = sum(invoices.mapped('amount_total') or [0.0])
                    else:
                        tu = 0.0
                        tt = 0.0
                        for inv in invoices:
                            curr = inv.currency_id or company_currency
                            try:
                                tu += company_currency._convert(inv.amount_untaxed, company_currency, inv.company_id or self.env.company, inv.invoice_date or fields.Date.today())
                                tt += company_currency._convert(inv.amount_total, company_currency, inv.company_id or self.env.company, inv.invoice_date or fields.Date.today())
                            except Exception:
                                tu += float(inv.amount_untaxed or 0.0)
                                tt += float(inv.amount_total or 0.0)
                        total_untaxed = tu
                        total_taxed = tt
            except Exception as e:
                _logger.exception("Error summing invoices for lead %s: %s", lead.id, e)
                total_untaxed = 0.0
                total_taxed = 0.0

            payroll_total = 0.0
            try:
                applicant_lines = lead.mapped('crm_applicant_line_ids')
                employees = applicant_lines.mapped('employee_id')
                if employees:
                    payslip_obj = self.env['hr.payslip']
                    payslips = payslip_obj.search([('employee_id', 'in', employees.ids), ('state', '=', 'done')], limit=1000)
                    if payslips:
                        for slip in payslips:
                            net_lines = slip.line_ids.filtered(lambda l: (getattr(l, 'code', '') or '').upper() in ('NET', 'NETT', 'NET_PAY', 'NET_SALARY', 'NETPAY'))
                            if net_lines:
                                payroll_total += sum(net_lines.mapped('amount') or [0.0])
                            else:
                                added = 0.0
                                if hasattr(slip, 'net_wage') and slip.net_wage:
                                    added = float(slip.net_wage)
                                elif hasattr(slip, 'amount_total') and slip.amount_total:
                                    added = float(slip.amount_total)
                                else:
                                    for ln in slip.line_ids:
                                        if hasattr(ln, 'amount_org') and (ln.amount_org is not None):
                                            try:
                                                added += float(ln.amount_org)
                                            except Exception:
                                                pass
                                        elif hasattr(ln, 'amount') and (ln.amount is not None):
                                            try:
                                                added += float(ln.amount)
                                            except Exception:
                                                pass
                                payroll_total += added
            except Exception as e:
                _logger.exception("Error computing payroll for lead %s: %s", lead.id, e)
                payroll_total = payroll_total or 0.0

            # Rounding
            currency = lead.currency_id or self.env.company.currency_id
            prec = self._get_currency_precision(currency) or 2

            try:
                total_untaxed = float_round(float(total_untaxed or 0.0), precision_digits=prec)
            except Exception:
                total_untaxed = round(float(total_untaxed or 0.0), prec)
            try:
                total_taxed = float_round(float(total_taxed or 0.0), precision_digits=prec)
            except Exception:
                total_taxed = round(float(total_taxed or 0.0), prec)
            try:
                payroll_total = float_round(float(payroll_total or 0.0), precision_digits=prec)
            except Exception:
                payroll_total = round(float(payroll_total or 0.0), prec)

            profit = float_round((total_taxed - payroll_total) or 0.0, precision_digits=prec)

            # write computed values
            lead.total_untaxed = total_untaxed
            lead.total_taxed = total_taxed
            lead.total_payroll_net = payroll_total
            lead.profitability = profit


class CRMApplicantLine(models.Model):
    _name = 'crm.applicant.line'
    _description = 'CRM Applicant Line'

    crm_lead_id = fields.Many2one('crm.lead')
    tv_seq = fields.Char(related="recruitment_order_id.sequence", string="Recruitment ID")
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
    show_salary_expectation = fields.Boolean()
    wife = fields.Char(string='Dependents (Wife)')
    show_wife = fields.Boolean()
    show_kids = fields.Boolean()
    kids = fields.Char(string='Dependents (Kids)')
    profession = fields.Char(string='Profession on iqama')
    number_iqama = fields.Char(string='Number of Iqama Transfers')
    current_salary = fields.Float(string='Current Salary')
    show_current_salary = fields.Boolean()
    resume = fields.Binary(string='Resume')
    # file_name = fields.Char('File Name', )
    file_name = fields.Char('File Name')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('reject', 'Rejected')
    ], string='Status', default='draft')
    rejection_reason = fields.Text(string="Rejection Reason")
    selection_link = fields.Char(string='Selection Link', help='URL for accessing the selection page')
    access_token = fields.Char('Security Token')
    rejection_date = fields.Datetime(string="Rejection Date", readonly=True)

    # Cost Analysis
    basic = fields.Float('Basic Salary')
    housing = fields.Float()
    transportation = fields.Float('Transportation')
    vac_salary = fields.Float("Vac Salary 12 months PO")
    end_of_service = fields.Float()
    employee_health = fields.Float("Employee Health Insurance")
    spouse_health_insurance = fields.Float("Spouse Health Insurance")
    kids_health_insurance = fields.Float("Kids  Health Insurance")
    family_health_insurance = fields.Float("Family Health Insurance")
    employee_annual_flight_ticket = fields.Float()
    employee_monthly_flight_ticket = fields.Float(string="Employee Monthly Flight Ticket")
    wife_annual_flight_ticket = fields.Float()
    wife_monthly_flight_ticket = fields.Float(string="Wife Monthly Flight Ticket")
    child_flight_ticket = fields.Float("Child Annual Flight Ticket")
    child_monthly_flight_ticket = fields.Float(string="child Monthly Flight Ticket")
    saudi_eng_council = fields.Float("Saudi Engineering Council")
    hire_right_process = fields.Float("Hire Right Process")
    employee_visa = fields.Float("Employee Visa Cost")
    employee_visa_endorsement = fields.Float("Employee Visa Endorsement")
    family_visa_cost = fields.Float("Family Visa Cost")
    family_visa_endorsement = fields.Float("Family Visa Endorsement")
    gosi = fields.Float()
    gosi_share = fields.Float()
    saudization = fields.Float()
    iqama_fees = fields.Float()
    iqama_transfer_fees = fields.Float()
    mobilization_cost = fields.Float()
    ajeer = fields.Float()
    exit_reentry = fields.Float()
    profile_fees = fields.Float("Profile Fees (One-time)")
    candidate_type = fields.Selection(
        [("saudi_local", "Saudi Local"), ("no_saudi", "Non-Saudi")],
        default="saudi_local",
    )
    marital_status = fields.Selection(
        [("married", "Married"), ("unmarried", "Un-Married")],
        default="unmarried",
    )
    candidate_class = fields.Selection(
        [("class_a", "A"),
         ("class_a_plus", "A+"),
         ("class_b", "B"),
         ("class_b_plus", "B+"),
         ("class_c", "C"),
         ("class_c_plus", "C+")],
        default="class_a",
    )
    package = fields.Float()
    misc = fields.Float("Miscellaneous")
    flint_fee = fields.Float()
    number_of_kids = fields.Integer("kids", default=0)
    number_of_spouses = fields.Integer("Spouses", default=0)
    invoice_period = fields.Float("Invoice Period (No. of months)", required=True)
    total_monthly_cost = fields.Float()
    total_monthly_cost_usd = fields.Float()
    total_annual_cost_usd = fields.Float()
    per_25 = fields.Float()
    per_15 = fields.Float()
    per_day_cost = fields.Float()

    net_monthly_salary = fields.Float(string='Net Salary')
    yearly_employee_cost = fields.Float()
    # Validation fields
    is_create_job = fields.Boolean(string="Create Job")
    applicant_ids_count = fields.Integer(string="Applicants")


class CrmCostingSummaryLine(models.Model):
    _name = "crm.costing.summary.line"
    _description = "CRM Costing Summary Line"

    lead_id = fields.Many2one('crm.lead', string='Lead', ondelete='cascade', index=True)
    applicant_line_id = fields.Many2one('crm.applicant.line', string='Applicant Line')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    employee_name = fields.Char(string='Employee Name', related='employee_id.name', readonly=True, store=True)
    file_number = fields.Char(string='File Number', related='employee_id.code', readonly=True, store=True)
    net_salary = fields.Float(string='Net Salary (Total)', digits=(16, 2))
    payslip_count = fields.Integer(string='Payslip Count')

    _sql_constraints = [
        ('lead_employee_uniq', 'unique(lead_id, employee_id, applicant_line_id)', 'Duplicate costing line!')
    ]
