# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'


    user_name = fields.Char(string='User Name', config_parameter='era_muqeem_client.user_name')
    user_pass = fields.Char(string='User Pass', config_parameter='era_muqeem_client.user_pass')
    user_environment=fields.Selection([('sandbox','Sandbox'),('production','Production')],config_parameter='era_muqeem_client.user_environment')





