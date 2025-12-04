from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class GovernmentPaymentLine(models.Model):
    _name = "government.payment.line"
    _description = "Government Payment Line"

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    government_payment_id = fields.Many2one('government.payment', string="Government Payment", required=True)
    employee_id = fields.Many2one("hr.employee", string="Employee", required=True)
    iqama_no = fields.Char(related="employee_id.visa_no", string="Iqama Number")
    iqama_expire_date = fields.Date(related="employee_id.visa_expire", string="Iqama Expiry Date")
    project_id = fields.Many2one(related="employee_id.project_id", string="Client Project")
    file_no = fields.Char(related="employee_id.registration_number", string="File No")
    amount = fields.Monetary("Amount", currency_field="currency_id", required=True)
    currency_id = fields.Many2one("res.currency", string="Currency", related='government_payment_id.currency_id')
    payment_reference = fields.Many2one("account.payment", string="Payment Reference", readonly=True)
    service_type_ids = fields.Many2many("service.type", domain=[('service_type', '=', 'individual')])
    saddad_no = fields.Char("Saddad No")
    payment_state = fields.Selection([
        ('not_paid', 'Not Paid'),
        ('paid', 'Paid'),
        ('validated', 'Validated'),
    ],
        string="Payment State", default='not_paid', readonly=True, copy=False)
    operation_order_attachment = fields.Many2many('ir.attachment', string="Attachments",
                                                  relation='operation_order_attachment_rel')
    has_muqeem_service = fields.Boolean(
        string="Has Muqeem Service",
        compute="_compute_has_muqeem_service",
        store=True,
    )

    saddad_no_readonly = fields.Boolean(
        string="Saddad No Readonly",
        compute='_compute_saddad_no_readonly',
        store=True
    )

    @api.depends('service_type_ids.is_muqeem_service')
    def _compute_has_muqeem_service(self):
        for record in self:
            record.has_muqeem_service = any(record.service_type_ids.mapped('is_muqeem_service'))

    @api.depends('service_type_ids.saddad_type')
    def _compute_saddad_no_readonly(self):
        for record in self:
            record.saddad_no_readonly = any(rec.saddad_type == 'moi' for rec in record.service_type_ids)

    def create_payment(self):
        self.ensure_one()

        # Check if payment already exists
        if self.payment_reference or self.payment_state != 'not_paid':
            raise UserError(_("Payment already exists for line with employee %s") % self.employee_id.name)

        if not self.saddad_no and any(service.is_saddad_required for service in self.service_type_ids):
            raise UserError(_("Saddad No is required for one of the selected service types!"))

        # Get partner ID
        partner_id = False
        if self.project_id and self.project_id.partner_id:
            partner_id = self.project_id.partner_id.id
        elif self.employee_id.address_id:
            partner_id = self.employee_id.address_id.id

        if not partner_id:
            raise UserError(_("No partner found for employee %s! or the project %s") % (self.employee_id.name,
                                                                                        self.project_id.name))
        payment_obj = self.env['account.payment'].sudo()
        journal_id = self.env['res.config.settings'].sudo().get_values().get('gov_pay_default_journal_id')
        if not journal_id:
            raise UserError(_("Please configure the default journal for government payments!"))
        # Prepare the payment values
        vals = {
            'payment_type': 'outbound',
            'partner_type': 'supplier',
            'partner_id': partner_id,
            'amount': self.amount,
            'currency_id': self.currency_id.id,
            'date': fields.Date.today(),
            'saddad_no': self.saddad_no,
            'service_name': 'individual Service Payment / %s' % (
                str(self.service_type_ids.mapped('name')).replace('[', '').replace(']', '').replace("'", "")),
            'government_payment_ref_id': self.government_payment_id.id,
            'government_payment_line_ref_id': self.id,
            'project_id': self.employee_id.project_id.id,
            'employee_id': self.employee_id.id or False,
            'file_no': self.file_no,
            'employee_iqama_no': self.iqama_no,
            'journal_id': journal_id,
            'ref': '{} - {} - ID #{} - SADDAD#{}'.format(
                self.service_type_ids[0].name if self.service_type_ids else self.government_payment_id.service_type_id.name,
                self.project_id.name or self.employee_id.project_id.name,
                self.file_no, self.saddad_no),
        }

        # Add analytic account if available
        analytic_account_id = self.employee_id.contract_id.analytic_account_id.id or \
                            self.employee_id.project_id.analytic_account_id.id
        if analytic_account_id:
            vals['analytic_account_id'] = analytic_account_id

        try:
            if self.government_payment_id.include_payment:
                # Create the payment record
                payment = payment_obj.create(vals)
                self.write({
                    'payment_reference': payment.id,
                    'payment_state': 'paid'
                })
                self.government_payment_id.check_all_lines_paid()
                return payment
        except Exception as e:
            self.write({'payment_state': 'not_paid'})
            raise ValidationError(_("Failed to create payment for employee %s: %s") % (self.employee_id.name, str(e)))

    @api.constrains('saddad_no')
    def _check_saddad_no(self):
        for rec in self:
            if rec.saddad_no:
                if self.search_count([('saddad_no', '=', rec.saddad_no), ('id', '!=', rec.id)]):
                    raise ValidationError(_("Saddad No must be unique per line!"))
            elif not rec.saddad_no and any(service.is_saddad_required for service in rec.service_type_ids):
                raise ValidationError(_("Saddad No is required for one of the selected service types!"))

    @api.constrains('amount')
    def _check_amount(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError(_("Amount must be greater than zero!"))

    @api.onchange('service_type_ids')
    def _onchange_service_type_ids(self):
        if len(self.service_type_ids) > 1:
            self.service_type_ids = self.service_type_ids[:1]
            return {
                'warning': {
                    'title': _('Warning!'),
                    'message': _('You can select only one service type per line!')
                }
            }
        return {}

    # constraint to check if on the same service is selected for the same employee in the same payment
    @api.constrains('service_type_ids')
    def _check_service_type_ids(self):
        for rec in self:
            if rec.service_type_ids:
                if (self.search_count([('employee_id', '=', rec.employee_id.id),
                                       ('service_type_ids', 'in', rec.service_type_ids.ids),
                                       ('id', '!=', rec.id)]) > 1 and not
                self.env.user.has_group('scs_operation.group_operation_admin')):
                    raise ValidationError(
                        _("You can't select the same service type for the same employee in the same payment!"))
