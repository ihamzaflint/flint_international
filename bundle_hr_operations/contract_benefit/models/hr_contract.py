# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrContract(models.Model):
    _inherit = 'hr.contract'

    grade_ids = fields.Many2many('itq.hr.grade', string='Grades', compute='_compute_grade_ids', store=True)
    benefit_ids = fields.Many2many(comodel_name="itq.hr.benefit.integration", compute='_compute_available_benefits',
                                   relation="hr_contract_benefit_integration_change_request", string="Benefits", )
    valuable_benefit_ids = fields.One2many(comodel_name="itq.hr.contract.benefit", inverse_name="valuable_benefit_id",
                                           domain=[('calculation_type', 'in', ['perc_from_bs', 'amount'])],
                                           required=False)
    non_valuable_benefit_ids = fields.One2many(comodel_name="itq.hr.contract.benefit",
                                               inverse_name="non_valuable_benefit_id",
                                               domain=[('calculation_type', '=', 'count')], required=False)
    allow_basic_salary = fields.Boolean(string="Allow Basic Salary", default=False)
    gross_salary = fields.Monetary(required=False, compute='_compute_gross_salary', compute_sudo=True)

    @api.depends('salary_grade_id')
    def _compute_grade_ids(self):
        for record in self:
            if record.salary_grade_id:
                record.grade_ids = [(6, 0, [record.salary_grade_id.id])]
            else:
                record.grade_ids = [(5, 0, 0)]

    @api.depends('valuable_benefit_ids', 'non_valuable_benefit_ids',
                 'valuable_benefit_ids.benefit_id', 'non_valuable_benefit_ids.benefit_id')
    def _compute_available_benefits(self):
        benefits = self.env['itq.hr.benefit.integration'].sudo().search([('appear_on_contract', '=', True)])
        for record in self:
            grade_benefits = benefits.filtered(
                lambda b: record.salary_grade_id in b.grade_ids and record.schema_id == b.schema_id and
                          b.id not in record.valuable_benefit_ids.mapped(
                    'benefit_id').ids and b.id not in record.non_valuable_benefit_ids.mapped('benefit_id').ids)
            record.benefit_ids = [(6, 0, grade_benefits.ids)]

    @api.depends('wage', 'valuable_benefit_ids')
    def _compute_gross_salary(self):
        for record in self:
            valuable_benefit = sum(record.valuable_benefit_ids.mapped('calculated_value'))
            record.gross_salary = record.wage + valuable_benefit

    @api.onchange('salary_grade_id')
    def _onchange_salary_grade_id(self):
        if not self.salary_grade_id:
            self.salary_degree_id = False
        if self.salary_grade_id and not self.contract_template_id:
            self.valuable_benefit_ids = False
            self.non_valuable_benefit_ids = False
            benefit_ids = self.env['itq.hr.benefit.integration'].sudo().search(
                [("appear_on_contract", '=', True), ('grade_ids', 'in', [self.salary_grade_id.id]),
                 ('schema_id', '=', self.schema_id.id)])
            valuable_benefit_ids = benefit_ids.filtered(
                lambda b: b.calculation_type in ['perc_from_bs', 'amount'])
            non_valuable_benefit_ids = benefit_ids.filtered(
                lambda b: b.calculation_type == 'count')
            valuable_benefit = []
            for line in valuable_benefit_ids:
                valuable_benefit.append(
                    (0, 0, {'benefit_id': line.id, 'benefit_value': line.benefit_value}))
            non_valuable_benefit = []
            for line in non_valuable_benefit_ids:
                non_valuable_benefit.append(
                    (0, 0, {'benefit_id': line.id, 'benefit_value': line.benefit_value}))
            self.update({'non_valuable_benefit_ids': non_valuable_benefit, 'valuable_benefit_ids': valuable_benefit})

        @api.onchange('contract_template_id')
        def _onchange_contract_template_id(self):
            if self.contract_template_id:
                if self.schema_design == self.contract_template_id.schema_design:
                    self.valuable_benefit_ids = False
                    self.non_valuable_benefit_ids = False
                    self.job_id = self.contract_template_id.job_id
                    self.structure_type_id = self.contract_template_id.structure_type_id.id
                    self.schema_id = self.contract_template_id.schema_id.id
                    self.salary_grade_id = self.contract_template_id.grade_id
                    self.salary_degree_id = self.contract_template_id.degree_id
                    valuable_benefit_ids = self.contract_template_id.line_ids.filtered(
                        lambda b: b.calculation_type in ['perc_from_bs', 'amount'])
                    non_valuable_benefit_ids = self.contract_template_id.line_ids.filtered(
                        lambda b: b.calculation_type == 'count')
                    valuable_benefit = []
                    for line in valuable_benefit_ids:
                        valuable_benefit.append(
                            (0, 0, {'benefit_id': line.benefit_id.id, 'benefit_value': line.benefit_value}))
                    non_valuable_benefit = []
                    for line in non_valuable_benefit_ids:
                        non_valuable_benefit.append(
                            (0, 0, {'benefit_id': line.benefit_id.id, 'benefit_value': line.benefit_value}))
                    self.update(
                        {'non_valuable_benefit_ids': non_valuable_benefit, 'valuable_benefit_ids': valuable_benefit})

    @api.constrains('valuable_benefit_ids', 'allow_basic_salary')
    def validate_benefit_cap(self):
        for rec in self:
            if not rec.allow_basic_salary:
                if any(rec.valuable_benefit_ids.filtered(lambda benefit: benefit.benefit_value > benefit.cap)):
                    raise ValidationError(_("The Benefit value must be equal or less than cap"))
                if any(rec.valuable_benefit_ids.filtered(lambda benefit: benefit.benefit_value <= 0)):
                    raise ValidationError(_("The Benefit value must be greater than 0 ."))