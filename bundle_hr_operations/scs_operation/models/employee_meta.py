from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HrInsuranceCompany(models.Model):
    _name = "itq.hr.insurance.company"
    _inherit = ['mail.thread']
    _description = "Hr Insurance Company"

    name = fields.Char(required=True, tracking=True)

    _sql_constraints = [
        ('unique_name', 'unique (name)', 'This name already exists')
    ]

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {}, name=_("%s (copy)") % (self.name))
        return super(HrInsuranceCompany, self).copy(default)


class HrResidencePermitProfession(models.Model):
    _name = "itq.hr.accommodation.profession"
    _inherit = ['mail.thread']
    _description = "Hr Residence Permit Profession"

    name = fields.Char(required=True, tracking=True)

    _sql_constraints = [
        ('unique_name', 'unique (name)', 'This name already exists')
    ]

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {}, name=_("%s (copy)") % (self.name))
        return super(HrResidencePermitProfession, self).copy(default)
