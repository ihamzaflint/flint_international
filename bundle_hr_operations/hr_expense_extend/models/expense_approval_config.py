# -*- coding: utf-8 -*-
from odoo import fields, models, _, api
from odoo.exceptions import UserError, ValidationError
import re


class ExpenseApprovalConfig(models.Model):
    _name = 'expense.approval.config'
    _description = 'Purchase Order Approval Config'
    _rec_name = 'name'
    _rec_names_search = ['name', 'code']
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string="Hierarchy Name", tracking=True, required=True)
    code = fields.Char(string="Code", tracking=True, required=True)
    min_limit = fields.Float(string="Min Limit")
    max_limit = fields.Float(string="Max Limit")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('lock', 'Lock'),
    ],
        string='Status', default='draft', tracking=True
    )

    expense_approval_config_line_ids = fields.One2many(
        'expense.approval.config.line', 'expense_approval_config_id',
        string="Approval Lines", tracking=True
    )

    @api.onchange('name')
    def _onchange_name(self):
        for rec in self:
            if not rec.code:
                rec.code = re.sub(r'[^a-zA-Z0-9]', '_', rec.name).lower() if rec.name else ''

    def change_state_to_lock(self):
        """
        Changes the state of the approval configuration to 'lock'.
        Once locked, the configuration cannot be edited or modified.
        Also, ensures the min/max limits do not collide with existing locked configurations.
        """
        for rec in self:
            exclude_self_domain = [('id', '!=', rec.id)] if rec.id else []

            if self.env['expense.approval.config'].search_count([('code', '=', rec.code),('state', '=', 'lock'),] + exclude_self_domain) > 0:
                raise ValidationError(_("Another record with the same code already exists and is locked. Please choose a unique code."))

            elif self.env['expense.approval.config'].search([('state', '=', 'lock'),('min_limit', '<=', rec.max_limit),('max_limit', '>=', rec.min_limit),] + exclude_self_domain,  limit=1):
                raise ValidationError(_("The limits of this configuration collide with an already locked configuration."))

            elif rec.min_limit >= rec.max_limit:
                raise ValidationError(_("Min Limit or Max Limit cannot be equal or intersect each other."))

            elif not rec.expense_approval_config_line_ids:
                raise ValidationError(_("There should be at-least 1 approver present."))

            else:
                rec.state = 'lock'

    def change_state_to_draft(self):
        """
        Changes the state of the approval configuration to 'draft'.
        This allows the configuration to be edited or modified.
        """
        for rec in self:
            rec.state = 'draft'

class ExpenseApprovalConfigLine(models.Model):
    _name = 'expense.approval.config.line'
    _description = 'Expense Approval Config Line'

    expense_approval_config_id = fields.Many2one('expense.approval.config')
    approver_id = fields.Many2one('res.users', string="Approvers")
