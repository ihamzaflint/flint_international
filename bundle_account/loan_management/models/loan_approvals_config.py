# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import re


class LoanApprovalConfig(models.Model):
    _name = "loan.approval.config"
    _description = 'Loan Approval Config'
    _rec_name = 'name'
    _order = 'id desc'

    name = fields.Char('Hierarchy Name')
    code = fields.Char('Code')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
    ], default='draft', string='Status')
    journal_id = fields.Many2one('account.journal', string='Journal', required=True)
    debit_account_id = fields.Many2one('account.account', string='Debit Account', required=True)
    credit_account_id = fields.Many2one('account.account', string='Credit Account', required=True,
                                        related="journal_id.default_account_id")
    loan_approval_line_ids = fields.One2many(
        'loan.approval.line',
        'loan_approval_config_id',
        string='Loan Approval Line'
    )

    @api.onchange('name')
    def _onchange_name(self):
        for rec in self:
            if not rec.code:
                rec.code = re.sub(r'[^a-zA-Z0-9]', '_', rec.name).lower() if rec.name else ''

    def button_confirm(self):
        """
        Activate record for use.
        """
        for rec in self:
            if self.env['loan.approval.config'].search_count([('code', '=', rec.code), ('state', '=', 'confirm')]) == 0:
                rec.write({'state': 'confirm'})
            else:
                raise ValidationError(
                    _('Another record with the same code already exists. Please choose a unique code.'))

    def button_draft(self):
        """
        Draft record to stop use.
        """
        for rec in self:
            rec.state = 'draft'


class PurchaseApprovalLine(models.Model):
    _name = 'loan.approval.line'
    _description = 'Loan Approval Line'

    loan_approval_config_id = fields.Many2one('loan.approval.config', string='Loan Approval Config')
    approver_id = fields.Many2one('res.users', string="Approver")
