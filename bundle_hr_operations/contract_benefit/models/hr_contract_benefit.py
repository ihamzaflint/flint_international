from odoo import models, fields, _, api
from odoo.exceptions import UserError


class ItqHrBenefitBenefit(models.Model):
    _name = 'itq.hr.contract.benefit'
    _description = 'Hr Contract Benefit'
    _inherit = 'itq.hr.benefit.abstract'
    _rec_name = 'benefit_id'

    valuable_benefit_id = fields.Many2one('hr.contract', required=False, ondelete='cascade', index=True)
    non_valuable_benefit_id = fields.Many2one('hr.contract', required=False, ondelete='cascade', index=True)
    calculated_value = fields.Float(compute='_compute_calculated_value')

    @api.depends('benefit_value')
    def _compute_calculated_value(self):
        calculated_value = 0.0
        for record in self:
            if record.calculation_type == 'amount':
                calculated_value = record.benefit_value
            elif record.calculation_type == 'perc_from_bs':
                calculated_value = (record.benefit_value / 100) * record.valuable_benefit_id.wage
            record.calculated_value = calculated_value

    @api.onchange('benefit_id')
    def update_benefit_value(self):
        for record in self:
            if record.benefit_id:
                record.benefit_value = record.benefit_id.benefit_value
            else:
                record.benefit_value = 0.0

    @api.model
    def create(self, vals):
        if not vals.get('benefit_id'):
            raise UserError(_('You must select a benefit'))
        return super(ItqHrBenefitBenefit, self).create(vals)
