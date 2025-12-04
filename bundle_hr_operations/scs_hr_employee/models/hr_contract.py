from odoo import api, models,_, fields
from odoo.exceptions import ValidationError


class HrContract(models.Model):
    _inherit = 'hr.contract'

    @api.model
    def _get_employee_name(self):
        if self.employee_id:
            return self.employee_id.name
        return ''

    name = fields.Char(string="Contract Name", required=True, default=_get_employee_name)

    @api.constrains('analytic_account_id')
    def _check_analytic_account_id(self):
        for rec in self:
            if not rec.analytic_account_id:
                continue
            if not rec.employee_id.project_id:
                raise ValidationError(_("Employee Project is not set"))
            if not rec.employee_id.project_id.analytic_account_id:
                raise ValidationError(_("Analytic Account is not set for Employee Project"))
            if rec.analytic_account_id != rec.employee_id.project_id.analytic_account_id:
                raise ValidationError(_("Analytic Account should be same as Employee Project's Analytic Account"))

    @api.model
    def create(self, vals_list):
        res = super(HrContract, self).create(vals_list)
        if vals_list.get('analytic_account_id'):
            vals_list['analytic_account_id'] = res.employee_id.project_id.analytic_account_id.id
        return res