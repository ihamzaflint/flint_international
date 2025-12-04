# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class RecruitmentPolicy(models.Model):
    _name = 'recruitment.policy'
    _description = 'Recruitment Policy'

    name = fields.Char(required=True)
    stage = fields.Selection([
        ('draft', 'Draft'),
        ('head_hunting', 'Head Hunting'),
        ('client_selection', 'Client Selection'),
        ('in_progress', 'In Progress'),
    ], required=True, copy=False)
    max_days = fields.Integer(string="Max Days in Stage", required=True,
                              help="Number of days before sending a notification")

    @api.constrains('stage')
    def _check_unique_stage(self):
        """ Ensure that each stage has only one policy. """
        for record in self:
            existing_policy = self.search([
                ('stage', '=', record.stage),
                ('id', '!=', record.id)
            ])
            if existing_policy:
                raise ValidationError(f"A policy for the stage '{record.stage}' already exists.")

    @api.constrains('max_days')
    def _check_max_days(self):
        for record in self:
            if record.max_days <= 0:
                raise ValidationError("Max Days in Stage must be greater than zero.")
