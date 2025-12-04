from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class ItqPrintOutGroup(models.Model):
    _name = 'print.out.group'
    _description = 'Print Out Group'
    _inherit = 'mail.thread'

    name = fields.Char(required=True)
    salary_rule_ids = fields.One2many(comodel_name='hr.salary.rule', inverse_name='print_out_group_id')

    def unlink(self):
        for rec in self:
            if rec.salary_rule_ids:
                raise ValidationError(_("You Can't delete print out group related to salary rule."))

    @api.constrains('salary_rule_ids')
    def salary_rule_validation(self):
        for rec in self:
            if rec.salary_rule_ids and len(set(rec.salary_rule_ids.mapped('category_id'))) > 1:
                raise ValidationError(_("The Salary rules are not the same type."))





