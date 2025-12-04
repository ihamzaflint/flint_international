# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class BlockVisaJobCategory(models.Model):
    _name = 'block.visa.job.category'
    _description = 'Block Visa Job Category'

    request_id = fields.Many2one('block.visa.request', string='Visa Request', required=True)
    job_title = fields.Char(string='Job Title', required=True)
    number_of_positions = fields.Integer(string='Number of Positions', required=True)
    minimum_salary = fields.Float(string='Minimum Salary')
    qualification = fields.Char(string='Required Qualification')
    experience_years = fields.Integer(string='Required Experience (Years)')
    nationality_preference = fields.Many2many('res.country', string='Preferred Nationalities')
    
    @api.constrains('number_of_positions')
    def _check_positions(self):
        for record in self:
            if record.number_of_positions <= 0:
                raise ValidationError(_('Number of positions must be greater than zero.'))

