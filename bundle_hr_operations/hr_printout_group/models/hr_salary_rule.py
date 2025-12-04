# -*- coding:utf-8 -*-
from odoo import fields, models


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    print_out_group_id = fields.Many2one('print.out.group', string="Print Out Group")