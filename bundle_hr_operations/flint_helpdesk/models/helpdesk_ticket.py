from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class Helpdesk(models.Model):
    _inherit = "helpdesk.ticket"

    available_service_type_ids = fields.Many2many(
        "service.type",
        "service_type_helpdesk_ticket_rel",
        "ticket_id",
        "service_type_id",
        compute="_compute_available_service_type_ids",
    )
    stage_under_approval = fields.Boolean(
        related="stage_id.under_approval", string="Under Approval"
    )
    stage_is_draft = fields.Boolean(related="stage_id.is_draft", string="Draft")
    is_closed = fields.Boolean(string='Is Closed', default=False, related='stage_id.is_closed')
    in_progress = fields.Boolean(string='In Progress', default=False, related='stage_id.in_progress')
    is_operation_manager_reject = fields.Boolean(string='Operation Manager Reject', default=False,
                                                 related='stage_id.is_operation_manager_reject')
    is_on_hold = fields.Boolean(string='Is On Hold', default=False, related='stage_id.is_on_hold')
    service_type_ids = fields.Many2many("service.type", string="Service Type")
    request_user_ids = fields.Many2many(
        "res.users",
        "res_users_helpdesk_request_users",
        "ticket_id",
        "user_id",
        string="Responsible Users",
        domain=lambda self: [
            ("groups_id", "in", self.env.ref("helpdesk.group_helpdesk_user").id)
        ],
    )

    employee_id = fields.Many2one("hr.employee", compute_sudo=True, required=True)
    employee_country_id = fields.Many2one("res.country", related="employee_id.country_id")
    registration_number = fields.Char()
    analytic_account_id = fields.Many2one("account.analytic.account",
                                          related='employee_id.project_id.analytic_account_id')
    project_id = fields.Many2one('client.project', string='Project')
    iqama_no = fields.Char(
        related="employee_id.visa_no",
        string="Iqama Number",
        tracking=False,
    )
    visa_expire = fields.Date(
        related="employee_id.visa_expire",
        string="Iqama Expiry Date",
        tracking=False,
    )
    email = fields.Char(string="Email", tracking=False, required=True)
    include_payment = fields.Boolean(string="Include Payment", default=False, readonly=True)
    government_payment_id = fields.Many2one("government.payment", string="Government Payment", readonly=True,
                                            copy=False)
    logistic_order_id = fields.Many2one("logistic.order", string="Logistic Order", copy=False)
    flight_type = fields.Selection([
        ('employee', 'Employee'),
        ('family', 'Family'),
        ('both', 'Both'),
    ], string='Flight Type', default='employee')
    location_country_id = fields.Many2one('res.country', 'Departure country')
    available_departure_location = fields.Many2many('airport.airport',
                                                    compute='_compute_available_departure_location')

    departure_airport_id = fields.Many2one('airport.airport', string='Departure Airport')
    departure_city = fields.Char(string='Departure City')
    destination_country_id = fields.Many2one('res.country', string='Destination country')
    available_destination_location = fields.Many2many('airport.airport',
                                                      compute='_compute_available_destination_location')
    destination_airport_id = fields.Many2one('airport.airport', string='Destination Airport')
    destination_city = fields.Char(string='Destination City')
    departure_date = fields.Date(string='Departure Date')
    return_date = fields.Date(string='Return Date')
    hotel_name = fields.Char(string='Hotel Name', readonly=True)
    date_from = fields.Date(string='Check In')
    date_to = fields.Date(string='Check Out')
    insurance_type = fields.Selection([
        ('employee', 'Employee'),
        ('family', 'Family'),
        ('both', 'Both Employee & Family'),
    ], string='Insurance Type', default='employee')
    insurance_policy = fields.Char(string='Insurance Policy')
    required_insurance_action = fields.Selection([
        ('addition', 'Addition'),
        ('deletion', 'Deletion'),
        ('update', 'Update'),
        ('upgrade', 'Upgrade'),
        ('downgrade', 'Downgrade')
    ],
        ondelete={'cancelation': 'set default'},
        string='Required Action', help="Insurance action to be performed")
    insurance_class_from_id = fields.Many2one(
        'insurance.class',
        string='Insurance Class From',
        help="Current insurance class for upgrade/downgrade actions"
    )
    insurance_class_to_id = fields.Many2one(
        'insurance.class',
        string='Insurance Class To',
        help="Target insurance class for upgrade/downgrade actions"
    )
    family_member_ids = fields.Many2many('hr.employee.family', string='Family Member',
                                         relation='helpdesk_ticket_family_member_rel')
    available_family_member_ids = fields.Many2many('hr.employee.family', string='Available Family Members',
                                                   relation='helpdesk_ticket_available_family_member_rel',
                                                   compute='_compute_available_family_member_ids')
    service_logistic_order_type = fields.Selection(related='service_type_ids.logistic_order_type')
    is_logistics = fields.Boolean(related='ticket_type_id.is_logistics')
    is_operation = fields.Boolean(related='ticket_type_id.is_operation')
    flight_ticket = fields.Many2many('ir.attachment', string='Flight Ticket',
                                     relation='helpdesk_ticket_flight_ticket_rel')
    passport_no = fields.Char(string='Passport No', related='employee_id.passport_id')
    passport_copy = fields.Many2many('ir.attachment', string='Passport Copy',
                                     related='employee_id.passport_copy')
    passport_exp_date = fields.Date(string='Passport Expiry Date', related='employee_id.passport_exp_date')
    passport_exp_date_hijri = fields.Char(string='Passport Expiry Date Hijri',
                                          related='employee_id.passport_exp_date_hijri')
    is_citizen = fields.Boolean(string='Is Citizen', related='employee_id.is_citizen')
    identification_id = fields.Char(string='Identification No', related='employee_id.identification_id')

    name = fields.Char(string='Subject', required=True, index=True, tracking=True, default='_New', readonly=True)
    insurance_membership_no = fields.Char(string='Insurance Membership No')
    request_state = fields.Selection([
        ('not_started', 'Not Started'),
        ('done', 'Done'),
        ('in_progress', 'In Progress'),
        ('on_hold', 'On Hold'),
        ('rejected', 'Rejected'),
    ], string='Request State', default='not_started', compute='_compute_request_state', store=True)
    effective_date = fields.Date(string="Effective Date")
    sponsor_no = fields.Char(string="Sponsor No.")

    flight_direction = fields.Selection([
        ('one_way', 'One Way'),
        ('round_trip', 'Round Trip'),
    ], string='Flight Directions', default='one_way')
    preferred_travel_time = fields.Selection([
        ('morning', 'Morning (6:00 AM - 12:00 PM)'),
        ('afternoon', 'Afternoon (12:00 PM - 6:00 PM)'),
        ('evening', 'Evening (6:00 PM - 12:00 AM)'),
        ('night', 'Night (12:00 AM - 6:00 AM)'),
    ], string='Preferred Travel Time', readonly=True)
    reject_reason = fields.Text(string='Reject Reason', readonly=True)
    required_insurance_action = fields.Selection([
        ('addition', 'Addition'),
        ('deletion', 'Deletion'),
        ('update', 'Update'),
        ('upgrade', 'Upgrade'),
        ('downgrade', 'Downgrade'),
    ], string='Required Insurance Action')
    update_note = fields.Text(string='Update Note')
    ticket_number = fields.Char(string='Ticket Number')
    courier_type = fields.Selection([
        ('domestic', 'Domestic'),
        ('international', 'International'),
    ], string='Courier Type')
    recipient_name = fields.Char(string="Recipient Name")
    recipient_address = fields.Char(string="Full Address")
    recipient_phone_number = fields.Char(string="Recipient Ph.No.")
    recipient_postal_code = fields.Char(string="Postal Code")
    recipient_city = fields.Char(string=" City")
    recipient_country = fields.Many2one('res.country', string=" Country")
    courier_type = fields.Selection([
        ('domestic', 'Domestic'),
        ('international', 'International'),
    ], string='Courier Type')
    agency_name = fields.Char(string="Agency Name")

    required_document_ids = fields.Many2many(
        'document.type',
        string="Required Docs",
        copy=False,
        domain=[('state', '=', 'active')],
        required=True
    )
    required_document_count = fields.Integer(
        compute="_compute_document_count",
        string="Required Docs Count",
    )
    document_ids = fields.Many2many(
        'ir.attachment',
        string="Documents",
        relation='rel_ht_document_ids',
        copy=False
    )

    @api.constrains('insurance_type', 'family_member_ids')
    def _check_family_member_ids(self):
        """Validate insurance class selections for upgrade/downgrade actions"""
        for rec in self:
            if rec.insurance_type in ['family', 'both'] and len(rec.family_member_ids) == 0:
                raise ValidationError(_("Please make sure you have selected at-least 1 family member for the insurance."))

    @api.depends('required_document_ids')
    def _compute_document_count(self):
        for rec in self:
            if rec.required_document_ids:
                rec.required_document_count = len(rec.required_document_ids)
            else:
                rec.required_document_count = 0

    @api.depends('employee_id')
    def _compute_available_family_member_ids(self):
        for rec in self:
            rec.available_family_member_ids = rec.employee_id.family_ids.ids

    @api.onchange("employee_id")
    def _onchange_employee_id(self):
        self.partner_id = (self.employee_id.contract_id.analytic_account_id.partner_id.id or
                           self.employee_id.project_id.partner_id.id)
        self.registration_number = self.employee_id.registration_number
        self.analytic_account_id = (self.employee_id.project_id.analytic_account_id.id or
                                    self.employee_id.contract_id.analytic_account_id.id)
        self.project_id = self.employee_id.project_id
        self.email = self.employee_id.work_email or self.employee_id.personal_email

    @api.depends('partner_id.phone', 'employee_id.mobile_phone', 'employee_id.work_phone')
    def _compute_partner_phone(self):
        for ticket in self:
            if ticket.employee_id:
                # Prioritize employee phone numbers
                ticket.partner_phone = ticket.employee_id.mobile_phone or ticket.employee_id.work_phone
            elif ticket.partner_id:
                # Fall back to partner phone if no employee phone is available
                ticket.partner_phone = ticket.partner_id.phone
            else:
                ticket.partner_phone = False

    def _inverse_partner_phone(self):
        for ticket in self:
            if not self.employee_id:
                if ticket._get_partner_phone_update() or not ticket.partner_id.phone:
                    ticket.partner_id.phone = ticket.partner_phone

    @api.model
    def create(self, vals_list):
        record = super().create(vals_list)
        for rec in record.filtered(lambda l: l.partner_id and not l.employee_id):
            rec.employee_id = self.env["hr.employee"].search(
                [
                    ("address_id", "=", rec.partner_id.id),
                    ("address_id", "!=", False),
                ],
                limit=1,
            )
            rec.registration_number = rec.employee_id.registration_number
            rec.analytic_account_id = rec.employee_id.contract_id.analytic_account_id
            rec.project_id = rec.employee_id.project_id
            if rec.employee_id.work_email or rec.employee_id.personal_email:
                rec.partner_email = (
                        rec.employee_id.personal_email or rec.employee_id.work_email
                )
        self._task_message_auto_subscribe_notify(
            {res: res.request_user_ids - self.env.user for res in record}
        )
        if record.name == _('_New'):
            name = self.env['ir.sequence'].next_by_code('helpdesk.ticket') or _('New')
            record.update({'name': name})
        return record

    @api.onchange("partner_id")
    def _onchange_employee(self):
        for rec in self:
            if not self.employee_id:
                rec.employee_id = self.env["hr.employee"].search(
                    [
                        ("address_id", "=", self.partner_id.id),
                        ("address_id", "!=", False),
                    ],
                    limit=1,
                )
                rec.registration_number = rec.employee_id.registration_number
                rec.project_id = rec.employee_id.project_id
                rec.analytic_account_id = rec.employee_id.contract_id.analytic_account_id
                rec.partner_id = rec.employee_id.address_id

    @api.onchange("ticket_type_id")
    def _onchange_ticket_type_id(self):
        self.service_type_ids = False

    def write(self, vals):
        old_user_ids = {t: t.request_user_ids for t in self}
        res = super().write(vals)
        self._task_message_auto_subscribe_notify(
            {
                ticket: ticket.request_user_ids - old_user_ids[ticket] - self.env.user
                for ticket in self
            }
        )
        if (
                vals.get("kanban_state")
                and vals.get("kanban_state") in ("done", "blocked")
                and not self.env.user.user_has_groups("flint_helpdesk.group_helpdesk_final_approved")
        ):
            raise ValidationError(
                _(
                    "You are not allowed to approve the ticket. Please get in touch with authorized person"
                )
            )

        return res

    @api.model
    def _task_message_auto_subscribe_notify(self, users_per_task):
        # Utility method to send assignation notification upon writing/creation.
        template_id = self.env["ir.model.data"]._xmlid_to_res_id(
            "flint_helpdesk.helpdesk_message_user_assigned", raise_if_not_found=False
        )
        if not template_id:
            return
        view = self.env["ir.ui.view"].browse(template_id)
        task_model_description = self.env["ir.model"]._get(self._name).display_name
        for task, users in users_per_task.items():
            if not users:
                continue
            values = {
                "object": task,
                "model_description": task_model_description,
                "access_link": task._notify_get_action_link("view"),
            }
            for user in users:
                values.update(assignee_name=user.sudo().name)
                assignation_msg = view._render_template(
                    values=values, template="flint_helpdesk.helpdesk_message_user_assigned"
                )
                assignation_msg = self.env["mail.render.mixin"]._replace_local_links(
                    assignation_msg
                )
                task.message_notify(
                    subject=_("You have been assigned to %s", task.display_name),
                    body=assignation_msg,
                    partner_ids=user.partner_id.ids,
                    record_name=task.display_name,
                    email_layout_xmlid="mail.mail_notification_light",
                    model_description=task_model_description,
                )

    @api.depends("ticket_type_id")
    def _compute_available_service_type_ids(self):
        for rec in self:
            rec.available_service_type_ids = rec.ticket_type_id.selected_ticket_type_ids

    @api.constrains('required_insurance_action', 'insurance_class_from_id', 'insurance_class_to_id')
    def _check_insurance_class_upgrade_downgrade(self):
        """Validate insurance class selections for upgrade/downgrade actions"""
        for record in self:
            if record.required_insurance_action in ['upgrade',
                                                    'downgrade'] and record.insurance_class_from_id and record.insurance_class_to_id:
                if record.required_insurance_action == 'upgrade' and record.insurance_class_from_id.sequence >= record.insurance_class_to_id.sequence:
                    raise ValidationError(_(
                        "For an upgrade, the 'Insurance Class To' must be higher than 'Insurance Class From'. "
                        "Please select a higher insurance class."))
                elif record.required_insurance_action == 'downgrade' and record.insurance_class_from_id.sequence <= record.insurance_class_to_id.sequence:
                    raise ValidationError(_(
                        "For a downgrade, the 'Insurance Class To' must be lower than 'Insurance Class From'. "
                        "Please select a lower insurance class."))

    @api.onchange('required_insurance_action', 'employee_id')
    def _onchange_required_insurance_action(self):
        """Set the current employee insurance class when selecting upgrade/downgrade"""
        for record in self:
            if record.required_insurance_action in ['upgrade',
                                                    'downgrade'] and record.employee_id and record.employee_id.insurance_class_id:
                record.insurance_class_from_id = record.employee_id.insurance_class_id.id

    def _update_employee_insurance_class(self):
        """Update the employee's insurance class based on the ticket's action"""
        self.ensure_one()
        if self.service_logistic_order_type == 'insurance' and self.required_insurance_action in ['upgrade',
                                                                                                  'downgrade',
                                                                                                  'addition']:
            if not self.insurance_class_to_id:
                return

            # Update the employee's insurance class
            if self.employee_id:
                self.employee_id.write({
                    'insurance_class_id': self.insurance_class_to_id.id
                })
                message = _(
                    "Insurance class updated to '%s' via helpdesk ticket %s") % (
                              self.insurance_class_to_id.name, self.name
                          )
                self.employee_id.message_post(body=message)

                # Also log in the ticket
                self.message_post(body=_(
                    "Employee insurance class has been updated from '%s' to '%s'") % (
                                           self.insurance_class_from_id.name if self.insurance_class_from_id else _(
                                               'None'),
                                           self.insurance_class_to_id.name
                                       )
                                  )

    def action_approve(self):
        on_progress_stage = self.env["helpdesk.stage"].search(
            [("in_progress", "=", True)], limit=1
        )
        if not on_progress_stage:
            raise ValidationError(
                _("Please configure 'On Progress' stage in helpdesk settings")
            )

        for rec in self:
            if rec.include_payment and rec.ticket_type_id.is_operation:
                # Create a single government payment for all services
                gov_payment_vals = {
                    "payment_type": "individual",
                    'operation_type': 'with_payment',
                    'create_uid': self.env.user.id,
                    'create_date': fields.Datetime.now(),
                    'payment_method': 'bank',
                    'state': 'draft',
                    'include_payment': True,
                    'payment_line_ids': []
                }

                # Create a payment line for each service type
                for service in rec.service_type_ids:
                    gov_payment_line_vals = {
                        'employee_id': rec.employee_id.id,
                        'service_type_ids': [(4, service.id)],
                        'amount': service.initial_cost or 1,
                        'project_id': rec.project_id.id,
                        'helpdesk_ticket_id': rec.id
                    }
                    gov_payment_vals['payment_line_ids'].append((0, 0, gov_payment_line_vals))

                try:
                    gov_payment_ref = self.env['government.payment'].sudo().create(gov_payment_vals)
                    rec.government_payment_id = gov_payment_ref.id
                except Exception as e:
                    raise ValidationError(_(str(e)))

            elif not rec.include_payment and rec.ticket_type_id.is_operation:
                gov_payment_vals = {
                    "payment_type": "no_payment",
                    'operation_type': 'without_payment',
                    'employee_id': rec.employee_id.id,
                    'create_uid': self.env.user.id,
                    'create_date': fields.Datetime.now(),
                    'service_type_ids': [(4, service.id) for service in rec.service_type_ids],
                    'payment_method': 'bank',
                    'state': 'draft',
                    'include_payment': True,
                    'payment_line_ids': []
                }
                try:
                    gov_payment_ref = self.env['government.payment'].sudo().create(gov_payment_vals)
                    rec.government_payment_id = gov_payment_ref.id
                except Exception as e:
                    raise ValidationError(_(str(e)))

            if rec.ticket_type_id.is_logistics:
                logistic_order_vals = {
                    'employee_id': rec.employee_id.id,
                    'project_id': rec.project_id.id,
                    'analytic_account_id': rec.analytic_account_id.id,
                    'helpdesk_ticket_id': rec.id,
                    'state': 'draft',
                }
                if rec.service_type_ids[0].logistic_order_type == 'flight':
                    logistic_order_vals.update({
                        'order_type': 'flight',
                        'flight_type': rec.flight_type,
                        'location_country_id': rec.location_country_id.id,
                        'destination_country_id': rec.destination_country_id.id,
                        'departure_airport_id': rec.departure_airport_id.id,
                        'departure_city': rec.departure_city,
                        'destination_airport_id': rec.destination_airport_id.id,
                        'destination_city': rec.destination_city,
                        'departure_date': rec.departure_date,
                        'return_date': rec.return_date,
                        'helpdesk_ticket_id': rec.id,
                        'flight_direction': rec.flight_direction,
                        'preferred_travel_time': rec.preferred_travel_time,
                    })
                    if self.flight_type == 'family':
                        logistic_order_line_ids = []
                        for member in self.family_member_ids:
                            logistic_order_line_vals = {
                                'passenger_type': member.family_type,
                                'flight_type': 'family',
                                'family_member_id': member.id,
                                'name': member.name,
                                'passport_no': member.passport_id,
                            }
                            logistic_order_line_ids.append((0, 0, logistic_order_line_vals))
                        logistic_order_vals.update({
                            'logistic_order_line_ids': logistic_order_line_ids
                        })
                    elif self.flight_type == 'both':
                        logistic_order_line_ids = []
                        for member in self.family_member_ids:
                            logistic_order_line_vals = {
                                'passenger_type': member.family_type,
                                'flight_type': 'family',
                                'family_member_id': member.id,
                                'name': member.name,
                                'passport_no': member.passport_id,
                            }
                            logistic_order_line_ids.append((0, 0, logistic_order_line_vals))
                        logistic_order_vals.update({
                            'logistic_order_line_ids': logistic_order_line_ids
                        })
                    else:
                        logistic_order_vals.update({
                            'logistic_order_line_ids': [(0, 0, {
                                'passenger_type': 'employee',
                                'flight_type': 'employee',
                                'employee_id': self.employee_id.id,
                                'name': self.employee_id.name,
                                'passport_no': self.employee_id.passport_id,
                            })]
                        })
                elif rec.service_type_ids[0].logistic_order_type == 'hotel':
                    logistic_order_vals.update({
                        'order_type': 'hotel',
                        'date_from': self.date_from,
                        'date_to': self.date_to,

                    })
                elif rec.service_type_ids[0].logistic_order_type == 'insurance':
                    logistic_order_vals.update({
                        'order_type': 'insurance',
                        'insurance_required_action': rec.required_insurance_action,
                        'effective_date': rec.effective_date,
                        'sponsor_no': rec.sponsor_no,
                        'insurance_membership_no': rec.insurance_membership_no,
                    })

                    # Transfer insurance class information - FIX: Use ID values instead of codes
                    if rec.insurance_class_from_id:
                        logistic_order_vals.update({
                            'insurance_class_from': rec.insurance_class_from_id.id,
                        })

                    if rec.insurance_class_to_id:
                        logistic_order_vals.update({
                            'insurance_class_to': rec.insurance_class_to_id.id,
                            'insurance_class': rec.insurance_class_to_id.id,  # Set current insurance class as well
                        })

                    if rec.insurance_type in ['family', 'both']:
                        if rec.insurance_type == 'family':
                            logistic_order_vals.update({
                                'insurance_type': 'family',
                            })

                        if rec.insurance_type == 'both':
                            logistic_order_vals.update({
                                'insurance_type': 'both',
                            })

                        logistic_order_line_ids = []
                        if self.family_member_ids:
                            for member in self.family_member_ids:
                                # Get employee's insurance class as default - FIX: Use ID instead of code
                                default_insurance_class = self.employee_id.insurance_class_id
                                insurance_class_id = None
                                insurance_cost = 0

                                if default_insurance_class:
                                    insurance_class_id = default_insurance_class.id
                                    # Get the appropriate cost based on passenger type
                                    if member.family_type == 'employee':
                                        insurance_cost = default_insurance_class.employee_cost or 0
                                    elif member.family_type == 'spouse':
                                        insurance_cost = default_insurance_class.spouse_cost or 0
                                    else:  # child, father, mother, etc.
                                        insurance_cost = default_insurance_class.child_cost or 0

                                logistic_order_line_vals = {
                                    'employee_id': self.employee_id.id,
                                    'passenger_type': member.family_type,
                                    'family_member_id': member.id,
                                    'name': member.name,
                                    'passport_no': member.passport_id,
                                    'insurance_class': insurance_class_id,  # FIX: Use ID instead of code
                                }
                                logistic_order_line_ids.append((0, 0, logistic_order_line_vals))
                        else:
                            default_insurance_class = self.employee_id.insurance_class_id
                            insurance_class_id = None
                            if default_insurance_class:
                                insurance_class_id = default_insurance_class.id  # FIX: Use ID instead of code
                            logistic_order_line_vals = {
                                'employee_id': self.employee_id.id,
                                'passenger_type': 'employee',
                                'name': self.employee_id.name,
                                'passport_no': self.employee_id.passport_id,
                                'insurance_class': insurance_class_id,  # FIX: Use ID instead of code

                            }
                            logistic_order_line_ids.append((0, 0, logistic_order_line_vals))
                        logistic_order_vals.update({
                            'logistic_order_line_ids': logistic_order_line_ids
                        })

                    else:
                        logistic_order_vals.update(
                            {
                                'insurance_type': 'employee',
                            }
                        )
                    if rec.required_insurance_action == 'update':
                        logistic_order_vals.update({
                            'update_note': rec.update_note,
                        })
                elif rec.service_type_ids[0].logistic_order_type == 'pick_up_drop_off':
                    logistic_order_vals.update({
                        'order_type': 'pick_up_drop_off',
                        'preferred_travel_time': rec.preferred_travel_time,
                        'ticket_number': rec.ticket_number,
                    })
                elif rec.service_type_ids[0].logistic_order_type == 'courier':
                    # required_document_ids = []
                    # document_ids = []
                    # for rdi in rec.required_document_ids:
                    #     required_document_ids.append(rdi)
                    #
                    # for di in rec.document_ids:
                    #     document_ids.append(di)

                    logistic_order_vals.update({
                        'order_type': 'courier',
                        'recipient_name': rec.recipient_name,
                        'recipient_address': rec.recipient_address,
                        'recipient_phone_number': rec.recipient_phone_number,
                        'recipient_postal_code': rec.recipient_postal_code,
                        'recipient_city': rec.recipient_city,
                        'recipient_country': rec.recipient_country.id,
                        'courier_type': rec.courier_type,
                        'agency_name': rec.agency_name,
                        'required_document_ids': [(6, 0, rec.required_document_ids.ids)],
                        'required_document_count': rec.required_document_count,
                        'document_ids': [(6, 0, rec.document_ids.ids)],
                    })

                try:
                    logistic_order_ref = self.env['logistic.order'].sudo().create(
                        logistic_order_vals
                    )
                    self.logistic_order_id = logistic_order_ref.id

                except Exception as e:
                    raise ValidationError(_(str(e)))

            rec.stage_id = on_progress_stage.id
            self.message_post(body=_("Ticket approved by %s and Process number %s" % (self.env.user.name,
                                                                                      self.government_payment_id.name)))
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                summary=_('Ticket Approved'),
                note=_('Dear %s,Your request has been Approved,'
                       ' Please proceed with the ticket %s') % (self.user_id.name, rec.name),
                user_id=self.user_id.id
            )

    def action_confirm(self):
        under_approval_stage = self.env["helpdesk.stage"].search(
            [("under_approval", "=", True)], limit=1
        )
        for rec in self:
            if not under_approval_stage:
                raise ValidationError(
                    _("Please configure 'Under Approval' stage in helpdesk settings")
                )
            if not self.ticket_type_id or not self.service_type_ids:
                raise ValidationError(_("Please select the Service Category and service type for your ticket."))
            rec.stage_id = under_approval_stage.id
            rec.message_post(body=_("Ticket confirmed by %s" % self.env.user.name))
            for user in self.env.ref('scs_operation.group_operation_admin').users:
                rec.activity_schedule(
                    'mail.mail_activity_data_todo',
                    summary=_('Ticket Approval'),
                    note=_('Dear %s, Please approve the ticket %s') % (user.name, rec.name),
                    user_id=user.id
                )

    def action_on_hold(self):
        on_hold_stage = self.env["helpdesk.stage"].search(
            [("is_on_hold", "=", True)], limit=1
        )
        for rec in self:
            if not on_hold_stage:
                raise ValidationError(
                    _("Please configure 'On Hold' stage in helpdesk settings")
                )
            rec.stage_id = on_hold_stage.id
            rec.message_post(body=_("Ticket is on hold by %s" % self.env.user.name))

    def action_operation_manager_reject(self):
        return {
            'name': _('Operation Manager Reject Reason'),
            'view_mode': 'form',
            'res_model': 'rejection.reason.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def action_close(self):
        close_stage = self.env["helpdesk.stage"].search(
            [("is_closed", "=", True)], limit=1
        )
        for rec in self:
            if not close_stage:
                raise ValidationError(
                    _("Please configure 'Close' stage in helpdesk settings")
                )
            rec._validate_closing()

            # Handle insurance class updates when ticket is closed
            if rec.service_logistic_order_type == 'insurance' and rec.required_insurance_action in ['upgrade',
                                                                                                    'downgrade',
                                                                                                    'addition']:
                rec._update_employee_insurance_class()

            # Get attachments based on ticket type
            attachments = []
            if rec.is_logistics and rec.service_logistic_order_type == 'flight':
                attachments = rec.flight_ticket.ids if rec.flight_ticket else []
            elif rec.is_operation:
                if rec.government_payment_id:
                    if rec.include_payment:
                        # Get attachments from government.payment.line
                        payment_lines = rec.government_payment_id.sudo().mapped('payment_line_ids').filtered(
                            lambda l: l.helpdesk_ticket_id == rec
                        )
                        attachments = payment_lines.sudo().mapped('operation_order_attachment').ids
                    else:
                        # Get attachments directly from government.payment
                        attachments = rec.government_payment_id.muqeem_attachment_ids.ids

            # Get all message attachments from the chatter
            chatter_attachments = rec.message_ids.mapped('attachment_ids').ids
            all_attachments = list(set(attachments + chatter_attachments))

            # Prepare email body
            email_body = f"""
                <div style="margin: 0px; padding: 0px;">
                    <p style="font-size: 13px;">
                        Dear {rec.employee_id.name},
                        <br/><br/>
                        We are pleased to inform you that your service request ticket <strong>#{rec.name}</strong> has been successfully completed.
                        <br/><br/>
                        <strong>Ticket Details:</strong>
                        <ul>
                            <li>Service Category: {rec.ticket_type_id.name}</li>
                            <li>Service Type: {', '.join(rec.service_type_ids.mapped('name'))}</li>
                            <li>Description: {rec.description or ''}</li>
                        </ul>
                        {'<p>Please find attached your flight ticket documents.</p>' if rec.is_logistics and rec.service_logistic_order_type == 'flight' else ''}
                        {'<p>Please find attached the relevant government documents.</p>' if rec.is_operation and rec.government_payment_id else ''}
                        <br/>
                        If you have any questions or need further assistance, please don't hesitate to contact us.
                        <br/><br/>
                        Best regards,<br/>
                        {self.env.user.name}
                    </p>
                </div>
            """

            # Return the email compose wizard action
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'mail.compose.message',
                'views': [(False, 'form')],
                'target': 'new',
                'context': {
                    'default_model': 'helpdesk.ticket',
                    'default_use_template': False,
                    'default_composition_mode': 'comment',
                    'default_partner_ids': [(6, 0, [rec.employee_id.address_id.id])],
                    'default_attachment_ids': [(6, 0, all_attachments)],
                    'default_subject': f'Ticket #{rec.name} - Service Request Completed',
                    'default_body': email_body,
                    'custom_layout': 'mail.mail_notification_light',
                    'force_email': True,
                    'mark_so_as_sent': True,
                    'close_ticket': True,  # Custom context key to identify ticket closure
                    'active_id': rec.id,
                    'active_ids': [rec.id],
                    'active_model': 'helpdesk.ticket',
                }
            }

    def reset_to_draft(self):
        draft_stage = self.env["helpdesk.stage"].search(
            [("is_draft", "=", True)], limit=1
        )
        for rec in self:
            if not draft_stage:
                raise ValidationError(
                    _("Please configure 'Draft' stage in helpdesk settings")
                )
            rec.stage_id = draft_stage.id
            if rec.government_payment_id:
                rec.government_payment_id.payment_line_ids = [(5, 0, 0)]
                rec.government_payment_id.unlink()
            if rec.logistic_order_id:
                rec.logistic_order_id.unlink()
            rec.message_post(body=_("Ticket is in draft by %s" % self.env.user.name))

    @api.onchange('service_type_ids')
    def _onchange_service_type_id(self):
        if self.service_type_ids:
            self.include_payment = self.service_type_ids[0].including_payment
        if all(service.including_payment for service in self.service_type_ids):
            self.include_payment = True
        elif all(not service.including_payment for service in self.service_type_ids):
            self.include_payment = False
        elif any(service.including_payment for service in self.service_type_ids) and any(
                not service.including_payment for service in self.service_type_ids):
            raise ValidationError(
                _("You can't select mixed(Include Payment and Without Payment ) services on the same ticket."))
        else:
            self.include_payment = False

    def _validate_closing(self):
        if self.ticket_type_id.is_operation and self.include_payment:
            if self.government_payment_id and self.government_payment_id.state != 'validate':
                raise ValidationError(
                    _("Please check the payment & the operation order with the operation responsible."))
        elif self.logistic_order_id and self.logistic_order_id.state != 'done':
            raise ValidationError(_("Please check the logistic order with the logistic responsible."))

    def action_view_logistic_order(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Logistic Orders',
            'res_model': 'logistic.order',
            'view_mode': 'form',
            'res_id': self.logistic_order_id.id,
            'domain': [('helpdesk_ticket_id', '=', self.id)],
            'target': 'current',
        }

    @api.constrains('date_from', 'date_to')
    def _check_from_to(self):
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValidationError(_("Check Out Date should be after the Check In Date."))

    def view_government_payment(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Government Payment',
            'res_model': 'government.payment',
            'view_mode': 'tree',
            'view_id': self.env.ref('scs_operation.government_payment_ticket_tree_view').id,
            'res_id': self.government_payment_id.id,
            'context': {
                'create': False,
                'edite': False,
            },
            'target': 'current',
            'domain': [('id', '=', self.government_payment_id.id)]
        }

    @api.constrains('service_type_ids')
    def _check_service_type_ids(self):
        if len(self.service_type_ids.ids) > 1 and self.ticket_type_id.is_logistics:
            raise ValidationError(_("You can't select more than one service type for logistics ticket."))

    # constraint to prevent duplication of same employee same services on the same month
    @api.constrains('employee_id', 'service_type_ids')
    def _check_employee_service_type(self):
        for rec in self:
            if rec.employee_id and rec.service_type_ids:
                for service in rec.service_type_ids:
                    if self.search_count(
                            [('employee_id', '=', rec.employee_id.id), ('service_type_ids', 'in', service.id),
                             ('stage_id.is_closed', '=', False),
                             ('id', '!=', rec.id)]) and not rec.ticket_type_id.is_logistics:
                        raise ValidationError(
                            _("You can't create a ticket for the same employee"
                              " with the same service type in the same month."))
                    elif not self.service_type_ids:
                        raise ValidationError(_("Please select the Service Category and service type for your ticket."))
                    elif not self.ticket_type_id:
                        raise ValidationError(_("Please select the service Category for your ticket."))

    def set_government_payment_on_progress(self):
        if self.government_payment_id.state == 'on_hold':
            # Check if all payment lines are paid
            all_lines_paid = all(
                line.payment_state in ['paid', 'validated'] for line in self.government_payment_id.payment_line_ids)

            # Set the appropriate state based on payment lines status
            if all_lines_paid and self.government_payment_id.payment_type != 'no_payment':
                target_state = 'paid'
            else:
                target_state = 'approve'

            self.government_payment_id.write({
                'state': target_state,
                'previous_state': False  # Clear the previous state field
            })

            self.government_payment_id.activity_schedule(
                'mail.mail_activity_data_todo',
                summary=_('Government Payment In Progress'),
                note=_('Dear %s, The on holding reason has been resolved. '
                       'Payment has been restored to %s state.') % (self.user_id.name, target_state),
                user_id=self.user_id.id
            )

            # Post a message in the chatter
            self.government_payment_id.message_post(
                body=_('Payment has been proceeded from on-hold state by %s and set to %s state')
                     % (self.env.user.name, target_state),
                subtype_id=self.env.ref('mail.mt_note').id
            )

        for line in self.government_payment_id.payment_line_ids:
            if line.payment_reference and line.payment_reference.state == 'on_hold':
                line.payment_reference.sudo().write({'state': 'draft'})
                line.payment_reference.sudo().activity_schedule(
                    'mail.mail_activity_data_todo',
                    summary=_('Issue with Payment resolved'),
                    note=_('Dears accounting team, The issue with the payment has been resolved. '
                           'Please proceed with the Payment.'),
                )
        self.stage_id = self.env["helpdesk.stage"].search(
            [("in_progress", "=", True)], limit=1
        ).id

    @api.depends('government_payment_id', 'logistic_order_id')
    def _compute_request_state(self):
        for rec in self:
            if rec.government_payment_id:
                if rec.government_payment_id.state == 'draft':
                    rec.request_state = 'not_started'
                elif rec.government_payment_id.state in ['submit', 'approve']:
                    rec.request_state = 'in_progress'
                elif rec.government_payment_id.state == 'validate':
                    rec.request_state = 'done'
                elif rec.government_payment_id.state == 'reject':
                    rec.request_state = 'rejected'
                elif rec.government_payment_id.state == 'on_hold':
                    rec.request_state = 'on_hold'
            elif rec.logistic_order_id:
                if rec.logistic_order_id.state == 'draft':
                    rec.request_state = 'not_started'
                elif rec.logistic_order_id.state in ['bidding', 'approval', 'in_progress']:
                    rec.request_state = 'in_progress'
                elif rec.logistic_order_id.state == 'done':
                    rec.request_state = 'done'
            else:
                rec.request_state = 'not_started'

    def unlink(self):
        for rec in self:
            draft_stage = self.env["helpdesk.stage"].search(
                [("is_draft", "=", True)], limit=1
            )
            print(draft_stage, rec.stage_id)
            if rec.stage_id.id != draft_stage.id:
                raise ValidationError(_("You can't delete a ticket in progress."))
        return super(Helpdesk, self).unlink()

    @api.depends('location_country_id')
    def _compute_available_departure_location(self):
        for record in self:
            if record.location_country_id:
                record.available_departure_location = self.env['airport.airport'].search([('country_id', '=',
                                                                                           record.location_country_id
                                                                                           .id)]).ids
            else:
                record.available_departure_location = False

    @api.depends('destination_country_id')
    def _compute_available_destination_location(self):
        for record in self:
            if record.destination_country_id:
                record.available_destination_location = self.env['airport.airport'].search([('country_id', '=',
                                                                                             record
                                                                                             .destination_country_id.
                                                                                             id)]).ids
            else:
                record.available_destination_location = False

    @api.onchange('flight_direction')
    def _onchange_flight_direction(self):
        if self.flight_direction == 'one_way':
            self.return_date = False

    @api.constrains('departure_date', 'return_date')
    def _check_dates(self):
        if (self.departure_date and self.return_date and
                (self.departure_date > self.return_date or self.departure_date == fields.Date.today())):
            raise ValidationError(_("Return Date should be after the Departure Date."))

    @api.constrains('departure_airport_id', 'destination_airport_id')
    def _check_airports(self):
        if (self.departure_airport_id and self.destination_airport_id
                and self.departure_airport_id == self.destination_airport_id):
            raise ValidationError(_("Departure Airport and Destination Airport should be different."))

    @api.onchange('required_insurance_action')
    def _onchange_required_insurance_action(self):
        if self.required_insurance_action:
            self.insurance_class_from_id = False
            self.insurance_class_to_id = False

    @api.onchange('insurance_type')
    def _onchange_insurance_type(self):
        if self.insurance_type == 'family':
            self.family_member_ids = False
            # Set employee's insurance class as default for family insurance
            if self.employee_id and self.employee_id.insurance_class_id:
                self.insurance_class_from_id = self.employee_id.insurance_class_id.id
                self.insurance_class_to_id = self.employee_id.insurance_class_id.id
            else:
                self.insurance_class_from_id = False
                self.insurance_class_to_id = False
            self.required_insurance_action = False
