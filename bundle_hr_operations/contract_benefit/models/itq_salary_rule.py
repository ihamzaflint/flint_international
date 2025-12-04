from odoo import models, _
from odoo.exceptions import ValidationError


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    def action_archive(self):
        for rec in self:
            if rec.allowance_rule_type == 'benefit':
                contracts = self.env['hr.contract'].search(
                    [('valuable_benefit_ids', '!=', False), ('state', '!=', 'cancel')])
                if contracts.mapped('valuable_benefit_ids').filtered(lambda r: r.benefit_id == rec.benefit_id):
                    raise ValidationError(_("you can't archive benefits related to contract."))
                rec.benefit_id.active = False
        return super(HrSalaryRule, self).action_archive()

    def write(self, values):
        for rec in self:
            if values.get('category_id', False):
                values['print_out_group_id'] = False
            if rec.benefit_id and (values.get('category_id') or values.get('benefit_id')):
                if self.env['hr.payslip.line'].search([('salary_rule_id', '=', rec.id)]):
                    raise ValidationError(_("You can’t change salary rule used in pay-slip."))
                if self.env['hr.payroll.structure'].search([('rule_ids', 'in', rec.id)]):
                    raise ValidationError(_("You can’t change salary rule used in salary structure."))
                contracts = self.env['hr.contract'].search([('valuable_benefit_ids', '!=', False)]).mapped(
                    'valuable_benefit_ids').filtered(lambda r: r.benefit_id == rec.benefit_id)
                if contracts:
                    raise ValidationError(_("you can't change salary rule its benefit assigned to contract."))
        return super(HrSalaryRule, self).write(values)

    def unlink(self):
        for rec in self:
            if not self.env.context.get('pass_validation'):
                salary_structure = self.env['hr.payroll.structure'].search([('rule_ids', 'in', rec.id)])
                if salary_structure:
                    raise ValidationError(_(
                        "you can't delete salary rule related to payslip or salary structure."))
                if rec.allowance_rule_type == 'benefit':
                    if rec.benefit_id.is_used:
                        raise ValidationError(_(
                            "you can't delete benefit related to contract."))
                    rec.benefit_id.sudo().with_context({'from_salary_rule': True}).unlink()

        return super(HrSalaryRule, self).unlink()