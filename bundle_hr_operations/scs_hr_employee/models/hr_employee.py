from odoo import api, models, fields,_
from odoo.exceptions import ValidationError

import logging
from odoo.osv import expression
_logger = logging.getLogger(__name__)


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    ar_name = fields.Char(string="Arabic Name", compute="_compute_ar_name", store=False)
    ar_first_name = fields.Char(string="Arabic First Name", required=False)
    ar_second_name = fields.Char(string="Arabic Second Name", required=False)
    ar_grandfather_name = fields.Char(string="Arabic Grandfather Name", required=False)
    ar_family_name = fields.Char(string="Arabic Family Name", required=False)
    current_open_contract = fields.Many2one("hr.contract")
    employee_assigned_to = fields.Selection(string="Assigned To",
                                            selection=[('business_unit', 'Business Unit'),
                                                       ('project', 'Project'), ],
                                            required=False, tracking=True,
                                            )
    is_contract_renew = fields.Boolean(string="Contract Renewable")
    department_id = fields.Many2one(comodel_name="hr.department")
    state = fields.Selection(string="Employee State", selection=[('new_hire', 'New-Hire'),
                                                                 ('onboarding', 'Onboarding'),
                                                                 ('active', 'Active'),
                                                                 ('pending_deactivation', 'Pending Deactivation'),
                                                                 ('extended', 'Extended'),
                                                                 ('termination_process', 'Termination Process'),
                                                                 ('under_review', 'Under Review'),
                                                                 ('inactive', 'Inactive'),
                                                                 ], default='new_hire')
    is_citizen = fields.Boolean()


    @api.depends('ar_first_name', 'ar_second_name',
                 'ar_grandfather_name', 'ar_family_name')
    def _compute_ar_name(self):
        for record in self:
            ar_name = False
            if record.ar_first_name and record.ar_second_name and record.ar_grandfather_name and record.ar_family_name:
                ar_name = record.ar_first_name + " " + record.ar_second_name + " " + \
                          record.ar_grandfather_name + " " + record.ar_family_name
            record.ar_name = ar_name


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    client_type_id = fields.Many2one("client.type", string="Client Type")
    project_id = fields.Many2one("client.project", string="Client Project")
    client_id = fields.Many2one("res.partner", string="Client",related='project_id.partner_id',
                                readonly=True)
    muqeem_name = fields.Char("Name As per Muqeem")
    muqeem_profession = fields.Char("Profession as per Muqeem")
    emp_degree_id = fields.Many2one("employee.degree", string="Degree")
    client_employee_id = fields.Char("Client Employee ID")
    contract_state_id = fields.Selection(related="contract_id.state")
    address_id = fields.Many2one(related='work_contact_id',readonly=True)

    department_id = fields.Many2one(comodel_name="hr.department", required=False, tracking=True)
    employee_role = fields.Selection(string="Role", selection=[('staff', 'Staff'),
                                                               ('manager', 'Manager'), ('manager', 'Manager'),
                                                               ('director', 'Director'),
                                                               ('vp', 'VP'), ('CEO', ' CEO'),
                                                               ('CFO', ' CFO'),
                                                               ('COO', ' COO'), ('CTO', ' CTO'),
                                                               ('PM', ' PM')],
                                     required=False, tracking=True
                                     , groups="hr.group_hr_user")
    is_citizen = fields.Boolean(tracking=True,
                                compute="_compute_is_citizen", store=True)
    id_issue_date = fields.Date('ID Issue Date', tracking=True, groups="hr.group_hr_user",
                                copy=False)
    id_issue_location = fields.Char('ID Issue Location', tracking=True, groups="hr.group_hr_user",
                                    copy=False)
    id_exp_date = fields.Date('ID Expiry Date', tracking=True, groups="hr.group_hr_user",
                              copy=False)
    id_exp_date_hijri = fields.Char('ID Expiry Date Hijri', tracking=True, groups="hr.group_hr_user",
                                    copy=False)
    passport_copy = fields.Many2many('ir.attachment',
                                     string="Passport Copy",
                                     domain="[('res_model', '=', 'hr.employee'), ('res_id', '=', id)]"
                                     )
    family_ids = fields.One2many('hr.employee.family', 'employee_id', string='Family',
                                 groups="hr.group_hr_user", copy=False)

    # Residence Permit
    accommodation_provided = fields.Char(tracking=True, groups="hr.group_hr_user",
                                         copy=False)
    insurance_id = fields.Many2one(comodel_name="res.partner", string="Insurance Covered",
                                   tracking=True, groups="hr.group_hr_user",
                                   copy=False)
    passport_exp_date = fields.Date('Passport Expiry Date', tracking=True, groups="hr.group_hr_user",
                                    copy=False)
    passport_exp_date_hijri = fields.Char('Passport Expiry Date Hijri', compute="get_passport_hijri_date",
                                          tracking=True, groups="hr.group_hr_user",
                                          copy=False)
    other_id = fields.Char(string="Other ID", tracking=True, groups="hr.group_hr_user", copy=False)
    gosi_no = fields.Char(string="GOSI Number", tracking=True, groups="hr.group_hr_user", copy=False)
    accommodation_no = fields.Char(string="Residence Permit Number", tracking=True,
                                   groups="hr.group_hr_user", copy=False)
    accommodation_issue_date = fields.Date(string="Residence Permit Issue Date", tracking=True,
                                           groups="hr.group_hr_user", copy=False)
    accommodation_issue_location = fields.Char(string="Residence Permit Issue Location", tracking=True,
                                               groups="hr.group_hr_user", copy=False)
    accommodation_exp_date = fields.Date('Residence Permit Expiry Date', tracking=True,
                                         groups="hr.group_hr_user", copy=False)
    accommodation_exp_date_hijri = fields.Char('Residence Permit Expiry Date Hijri', tracking=True,
                                               groups="hr.group_hr_user", copy=False)
    sponsor = fields.Selection(selection=[('company', 'Company'),
                                          ('sister_company', 'Sister Company'),
                                          ('free', 'Free')],
                               tracking=True
                               , groups="hr.group_hr_user", copy=False)
    sponsor_name = fields.Char(tracking=True, groups="hr.group_hr_user", copy=False)
    sponsor_contact_name = fields.Char(tracking=True, groups="hr.group_hr_user", copy=False)
    sponsor_contact_no = fields.Char(tracking=True, groups="hr.group_hr_user", copy=False)
    gender = fields.Selection(required=False, tracking=True, groups="hr.group_hr_user")
    birthday = fields.Date(required=False, tracking=True, groups="hr.group_hr_user")
    country_of_birth = fields.Many2one(required=False, tracking=True, groups="hr.group_hr_user")
    pin = fields.Char(required=False, tracking=True, string="Employee Code", copy=False, groups="hr.group_hr_user")
    salary_payment = fields.Selection(selection=[('wage', 'Wage'),
                                                 ('bank', ' Bank'),
                                                 ('sister_company', 'Sister-Company')],
                                      tracking=True, required=False
                                      , groups="hr.group_hr_user")
    job_id = fields.Many2one(required=False, tracking=True)
    initial_employment_date = fields.Date(tracking=True, copy=False, groups="hr.group_hr_user")
    length_of_service = fields.Char(compute="_compute_length_of_service", groups="hr.group_hr_user")
    length_of_service_days = fields.Float(compute="_compute_length_of_service", groups="hr.group_hr_user")
    wfm_user = fields.Char(string="WFM User", tracking=True, copy=False, groups="hr.group_hr_user")
    hrfd_support = fields.Boolean(string="HRFD Support", tracking=True, copy=False, groups="hr.group_hr_user")
    state = fields.Selection(string="", selection=[('new_hire', 'New-Hire'),
                                                   ('onboarding', 'Onboarding'),
                                                   ('active', 'Active'),
                                                   ('pending_deactivation', 'Pending Deactivation'),
                                                   ('extended', 'Extended'),
                                                   ('termination_process', 'Termination Process'),
                                                   ('under_review', 'Under Review'),
                                                   ('inactive', 'Inactive'),
                                                   ], required=True, default='new_hire',
                             tracking=True, copy=False,
                             readonly=True)
    current_open_contract = fields.Many2one("hr.contract", compute="_compute_current_open_contract",
                                            compute_sudo=True, store=True, groups="hr.group_hr_user")
    km_home_work = fields.Integer(groups="hr.group_hr_user")
    employee_assigned_to = fields.Selection(string="Assigned To",
                                            selection=[('business_unit', 'Business Unit'),
                                                       ('project', 'Project'), ],
                                            required=False, tracking=True,
                                            )

    bank_account_ids = fields.One2many('res.partner.bank', 'employee_bank_account_id',
                                       string="Employee Bank Account")
    bank_account_id = fields.Many2one('res.partner.bank', string="Bank", compute='compute_current_bank', store=True,
                                      groups="hr.group_hr_user")
    is_terminated = fields.Boolean(string="Employee Terminated", copy=False, readonly=True, groups="hr.group_hr_user")
    terminated_date = fields.Date(string="Termination date", copy=False, required=False, readonly=True,
                                  groups="hr.group_hr_user")

    age = fields.Integer(compute='calculate_age', groups="hr.group_hr_user")

    contract_state = fields.Selection(related='contract_id.state')
    check_readonly = fields.Boolean(compute="_compute_check_readonly")
    fields_readonly = fields.Boolean(compute="_compute_check_readonly")
    ar_name = fields.Char(string="Arabic Name", compute="_compute_ar_name", store=False)
    ar_first_name = fields.Char(string="Arabic First Name", required=False)
    ar_second_name = fields.Char(string="Arabic Second Name", required=False)
    ar_grandfather_name = fields.Char(string="Arabic Grandfather Name", required=False)
    ar_family_name = fields.Char(string="Arabic Family Name", required=False)

    @api.depends('ar_first_name', 'ar_second_name',
                 'ar_grandfather_name', 'ar_family_name')
    def _compute_ar_name(self):
        for record in self:
            ar_name = False
            if record.ar_first_name and record.ar_second_name and record.ar_grandfather_name and record.ar_family_name:
                ar_name = record.ar_first_name + " " + record.ar_second_name + " " + \
                          record.ar_grandfather_name + " " + record.ar_family_name
            record.ar_name = ar_name

    @api.constrains('country_id', 'identification_id')
    def _constraint_on_identification_id(self):
        for record in self:
            if record.country_id and record.identification_id:
                employee_ids = self.env['hr.employee'].search_count(
                    ['|', ('active', '=', True), ('active', '=', False), ('country_id', '!=', False),
                     ('identification_id', '!=', False), ('country_id', '=', record.country_id.id),
                     ('identification_id', '=', record.identification_id), ('id', '!=', record.id)])
                if employee_ids > 1:
                    raise ValidationError(_("Identification Id must be unique"))

    @api.constrains('country_id', 'passport_id')
    def _constraint_on_passport_id(self):
        for record in self:
            if record.country_id and record.passport_id:
                employee_ids = self.env['hr.employee'].search_count(
                    ['|', ('active', '=', True), ('active', '=', False), ('country_id', '!=', False),
                     ('passport_id', '!=', False), ('country_id', '=', record.country_id.id),
                     ('passport_id', '=', record.passport_id), ('id', '!=', record.id)])

                if employee_ids > 1:
                    raise ValidationError(_("Passport Id must be unique"))

    @api.constrains('work_email')
    def _constraint_on_work_email(self):
        for record in self:
            if record.work_email:
                employee_ids = self.env['hr.employee'].search_count(
                    ['|', ('active', '=', True), ('active', '=', False),
                     ('work_email', '!=', False),
                     ('work_email', '=', record.work_email), ('id', '!=', record.id)])
                if employee_ids > 1:
                    raise ValidationError(_("Work email must be unique"))

    @api.constrains('mobile_phone')
    def _constraint_on_mobile_phone(self):
        for record in self:
            if record.mobile_phone:
                employee_ids = self.env['hr.employee'].search_count(
                    ['|', ('active', '=', True), ('active', '=', False), ('mobile_phone', '!=', False),
                     ('mobile_phone', '=', record.mobile_phone), ('id', '!=', record.id)])

                if employee_ids > 1:
                    raise ValidationError(_("Work mobile must be unique"))

    category_ids = fields.Many2many(tracking=True)

    def is_manager_value(self):
        for rec in self:
            if rec.employee_assigned_to == 'business_unit' and rec.department_id.manager_id == rec:
                return True

    @api.depends('contract_id', 'state')
    def _compute_check_readonly(self):
        for rec in self:
            rec.check_readonly = False
            rec.fields_readonly = False
            if rec.contract_id:
                rec.check_readonly = rec.state != 'new_hire' and not rec.is_manager_value()
                rec.fields_readonly = rec.state != 'new_hire'

    @api.onchange('department_id', 'employee_assigned_to')
    def _onchange_employee_department_id(self):
        if self.department_id and self.employee_assigned_to == 'business_unit' and self.department_id.manager_id:
            related_employee = self.department_id.manager_id
            self.parent_id = related_employee

    @api.depends('birthday')
    def calculate_age(self):
        for rec in self:
            age = False
            today = fields.Date.today()
            if rec.birthday:
                age = today.year - rec.birthday.year - (
                        (today.month, today.day) < (rec.birthday.month, rec.birthday.day))
            rec.age = age

    @api.depends('bank_account_ids', 'bank_account_ids.is_default_account')
    def compute_current_bank(self):
        for rec in self:
            if rec.bank_account_ids:
                default_bank_account = rec.bank_account_ids.filtered(lambda b: b.is_default_account)
                if default_bank_account:
                    rec.bank_account_id = default_bank_account[0].id

    @api.depends('passport_exp_date')
    def get_passport_hijri_date(self):
        for record in self:
            record.passport_exp_date_hijri = self.env.company.get_hijri_date(record.passport_exp_date)

    @api.constrains('salary_payment', 'sponsor')
    def _constrain_sponsor_with_salary_payment(self):
        for record in self:
            if record.salary_payment == 'sister_company' and record.sponsor != 'sister_company':
                raise ValidationError("Sponsor must be 'Sister-Company' as salary payment 'Sister-Company'")
            if record.salary_payment != 'sister_company' and record.sponsor == 'sister_company':
                raise ValidationError("Salary payment must be 'Sister-Company' as Sponsor 'Sister-Company'")

    @api.constrains('bank_account_ids')
    def _constrain_bank_account_ids(self):
        for record in self:
            default_accounts = record.bank_account_ids.filtered(lambda b: b.is_default_account).mapped(
                'is_default_account')
            if record.bank_account_ids and len(default_accounts) < 1:
                raise ValidationError(_("Employee must have only one default bank account."))
            if record.bank_account_ids and len(default_accounts) > 1:
                raise ValidationError(_("Employee must have only one default bank account."))

    @api.depends('contract_ids', 'contract_ids.state')
    def _compute_current_open_contract(self):
        for record in self:
            current_open_contract = False
            if record.contract_ids and len(record.with_context(itq_ignore_apply_access=True).contract_ids.filtered(
                    lambda l: l.state == 'open')) == 1:
                current_open_contract = record.with_context(itq_ignore_apply_access=True).contract_ids.filtered(
                    lambda l: l.state == 'open').id
            record.current_open_contract = current_open_contract

    @api.constrains('pin')
    def _constrain_pin(self):
        for record in self:
            if record.pin:
                if self.search_count([('pin', '=', record.pin)]) > 1:
                    raise ValidationError(_("Employee Code already exists"))

    @api.constrains('gender', 'family_ids')
    def _constrain_gender_spouse(self):
        for record in self:
            if record.family_ids and record.gender == 'female' and \
                    len(record.family_ids.filtered(lambda f: f.family_type == 'spouse')) > 1:
                raise ValidationError("Female employee can have only one spouse")
            if record.family_ids and record.gender == 'male' and \
                    len(record.family_ids.filtered(lambda f: f.family_type == 'spouse')) > 4:
                raise ValidationError("Male employee can have till 4 spouses only")

    @api.depends('initial_employment_date')
    def _compute_length_of_service(self):
        for record in self:
            record = record.sudo()
            length_of_service = 0.0
            length_of_service_days = 0.0
            if record.initial_employment_date:
                try:
                    today = fields.Date.from_string(fields.Date.today())
                    initial_date = fields.Date.from_string(record.initial_employment_date)
                    if today and initial_date:
                        difference_date = today - initial_date
                        length_of_service = difference_date.days / 365
                        length_of_service_days = difference_date.days
                except (ValueError, TypeError):
                    length_of_service = 0.0
                    length_of_service_days = 0.0
            record.length_of_service = length_of_service
            record.length_of_service_days = length_of_service_days

    @api.depends('country_id', 'company_id')
    def _compute_is_citizen(self):
        for record in self:
            is_citizen = False
            if record.country_id and record.country_id == record.company_id.country_id:
                is_citizen = True
            record.is_citizen = is_citizen

    # @api.constrains('department_id', 'parent_id')
    # def _check_parent_id(self):
    #     """
    #     Prevent manager of employee to be himself.
    #     """
    #     for emp in self:
    #         if emp == emp.parent_id:
    #             raise ValidationError(_('You can not  be manager for yourself'))
    #     if not self._check_recursion():
    #         raise ValidationError(_('You cannot create a recursive Employee Managers.'))

    @api.constrains('birthday')
    def _check_birthday(self):
        for record in self:
            age_restriction = int(self.env['ir.config_parameter'].sudo().get_param('itq_hr_base.emp_age_restriction'))
            if age_restriction > 0 and record.birthday and record.birthday > fields.Date.today():
                raise ValidationError(_("Employee age should be more than or equal {} years".format(
                    age_restriction)))

    @api.constrains('id_exp_date', 'id_issue_date')
    def _check_id_issue_date(self):
        for record in self:
            if record.id_issue_date and record.id_exp_date and (record.id_issue_date >= record.id_exp_date):
                raise ValidationError(_("ID Expiry Date must be greater than ID Issue Date"))

    @api.constrains('accommodation_exp_date', 'accommodation_issue_date')
    def _check_accommodation_exp_date(self):
        for record in self:
            if record.accommodation_exp_date and record.accommodation_issue_date and \
                    (record.accommodation_issue_date >= record.accommodation_exp_date):
                raise ValidationError(
                    _("Residence Permit Expiry Date must be greater than Residence Permit Issue Date"))

    def check_employee_has_contracts(self):
        if not self.contract_ids:
            raise ValidationError(_("You can not move employee state "
                                    "if there is no contract for this employee"))

        return True

    @api.constrains('pin')
    def _verify_pin(self):
        for employee in self:
            if employee.pin and not employee.pin.isdigit():
                raise ValidationError(_("The employee code must be a sequence of digits."))

    def action_onboarding(self):
        for record in self:
            if record.state != 'new_hire':
                raise ValidationError(_("You can not move employee to state onboarding "
                                        "if employee not in state new-hire"))
            record.check_employee_has_contracts()

            record.state = 'onboarding'
        return True

    def action_active(self):
        for record in self:
            if record.state not in ['onboarding', 'new_hire', 'pending_deactivation']:
                raise ValidationError(_("You can not move employee to state active "
                                        "if employee not in state onboarding , new hire"))

            if 'open' not in record.contract_ids.mapped('state'):
                raise ValidationError(_("You can not move employee to state active "
                                        "if there is no running contract for this employee"))

            record.state = 'active'
        return True

    def set_pending_deactive(self):
        for record in self:
            if record.state != 'active':
                raise ValidationError(_("You can not move employee to state pending deActive "
                                        "if employee not in state active or new hire"))
            record.check_employee_has_contracts()

            record.state = 'pending_deactivation'
        return True

    def set_inactive(self):
        for record in self:
            if record.state != 'active':
                raise ValidationError(_("You can not move employee to state inActive "
                                        "if employee not in state active"))
            record.check_employee_has_contracts()

            record.state = 'inactive'
        return True

    def set_reactive(self):
        for record in self:
            if record.state != 'inactive':
                raise ValidationError(_("You can not move employee to state Reactive "
                                        "if employee not in state Inactive"))
            if 'open' not in record.contract_ids.mapped('state'):
                raise ValidationError(_("You can not move employee to state Reactive "
                                        "if there is no running contract for this employee"))

            record.state = 'active'
        return True

    def unlink(self):
        for record in self:
            if record.state != 'new_hire':
                raise ValidationError(_("You can only delete employee with status 'new-hire' "))
            if record.contract_ids:
                raise ValidationError(_("You can not delete employee with contracts "))
        return super(HrEmployee, self).unlink()

    def action_create_user(self):
        employees_with_no_user = self.filtered(lambda e: not e.user_id)
        for record in employees_with_no_user:
            if not record.work_email:
                raise ValidationError(
                    _("You can not create user for employee {} as it doesn't have work email").format(record.name))

            user_vals = {'name': record.name,
                         'login': record.work_email,
                         'email': record.work_email,
                         'company_id': self.env.company.id,
                         }
            if record.address_id:
                user_vals['partner_id'] = record.address_id.id
            created_user = self.env['res.users'].sudo().create(user_vals)
            record.user_id = created_user.id
            if not record.address_id:
                record.address_id = created_user.partner_id.id

    @api.model
    def _name_search(self, name='', domain=None, operator='ilike', limit=None, order=None):
        _logger.info(f"_name_search called with name: {name}, domain: {domain}, operator: {operator}")

        args = domain or []
        if operator == 'ilike' and not (name or '').strip():
            _logger.warning("Empty name passed to _name_search, setting domain to empty list")
            domain = []
        else:
            if self.env.user.has_group('hr.group_hr_user'):
                domain = ['|',
                          ('name', 'ilike', name),
                          ('registration_number', 'ilike', name)]
            else:
                domain = ['|', ('name', 'ilike', name), ('ar_name', 'ilike', name)]

        _logger.info(f"Final domain for _search: {expression.AND([domain, args])}")
        return self._search(expression.AND([domain, args]), limit=limit)

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, access_rights_uid=None):
        _logger.info(f"_search called with args: {domain}")
        new_args = []
        for item in domain:
            if item[0] == 'pin' and item[1] in ['=', 'like', 'ilike'] and ',' in item[2]:
                pin_domain = [item]
                for pin in item[2].split(','):
                    pin_domain = ['|'] + pin_domain + [('pin', '=', pin.strip())]
                new_args.extend(pin_domain)
            else:
                new_args.append(item)
        _logger.info(f"Modified args for super._search: {new_args}")
        return super(HrEmployee, self)._search(domain=new_args, offset=offset, limit=limit, order=order,
                                               access_rights_uid=access_rights_uid)

    @api.onchange('is_citizen')
    def _onchange_is_citizen(self):
        for record in self:
            if record.is_citizen:
                record.country_id = self.env.company.country_id.id
            else:
                record.country_id = False

    @api.constrains('bank_account_ids')
    def _employee_bank_account_constrains(self):
        for record in self:
            if record.bank_account_ids and len(record.bank_account_ids.filtered(lambda b: b.is_default_account)) > 1:
                raise ValidationError(_("Employee must have only one default bank account."))
            if record.bank_account_ids and len(record.bank_account_ids.filtered(lambda b: b.is_default_account)) < 1:
                raise ValidationError(_("Employee must have only one default bank account."))


    @api.model
    def create(self, vals_list):
        employee_creation = self.env.context.get('create_employee', False) if self.env.context else False
        if not vals_list.get('is_citizen') and not vals_list.get('passport_copy') and not employee_creation:
            raise ValidationError("Passport Copy is required for non-citizens.")
        res = super(HrEmployee, self).create(vals_list)
        res.address_id = res.work_contact_id.id
        if vals_list.get('passport_copy'):
            # Update attachments to link them to this employee record
            self.env['ir.attachment'].sudo().browse(vals_list['passport_copy'][0][1]).write({
                'res_model': 'hr.employee',
                'res_id': res.id,
                'public': True,  # Make attachment accessible
            })
        return res

    def write(self, vals):
        """Override write to handle attachment linking"""
        # If updating passport_copy attachments
        if vals.get('passport_copy'):
            # Update new attachments to link them to this employee record
            self.env['ir.attachment'].sudo().browse(vals['passport_copy'][0][1]).write({
                'res_model': 'hr.employee',
                'res_id': self.id,
                'public': True,  # Make attachment accessible
            })

        return super(HrEmployee, self).write(vals)

    def _get_employee_attachments(self):
        """Helper method to get employee's attachments with proper access"""
        domain = [
            ('res_model', '=', 'hr.employee'),
            ('res_id', '=', self.id),
        ]
        return self.env['ir.attachment'].sudo().search(domain)

    @api.depends("contract_id", "contract_id.date_end")
    def compute_kanban_color(self):
        for rec in self:
            rec.kanban_color = (
                "lightgreen"
                if rec.contract_id
                and (
                    (rec.contract_id.date_end and rec.contract_id.date_end >= fields.Date.today())
                    or not rec.contract_id.date_end
                )
                else "red"
            )

    kanban_color = fields.Char(compute="compute_kanban_color", store=True)

    @api.constrains('project_id')
    def _check_project_id(self):
        for rec in self:
            if not rec.project_id:
                raise ValidationError(_("Employee Project is not set"))
            if rec.project_id and not rec.project_id.analytic_account_id:
                raise ValidationError(_("Analytic Account is not set for Employee Project"))
            if not rec.project_id.partner_id:
                raise ValidationError(_("Client is not set for Employee Project"))
