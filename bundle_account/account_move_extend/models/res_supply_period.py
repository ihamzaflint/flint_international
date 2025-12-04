# -*- coding: utf-8 -*-
from odoo import fields, models, _, api
from odoo.exceptions import UserError, ValidationError
import re

def get_years():
    return [(str(year), str(year)) for year in range(2000, 2050)]


class ResSupplyPeriod(models.Model):
    _name = 'res.supply.period'
    _rec_name = 'display_name'
    _rec_names_search = ['month', 'year', 'display_name']
    _description = 'Supply Period'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    month = fields.Selection(
        [
            ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
            ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
            ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
        ],
        string='Month',
        tracking=True,
        required=True
    )

    year = fields.Selection(
        selection=get_years(),
        string='Year',
        tracking=True,
        required=True
    )

    display_name = fields.Char(
        string='Name',
        compute='_compute_display_name',
        store=True
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
    ],
        string='Status', default='draft', tracking=True)

    @api.depends('month', 'year')
    def _compute_display_name(self):
        month_dict = dict(self.fields_get(allfields=['month'])['month']['selection'])
        for rec in self:
            month_name = month_dict.get(rec.month)
            if month_name and rec.year:
                rec.display_name = f"{month_name}, {rec.year}"
            else:
                rec.display_name = ''

    def button_activate(self):
        """
        Activate record for use.
        """
        for rec in self:
            if self.env['res.supply.period'].search_count(
                    [('display_name', '=', rec.display_name), ('state', '=', 'active')]) == 0:
                rec.write({'state': 'active'})
            else:
                raise ValidationError(
                    _('Another record with the same period already exists. Please choose a unique code.'))

    def button_draft(self):
        """
       Draft record to stop use.
        """
        for rec in self:
            rec.state = 'draft'
