from odoo import api, fields, models
from odoo.tools.float_utils import float_round
from odoo.exceptions import ValidationError


class SaleOrderServiceLine(models.Model):
    _name = 'sale.order.service.line'
    _description = 'Sale Order Service Line'

    name = fields.Char(string='Description', required=True, readonly=True, copy=False, default='Draft')
    order_line_id = fields.Many2one('sale.order.line', string='Order Line', ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Client',
                                 default=lambda self:
                                 self.env['sale.order'].browse(self._context.get('active_id')).partner_id.id,
                                 store=True, readonly=True, required=True)
    hr_job_id = fields.Many2one('hr.job', string='Job Position', required=True)
    job_list_id = fields.Many2one('job.list', string='Job List', store=True)
    net_monthly_salary = fields.Float(string='Net Salary', compute="_compute_net_monthly", store=True)
    candidate_type = fields.Selection(
        [("saudi_local", "Saudi Local"), ("no_saudi", "Non-Saudi")],
        required=True,
        default="saudi_local",
    )
    gosi = fields.Float(required=True)
    saudization = fields.Float(required=True)
    iqama_fees = fields.Float(required=True)
    iqama_transfer_fees = fields.Float(required=True)
    mobilization_cost = fields.Float(required=True)
    ajeer = fields.Float()
    housing = fields.Float()
    transportation = fields.Float("Transportation")
    basic = fields.Float('Basic Salary')
    nationality_id = fields.Many2one("res.country", compute='_compute_nationality', store=True,
                                     inverse='_inverse_nationality')
    contract_type = fields.Selection([
        ('permanent', 'Permanent Role'),
        ('contracted', 'Contract through Flint')
    ], string='Contract Type', default='permanent', required=True)
    marital = fields.Selection(
        [
            ("single", "Single"),
            ("married", "Married"),
            ("cohabitant", "Legal Cohabitant"),
            ("widower", "Widower"),
            ("divorced", "Divorced"),
        ],
        string="Marital Status",
        default="single",
        required=True
    )
    job_description = fields.Html(related='hr_job_id.description', string='Job Description')
    # experience_level = fields.Many2one('experience.level', ondelete='restrict', string='Experience Level')
    child_flight_ticket = fields.Float("Child Annual Flight Ticket")
    profile_fees = fields.Float("Profile Fees (One-time)")
    yearly_employee_cost = fields.Float(
        compute="_compute_yearly_cost",
        store=True,
    )
    total_monthly_cost = fields.Float(
        compute="_compute_total_monthly_cost",
        store=True,
    )
    invoice_period = fields.Float("Invoice Period (No. of months)", required=True)
    package = fields.Float()
    vac_salary = fields.Float("Vac Salary 12 months PO", required=True)
    end_of_service = fields.Float()
    employee_annual_flight_ticket = fields.Float()
    wife_annual_flight_ticket = fields.Float()

    employee_health = fields.Float("Employee Health Insurance (Categories)")
    spouse_health_insurance = fields.Float("Spouse Health Insurance")
    kids_health_insurance = fields.Float("Kids  Health Insurance")
    exit_reentry = fields.Float()

    @api.depends("candidate_type")
    def _compute_nationality(self):
        for record in self:
            if record.candidate_type == "saudi_local":
                record.nationality_id = self.env.ref("base.sa").id
            else:
                record.nationality_id = False

    @api.depends('candidate_type')
    def _inverse_nationality(self):
        for record in self:
            if record.candidate_type == "saudi_local":
                record.nationality_id = self.env.ref("base.sa").id
            else:
                record.nationality_id = False

    @api.depends('basic', 'housing', 'transportation')
    def _compute_net_monthly(self):
        for rec in self:
            rec.net_monthly_salary = rec.basic + rec.housing + rec.transportation
            rec.end_of_service = (
                                     float_round(
                                         rec.net_monthly_salary and rec.net_monthly_salary / 24,
                                         precision_digits=2,
                                     )
                                 ) or 0
            if rec.candidate_type == "no_saudi":
                rec.gosi = float_round(
                    ((rec.basic + rec.housing) * 0.02), precision_digits=2
                )
                rec.iqama_fees = float_round(((9700 + 650) / 12), precision_digits=2)
                rec.iqama_transfer_fees = 6000 / 12
                rec.ajeer = float_round((420 / 12), precision_digits=2)
                rec.exit_reentry = float_round(((200 * 4) / 12), precision_digits=2)
            else:
                rec.gosi = float_round(
                    ((rec.basic + rec.housing) * 0.1175), precision_digits=2
                )
                if rec.invoice_period and rec.net_monthly_salary:
                    rec.profile_fees = float_round(
                        (rec.net_monthly_salary / 12),
                        precision_digits=2,
                    )

    @api.depends("exit_reentry", "mobilization_cost", "profile_fees", "ajeer", "iqama_transfer_fees", "iqama_fees",
                 "saudization", "gosi", "employee_health", "spouse_health_insurance", "kids_health_insurance",
                 "child_flight_ticket",
                 "wife_annual_flight_ticket", "employee_annual_flight_ticket", "end_of_service", "vac_salary",
                 "total_monthly_cost", 'invoice_period',
                 )
    def _compute_total_monthly_cost(self):
        for rec in self:
            if rec.candidate_type == "no_saudi":
                rec.total_monthly_cost = (
                                                 rec.net_monthly_salary
                                                 + rec.vac_salary
                                                 + rec.end_of_service
                                                 + rec.employee_annual_flight_ticket
                                                 + rec.wife_annual_flight_ticket
                                                 + rec.child_flight_ticket
                                                 + rec.employee_health
                                                 + rec.spouse_health_insurance
                                                 + rec.kids_health_insurance
                                                 + rec.gosi
                                                 + rec.saudization
                                                 + rec.iqama_fees
                                                 + rec.iqama_transfer_fees
                                                 + rec.mobilization_cost
                                                 + rec.ajeer
                                                 + rec.exit_reentry
                                         ) / rec.invoice_period if rec.invoice_period else 0
            else:
                rec.total_monthly_cost = (
                                                 rec.net_monthly_salary
                                                 + rec.vac_salary
                                                 + rec.end_of_service
                                                 + rec.employee_health
                                                 + rec.spouse_health_insurance
                                                 + rec.kids_health_insurance
                                                 + rec.gosi
                                                 + rec.employee_annual_flight_ticket
                                                 + rec.wife_annual_flight_ticket
                                                 + rec.child_flight_ticket
                                                 + rec.profile_fees
                                         ) / rec.invoice_period if rec.invoice_period else 0

    @api.depends("total_monthly_cost")
    def _compute_yearly_cost(self):
        for rec in self:
            rec.yearly_employee_cost = float_round(
                rec.total_monthly_cost * rec.invoice_period, precision_digits=2)

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

    @api.constrains("basic", "housing", "transportation",
                    "employee_health", "spouse_health_insurance", "kids_health_insurance",
                    "child_flight_ticket", "wife_annual_flight_ticket", "employee_annual_flight_ticket",
                    "vac_salary", "end_of_service")
    def _check_null_values(self):
        for rec in self:
            if any(
                    [not rec.basic,
                     not rec.housing,
                     not rec.transportation,
                     not rec.employee_health,
                     not rec.spouse_health_insurance,
                     not rec.vac_salary,
                     not rec.end_of_service,
                     ]
            ):
                raise ValidationError("one or more fields are empty, please fill all fields")
            if (
                    not rec.kids_health_insurance or not rec.child_flight_ticket or not rec.wife_annual_flight_ticket) and rec.marital == "married":
                raise ValidationError("Please fill all fields")
            if (
                    not rec.employee_annual_flight_ticket or not rec.exit_reentry or not rec.iqama_fees or
                    rec.iqama_transfer_fees
                    or not rec.mobilization_cost or not rec.ajeer or not rec.saudization or not rec.profile_fees
            ) and rec.candidate_type == 'no_saudi':
                raise ValidationError("Please fill all fields")

    @api.model
    def create(self, vals):
        # Ensure that `vals` is a dictionary and set `partner_id` appropriately
        default_partner_id = self._context.get('default_partner_id')
        if default_partner_id:
            vals['partner_id'] = self.env['res.partner'].browse(default_partner_id).id

        # Create the record
        res = super(SaleOrderServiceLine, self).create(vals)

        # Set the name based on conditions
        if res.partner_id and res.hr_job_id:
            sequence_code = self.env['ir.sequence'].next_by_code('service_line_sequence')
            prefix = f'{res.partner_id.name}/{res.hr_job_id.name}/'
            res.name = f'{prefix}{sequence_code}'
        else:
            res.name = 'Draft'

        # Calculate and set the price unit to be the sum of the service line total yearly cost
        res.order_line_id.price_unit = res.order_line_id.price_subtotal = \
            (sum(res.order_line_id.order_id.hr_applicant_id.recruitment_order_id.lead_id.mapped('package')) or \
             sum(res.order_line_id.order_id.hr_applicant_id.lead_id.mapped('package')) or \
             res.order_line_id.product_id.lst_price)
        return res

    def write(self, vals):
        res = super(SaleOrderServiceLine, self).write(vals)
        if 'hr_job_id' in vals or 'partner_id' in vals:
            for record in self:
                sequence_code = self.env['ir.sequence'].next_by_code('service_line_sequence')
                prefix = f'{record.partner_id.name}/{record.hr_job_id.name}/'
                record.name = f'{prefix}{sequence_code}'
        return res

    @api.onchange('candidate_type')
    def _onchange_candidate_type(self):
        for rec in self:
            for field_name in ['gosi', 'saudization', 'iqama_fees', 'iqama_transfer_fees', 'mobilization_cost', 'ajeer',
                               'housing', 'transportation', 'basic', 'profile_fees', 'package', 'vac_salary',
                               'end_of_service', 'employee_annual_flight_ticket', 'wife_annual_flight_ticket',
                               'child_flight_ticket', 'employee_health', 'spouse_health_insurance',
                               'kids_health_insurance',
                               'exit_reentry', 'invoice_period', 'total_monthly_cost', 'yearly_employee_cost']:
                rec[field_name] = 0.0
