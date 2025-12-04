# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class era_muqeem_client(models.Model):
#     _name = 'era_muqeem_client.era_muqeem_client'
#     _description = 'era_muqeem_client.era_muqeem_client'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

