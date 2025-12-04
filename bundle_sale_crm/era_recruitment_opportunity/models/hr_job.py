# -*- coding: utf-8 -*-

from odoo import fields, models, api


class HrJob(models.Model):
    _inherit = 'hr.job'

    lead_id = fields.Many2one('crm.lead')
