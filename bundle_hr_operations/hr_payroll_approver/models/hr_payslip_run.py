# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, _, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    state = fields.Selection(selection_add=[
        ('verify',),
        ('hr_approval', 'HR Approval'),
        ('hr_rejected', 'HR Rejected'),
        ('auditor_approval', 'Auditor Approval'),
        ('auditor_rejected', 'Auditor Rejected'),
        ('finance_approval', 'Finance Approval'),
        ('finance_rejected', 'Finance Rejected'),
        ('ceo_approval', 'CEO Approval'),
        ('ceo_rejected', 'CEO Rejected'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('close', 'Done'),
        ('paid', 'Paid'),
    ],
        ondelete={'verify': 'set default', 'hr_approval': 'set default', 'hr_rejected': 'set default',
                  'auditor_approval': 'set default', 'auditor_rejected': 'set default',
                  'finance_approval': 'set default', 'finance_rejected': 'set default', 'ceo_approval': 'set default',
                  'ceo_rejected': 'set default', 'approved': 'set default', 'rejected': 'set default',
                  'close': 'set default', 'paid': 'set default'})
    rejection_reason = fields.Text(string='Rejection Reason', readonly=True)

    def action_send_for_approval(self):
        # for rec in self:
        if all(r.state == 'verify' for r in self):
            payroll_office_manager = self.env.ref('hr_payroll.group_hr_payroll_employee_manager').users
            if not payroll_office_manager:
                raise UserError(_("No users configured as Payroll HR Approval, Please configure."))
            finance_manager = self.env.ref('hr_payroll_approver.group_payroll_finance_approval').users
            if not finance_manager:
                raise UserError(_("No users configured as Payroll Finance Approval, Please configure."))
            payroll_approver = self.env.ref('hr_payroll_approver.group_payroll_hr_approval').users
            if not payroll_approver:
                raise UserError(_("No users configured as Payroll HR Approval, Please configure."))

            users = payroll_office_manager + finance_manager + payroll_approver
            self.payroll_approval_send_mail(payroll_approver.mapped('login'), payroll_approver[0].name,
                                            'hr_approval')

            self.state = 'hr_approval'
        else:
            raise UserError("Action only allowed in Verify state.")

    def action_approve_hr(self):
        #         for rec in self:
        if all(r.state == 'hr_approval' for r in self):
            payroll_auditor = self.env.ref('hr_payroll_approver.group_payroll_bank_auditor').users
            if not payroll_auditor:
                raise UserError(_("No users configured as Payroll Auditor Approval, Please configure."))
            self.payroll_approval_send_mail(payroll_auditor.mapped('login'), payroll_auditor[0].name,
                                            'auditor_approval', self.env.user.name)

            self.state = 'auditor_approval'

        else:
            raise UserError("Action only allowed in HR Approval state.")

    def action_reject_hr(self):
        #         for rec in self:
        if all(r.state == 'hr_approval' for r in self):
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'payroll.rejection.reason.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {'rejection_department': 'hr_rejected'}
            }
        else:
            raise UserError("Action only allowed in HR Approval state.")

    def action_approve_auditor(self):
        #         for rec in self:
        if all(r.state == 'auditor_approval' for r in self):
            finance = self.env.ref('hr_payroll_approver.group_payroll_finance_approval').users
            if not finance:
                raise UserError(_("No users configured as Payroll Finance Approval, Please configure."))
            self.payroll_approval_send_mail(finance.mapped('login'), finance[0].name, 'finance_approval',
                                            self.env.user.name)

            self.state = 'finance_approval'
        else:
            raise UserError("Action only allowed in Auditor Approval state.")

    def action_reject_auditor(self):
        #         for rec in self:
        if all(r.state == 'auditor_approval' for r in self):
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'payroll.rejection.reason.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {'rejection_department': 'auditor_rejected'}
            }
        else:
            raise UserError("Action only allowed in CEO Approval state.")

    def action_approve_finance(self):
        #         for rec in self:
        if all(r.state == 'finance_approval' for r in self):
            ceo = self.env.ref('hr_payroll_approver.group_payroll_approval_ceo').users
            if not ceo:
                raise UserError(_("No users configured as CEO Approval, Please configure."))
            self.payroll_approval_send_mail(ceo.mapped('login'), ceo[0].name, 'ceo_approval', self.env.user.name)

            self.state = 'ceo_approval'

        else:
            raise UserError("Action only allowed in Finance Approval state.")

    def action_reject_finance(self):
        #         for rec in self:
        if all(r.state == 'finance_approval' for r in self):
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'payroll.rejection.reason.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {'rejection_department': 'finance_rejected'}
            }
        else:
            raise UserError("Action only allowed in Finance Approval state.")

    # def action_approve_ceo(self):
    #     #         for rec in self:
    #     if all(r.state == 'ceo_approval' for r in self):
    #         # Calculate total amount for the batch
    #         total_amount = sum(slip.net_wage for slip in self.slip_ids)
    #         currency_symbol = self.company_id.currency_id.symbol
    #
    #         # Send email to bank auditor group with total amount information
    #         users = self.env.ref('hr_payroll_approver.group_payroll_bank_auditor').users
    #         if not users:
    #             raise UserError(_("No users configured as Bank Auditor, Please configure."))
    #
    #         # Custom message for bank auditor with transfer amount
    #         for batch in self:
    #             template = """
    #                <body style="font-family:sans-serif;line-height:2;">
    #                Hello {username},<br/>
    #                Payroll batch <b>{batch}</b> has been approved by CEO.<br/>
    #                <p>Please process an internal transfer between company banks for the total amount: <b>{currency_symbol}{total_amount:,.2f}</b></p>
    #                <p>This amount covers {employee_count} employees in this payroll batch.</p>
    #                Thanks.<br/>
    #                <br/>
    #                 <hr/>
    #                 <p style="color:#8a8686;">
    #                 {description} ...</p>
    #                 </body>
    #                 """.format(
    #                 username=users[0].name,
    #                 batch=batch.name,
    #                 description=batch.company_id.name,
    #                 currency_symbol=currency_symbol,
    #                 total_amount=total_amount,
    #                 employee_count=len(batch.slip_ids)
    #             )
    #
    #             template_id = self.env.ref('hr_payroll_approver.email_template_payroll_approve').id
    #             if template_id:
    #                 email_template_obj = self.env['mail.template'].browse(template_id)
    #                 email_values = {
    #                     'email_to': ','.join(users.mapped('login')),
    #                     'email_from': self.env.user.partner_id.email,
    #                     'body_html': template,
    #                     'subject': _('Bank Transfer Request: Payroll Batch %s - %s', batch.name,
    #                                  currency_symbol + format(total_amount, ',.2f'))
    #                 }
    #                 email_template_obj.send_mail(batch.id, force_send=True, email_values=email_values)
    #
    #         # Make the payslip loan dedcution line approved mapping it to hr.loan module
    #         for slip in self.slip_ids:
    #             # Check if any payslip line name contains 'loan' (case-insensitive)
    #             if any('loan' in name.lower() for name in slip.line_ids.mapped('name')):
    #                 # Find the related loan for the employee
    #                 hr_loan = self.env['hr.loan'].search(
    #                     [('employee_id', '=', slip.employee_id.id), ('state', '=', 'confirm')], limit=1)
    #                 if hr_loan:
    #                     # Get the latest draft installment line
    #                     draft_installments = hr_loan.hr_loan_installment_line_ids.filtered(
    #                         lambda l: l.state == 'draft').sorted(key=lambda l: l.id, reverse=False)
    #                     if draft_installments:
    #                         latest_installment = draft_installments[0]
    #                         latest_installment.write({
    #                             'hr_payslip_run_id': self.id,
    #                             'process_user_id': self.env.user.id,  # User who processed Payroll
    #                             'process_date_time': datetime.now(),  # Current server datetime
    #                             'state': 'paid',
    #                             'remarks': "This loan was adjusted by %s on %s against %s" % (
    #                                 self.env.user.name,
    #                                 datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    #                                 self.name
    #                             ),
    #                         })
    #                     if not self.env['hr.loan'].search(
    #                             [('employee_id', '=', slip.employee_id.id), ('state', '=', 'confirm')],
    #                             limit=1).hr_loan_installment_line_ids.filtered(
    #                             lambda l: l.state == 'draft').sorted(key=lambda l: l.id, reverse=False):
    #                         hr_loan.state == 'paid'
    #
    #         self.state = 'approved'
    #
    #     else:
    #         raise UserError("Action only allowed in CEO Approval state.")
    from datetime import datetime
    from odoo.exceptions import UserError

    def action_approve_ceo(self):
        for batch in self:
            if all(r.state == 'ceo_approval' for r in batch):
                total_amount = sum(slip.net_wage for slip in batch.slip_ids)
                currency_symbol = batch.company_id.currency_id.symbol

                # Send email to Bank Auditor
                users = self.env.ref('hr_payroll_approver.group_payroll_bank_auditor').users
                if not users:
                    raise UserError(_("No users configured as Bank Auditor, Please configure."))

                for batch_rec in batch:
                    template = """
                    <body style="font-family:sans-serif;line-height:2;">
                    Hello {username},<br/>
                    Payroll batch <b>{batch}</b> has been approved by CEO.<br/>
                    <p>Please process an internal transfer between company banks for the total amount: 
                    <b>{currency_symbol}{total_amount:,.2f}</b></p>
                    <p>This amount covers {employee_count} employees in this payroll batch.</p>
                    Thanks.<br/><hr/>
                    <p style="color:#8a8686;">{description}</p></body>
                    """.format(
                        username=users[0].name,
                        batch=batch_rec.name,
                        description=batch_rec.company_id.name,
                        currency_symbol=currency_symbol,
                        total_amount=total_amount,
                        employee_count=len(batch_rec.slip_ids)
                    )

                    template_id = self.env.ref('hr_payroll_approver.email_template_payroll_approve').id
                    if template_id:
                        email_template_obj = self.env['mail.template'].browse(template_id)
                        email_values = {
                            'email_to': ','.join(users.mapped('login')),
                            'email_from': self.env.user.partner_id.email,
                            'body_html': template,
                            'subject': _('Bank Transfer Request: Payroll Batch %s - %s') % (
                                batch_rec.name, currency_symbol + format(total_amount, ',.2f'))
                        }
                        email_template_obj.send_mail(batch_rec.id, force_send=True, email_values=email_values)

                # Handle loan installments
                # for slip in batch.slip_ids:
                #     if any('loan' in name.lower() for name in slip.line_ids.mapped('name')):
                #         hr_loan = self.env['hr.loan'].search(
                #             [('employee_id', '=', slip.employee_id.id), ('state', '=', 'confirm')],
                #             limit=1
                #         )
                #         if hr_loan:
                #             draft_installments = hr_loan.hr_loan_installment_line_ids.filtered(
                #                 lambda l: l.state == 'draft'
                #             ).sorted(key=lambda l: l.id)
                #
                #             # Mark first draft as paid
                #             if draft_installments:
                #                 latest_installment = draft_installments[0]
                #                 latest_installment.write({
                #                     'hr_payslip_run_id': batch.id,
                #                     'process_user_id': self.env.user.id,
                #                     'process_date_time': datetime.now(),
                #                     'state': 'paid',
                #                     'remarks': latest_installment.remarks or "This loan was adjusted by %s on %s against %s" % (
                #                         self.env.user.name,
                #                         datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                #                         batch.name
                #                     ),
                #                 })
                #
                #             # If *all* installments are paid → mark loan as paid
                #             unpaid_installments = hr_loan.hr_loan_installment_line_ids.filtered(
                #                 lambda l: l.state != 'paid'
                #             )
                #             if not unpaid_installments:
                #                 hr_loan.state = 'paid'

                batch.state = 'approved'
            else:
                raise UserError(_("Action only allowed in CEO Approval state."))

    def action_reject_ceo(self):
        #         for rec in self:
        if all(r.state == 'ceo_approval' for r in self):
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'payroll.rejection.reason.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {'rejection_department': 'ceo_rejected'}
            }
        else:
            raise UserError("Action only allowed in CEO Approval state.")

    def payroll_approval_send_mail(self, to_email_list, username, approval_stage=None, approved_by=None):
        """
        Send approval notification emails with proper messages for each approval stage
        
        Args:
            to_email_list: List of email addresses to send to
            username: Name of the recipient
            approval_stage: Current approval stage (hr_approval, auditor_approval, finance_approval, ceo_approval)
            approved_by: Name of the person who approved the previous stage
        """
        for batch in self:
            # Calculate batch details for context
            total_amount = sum(slip.net_wage for slip in batch.slip_ids)
            currency_symbol = batch.company_id.currency_id.symbol
            employee_count = len(batch.slip_ids)

            # Define stage-specific messages
            stage_messages = {
                'hr_approval': {
                    'title': 'HR Approval Required',
                    'message': f"""
                        <p>Hello {username},</p>
                        <p>A new payroll batch <b>{batch.name}</b> has been submitted and requires your HR approval.</p>
                        <p><strong>Batch Details:</strong></p>
                        <ul>
                            <li>Total Amount: {currency_symbol}{total_amount:,.2f}</li>
                            <li>Number of Employees: {employee_count}</li>
                            <li>Company: {batch.company_id.name}</li>
                        </ul>
                        <p>Please review the payroll batch and approve or reject accordingly.</p>
                        <p>Thanks.</p>
                    """
                },
                'auditor_approval': {
                    'title': 'Auditor Approval Required',
                    'message': f"""
                        <p>Hello {username},</p>
                        <p>Payroll batch <b>{batch.name}</b> has been approved by HR and now requires your audit review.</p>
                        <p><strong>Batch Details:</strong></p>
                        <ul>
                            <li>Total Amount: {currency_symbol}{total_amount:,.2f}</li>
                            <li>Number of Employees: {employee_count}</li>
                            <li>Approved by: {approved_by or 'HR Department'}</li>
                        </ul>
                        <p>Please review the payroll calculations and approve or reject accordingly.</p>
                        <p>Thanks.</p>
                    """
                },
                'finance_approval': {
                    'title': 'Finance Approval Required',
                    'message': f"""
                        <p>Hello {username},</p>
                        <p>Payroll batch <b>{batch.name}</b> has been approved by the Auditor and now requires your financial approval.</p>
                        <p><strong>Batch Details:</strong></p>
                        <ul>
                            <li>Total Amount: {currency_symbol}{total_amount:,.2f}</li>
                            <li>Number of Employees: {employee_count}</li>
                            <li>Approved by: {approved_by or 'Auditor'}</li>
                        </ul>
                        <p>Please review the financial aspects and approve or reject accordingly.</p>
                        <p>Thanks.</p>
                    """
                },
                'ceo_approval': {
                    'title': 'CEO Approval Required',
                    'message': f"""
                        <p>Hello {username},</p>
                        <p>Payroll batch <b>{batch.name}</b> has been approved by Finance and now requires your final approval.</p>
                        <p><strong>Batch Details:</strong></p>
                        <ul>
                            <li>Total Amount: {currency_symbol}{total_amount:,.2f}</li>
                            <li>Number of Employees: {employee_count}</li>
                            <li>Approved by: {approved_by or 'Finance Department'}</li>
                        </ul>
                        <p>This is the final approval step before payroll processing. Please review and approve or reject accordingly.</p>
                        <p>Thanks.</p>
                    """
                }
            }

            # Get the appropriate message based on approval stage
            if approval_stage and approval_stage in stage_messages:
                message_data = stage_messages[approval_stage]
                template = f"""
                    <body style="font-family:sans-serif;line-height:2;">
                    {message_data['message']}
                    <hr/>
                    <p style="color:#8a8686;">{batch.company_id.name}</p>
                    </body>
                """
                subject = _(f"{message_data['title']}: Payroll Batch {batch.name}")
            else:
                # Fallback to generic message
                template = f"""
               <body style="font-family:sans-serif;line-height:2;">
                    <p>Hello {username},</p>
                    <p>Please approve payroll batch <b>{batch.name}</b></p>
                    <p><strong>Batch Details:</strong></p>
                    <ul>
                        <li>Total Amount: {currency_symbol}{total_amount:,.2f}</li>
                        <li>Number of Employees: {employee_count}</li>
                    </ul>
                    <p>Thanks.</p>
                <hr/>
                    <p style="color:#8a8686;">{batch.company_id.name}</p>
                </body>
                """
                subject = _('Approval Request: Payroll Batch %s', batch.name)

            template_id = self.env.ref('hr_payroll_approver.email_template_payroll_approve').id
            if template_id:
                email_template_obj = self.env['mail.template'].browse(template_id)
                email_values = {
                    'email_to': ','.join(to_email_list),
                    'email_from': self.env.user.partner_id.email,
                    'body_html': template,
                    'subject': subject
                }
                email_template_obj.send_mail(batch.id, force_send=True, email_values=email_values)
        return True

    def _send_rejection_notification(self, rejected_by):
        # Send notification to creator of the batch
        creator = self.create_uid
        if not creator:
            return

        for batch in self:
            template = """
               <body style="font-family:sans-serif;line-height:2;">
               <p>Hello,</p>
               <p>Payroll batch <b>{batch}</b> has been <span style="color:red;">rejected</span> at the {rejected_by} approval stage.</p>
               <p>Please review the batch and make necessary corrections before resubmitting for approval.</p>
               <p>Thanks.</p>
               <hr/>
               <p style="color:#8a8686;">{description}</p>
               </body>
            """.format(
                batch=batch.name,
                description=batch.company_id.name,
                rejected_by=rejected_by
            )

            template_id = self.env.ref('hr_payroll_approver.email_template_payroll_approve').id
            if template_id:
                email_template_obj = self.env['mail.template'].browse(template_id)
                email_values = {
                    'email_to': creator.partner_id.email,
                    'email_from': self.env.user.partner_id.email,
                    'body_html': template,
                    'subject': _('Payroll Batch %s Rejected', batch.name)
                }
                email_template_obj.send_mail(batch.id, force_send=True, email_values=email_values)

    @api.depends('slip_ids', 'state')
    def _compute_state_change(self):
        pass

    def action_draft(self):
        res = super(HrPayslipRun, self).action_draft()
        # empty the payslip generated field
        self.slip_ids.unlink()
        return res
