import base64
import uuid

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class LogisticOrder(models.Model):
    _name = 'logistic.order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Logistic Order including the insurance and the flight hotel tickets'
    _order = 'id desc'

    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, index=True,
                       default=lambda self: _('New'))
    selection_link = fields.Char(string='Selection Link', readonly=True, copy=False,
                                 help='URL for accessing the selection page')
    request_date = fields.Date(string='Request Date', required=True, default=fields.Date.context_today, readonly=True)
    order_type = fields.Selection([('flight', 'Flight'), ('hotel', 'Hotel'), ('insurance', 'Insurance'),
                                   ('pick_up_drop_off', 'Pick-Up / Drop-Off'), ('courier', 'Courier'), ],
                                  string='Order Type', required=True, default='flight', readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, readonly=True)
    project_id = fields.Many2one('client.project', string='Project', related='employee_id.project_id', readonly=True,
                                 required=True)

    # Employee Details
    file_no = fields.Char(string='File No', related='employee_id.registration_number', readonly=True)
    iqama_no = fields.Char(string='Iqama No', compute='_compute_iqama_no', readonly=True, store=True)
    visa_expire = fields.Date(string='Iqama Expiry', related='employee_id.visa_expire', readonly=True)
    passport_no = fields.Char(string='Passport No', related='employee_id.passport_id', readonly=True)
    nationality_id = fields.Many2one('res.country', string='Nationality', related='employee_id.country_id',
                                     readonly=True)
    birthday = fields.Date(string='Date of Birth', related='employee_id.birthday', readonly=True)
    gender = fields.Selection(related='employee_id.gender', readonly=True)
    marital = fields.Selection(related='employee_id.marital', readonly=True)
    mobile_phone = fields.Char(string='Mobile', related='employee_id.mobile_phone', readonly=True)
    work_email = fields.Char(string='Work Email', related='employee_id.work_email', readonly=True)
    department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id',
                                    readonly=True)
    job_id = fields.Many2one('hr.job', string='Job Position', related='employee_id.job_id', readonly=True)
    location_country_id = fields.Many2one('res.country', string='Departure Country')
    departure_airport_id = fields.Many2one('airport.airport', string='Departure Airport')
    departure_city = fields.Char(string='Departure City')

    destination_country_id = fields.Many2one('res.country', string='Destination Country')
    destination_airport_id = fields.Many2one('airport.airport', string='Destination Airport')
    destination_city = fields.Char(string='Destination City')

    departure_date = fields.Date(string='Departure Date')
    return_date = fields.Date(string='Return Date')
    hotel_partner_id = fields.Many2one('res.partner', string='Hotel', domain=[('vendor_type', '=', 'hotel')])
    available_address_ids = fields.Many2many('hotel.location', string='Available Hotel Address',
                                             compute='_compute_available_address_ids')
    hotel_location_id = fields.Many2one('hotel.location', string='Hotel Address')
    date_from = fields.Date(string='Check In')
    date_to = fields.Date(string='Check Out')
    duration = fields.Integer(string='Duration', compute='_compute_duration', store=True)
    hotel_phone = fields.Char(string='Hotel Phone', related='hotel_partner_id.phone')
    insurance = fields.Boolean(string='Insurance Issuing')
    insurance_partner_id = fields.Many2one('res.partner', string='Insurance Company',
                                           domain="[('supplier_rank', '>', 0)]")
    insurance_type = fields.Selection([
        ('employee', 'Employee'),
        ('family', 'Family'),
        ('both', 'Both Employee & Family'),
    ], string='Insurance Type')
    flight_type = fields.Selection([
        ('employee', 'Employee'),
        ('family', 'Family'),
        ('both', 'Both'),
    ], string='Flight Type')
    insurance_policy_id = fields.Many2one('insurance.policy', string='Insurance Policy',
                                          domain=[('state', '=', 'active')],
                                          help='Select an active insurance policy for this order')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('bidding', 'Bidding'),
        ('selection', 'Selection'),
        ('rejected', 'Rejected'),
        ('approval', 'Waiting Approval'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'cancelled')
    ], string='Status', readonly=True, copy=False, index=True, tracking=True, default='draft')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency', related='company_id.currency_id', readonly=True)
    daily_cost = fields.Monetary(string='Daily Cost', currency_field='currency_id')
    total_amount = fields.Monetary(string='Total Amount', compute='_compute_total_amount', store=True,
                                   currency_field='currency_id')
    notes = fields.Text(string='Notes')

    # New fields for logistic order lines
    logistic_order_line_ids = fields.One2many('logistic.order.line', 'logistic_order_id', string='Logistic Order Lines')
    employee_insurance_cost = fields.Monetary(string='Employee Insurance Cost', currency_field='currency_id')
    employee_passport_copy = fields.Many2many('ir.attachment', string='Employee Passport Copy',
                                              related='employee_id.passport_copy',
                                              readonly=True,
                                              relation="rel_employee_passport_copy")
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    flight_ticket = fields.Many2many('ir.attachment', string='Flight Ticket', relation='rel_flight_ticket')
    flight_type = fields.Selection([
        ('employee', 'Employee'),
        ('family', 'Family'),
    ], string='Flight Type', readonly=True)
    rejection_reason = fields.Text(string='Rejection Reason')
    flight_direction = fields.Selection([
        ('one_way', 'One Way'),
        ('round_trip', 'Round Trip'),
    ], string='Flight Direction')
    flight_bidding_ids = fields.One2many('flight.bidding',
                                         'logistic_order_id', string='Flight Bidding')
    display_approval_buttons = fields.Boolean(compute='_compute_display_approval_button', default=False)
    vendor_id = fields.Many2one('res.partner', string='Vendor')
    available_vendors = fields.Many2many('res.partner', string='Available Vendors',
                                         compute='_compute_available_vendors')
    access_token = fields.Char('Security Token', copy=False)
    preferred_travel_time = fields.Selection([
        ('morning', 'Morning (6:00 AM - 12:00 PM)'),
        ('afternoon', 'Afternoon (12:00 PM - 6:00 PM)'),
        ('evening', 'Evening (6:00 PM - 12:00 AM)'),
        ('night', 'Night (12:00 AM - 6:00 AM)')
    ], string='Preferred Travel Time',
        help='Select the preferred time of day for travel')
    bill_count = fields.Integer(string='Bill Count', compute='_compute_bill_count')
    total_insurance_cost = fields.Monetary(string='Total Insurance Cost', currency_field='currency_id',
                                           compute='_compute_total_insurance_cost', store=True,
                                           help='Total insurance cost for all passengers')
    helpdesk_ticket_id = fields.Many2one('helpdesk.ticket', string='Helpdesk Ticket', readonly=True, copy=False)

    # Insurance class related fields
    insurance_class = fields.Many2one('insurance.class', string='Insurance Class', readonly=True, copy=False,
                                      help='Insurance coverage class for this order')
    insurance_required_action = fields.Selection([
        ('addition', 'Addition'),
        ('deletion', 'Deletion'),
        ('update', 'Update'),
        ('downgrade', 'Downgrade'),
        ('upgrade', 'Upgrade'),
    ], string='Required Action', readonly=True, copy=False,
        help='Required action for insurance policy')
    insurance_class_from = fields.Many2one('insurance.class', string='From Class', readonly=True, copy=False,
                                           help='Original insurance class for upgrade/downgrade actions')
    insurance_class_to = fields.Many2one('insurance.class', string='To Class', readonly=True, copy=False,
                                         help='Target insurance class for upgrade/downgrade actions')
    auto_create_insurance_lines = fields.Boolean(string='Auto Create Insurance Lines',
                                                 default=True,
                                                 help='Automatically create insurance lines when order is approved')
    insurance_action_summary = fields.Text(string='Insurance Action Summary',
                                           compute='_compute_insurance_summary')
    update_note = fields.Text(string='Update Note', readonly='True')
    ticket_number = fields.Char()
    driver_name = fields.Char()
    driver_number = fields.Char()
    pick_up_drop_off_cost = fields.Monetary()
    courier_cost = fields.Monetary()
    courier_no = fields.Char()

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
        relation='rel_document_ids',
        copy=False
    )
    effective_date = fields.Date(string="Effective Date")
    sponsor_no = fields.Char(string="Sponsor No.")

    @api.depends('required_document_ids')
    def _compute_document_count(self):
        for rec in self:
            if rec.required_document_ids:
                rec.required_document_count = len(rec.required_document_ids)
            else:
                rec.required_document_count = 0

    @api.depends('logistic_order_line_ids', 'insurance_required_action', 'insurance_class_from', 'insurance_class_to')
    def _compute_insurance_summary(self):
        for order in self:
            if order.order_type != 'insurance':
                order.insurance_action_summary = False
                continue

            summary_lines = []

            if order.insurance_required_action:
                action_desc = {
                    'addition': 'Adding new insurance coverage',
                    'deletion': 'Removing insurance coverage',
                    'update': 'Updating insurance details',
                    'upgrade': f'Upgrading from Class {order.insurance_class_from.name if order.insurance_class_from else "?"} to Class {order.insurance_class_to.name if order.insurance_class_to else "?"}',
                    'downgrade': f'Downgrading from Class {order.insurance_class_from.name if order.insurance_class_from else "?"} to Class {order.insurance_class_to.name if order.insurance_class_to else "?"}'
                }
                summary_lines.append(
                    f"Action: {action_desc.get(order.insurance_required_action, order.insurance_required_action)}")

            if order.logistic_order_line_ids:
                summary_lines.append(f"Passengers: {len(order.logistic_order_line_ids)}")
                for line in order.logistic_order_line_ids:
                    passenger_info = f"- {line.name} ({line.passenger_type}): Class {line.insurance_class.name if line.insurance_class else 'Not Set'}"
                    if line.insurance_cost:
                        passenger_info += f" - {line.insurance_cost} SAR"
                    summary_lines.append(passenger_info)

            order.insurance_action_summary = '\n'.join(summary_lines) if summary_lines else False

    def _validate_insurance_order(self):
        """Validate insurance order before approval"""
        self.ensure_one()

        if self.order_type != 'insurance':
            return True

        errors = []

        # Check if insurance policy is selected
        if not self.insurance_policy_id:
            errors.append("Insurance Policy must be selected for insurance orders.")

        # Check if order lines have insurance classes
        for line in self.logistic_order_line_ids:
            if not line.insurance_class:
                errors.append(f"Insurance class is required for passenger {line.name}")

        # Check for required action type
        if not self.insurance_required_action:
            errors.append("Insurance action type is required.")

        # For upgrade/downgrade, check if from/to classes are specified
        if self.insurance_required_action in ['upgrade', 'downgrade']:
            if not self.insurance_class_from or not self.insurance_class_to:
                errors.append("From and To insurance classes are required for upgrade/downgrade actions.")

        if errors:
            raise ValidationError('\n'.join(errors))

        return True

    def _process_employee_insurance(self):
        for rec in self:
            if rec.order_type == 'insurance':
                # Selected family member IDs from the order
                selected_family_ids = rec.logistic_order_line_ids.mapped('family_member_id.id')

                # Get the employee directly
                employee = rec.employee_id

                if employee:
                    # Case for Add, Upgrade, Delete
                    if rec.insurance_required_action in ['addition', 'upgrade', 'downgrade']:
                        if rec.insurance_type in ['employee', 'both']:
                            employee.insurance_class_id = rec.insurance_class_to.id
                            employee.sponsor_no = rec.sponsor_no

                        if rec.insurance_type in ['family', 'both']:
                            for fam in employee.family_ids:
                                if fam.id in selected_family_ids:
                                    fam.insurance_class_id = rec.insurance_class_to.id
                                    fam.sponsor_no = rec.sponsor_no

                    # Case for Delete
                    if rec.insurance_required_action == 'deletion':
                        if rec.insurance_type in ['employee', 'both']:
                            employee.insurance_class_id = False
                            employee.sponsor_no = False

                        if rec.insurance_type in ['family', 'both']:
                            for fam in employee.family_ids:
                                if fam.id in selected_family_ids:
                                    fam.insurance_class_id = False
                                    fam.sponsor_no = False

                    # No Case required for Update

    def _process_insurance_addition(self):
        """Process insurance addition"""
        for line in self.logistic_order_line_ids:
            if line.insurance_class:
                vals = {
                    'policy_id': self.insurance_policy_id.id,
                    'employee_id': self.employee_id.id,
                    'passenger_type': line.passenger_type,
                    'family_member_id': line.family_member_id.id if line.family_member_id else False,
                    'insurance_class': line.insurance_class.id,
                    'date_added': fields.Date.context_today(self),
                    'action_type': 'addition',
                    'notes': f'Created from logistic order: {self.name}'
                }

                insurance_line = self.env['employee.insurance.line'].create(vals)
                insurance_line.action_activate()

    def _process_insurance_deletion(self):
        """Process insurance deletion/removal"""
        for line in self.logistic_order_line_ids:
            # Find active insurance lines for this passenger
            domain = [
                ('employee_id', '=', self.employee_id.id),
                ('passenger_type', '=', line.passenger_type),
                ('state', '=', 'active')
            ]

            if line.family_member_id:
                domain.append(('family_member_id', '=', line.family_member_id.id))

            # If a specific policy is selected, filter by it
            if self.insurance_policy_id:
                domain.append(('policy_id', '=', self.insurance_policy_id.id))

            active_lines = self.env['employee.insurance.line'].search(domain)

            for insurance_line in active_lines:
                insurance_line.date_removed = fields.Date.context_today(self)
                insurance_line.action_end_coverage()

    def _process_insurance_change(self):
        """Process insurance class change (upgrade/downgrade/update)"""
        # First, end current coverage
        self._process_insurance_deletion()

        # Then, add new coverage with new class
        self._process_insurance_addition()

    def _process_insurance_order(self):
        """Process insurance order based on action type"""
        self.ensure_one()

        if self.order_type == 'insurance':
            if self.insurance_required_action == 'addition':
                self._process_insurance_addition()
            elif self.insurance_required_action == 'deletion':
                self._process_insurance_deletion()
            elif self.insurance_required_action in ['upgrade', 'downgrade', 'update']:
                self._process_insurance_change()

            # Log the processing
            self.message_post(
                body=f"Insurance order processed successfully. Action: {self.insurance_required_action}",
                subject="Insurance Order Processed"
            )

    @api.depends('hotel_partner_id')
    def _compute_available_address_ids(self):
        for record in self:
            if record.hotel_partner_id:
                record.available_address_ids = self.env['hotel.location'].search(
                    [('partner_id', '=', record.hotel_partner_id.id)])
            else:
                record.available_address_ids = self.env['hotel.location'].search([])

    @api.depends('order_type')
    def _compute_available_vendors(self):
        for record in self:
            if record.order_type == 'insurance':
                record.available_vendors = self.env['res.partner'].search([('vendor_type', '=', 'insurance')])
            elif record.order_type == 'flight':
                record.available_vendors = self.env['res.partner'].search([('vendor_type', '=', 'flight')])
            elif record.order_type == 'hotel':
                record.available_vendors = self.env['res.partner'].search([('vendor_type', '=', 'hotel')])
            elif record.order_type == 'courier':
                record.available_vendors = self.env['res.partner'].search([('vendor_type', '=', 'courier')])
            else:
                record.available_vendors = self.env['res.partner'].search([])

    def _compute_display_approval_button(self):
        for record in self:
            if any(record.flight_bidding_ids.filtered(lambda x: x.state == 'draft')):
                record.display_approval_buttons = False
            else:
                record.display_approval_buttons = True

    @api.onchange('order_type')
    def _onchange_order_type(self):
        if self.order_type == 'flight':
            self.insurance = False
        if self.order_type == 'insurance':
            self.flight_type = False

    @api.onchange('insurance_policy_id')
    def _onchange_insurance_policy_id(self):
        if self.insurance_policy_id and self.insurance_policy_id.insurance_company_id:
            self.insurance_partner_id = self.insurance_policy_id.insurance_company_id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Generate sequence for new orders
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('logistic_order') or _('New')

            # Handle string values for insurance class fields (backward compatibility)
            for field_name in ['insurance_class', 'insurance_class_from', 'insurance_class_to']:
                if field_name in vals and isinstance(vals[field_name], str):
                    class_code = vals[field_name].lower()
                    insurance_class = self.env['insurance.class'].search([('code', '=', class_code)], limit=1)
                    if insurance_class:
                        vals[field_name] = insurance_class.id
                        _logger.info(
                            f"Converted string value '{class_code}' to insurance.class ID {insurance_class.id}")
                    else:
                        _logger.warning(
                            f"Could not find insurance.class with code '{class_code}', setting field {field_name} to False")
                        vals[field_name] = False

        return super(LogisticOrder, self).create(vals_list)

    def write(self, vals):
        """Override write to handle attachment access rights and backward compatibility"""
        # Handle string values for insurance class fields (backward compatibility)
        for field in ['insurance_class', 'insurance_class_from', 'insurance_class_to']:
            if field in vals and isinstance(vals[field], str):
                class_code = vals[field].lower()
                insurance_class = self.env['insurance.class'].search([('code', '=', class_code)], limit=1)
                if insurance_class:
                    vals[field] = insurance_class.id
                    _logger.info(f"Converted string value '{class_code}' to insurance.class ID {insurance_class.id}")
                else:
                    _logger.warning(
                        f"Could not find insurance.class with code '{class_code}', setting field {field} to False")
                    vals[field] = False

        if 'flight_ticket' in vals:
            new_attachments = []
            commands = vals['flight_ticket']
            for command in commands:
                if command[0] == 6:  # (6, 0, [ids]) - Replace with ids
                    attach_ids = command[2]
                elif command[0] == 4:  # (4, id, 0) - Add an id
                    attach_ids = [command[1]]
                elif command[0] == 5:  # (5, 0, 0) - Remove all
                    continue
                elif command[0] == 1:  # (1, id, values) - Update
                    attach_ids = [command[1]]
                else:  # Other commands like (2, id, 0) - Remove, (3, id, 0) - Unlink
                    continue

                for attach_id in attach_ids:
                    attachment = self.env['ir.attachment'].browse(attach_id)
                    if attachment.exists():
                        # Create a copy of the attachment with proper access rights
                        new_attachment = self.env['ir.attachment'].create({
                            'name': attachment.name,
                            'type': attachment.type,
                            'datas': attachment.datas,
                            'mimetype': attachment.mimetype,
                            'res_model': self._name,
                            'res_id': self.id,
                            'public': True,  # Make it accessible to all users who can access the logistic order
                        })
                        new_attachments.append(new_attachment.id)
            if new_attachments:
                vals['flight_ticket'] = [(6, 0, new_attachments)]
        return super(LogisticOrder, self).write(vals)

    @api.depends('daily_cost', 'date_from', 'date_to', 'order_type',
                 'employee_insurance_cost',
                 'flight_bidding_ids.price', 'flight_bidding_ids.price', 'flight_bidding_ids.state')
    def _compute_total_amount(self):
        for order in self:
            if order.order_type == 'hotel' and order.daily_cost and order.date_from and order.date_to:
                order.total_amount = order.daily_cost * (order.date_to - order.date_from).days
            elif (order.order_type in ['insurance',
                                       'flight'] and order.insurance_type != 'employee' and
                  order.flight_bidding_ids):
                order.total_amount = sum(
                    order.flight_bidding_ids.filtered(lambda x: x.state == 'confirm').mapped('price'))
                order.total_amount = sum(
                    order.flight_bidding_ids.filtered(lambda x: x.state == 'confirm').mapped('price'))
            elif order.order_type == 'insurance' and order.insurance_type == 'employee':
                order.total_amount = order.employee_insurance_cost
            else:
                order.total_amount = 0

    @api.depends('logistic_order_line_ids.insurance_cost', 'employee_insurance_cost')
    def _compute_total_insurance_cost(self):
        """Compute the total insurance cost from all order lines"""
        for order in self:
            if order.order_type == 'insurance':
                order.total_insurance_cost = sum(order.logistic_order_line_ids.mapped('insurance_cost')) + order.employee_insurance_cost
            else:
                order.total_insurance_cost = 0.0

    @api.constrains('departure_date', 'return_date')
    def _check_dates(self):
        for order in self:
            if order.departure_date and order.return_date and order.departure_date > order.return_date:
                raise ValidationError(_("The return date must be after the departure date."))

    @api.depends('date_from', 'date_to')
    def _compute_duration(self):
        for order in self:
            if order.date_from and order.date_to:
                order.duration = (order.date_to - order.date_from).days + 1
            else:
                order.duration = 0

    def action_confirm(self):
        for record in self:
            if record.order_type == 'pick_up_drop_off' and record.pick_up_drop_off_cost == 0:
                raise ValidationError(_("Please add a cost for Pick-Ip / Drop-Off!"))

            if record.order_type == 'courier' and record.courier_cost == 0:
                raise ValidationError(_("Please add a cost for Courier!"))

            if record.order_type == 'flight':
                record.state = 'bidding'
            else:
                record.state = 'approval'
            self._validate_confirm()
            self.activity_update()
            if self.order_type == 'flight':
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                self.selection_link = base_url + self.action_generate_portal_url()['url']
                for user in self.env.ref('scs_operation.my_flight_user').users:
                    self.activity_schedule(
                        'mail.mail_activity_data_todo',
                        user_id=user.id,
                        note=_("Dear %s Logistic Order %s requires your approval") % (user.name, self.name),
                    )
            else:
                for user in self.env.ref('scs_operation.group_insurance_user').users:
                    self.activity_schedule(
                        'mail.mail_activity_data_todo',
                        user_id=user.id,
                        note=_("Dear %s Logistic Order %s requires your action.") % (user.name, self.name)
                    )

    def action_in_progress(self):
        self.ensure_one()
        self.write({'state': 'in_progress'})
        self.activity_update()
        for user in self.env.ref('scs_operation.group_insurance_user').users:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=user.id,
                note=_("Dear %s Logistic Order %s has been Approved and ready to be processed") % (
                    user.name, self.name),
            )

    def _find_mail_template(self):
        """Get the appropriate mail template based on the order type"""
        self.ensure_one()
        if self.order_type == 'flight':
            template = self.env.ref('scs_operation.email_template_flight_selection', raise_if_not_found=False)
        elif self.order_type == 'insurance':
            # Use a specific template for insurance selection if needed
            # For now, use the generic flight selection template
            template = self.env.ref('scs_operation.email_template_flight_selection', raise_if_not_found=False)
        else:
            # For hotel or other order types
            template = self.env.ref('scs_operation.email_template_flight_selection', raise_if_not_found=False)
        return template

    def action_send_for_selection(self):
        """ Opens a wizard to compose an email, with relevant mail template loaded by default """
        # check for zero values 
        if any(line.price == 0.0 for line in self.flight_bidding_ids):
            raise ValidationError("The total price of the order lines must be greater than zero.")
        if not self.flight_bidding_ids:
            raise ValidationError("Please add at least one flight bidding line.")
        self.ensure_one()
        lang = self.env.context.get('lang')
        mail_template = self._find_mail_template()
        if mail_template and mail_template.lang:
            lang = mail_template._render_lang(self.ids)[self.id]

        ctx = {
            'default_model': 'logistic.order',
            'default_res_ids': self.ids,
            'default_template_id': mail_template.id if mail_template else None,
            'default_composition_mode': 'comment',
            'mark_lo_as_sent': True,
            'default_email_layout_xmlid': 'mail.mail_notification_layout_with_responsible_signature',
            'force_email': True,
            'model_description': 'Logistic Order',
            'custom_layout': 'mail.mail_notification_light',
            'employee_email': self.employee_id.work_email or self.employee_id.personal_email,
            'employee_name': self.employee_id.name,
            'lang': lang,
            'company_id': self.company_id.id,
            'selection_link': self.selection_link
        }

        # Generate PDF report for flight orders
        if self.order_type == 'flight':
            try:
                report = self.env.ref('scs_operation.action_report_flight_logistics')
                if report:
                    pdf_content, _ = report._render_qweb_pdf(self.id)
                    attachment = self.env['ir.attachment'].create({
                        'name': f'Flight Logistics Order - {self.name}.pdf',
                        'type': 'binary',
                        'datas': base64.b64encode(pdf_content),
                        'res_model': self._name,
                        'res_id': self.id,
                        'mimetype': 'application/pdf'
                    })
                    ctx['default_attachment_ids'] = [(6, 0, [attachment.id])]
            except Exception as e:
                _logger.error("Error generating flight logistics report: %s", str(e))

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    def action_to_bidding(self):
        for record in self:
            record.state = 'bidding'

    def action_to_selection(self):
        for record in self:
            record.state = 'selection'
            template = self.env.ref('scs_operation.email_template_flight_selection')
            if template:
                template.send_mail(record.id, force_send=True)

    def action_to_approval(self):
        for record in self:
            record.state = 'approval'

    def action_approve(self):
        for record in self:
            record.state = 'in_progress'

    def action_approve_operation_manager(self):
        self.ensure_one()
        self.write({'state': 'in_progress'})
        self.activity_update()
        if self.order_type == 'flight':
            template = self.env.ref('scs_operation.email_template_flight_logistics')
            if template:
                template.send_mail(self.id, force_send=True)
        for user in self.env.ref('scs_operation.group_insurance_user').users:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=user.id,
                note=_("Dear %s Logistic Order %s has been Approved and ready to be processed") % (
                    user.name, self.name),
            )

    def _find_completion_mail_template(self):
        """ Find the email template for completion notification based on order type """
        self.ensure_one()
        if self.order_type == 'flight':
            return self.env.ref('scs_operation.email_template_flight_completion')
        elif self.order_type == 'insurance':
            return self.env.ref('scs_operation.email_template_insurance_completion', raise_if_not_found=False)
        elif self.order_type == 'hotel':
            return self.env.ref('scs_operation.email_template_hotel_completion', raise_if_not_found=False)
        elif self.order_type == 'pick_up_drop_off':
            return self.env.ref('scs_operation.email_template_pick_up_drop_off', raise_if_not_found=False)
        elif self.order_type == 'courier':
            return self.env.ref('scs_operation.email_template_courier', raise_if_not_found=False)
        else:
            raise UserError(_("Completion email template not found for order type %s") % self.order_type)

    def action_done(self):
        """ 
        Opens a wizard to compose an email for completion notification with flight tickets attached 
        and automatically closes the associated helpdesk ticket if present.
        """
        self.ensure_one()
        if not self.flight_ticket and self.order_type == 'flight':
            raise UserError(_("Please upload flight tickets before marking the order as done."))

        # Auto-close associated helpdesk ticket if it exists
        if self.helpdesk_ticket_id:
            # Find a closed stage for the ticket
            closed_stage = self.env['helpdesk.stage'].search([('is_closed', '=', True)], limit=1)
            if closed_stage:
                # Check if the ticket is already in a closed stage
                if self.helpdesk_ticket_id.stage_id.id != closed_stage.id:
                    # Update the ticket stage to closed
                    self.helpdesk_ticket_id.write({
                        'stage_id': closed_stage.id
                    })

                    # Log a message in the ticket for traceability
                    self.helpdesk_ticket_id.message_post(
                        body=_('Ticket Closed - Logistic Order Completed') + '<br/>' +
                             _('This ticket has been automatically closed because the associated logistic order %s has been marked as done.') % self.name,
                        subject=_('Ticket Closed - Logistic Order Completed'),
                        message_type='comment'
                    )

                    _logger.info('Helpdesk ticket %s automatically closed due to completion of logistic order %s',
                                 self.helpdesk_ticket_id.name, self.name)

        lang = self.env.context.get('lang')
        mail_template = self._find_completion_mail_template()
        if mail_template:
            lang = mail_template._render_lang(self.ids)[self.id]

        self._process_employee_insurance()
        # Prepare the context for email composition
        ctx = {
            'default_model': 'logistic.order',
            'default_res_ids': self.ids,
            'default_use_template': bool(mail_template),
            'default_template_id': mail_template.id if mail_template else None,
            'default_composition_mode': 'comment',
            'force_email': True,
            'model_description': 'Logistic Order',
            'custom_layout': 'mail.mail_notification_light',
            'employee_email': self.employee_id.work_email or self.employee_id.personal_email,
            'employee_name': self.employee_id.name,
            'lang': lang,
            'company_name': self.company_id.name,
            'default_attachment_ids': [(6, 0, self.flight_ticket.ids)] if self.flight_ticket else [],
            'mark_logistic_done': True,  # Custom context key to identify this is from logistic order done action
        }

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'target': 'new',
            'context': ctx,
        }

    def action_reject_operation_manager(self):
        self.ensure_one()
        self.activity_update()
        return {
            'name': 'Reject Logistic Order',
            'type': 'ir.actions.act_window',
            'res_model': 'rejection.reason.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_id': self.id,
                'active_model': self._name
            }
        }

    def action_cancel(self):
        self.ensure_one()
        self.write({'state': 'cancel'})
        self.activity_update()

    def action_draft(self):
        self.ensure_one()
        self.write({'state': 'draft'})
        self.flight_bidding_ids.state = 'draft'
        self.activity_update()

    def _validate_confirm(self):
        self.ensure_one()
        if not self.employee_id:
            raise UserError(_("Employee is required."))
        if self.order_type == 'flight' and not self.vendor_id:
            raise UserError(_("Vendor is required for this order."))
        if self.order_type == 'hotel' and not self.hotel_partner_id:
            raise UserError(_("Hotel is required for this order."))
        if self.order_type == 'insurance' and self.insurance_type == 'employee' and not self.employee_insurance_cost and self.insurance_required_action != 'update':
            raise UserError(_("Employee insurance cost cannot be zero for employee insurance orders."))

    def _create_operation_manager_activity(self):
        operation_manager = self.env.ref('scs_operation.group_operation_admin').users[:1]
        if operation_manager:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=operation_manager.id,
                note=_("Logistic Order %s requires your approval") % self.name,
            )

    def activity_update(self):
        for record in self:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=self.env.user.id,
                note=_("Logistic Order %s status changed to %s") % (record.name, record.state.capitalize()),
            )

    @api.ondelete(at_uninstall=False)
    def _unlink_except_draft_or_cancel(self):
        for record in self:
            if record.state not in ('draft', 'cancel'):
                raise UserError(_("You can only delete draft or cancelled orders."))

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.name} - {record.employee_id.name} ({record.order_type.capitalize()})"
            result.append((record.id, name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('employee_id.name', operator, name)]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)

    def _generate_access_token(self):
        for record in self:
            record.access_token = uuid.uuid4().hex

    def action_generate_portal_url(self):
        """Generate a portal URL for bidding selection"""
        self.ensure_one()
        if not self.access_token:
            self._generate_access_token()
        return {
            'type': 'ir.actions.act_url',
            'url': '/my/flight-bidding/%s?access_token=%s' % (self.id, self.access_token),
            'target': 'self',
        }

    def get_base_url(self):
        """ Get the base URL for the current record """
        self.ensure_one()
        if self.selection_link:
            return self.selection_link
        else:
            # Return the default base URL if selection_link is not set
            return self.env['ir.config_parameter'].sudo().get_param('web.base.url', '')

    def _prepare_account_move_vals(self):
        """Prepare the values for creating the vendor bill."""
        self.ensure_one()

        # Determine the correct partner based on order type
        partner_id = False
        if self.vendor_id:
            partner_id = self.vendor_id.id
        elif self.order_type == 'hotel' and self.hotel_partner_id:
            partner_id = self.hotel_partner_id.id
        elif self.order_type == 'insurance' and self.insurance_partner_id:
            partner_id = self.insurance_partner_id.id

        if not partner_id:
            raise UserError(_('Please select a vendor/partner for this %s order.') % self.order_type)

        # Get payment terms
        payment_term_id = False
        partner = self.env['res.partner'].browse(partner_id)
        if partner and partner.property_supplier_payment_term_id:
            payment_term_id = partner.property_supplier_payment_term_id.id

        return {
            'move_type': 'in_invoice',
            'partner_id': partner_id,
            'invoice_date': fields.Date.context_today(self),
            'ref': self.name,
            'currency_id': self.currency_id.id,
            'invoice_payment_term_id': payment_term_id,
            'company_id': self.company_id.id,
            'logistic_order_id': self.id,
        }

    def _prepare_account_move_line_vals(self, move):
        """Prepare the values for creating the vendor bill line."""
        self.ensure_one()

        # Get the appropriate product based on order type
        product = self._get_service_product()
        if not product:
            raise UserError(
                _('No service product found for %s orders. Please contact administrator.') % self.order_type)

        # Get the accounts from the product
        accounts = product.product_tmpl_id.get_product_accounts()
        if not accounts.get('expense'):
            raise UserError(_('The service product %s does not have an expense account configured.') % product.name)

        # Prepare service description based on order type
        service_descriptions = {
            'flight': f'Flight Booking Service - {self.name}',
            'hotel': f'Hotel Booking Service - {self.name}',
            'insurance': f'Insurance Service - {self.name}',
        }

        # Determine the correct amount to use for the bill
        bill_amount = self.total_amount
        if self.order_type == 'insurance' and self.insurance_type != 'employee' and self.total_insurance_cost:
            bill_amount = self.total_insurance_cost

        return {
            'move_id': move.id,
            'product_id': product.id,
            'name': service_descriptions.get(self.order_type, f'{self.order_type.title()} Service - {self.name}'),
            'product_uom_id': product.uom_id.id,
            'quantity': 1,
            'price_unit': bill_amount,
            'account_id': accounts['expense'].id,
        }

    def _get_service_product(self):
        """Get the appropriate service product based on order type."""
        self.ensure_one()

        # Define product references for each order type
        product_refs = {
            'flight': 'scs_operation.product_flight_booking_service',
            'hotel': 'scs_operation.product_hotel_booking_service',
            'insurance': 'scs_operation.product_insurance_service',
        }

        product_ref = product_refs.get(self.order_type)
        if not product_ref:
            return False

        try:
            return self.env.ref(product_ref)
        except ValueError:
            # If specific product doesn't exist, try to find a generic service product
            _logger.warning(f'Product reference {product_ref} not found for {self.order_type} order')

            # Fallback: try to find a generic service product or create one
            product = self.env['product.product'].search([
                ('name', 'ilike', f'{self.order_type} service'),
                ('type', '=', 'service')
            ], limit=1)

            if not product:
                # Last resort: use flight booking service if it exists
                try:
                    product = self.env.ref('scs_operation.product_flight_booking_service')
                    _logger.warning(f'Using flight booking service product for {self.order_type} order')
                except ValueError:
                    return False

            return product

    def _create_detailed_insurance_bill_lines(self, move):
        """Create detailed bill lines for each passenger in family insurance orders."""
        self.ensure_one()

        # Get the appropriate product for insurance service
        product = self._get_service_product()
        if not product:
            raise UserError(
                _('No service product found for %s orders. Please contact administrator.') % self.order_type)

        # Get the accounts from the product
        accounts = product.product_tmpl_id.get_product_accounts()
        if not accounts.get('expense'):
            raise UserError(_('The service product %s does not have an expense account configured.') % product.name)

        # Create a line for each passenger with insurance cost
        for line in self.logistic_order_line_ids.filtered(lambda l: l.insurance_cost > 0):
            passenger_name = line.name or 'Unknown Passenger'
            insurance_class = line.insurance_class.name or 'Unspecified'

            # Get human-readable passenger type
            passenger_type_mapping = {
                'employee': 'Employee',
                'spouse': 'Spouse',
                'father': 'Father',
                'mother': 'Mother',
                'child': 'Child',
                'family_member': 'Family Member'
            }
            passenger_type = passenger_type_mapping.get(line.passenger_type, line.passenger_type or 'Unknown')

            line_vals = {
                'move_id': move.id,
                'product_id': product.id,
                'name': f'Insurance Service - {passenger_name} ({passenger_type} - Class {insurance_class})',
                'product_uom_id': product.uom_id.id,
                'quantity': 1,
                'price_unit': line.insurance_cost,
                'account_id': accounts['expense'].id,
            }
            self.env['account.move.line'].create(line_vals)

    def generate_vendor_bill(self):
        """Generate vendor bill for the logistic order service."""
        self.ensure_one()

        # Validate required fields based on order type
        if self.order_type == 'flight' and not self.vendor_id:
            raise UserError(_('Please select a vendor first.'))
        elif self.order_type == 'hotel' and not (self.vendor_id or self.hotel_partner_id):
            raise UserError(_('Please select a vendor or hotel partner first.'))
        elif self.order_type == 'insurance' and not (self.vendor_id or self.insurance_partner_id):
            raise UserError(_('Please select a vendor or insurance partner first.'))

        # Check if there's a valid amount to bill
        bill_amount = self.total_amount
        if self.order_type == 'insurance':
            bill_amount = self.total_insurance_cost or self.total_amount

        if not bill_amount or bill_amount <= 0:
            if self.order_type == 'insurance':
                raise UserError(_('Please ensure insurance costs are calculated before generating the bill.'))
            else:
                raise UserError(_('The total amount must be greater than zero.'))

        try:
            # Create the vendor bill
            move_vals = self._prepare_account_move_vals()
            move = self.env['account.move'].create(move_vals)

            # Create the bill lines
            if self.order_type == 'insurance' and self.insurance_type != 'employee' and self.logistic_order_line_ids:
                # Create detailed lines for each passenger
                self._create_detailed_insurance_bill_lines(move)
            else:
                # Create single line for the order
                line_vals = self._prepare_account_move_line_vals(move)
                self.env['account.move.line'].create(line_vals)

            # Post the bill
            move.action_post()

            # Log success
            _logger.info(f'Vendor bill {move.name} created successfully for {self.order_type} order {self.name}')

            return {
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'res_id': move.id,
                'view_mode': 'form',
                'view_type': 'form',
                'target': 'current',
            }

        except Exception as e:
            _logger.error(f'Error generating vendor bill for {self.order_type} order {self.name}: {str(e)}')
            raise UserError(_('Error generating vendor bill: %s') % str(e))

    @api.depends('name')
    def _compute_bill_count(self):
        for record in self:
            record.bill_count = self.env['account.move'].search_count([
                ('ref', '=', record.name),
                ('move_type', '=', 'in_invoice')
            ])

    def action_view_helpdesk_ticket(self):
        """Navigate to the related helpdesk ticket"""
        self.ensure_one()
        if not self.helpdesk_ticket_id:
            return

        return {
            'type': 'ir.actions.act_window',
            'name': _('Helpdesk Ticket'),
            'res_model': 'helpdesk.ticket',
            'view_mode': 'form',
            'res_id': self.helpdesk_ticket_id.id,
            'target': 'current'
        }

    def action_view_bills(self):
        self.ensure_one()
        bills = self.env['account.move'].search([
            ('ref', '=', self.name),
            ('move_type', '=', 'in_invoice')
        ])
        action = {
            'name': _('Vendor Bills'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', bills.ids)],
            'context': {'create': False}
        }
        if len(bills) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': bills.id,
            })
        return action

    @api.model
    def sync_iqama_numbers(self):
        """
        Synchronize iqama numbers from employees to logistic orders.
        This method should be run once to update existing records where iqama_no was not saved.
        """
        _logger.info("Starting iqama number synchronization for logistic orders")

        # Get all logistic orders
        orders = self.search([])
        updated_count = 0

        for order in orders:
            if order.employee_id and order.employee_id.identification_id:
                # Force recompute the related field
                order.invalidate_recordset(['iqama_no'])
                # Explicitly store the value in the database
                order._cr.execute("""
                    UPDATE logistic_order 
                    SET iqama_no = %s 
                    WHERE id = %s
                """, (order.employee_id.identification_id, order.id))
                updated_count += 1

        _logger.info(f"Completed iqama number synchronization. Updated {updated_count} records")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Synchronization Complete'),
                'message': _('%s logistic orders have been updated with iqama numbers.') % updated_count,
                'type': 'success',
                'sticky': False,
            }
        }

    @api.depends('employee_id', 'employee_id.identification_id', 'order_type')
    def _compute_iqama_no(self):
        for record in self:
            record.iqama_no = record.employee_id.identification_id if record.order_type == 'insurance' else False

class LogisticOrderLine(models.Model):
    _name = 'logistic.order.line'
    _description = 'Logistic Order Line'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Handle string values for insurance class field (backward compatibility)
            if 'insurance_class' in vals and isinstance(vals['insurance_class'], str):
                class_code = vals['insurance_class'].lower()
                insurance_class = self.env['insurance.class'].search([('code', '=', class_code)], limit=1)
                if insurance_class:
                    vals['insurance_class'] = insurance_class.id
                    _logger.info(
                        f"LogisticOrderLine: Converted string value '{class_code}' to insurance.class ID {insurance_class.id}")
                else:
                    _logger.warning(
                        f"LogisticOrderLine: Could not find insurance.class with code '{class_code}', setting field insurance_class to False")
                    vals['insurance_class'] = False

        return super(LogisticOrderLine, self).create(vals_list)

    def write(self, vals):
        # Handle string values for insurance class field (backward compatibility)
        if 'insurance_class' in vals and isinstance(vals['insurance_class'], str):
            class_code = vals['insurance_class'].lower()
            insurance_class = self.env['insurance.class'].search([('code', '=', class_code)], limit=1)
            if insurance_class:
                vals['insurance_class'] = insurance_class.id
                _logger.info(
                    f"LogisticOrderLine: Converted string value '{class_code}' to insurance.class ID {insurance_class.id}")
            else:
                _logger.warning(
                    f"LogisticOrderLine: Could not find insurance.class with code '{class_code}', setting field insurance_class to False")
                vals['insurance_class'] = False

        return super(LogisticOrderLine, self).write(vals)

    logistic_order_id = fields.Many2one('logistic.order', string='Logistic Order', required=True, ondelete='cascade')
    passenger_type = fields.Selection(selection=[('employee', 'Employee'),
                                                 ('spouse', 'Spouse'),
                                                 ('father', 'Father'),
                                                 ('mother', 'Mother'),
                                                 ('child', 'Child')],
                                      required=True, tracking=True)
    employee_id = fields.Many2one('hr.employee', readonly=True)
    available_family_member_ids = fields.Many2many('hr.employee.family', string='Available Passengers',
                                                   compute='_compute_passenger_domain')
    family_member_id = fields.Many2one('hr.employee.family', string='Family Member')
    name = fields.Char(string='Passenger Name', required=True)
    passport_no = fields.Char(string='Passport No')
    currency_id = fields.Many2one('res.currency', related='logistic_order_id.currency_id', readonly=True)
    seat_number = fields.Char(string='Seat Number')
    order_type = fields.Selection(related='logistic_order_id.order_type', store=True)

    # Insurance fields
    insurance_class = fields.Many2one('insurance.class', string='Insurance Class',
                                      help='Insurance coverage class for this passenger')
    insurance_cost = fields.Monetary(string='Insurance Cost', currency_field='currency_id',
                                     store=True,
                                     help='Calculated insurance cost based on class and passenger type')
    insurance_type = fields.Selection(related='logistic_order_id.insurance_type', store=True)
    passport_copy = fields.Many2many('ir.attachment', string='Passport Copy', compute='_compute_passport_copy')
    insurance_policy = fields.Char(string='Insurance Policy')
    insurance_policy_id = fields.Many2one('insurance.policy', string='Insurance Policy')
    flight_type = fields.Selection([
        ('employee', 'Employee'),
        ('family', 'Family'),
        ('both', 'Both'),
    ], string='Flight Type', readonly=True)

    @api.depends('logistic_order_id.employee_id', 'passenger_type')
    def _compute_passenger_domain(self):
        for line in self:
            line.available_family_member_ids = self.env['hr.employee.family'].search(
                [('employee_id', '=', line.logistic_order_id.employee_id.id),
                 ('family_type', '=', line.passenger_type)])

    @api.onchange('insurance_class', 'passenger_type', 'order_type', 'logistic_order_id.insurance_policy_id')
    def _compute_insurance_cost(self):
        """Compute insurance cost based on class and passenger type"""
        for line in self:
            if line.order_type != 'insurance' or not line.insurance_class:
                line.insurance_cost = 0.0
                continue

            # If a policy is selected, use its cost calculation
            if line.logistic_order_id.insurance_policy_id and line.insurance_class:
                cost = line.logistic_order_id.insurance_policy_id.get_class_cost(
                    line.insurance_class.code, line.passenger_type
                )
                line.insurance_cost = cost
            else:
                # Fallback to system parameters for insurance costs
                ICPSudo = self.env['ir.config_parameter'].sudo()
                cost = 0.0
                param_prefix = ''

                # Determine the configuration parameter name based on passenger type and class
                if line.passenger_type == 'employee':
                    param_prefix = 'era_recruitment_opportunity.health_insurance_'
                elif line.passenger_type == 'spouse':
                    param_prefix = 'era_recruitment_opportunity.spouse_health_insurance_'
                elif line.passenger_type in ['father', 'mother', 'child']:
                    param_prefix = 'era_recruitment_opportunity.kids_health_insurance_'
                else:
                    line.insurance_cost = 0.0
                    continue

                if line.insurance_class and line.insurance_class.name:
                    # Get the cost based on the class
                    param_name = param_prefix + line.insurance_class.name
                    cost = float(ICPSudo.get_param(param_name, 0.0))
                    line.insurance_cost = cost
                else:
                    line.insurance_cost = 0.0

    @api.onchange('passenger_type', 'family_member_id')
    def _onchange_passenger(self):
        if self.family_member_id:
            self.name = self.family_member_id.name
            self.passport_no = self.family_member_id.passport_id

    @api.depends('family_member_id')
    def _compute_passport_copy(self):
        for line in self:
            if line.family_member_id:
                line.passport_copy = line.family_member_id.passport_copy.sudo().ids
            else:
                line.passport_copy = [(5, 0, 0)]


class FlightBooking(models.Model):
    _name = 'flight.booking'
