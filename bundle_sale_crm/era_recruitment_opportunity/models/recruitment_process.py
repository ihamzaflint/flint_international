# -*- coding: utf-8 -*-

from odoo import fields, models, api


class RecruitmentProcess(models.Model):
    _name = 'recruitment.process'
    _description = 'Recruitment Process'

    name = fields.Char()
    stages = fields.Many2many('hr.recruitment.stage')
