from odoo import _, models, fields, api
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class GovernmentPayment(models.Model):
    _name = "government.payment"
    _description = "Government Payment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"
    _sql_constraints = [
        ("saddad_no_uniq", "unique(saddad_no)", "Saddad No must be unique"),
    ]

    name = fields.Char("Name", copy=False, default=lambda self: _("New"), readonly=True)
    active = fields.Boolean(default=True)
    employee_id = fields.Many2one("hr.employee")
    iqama_no = fields.Char(related="employee_id.visa_no", string="Iqama Number", readonly=True)
    project_id = fields.Many2one(
        'client.project', string="Client Project", readonly=False
    )
    file_no = fields.Char(copy=False)
    saddad_no = fields.Char("Saddad No", copy=False)
    notes = fields.Text("Notes", copy=False)
    service_type_id = fields.Many2one("service.type")
    service_type_ids = fields.Many2many('service.type', string='Service Types')
    available_company_ids = fields.Many2many('sister.company',
                                             string='Available Sister Companies',
                                             compute='_compute_available_company_ids'
                                             )
    sponsor_company_id = fields.Many2one('sister.company',
                                         string='Sister Company',
                                         domain="[('id', 'in', available_company_ids)]"
                                         )
    is_saddad_required = fields.Boolean(related="service_type_id.is_saddad_required", readonly=True)
    sponsor_number = fields.Char("Sponsor Number", copy=False, related="sponsor_company_id.sponsorship_number",
                                 readonly=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submit", "Submit"),
            ("on_hold", "On Hold"),
            ("approve", "Approve"),
            ('paid', 'Paid'),
            ("validate", "Validate"),
            ("reject", "Reject"),
            ("cancel", "Cancel"),
        ],
        default="draft",
        tracking=True,
    )
    effective_date = fields.Date("Effective Date", copy=False, required=True, default=fields.Date.context_today)
    company_id = fields.Many2one("res.company", string="Company", required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one("res.currency", string="Currency", related='company_id.currency_id', readonly=True)
    payment_method = fields.Selection(
        [("cash", "Cash"), ("bank", "Bank")],
        default="bank",
        string="Payment Method",
        required=True,
    )
    payment_count = fields.Integer(compute="_compute_payment_count")
    payment_line_ids = fields.One2many('government.payment.line', 'government_payment_id', string="Payment Lines")
    total_amount = fields.Monetary(string="Total Amount", compute="_compute_total_amount", store=True,
                                   currency_field="currency_id")
    payment_reference_ids = fields.Many2many('account.payment',
                                             string="Payment References", copy=False,
                                             compute="_compute_payment_reference_ids")
    payment_type = fields.Selection([('individual', 'Individual'),
                                     ('enterprise', 'Enterprise'),
                                     ('no_payment', 'Without Payment')],
                                    default='individual',
                                    string='Payment Type',
                                    required=True,
                                    )
    wizard_partner_id = fields.Many2one('res.partner', string='Customer')
    is_flint_payment = fields.Boolean(string='Pay through Flint')
    include_payment = fields.Boolean(string="Include Payment", default=True)
    rejection_reason = fields.Text(string="Rejection Reason", copy=False)
    operation_type = fields.Selection([
        ('with_payment', 'With Payment'),
        ('without_payment', 'Without Payment')
    ], default='with_payment', string='Operation Type', required=True)
    services_display = fields.Char(string='Services', compute='_compute_service_type_display')
    saddad_no_display = fields.Char(string='Saddad No', compute='_compute_saddad_no_display')
    iqama_no_display = fields.Char(string='Iqama No', compute='_compute_iqama_number')
    bill_id = fields.Many2one('account.move', string="Bill", copy=False)

    def _compute_iqama_number(self):
        for record in self:
            unique_iqama_nos = set()
            if record.iqama_no:
                unique_iqama_nos.add(record.iqama_no)
            for line in record.payment_line_ids.filtered(lambda line: line.iqama_no):
                unique_iqama_nos.add(line.iqama_no)
            record.iqama_no_display = ', '.join(unique_iqama_nos) if unique_iqama_nos else False

    def check_all_lines_paid(self):
        for record in self:
            all_paid = all(rec.payment_state == 'paid' for rec in record.payment_line_ids)
            if all_paid:
                record.state = 'paid'
                self.activity_unlink(['mail.mail_activity_data_todo'])
                self.send_notify("Paid")

    @api.model
    def create(self, vals_list):
        if vals_list.get('name', _('New')) == _('New'):
            name = self.env['ir.sequence'].next_by_code('gov_payment') or _('New')
            vals_list['name'] = name
        return super(GovernmentPayment, self).create(vals_list)

    @api.depends('service_type_id')
    def _compute_available_company_ids(self):
        for record in self:
            record.available_company_ids = record.service_type_id.sister_company_ids

    def _compute_payment_reference_ids(self):
        for rec in self:
            rec.payment_reference_ids = self.env['account.payment'].search([('government_payment_ref_id', '=', rec.id)])

    @api.depends('payment_reference_ids')
    def _compute_payment_count(self):
        for rec in self:
            rec.payment_count = len(rec.payment_reference_ids)

    def send_notify(self, status):
        self.ensure_one()
        template_id = self.env.ref("scs_operation.email_template_gov_pay_approve")
        template_id.with_context(state=status).send_mail(
            self.id, force_send=True
        )

    def change_activity_state(self):
        self.ensure_one()
        self.activity_unlink(["mail.mail_activity_data_todo"])

    def change_state(self):
        self.ensure_one()
        ctx = self._context
        if ctx.get("submit"):
            self._validate_submit()
            if self.payment_type == 'enterprise' and (not self.project_id or not self.project_id.partner_id):
                return self._open_payment_wizard()
            if self.payment_type == 'no_payment':
                self.state = "approve"
            else:
                self.state = "submit"
            self.change_activity_state()
            users = self.env.ref("scs_operation.group_operation_admin").users
            note = _("Hello Mr. Mofleh kindly Approve payment request %s") % self.name
            if self.payment_type != 'no_payment':
                for user in users:
                    self.activity_schedule(
                        user_id=user.id,
                        note=note,
                    )
        elif ctx.get("approve"):
            self.state = "approve"
            self.change_activity_state()
            account_manager_group = self.env.ref("account.group_account_manager").users
            for user in account_manager_group:
                self.activity_schedule(
                    user_id=user.id,
                    note=_("Hello Accounting Team kindly process payment for request %s") % self.name,
                )
            self.send_notify("Approved")
        elif ctx.get("validate"):
            validation_state = self._validate_payments()
            if validation_state == 'partially_validated':
                return
            elif validation_state == 'fully_validated':
                self.state = "validate"
                self.change_activity_state()
                self.send_notify("Validate")
        elif ctx.get("reject"):
            return {
                "name": _("Rejection Reason"),
                "type": "ir.actions.act_window",
                "res_model": "rejection.reason.wizard",
                "view_mode": "form",
                "target": "new",
                "context": {"active_id": self.id, "active_model": self._name},
            }
        elif ctx.get("cancel"):
            self.state = "cancel"
        elif ctx.get("draft"):
            self.change_activity_state()
            self.state = "draft"

    def _validate_submit(self):
        self.ensure_one()
        if not self.effective_date:
            raise UserError(_("Effective Date is required."))
        if self.total_amount <= 0 and self.payment_type != 'no_payment':
            raise UserError(_("Total amount must be greater than zero."))
        if not self.project_id and self.service_type_id.is_project_required:
            raise UserError(_("Project is required for this service type."))
        elif self.project_id and not self.project_id.partner_id and self.payment_type != 'enterprise':
            raise UserError(_("Please add a customer to this project."))
        if any(line for line in self.payment_line_ids if
               not line.saddad_no and line.service_type_ids and line.service_type_ids[0].is_saddad_required):
            raise UserError(_("Please add Saddad Number to all payment lines that require a Saddad Number."))

    def _validate_payments(self):
        if self.payment_type == 'individual':
            for line in self.payment_line_ids:
                if line.payment_state == 'paid' and 'not_paid' in self.payment_line_ids.mapped('payment_state'):
                    line.payment_state = 'validated'
                    return 'partially_validated'
                elif line.payment_state == 'paid' and 'not_paid' not in self.payment_line_ids.mapped('payment_state'):
                    self.payment_line_ids.payment_state = 'validated'
                    return 'fully_validated'
                elif 'paid' not in line.payment_state and 'validated' not in line.payment_state:
                    raise UserError(_("one or All the payments must be paid before validating the government payment."))
        else:
            payments = self.env['account.payment'].search([('saddad_no', '=', self.saddad_no),
                                                           ('government_payment_ref_id', '=', self.id)])
            if not payments and self.payment_type != 'no_payment':
                raise UserError(_("No payments found for this government payment."))
            if any(payment.state != 'posted' for payment in payments):
                raise UserError(_("All payments must be validated before validating the government payment."))
            return 'fully_validated'

    @api.ondelete(at_uninstall=False)
    def _unlink_except_draft(self):
        for record in self:
            if record.state != "draft":
                raise UserError(_("You can only delete draft records"))

    def show_payment(self):
        self.ensure_one()
        domain = [('government_payment_ref_id', '=', self.name)] if self.payment_type == 'enterprise' else [
            ('id', 'in', self.env['account.payment'].search([('government_payment_ref_id', '=', self.id)]).ids)]
        return {
            "name": _("Payment"),
            "view_mode": "tree",
            "res_model": "account.payment",
            "type": "ir.actions.act_window",
            "domain": domain,
            "context": {"create": False},
        }

    def action_pay(self):
        self.ensure_one()

        # Check if payments already exist
        if self.payment_reference_ids:
            raise UserError(_("Payments already exist for this record"))

        if self.operation_type == 'without_payment':
            self.state = 'validate'
            return True

        if self.payment_type == 'individual' and not self.payment_line_ids:
            raise UserError(_("Please add payment lines before creating payments."))

        # Create Odoo payments first
        if self.payment_type == 'individual':
            created_payments = self._create_individual_payments()
            self.state = 'paid'
        elif self.payment_type == 'enterprise':
            action = self._create_enterprise_payment()
            self.state = 'paid'
            return action
        else:
            raise UserError(_("Invalid Payment Type"))

        self.activity_unlink(['mail.mail_activity_data_todo'])
        self.send_notify("Paid")

        return True

    def _create_individual_payments(self):
        # Check if any line already has payments
        if any(line.payment_state != 'not_paid' for line in self.payment_line_ids):
            raise UserError(_("Some payment lines already have payments"))

        payments = []
        for line in self.payment_line_ids:
            payment = line.create_payment()
            if payment:
                payments.append(payment)

        return self.env['account.payment'].union(*payments) if payments else self.env['account.payment']

    def _create_enterprise_payment(self):
        if self.service_type_id.is_saddad_required and not self.saddad_no:
            raise UserError(_("Please add Saddad Number before creating payments."))
        if not self.project_id and not self.project_id.partner_id and not self.wizard_partner_id and not self.is_flint_payment:
            raise UserError(_("Please add a customer to this project or select a partner to hold the payment."))
        payment = self.create_payment()
        return {
            'name': _('Payment'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'form',
            'res_id': payment.id,
            'target': 'current',
        }

    @api.depends('payment_line_ids.amount')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = sum(record.payment_line_ids.mapped('amount'))

    @api.constrains('saddad_no')
    def _check_saddad_no(self):
        for record in self:
            if record.saddad_no and not record.saddad_no.isdigit():
                raise ValidationError(_("Saddad Number must contain only numbers."))

    def _open_payment_wizard(self):
        action = self.env.ref('scs_operation.validate_payment_on_behalf_action').read()[0]
        action['context'] = {'default_government_payment_id': self.id}
        return action

    def create_payment(self):
        self.ensure_one()
        payment_obj = self.env['account.payment']
        if self.service_type_id.is_saddad_required and not self.saddad_no:
            raise UserError(_("Please add Saddad Number before creating payments."))

        if self.service_type_id.partner_id:
            partner_id = self.service_type_id.partner_id.id

        elif self.project_id and self.project_id.partner_id:
            partner_id = self.project_id.partner_id.id
        else:
            partner_id = self.wizard_partner_id.id

        if not partner_id and self.is_flint_payment:
            partner_id = self.env.company.partner_id.id
        if not partner_id and not self.is_flint_payment:
            raise UserError(_("Please select a customer or choose to pay through Flint."))
        vals = {
            'payment_type': 'outbound',
            'partner_type': 'supplier',
            'partner_id': partner_id or self.env.company.partner_id.id,
            'amount': self.total_amount,
            'currency_id': self.currency_id.id,
            'date': fields.Date.today(),
            'saddad_no': self.saddad_no,
            'employee_id': self.employee_id.id or False,
            'file_no': self.file_no,
            'employee_iqama_no': self.iqama_no,
            'service_type': self.service_type_id.id,
            'service_name': self.service_type_id.name,
            'state': 'draft',
            'government_payment_ref_id': self.id,
            'project_id': self.project_id.id if self.project_id else False,
            'analytic_account_id': self.project_id.analytic_account_id.id if self.project_id or
                                                                             self.employee_id.project_id.analytic_account_id.id
            else False,
            'journal_id': self.env['res.config.settings'].sudo().get_values().get('gov_pay_default_journal_id'),
            'ref': '{} - {} - ID #{} - SADDAD#'.format(
                self.service_type_id.name or self.payment_line_ids.mapped('service_type_ids').name,
                self.project_id.name,
                self.file_no, self.saddad_no),
        }

        try:
            payment = payment_obj.create([vals])
            return payment
        except Exception as e:
            _logger.error("Failed to create payment: %s", str(e))
            raise UserError(_("Failed to create payment. Please check the logs or contact your administrator."))

    def _compute_service_type_display(self):
        for record in self:
            if record.payment_type == 'individual':
                record.services_display = ', '.join(record.payment_line_ids.mapped('service_type_ids.name'))
            else:
                record.services_display = record.service_type_id.name

    def _compute_saddad_no_display(self):
        for record in self:
            record.saddad_no_display = record.saddad_no or record.payment_line_ids.filtered(
                lambda line: line.saddad_no).mapped('saddad_no')

    def bulk_pay(self):
        for record in self:
            if record.state == 'approve':
                if record.total_amount < 10:
                    raise ValidationError(
                        _("The record {} has an amount less than 10. You need to increase the amount to 10 or more to use this feature.".format(
                            record.name)))
            record.action_pay()
        # Return an action dictionary instead of a boolean
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def button_create_bill(self):
        for rec in self:
            if not rec.bill_id:
                service_type_id = rec.service_type_id
                line_vals = []

                if service_type_id.partner_id and service_type_id.product_id and service_type_id.tax_ids and service_type_id.account_id:
                    line_vals.append((0, 0, {
                        'product_id': service_type_id.product_id.id,
                        'quantity': 1,
                        'price_unit': rec.total_amount,
                        'account_id': service_type_id.account_id.id,
                        'tax_ids': [(6, 0, service_type_id.tax_ids.ids)],
                    }))

                    account_move_id = self.env['account.move'].create({
                        'partner_id': service_type_id.partner_id.id,
                        'ref': rec.name,
                        'move_type': 'in_invoice',
                        'state': 'approved',
                        'analytic_account_id': rec.project_id.analytic_account_id.id,
                        'invoice_line_ids': line_vals,
                        'government_payment_id': rec.id,
                    })

                    rec.bill_id = account_move_id.id

                else:
                    raise ValidationError(_("Please ensure Servie Type Partner, Product, Accounts and Taxes exists!"))

            else:
                raise ValidationError(_("Bill for this payment already exists!"))
