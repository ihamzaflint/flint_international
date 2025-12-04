# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from six import raise_from


class HrExpenseSheetExt(models.Model):
    _inherit = 'hr.expense.sheet'

    # expense hierarchy fields
    config_name = fields.Char(string="Hierarchy Name", tracking=True)
    config_code = fields.Char(string="Code", tracking=True)
    config_min_limit = fields.Float(string="Min Limit")
    config_max_limit = fields.Float(string="Max Limit")

    state = fields.Selection(
        selection=[
            ('draft', 'To Submit'),
            ('submit', 'Submitted'),
            ('waiting_approvals', 'Waiting Approvals'),
            ('approve', 'Approved'),
            ('post', 'Posted'),
            ('done', 'Done'),
            ('cancel', 'Refused')
        ],
        string="Status",
        compute='_compute_state', store=True, readonly=True,
        index=True,
        required=True,
        default='draft',
        tracking=True,
        copy=False,
    )

    hr_expense_sheet_approver_line_ids = fields.One2many(
        'hr.expense.sheet.approver.line', 'hr_expense_shet_expense_approval_id',
        string="Approver List", tracking=True
    )
    petty_cash_journal_id = fields.Many2one('account.journal', string="Petty Cash Journal",
                                            domain=[('is_petty_cash', '=', True)], relation='petty_cash_journal_id_rel')
    petty_cash_limit = fields.Integer(string="Petty Cash (Available)", compute="_compute_petty_cash_limit")

    @api.depends('petty_cash_journal_id')
    def _compute_petty_cash_limit(self):
        for rec in self:
            if rec.petty_cash_journal_id:
                # Use journal's default_account_id (usually how journals are linked to accounts)
                account = rec.petty_cash_journal_id.default_account_id
                if account:
                    move_lines = self.env['account.move.line'].search([
                        ('account_id', '=', account.id)
                    ])
                    total_debit = sum(line.debit for line in move_lines)
                    total_credit = sum(line.credit for line in move_lines)
                    rec.petty_cash_limit = total_debit - total_credit
                else:
                    rec.petty_cash_limit = 0.0
            else:
                rec.petty_cash_limit = 0.0

    def action_submit_sheet(self):
        for rec in self:
            if rec.user_id:
                rec.activity_schedule(
                    'mail.mail_activity_data_todo',
                    user_id=rec.user_id.id,
                    note="Please review and submit your expense sheet for approval.",
                    summary=f"Expense Sheet Submitted: {rec.name}"
                )
            return super(HrExpenseSheetExt, self).action_submit_sheet()

    def action_approve_expense_sheets(self):
        for rec in self:
            # Mark existing activities for this sheet as done (e.g., initial "submit to manager" activity)
            if self.env.user.id == rec.user_id.id:
                if rec.activity_ids:
                    rec.activity_ids.action_done()

                # If no approver lines are present, request approval based on configuration
                if not rec.hr_expense_sheet_approver_line_ids:
                    rec.request_approval()

            elif not rec.user_id:
                rec.request_approval()

            else:
                raise ValidationError(_("You cannot approve this request."))


                # # Set state to 'waiting_approvals' as the approval process has started
                # rec.state = 'waiting_approvals'

    def request_approval(self):
        for rec in self:
            # Find active approval configurations based on amount range
            expense_approval_config = self.env['expense.approval.config'].search([('state', '=', 'lock')]).filtered(lambda l: l.min_limit <= rec.total_amount <= l.max_limit)

            if not expense_approval_config:
                rec.state = 'approve'

                # raise UserError("No active approval configuration found for this expense amount.")
            if expense_approval_config:
                expense_approval_config = expense_approval_config[0] # Limit to 1 config

                # For visibility on each expense
                rec.config_name = expense_approval_config.name
                rec.config_code = expense_approval_config.code
                rec.config_min_limit = expense_approval_config.min_limit
                rec.config_max_limit = expense_approval_config.max_limit

                approver_lines = []
                for line in expense_approval_config.expense_approval_config_line_ids.sorted('id'):
                    approver_lines.append((0, 0, {
                        'approver_id': line.approver_id.id,
                        'is_approved': False,
                    }))

                # Clear existing approval lines (Safety Mechanism) and assign new ones
                rec.hr_expense_sheet_approver_line_ids = [(5, 0, 0)]
                rec.hr_expense_sheet_approver_line_ids = approver_lines

                # Schedule activity for the first approver in the list
                first_approver_line = rec.hr_expense_sheet_approver_line_ids.sorted('id')
                if first_approver_line and first_approver_line[0].approver_id:
                    rec.activity_schedule(
                        'mail.mail_activity_data_todo',
                        user_id=first_approver_line[0].approver_id.id,
                        note=f"Please approve the expense sheet: {rec.name}.",
                        summary=f"Approval Required: {rec.name}"
                    )

                # Set state to 'waiting_approvals' after initiating the approval workflow
                rec.state = 'waiting_approvals'

    def approve_expense_request(self):
        for rec in self:
            current_user = self.env.user  # Logged in user
            # Get approval lines, sorted to ensure consistent order for sequential approvals
            expense_approval_lines = rec.hr_expense_sheet_approver_line_ids.sorted('id')

            # Find the first pending approval line for the current user
            current_user_approval_line = expense_approval_lines.filtered(lambda l: l.approver_id == current_user and not l.is_approved)

            # Validate if the current user is indeed the one who should approve
            # Optionally, you might want to check if they are the FIRST pending approver if strict sequential.
            # For now, this allows any user with a pending line to approve their own.
            if not current_user_approval_line:
                raise UserError(_("You are not authorized to approve this expense at this stage, or your approval is already recorded."))

            # 1. Mark the current user's approval line as approved
            current_user_approval_line.is_approved = True
            rec.activity_ids.action_done()

            # 2. Mark the corresponding activity as done for the current user
            # Search for the specific activity associated with this expense sheet and the current user
            activity_to_complete = self.env['mail.activity'].search([
                ('res_model', '=', rec._name),  # Use rec._name for the model name
                ('res_id', '=', rec.id),
                ('user_id', '=', current_user.id),
                ('activity_type_id.category', '=', 'todo'),  # Target 'To Do' activities
                ('summary', 'ilike', 'Approval Required%'),  # More specific to approval activities
            ], limit=1)

            if activity_to_complete:
                # Use action_feedback to mark activity as done with a log message
                activity_to_complete.action_feedback(feedback=f"Expense sheet approved by {current_user.name}")
            # Else: No activity found for this user/expense, possibly manually cleared or an unusual state.

            # 3. Re-evaluate remaining pending lines after the current approval
            pending_lines_after_current_approval = expense_approval_lines.filtered(lambda l: not l.is_approved)

            if pending_lines_after_current_approval:
                # There are still remaining approvers, schedule activity for the next in sequence
                next_approver_line = pending_lines_after_current_approval[0]  # Assumes sorted order (by ID or sequence)
                if next_approver_line and next_approver_line.approver_id:
                    rec.activity_schedule(
                        'mail.mail_activity_data_todo',
                        user_id=next_approver_line.approver_id.id,
                        note=f"Please approve the expense sheet: {rec.name}.",
                        summary=f"Approval Required: {rec.name}"
                    )
                rec.state = 'waiting_approvals'  # State remains 'waiting_approvals'
            else:
                # All approval lines are now approved
                rec.state = 'approve'

    def action_reset_approval_expense_sheets(self):
        """
        Resets the approval process and clears approval-related fields when the expense order is reset to draft.
        - Clears configuration fields (`config_name`, `config_code`, etc.).
        - Deletes all approval lines to allow a new hierarchy to be applied upon re-confirmation.
        - Clears all related mail activities.
        """
        for rec in self:
            rec.config_name = False
            rec.config_code = False
            rec.config_min_limit = 0.0
            rec.config_max_limit = 0.0
            rec.hr_expense_sheet_approver_line_ids.unlink()
            rec.activity_ids.unlink()

        return super(HrExpenseSheetExt, self).action_reset_approval_expense_sheets()

class HrExpenseSheetApprovalLine(models.Model):
    _name = 'hr.expense.sheet.approver.line'
    _description = 'Hr Expense Approval Line'

    hr_expense_shet_expense_approval_id = fields.Many2one('hr.expense.sheet')
    approver_id = fields.Many2one('res.users', string="Approvers")
    is_approved = fields.Boolean(string="Approved", default=False)

    def schedule_activity_for_approver(self):
        for line in self:
            if line.is_approved:
                raise ValidationError(_("This Approver line is already approved. You can only change approver before approval."))
            line.hr_expense_shet_expense_approval_id.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=line.approver_id.id,
                note="Please review and submit your expense sheet for approval.",
                summary=f"Expense Sheet Submitted: {line.hr_expense_shet_expense_approval_id.name}"
            )
