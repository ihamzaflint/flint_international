from odoo.exceptions import ValidationError
from odoo import models, fields, api, _


class HrContractTemplate(models.Model):
    _inherit = 'hr.contract.template'

    benefit_ids = fields.Many2many('itq.hr.benefit.integration', compute='_compute_benefit_ids',
                                   string="Benefits")
    benefit_value = fields.Float(string="Benefit Value", required=False)

    @api.depends('line_ids', 'grade_id')
    def _compute_benefit_ids(self):
        for record in self:
            used_benefits = []
            if record.line_ids:
                used_benefits = record.line_ids.mapped('benefit_id').ids
            benefit_ids = self.env['itq.hr.benefit.integration'].sudo().search(
                [("appear_on_contract", '=', True), ("id", 'not in', used_benefits),
                 ('schema_id', '=', self.schema_id.id), ('grade_ids', 'in', [self.grade_id.id])]).ids
            record.benefit_ids = [(6, 0, benefit_ids)]

    @api.onchange('grade_id')
    def _onchange_grade_id(self):
        self.line_ids = False
        benefit_ids = self.env['itq.hr.benefit.integration'].sudo().search(
            [("appear_on_contract", '=', True), ('grade_ids', 'in', [self.grade_id.id]),
             ('schema_id', '=', self.schema_id.id)])
        benefit_list = []
        for line in benefit_ids:
            benefit_list.append(
                (0, 0, {'benefit_id': line.id, 'benefit_value': line.benefit_value}))
        self.sudo().update({'line_ids': benefit_list})
        if not self.grade_id:
            self.degree_id = False
        degrees = self.env['itq.hr.grade.line'].search(
            [('itq_salary_scale_schema_id.state', '=', 'active'),
             ('itq_salary_scale_schema_id', '=', self.schema_id.id),
             ('itq_hr_grade_id', '=', self.grade_id.id)]).mapped('itq_hr_degree_line_ids').mapped(
            'itq_hr_degree_id')
        return {'domain': {'degree_id': [('id', 'in', degrees.ids)]}}

    @api.constrains('benefit_ids', 'line_ids')
    def _constrain_benefit_value(self):
        for record in self:
            if any(not (
                    line.calculation_type == 'perc_from_bs' and (self.line_ids
                                                                         .filtered(
                lambda self: self.calculation_type == 'perc_from_bs')[0] > 100 or 0 >= self.benefit_value))
                   for line in
                   record.line_ids):
                raise ValidationError(_("Benefit Value must be between (1,100)"))
            elif any(not (line.calculation_type == 'amount' and line.benefit_value <= 0) for line in record.line_ids):
                raise ValidationError(_("Benefit Value must be greater than zero"))
            elif any(not (line.calculation_type == 'count' and line.benefit_value < 0) for line in record.line_ids):
                raise ValidationError(_("Benefit Value must be greater than or equal zero"))
            elif not record.allow_basic_salary and any(
                    not (line.benefit_value < line.benefit_id.cap) for line in record.line_ids):
                raise ValidationError(_("Benefit Value must be less than Cap"))


class HrContractTemplateLine(models.Model):
    _inherit = 'hr.contract.template.line'

    benefit_id = fields.Many2one(comodel_name="itq.hr.benefit.integration", string="Benefit", required=True)
    calculation_type = fields.Selection(related='benefit_id.calculation_type')
    benefit_value = fields.Float(string="Benefit Value", required=False)

    @api.onchange('benefit_id')
    def _onchange_benefit_id(self):
        self.benefit_value = self.benefit_id.benefit_value

    @api.onchange('benefit_value')
    def _constrain_benefit_value(self):
        if self.calculation_type == 'perc_from_bs' and (self.benefit_value > 100 or 0 >= self.benefit_value):
            raise ValidationError(_("Benefit Value must be between (1,100)"))
        elif self.calculation_type == 'amount' and self.benefit_value <= 0:
            raise ValidationError(_("Benefit Value must be greater than zero"))
        elif self.calculation_type == 'count' and self.benefit_value < 0:
            raise ValidationError(_("Benefit Value must be greater than or equal zero"))
        elif not self.contract_template_id.allow_basic_salary and self.benefit_value > self.benefit_id.cap:
            raise ValidationError(_("Benefit Value must be less than Cap"))
