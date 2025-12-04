# -*- coding: utf-8 -*-
from odoo import fields, models, _, api
from odoo.exceptions import UserError, ValidationError
import re


class DocumentType(models.Model):
    _name = 'document.type'
    _description = 'Document Type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _rec_names_search = ['name', 'code']
    _order = 'id desc'

    name = fields.Char(string='Name', required=True, tracking=True)
    code = fields.Char(string='Code', required=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
    ],
        string='Status', default='draft', tracking=True)

    @api.onchange('name')
    def _onchange_name(self):
        for rec in self:
            if not rec.code:
                rec.code = re.sub(r'[^a-zA-Z0-9]', '_', rec.name).lower() if rec.name else ''

    def button_activate(self):
        """
        Activate record for use.
        """
        for rec in self:
            if self.env['document.type'].search_count([('code', '=', rec.code), ('state', '=', 'active')]) == 0:
                rec.write({'state': 'active'})
            else:
                raise ValidationError(
                    _('Another record with the same code already exists. Please choose a unique code.'))

    def button_draft(self):
        """
       Draft record to stop use.
        """
        for rec in self:
            rec.state = 'draft'
