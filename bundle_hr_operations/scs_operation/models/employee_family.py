from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HrEmployeeFamily(models.Model):
    _name = "hr.employee.family"
    _description = "Hr Employee Family"

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

    sponsor_no = fields.Char(tracking=True)
    phone = fields.Char(tracking=True)
    birthday = fields.Date('Date of Birth', tracking=True)
    employer = fields.Char(tracking=True)
    insurance_class_id = fields.Many2one('insurance.class', string="Insurance Class", tracking=True)
    gender = fields.Selection(selection=[('male', 'Male'),
                                         ('female', 'Female'),
                                         ('other', 'Other')], required=True, tracking=True)

    accommodation_no = fields.Char(string="Residence Permit Number", tracking=True)
    accommodation_exp_date = fields.Date('Residence Permit Expiry Date', tracking=True)
    insurance_id = fields.Many2one(comodel_name="res.partner", string="Insurance Covered",
                                   tracking=True)
    employee_id = fields.Many2one(comodel_name="hr.employee", required=True, tracking=True,
                                  ondelete='cascade')
    passport_copy = fields.Many2many('ir.attachment',string='Passport Copy', tracking=True, required=True)

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

    @api.model_create_multi
    def create(self, vals_list):

        # Create records first
        records = super(HrEmployeeFamily, self).create(vals_list)
        attachment_sudo = self.env['ir.attachment'].sudo()

        # Loop through created records and their input values
        for record, vals in zip(records, vals_list):
            attachment_ids = []
            if vals.get('passport_copy'):
                for rel_command in vals['passport_copy']:
                    # (4, id) means "link existing attachment"
                    if rel_command[0] == 4:
                        attachment_ids.append(rel_command[1])
            if attachment_ids:
                # Browse attachments and update linking
                attachments = attachment_sudo.browse(attachment_ids)
                for at in attachments:
                    at.sudo().update({
                        'res_field': 'passport_copy',
                        'res_id': record.id,
                        'public': False,
                    })

        return records

    def write(self, values):
        """Override write to handle attachment linking"""
        res = super(HrEmployeeFamily, self).write(values)
        attachment_sudo = self.env['ir.attachment'].sudo()

        # Loop through each record in self
        for record in self:
            if values.get('passport_copy'):
                attachment_ids = []

                for rel_command in values['passport_copy']:
                    # (6, 0, [ids]) → replace all attachments
                    if rel_command[0] == 6:
                        attachment_ids = rel_command[2]

                    # (4, id) → add an attachment
                    elif rel_command[0] == 4:
                        attachment_ids.append(rel_command[1])

                    # (3, id) → remove an attachment (optional cleanup)
                    elif rel_command[0] == 3:
                        attachment_sudo.browse(rel_command[1]).write({
                            'res_model': False,
                            'res_field': False,
                            'res_id': False,
                        })

                # Update all attachments that are being added or replaced
                if attachment_ids:
                    attachments = attachment_sudo.browse(attachment_ids)
                    attachments.write({
                        'res_model': 'hr.employee.family',
                        'res_field': 'passport_copy',
                        'res_id': record.id,
                        'public': False,  # private visibility
                    })

        return res