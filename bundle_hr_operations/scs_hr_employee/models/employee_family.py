from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HrEmployeeFamily(models.Model):
    _name = "hr.employee.family"
    _description = "Hr Employee Family"

    employee_id = fields.Many2one(comodel_name="hr.employee", required=True, tracking=True,
                                  ondelete='cascade')
    family_type = fields.Selection(selection=[('spouse', 'Spouse'),
                                              ('father', 'Father'),
                                              ('mother', 'Mother'),
                                              ('child', 'Child')],
                                   required=True, tracking=True)
    name = fields.Char(required=True, tracking=True)
    ar_name = fields.Char(string="Arabic Name", tracking=True)

    passport_id = fields.Char('Passport No', tracking=True)
    passport_exp_date = fields.Date('Passport Expiry Date', tracking=True)
    border_number = fields.Char('Border Number', tracking=True)
    identification_id = fields.Char('ID', tracking=True)

    phone = fields.Char(tracking=True)
    birthday = fields.Date('Date of Birth', tracking=True)
    employer = fields.Char(tracking=True)

    accommodation_no = fields.Char(string="Residence Permit Number", tracking=True)
    accommodation_exp_date = fields.Date('Residence Permit Expiry Date', tracking=True)
    passport_copy = fields.Many2many('ir.attachment', string='Passport Copy', tracking=True, required=True)

    _sql_constraints = [
        ('unique_name', 'check(1==1)', 'This name already exists')
    ]

    @api.constrains('employee_id', 'family_type')
    def _check_family_type(self):
        for record in self:
            if self.search_count([('employee_id', '=', record.employee_id.id),
                                  ('family_type', '=', 'father')]) > 1:
                raise ValidationError(_('You cannot have more then one father.'))
            if self.search_count([('employee_id', '=', record.employee_id.id),
                                  ('family_type', '=', 'mother')]) > 1:
                raise ValidationError(_('You cannot have more then one mother.'))

    @api.constrains('birthday')
    def _check_birthday(self):
        for record in self:
            if record.birthday and (record.birthday > fields.Date.today()):
                raise ValidationError(_("Birthday should not be bigger than today"))
            if record.family_type == 'father' and record.birthday and \
                    (fields.Date.today().year - record.birthday.year) < 18:
                raise ValidationError(_("Father should be at least 18 years old"))
            if record.family_type == 'mother' and record.birthday and \
                    (fields.Date.today().year - record.birthday.year) < 18:
                raise ValidationError(_("Mother should be at least 18 years old"))
            # if record.family_type == 'child' and record.birthday and \
            #         (fields.Date.today().year - record.birthday.year) > 2:
            #     raise ValidationError(_("Child should be at most 2 years old"))

    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {}, name=_("%s (copy)") % (self.name))
        return super(HrEmployeeFamily, self).copy(default)
