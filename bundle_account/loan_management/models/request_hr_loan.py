# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class RequestHrLoan(models.Model):
    _name = "request.hr.loan"
    _description = "Request HR Loan"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'sequence'
    _rec_names_search = ['sequence', 'employee_id']
    _order = 'id desc'

    sequence = fields.Char(string='Request Loan Sequence', copy=False, readonly=True, default='New')

    employee_id = fields.Many2one('hr.employee', string="Employee", relation='edi_employee_id_rel', required=True,
                                  readonly=True, tracking=True, default=lambda self: self.env.user.employee_id.id)
    job_id = fields.Many2one('hr.job', string="Job Title", related='employee_id.job_id', readonly=True, tracking=True)
    department_id = fields.Many2one('hr.department', string="Department", related='employee_id.department_id',
                                    readonly=True, tracking=True)
    identification_no = fields.Char(string="ID No.", related='employee_id.identification_id', readonly=True,
                                    tracking=True)
    file_no = fields.Char(string="File No.", related='employee_id.registration_number', readonly=True, tracking=True)
    passport_no = fields.Char(string="Passport No.", related='employee_id.passportNumber', readonly=True, tracking=True)
    client_id = fields.Many2one(string="Client Project", related='employee_id.client_id', readonly=True, tracking=True)
    total_gross_wage = fields.Float(string="Total Gross Wage", related='employee_id.contract_id.total_gross_wage',
                                    readonly=True, tracking=True)
    requested_loan_amount = fields.Float(string="Loan Amount", tracking=True)
    no_of_installments = fields.Integer(string="Loan Installments", tracking=True)

    installment_type = fields.Selection([('equal', 'Split Equally'), ('custom', 'Custom')], string='Installment Type',
                                        default='equal', required=True, tracking=True)
    hr_loan_id = fields.Many2one('hr.loan', string='Hr Loan', tracking=True)
    request_hr_loan_installment_line_ids = fields.One2many('request.hr.loan.installment.line', 'request_hr_loan_id')
    approval_line_ids = fields.One2many('request.hr.loan.approvals.line', 'request_hr_loan_id')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approval', 'Waiting for Approval'),
        ('approved', 'Approved'),
        ('confirm', 'Confirmed'),
        ('rejected', 'Rejected'),
    ], string='Status', default='draft', tracking=True)

    @api.onchange('installment_type')
    def _onchange_installment_type(self):
        for rec in self:
            rec.request_hr_loan_installment_line_ids = [(5, 0, 0)]

    def create(self, vals):
        if vals.get('sequence', _('New')) == _('New'):
            vals['sequence'] = self.env['ir.sequence'].next_by_code('request.hr.loan') or _('New')
        res = super(RequestHrLoan, self).create(vals)
        return res

    def button_compute_installments(self):
        for rec in self:
            if rec.installment_type == 'equal' and rec.no_of_installments > 0:
                # Clear old lines if needed
                rec.request_hr_loan_installment_line_ids = [(5, 0, 0)]

                installment_amount = rec.requested_loan_amount / rec.no_of_installments

                # Create new lines
                lines = []
                for i in range(1, rec.no_of_installments + 1):
                    lines.append((0, 0, {
                        'name': f"Installment {i}",
                        'amount': installment_amount,
                        'remarks': '',
                    }))

                if lines:
                    rec.request_hr_loan_installment_line_ids = lines

    def _create_activity(self, user):
        """Schedule To-Do activity for given user"""
        self.activity_schedule(
            'mail.mail_activity_data_todo',
            user_id=user.id,
            note=f"Please approve loan: {self.sequence or self.id}"
        )

    def button_request_approval(self):
        """Request approval: auto-create loan if not selected"""
        for rec in self:
            # Validate total installment amount vs requested loan amount
            if sum(line.amount for line in rec.request_hr_loan_installment_line_ids) != rec.requested_loan_amount:
                raise ValidationError(
                    _("Requested loan amount and installment plan mismatch! Please create a correct structure."))

            # Check for any ongoing loan (approval/approved/confirm)
            existing_loan = self.env['request.hr.loan'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('state', 'in', ['approval', 'approved']),
                ('id', '!=', rec.id)
            ], limit=1)

            if existing_loan:
                raise ValidationError(
                    _("Another loan record for this employee already exists in '%s' state. Please complete or close it before requesting a new approval.") % existing_loan.state)

            approver_lines = []
            if rec.employee_id.parent_id:
                approver_lines.append((0, 0, {
                    'approver_id': rec.employee_id.parent_id.user_id.id,
                    'is_approved': False,
                }))

            if approver_lines:
                rec.approval_line_ids = [(5, 0, 0)]
                rec.approval_line_ids = approver_lines

                # Schedule activity for next approver (first unapproved line)
                first_line = rec.approval_line_ids[0]
                if first_line:
                    rec._create_activity(first_line.approver_id)

                rec.write({
                    'state': 'approval',
                })
            else:
                rec.write({
                    'state': 'approved',
                })

    def button_confirm(self):
        """Create Purchase Order after all approvals"""
        for rec in self:
            installment_lines = []
            for line in rec.request_hr_loan_installment_line_ids:
                installment_lines.append((0, 0, {
                    'name': line.name,
                    'remarks': line.remarks,
                    'amount': line.amount,
                    'state': 'draft',
                }))

            hr_loan_id = self.env['hr.loan'].create({
                'employee_id': rec.employee_id.id,
                'requested_loan_amount': rec.requested_loan_amount,
                'no_of_installments': rec.no_of_installments,
                'hr_loan_installment_line_ids': installment_lines,
                'request_loan_id': rec.id

            })
            hr_loan_id.button_request_approval()

            rec.write({
                'hr_loan_id': hr_loan_id.id,
                'state': 'confirm',
            })

    def button_draft(self):
        for rec in self:
            rec.state = 'draft'

    def button_approve(self):
        """Approve only current user's line and schedule next"""
        for rec in self:
            if len(rec.approval_line_ids) == 0:
                rec.state = 'approved'

            else:
                current_user = self.env.user
                pending_lines = rec.approval_line_ids.filtered(lambda l: not l.is_approved).sorted('id')

                if not pending_lines:
                    raise UserError("All approval lines are already approved!")

                # Current user must be next approver
                next_line = pending_lines[0]
                if next_line.approver_id != current_user:
                    raise UserError("You are not the current approver!")

                # Approve line
                next_line.is_approved = True

                # Complete activity
                rec.activity_ids.filtered(lambda a: a.user_id == current_user and a.active).action_done()

                # Schedule next approver
                remaining_lines = rec.approval_line_ids.filtered(lambda l: not l.is_approved).sorted('id')
                if remaining_lines:
                    rec._create_activity(remaining_lines[0].approver_id)

                else:
                    # All approved → state confirm
                    rec.state = 'approved'

    def button_reject(self):
        for rec in self:
            rec.state = 'rejected'

    def open_loan(self):
        for rec in self:
            if not rec.hr_loan_id:
                raise UserError(_('No Payment Exists!'))

            else:
                return {
                    'name': _('Loan'),
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'hr.loan',
                    'res_id': self.hr_loan_id.id,
                    'target': 'current',
                }


class RequestHrLoanInstallmentLine(models.Model):
    _name = "request.hr.loan.installment.line"
    _description = "Request Hr Loan Installment Line"

    request_hr_loan_id = fields.Many2one("request.hr.loan", string="Request HR Loan")
    name = fields.Char("Installment Name / No.")
    remarks = fields.Char("Remarks")
    amount = fields.Float("Amount")


class RequestLoanApprovalsLine(models.Model):
    _name = 'request.hr.loan.approvals.line'
    _description = "Request Loan Approval Line"

    request_hr_loan_id = fields.Many2one('request.hr.loan', string='Request HR Loan', ondelete='cascade')
    approver_id = fields.Many2one('res.users', string='Approver', required=True)
    is_approved = fields.Boolean(string='Approved', default=False)
