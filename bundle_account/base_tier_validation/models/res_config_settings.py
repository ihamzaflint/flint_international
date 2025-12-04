# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    module_base_tier_validation_formula = fields.Boolean(string="Tier Formula",
                                                         config_parameter=
                                                         'base_tier_validation.module_base_tier_validation_formula')
    module_base_tier_validation_forward = fields.Boolean("Tier Forward & Backward", config_parameter=
                                                         'base_tier_validation.module_base_tier_validation_forward')
    module_base_tier_validation_server_action = fields.Boolean("Tier Server Action",
                                                               config_parameter=
                                                               'base_tier_validation'
                                                               '.module_base_tier_validation_server_action')
    module_base_tier_validation_report = fields.Boolean("Tier Reports",
                                                        config_parameter=
                                                        'base_tier_validation.module_base_tier_validation_report')

    def set_values(self):
        res = super().set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'base_tier_validation.module_base_tier_validation_formula',
            self.module_base_tier_validation_formula)
        self.env['ir.config_parameter'].sudo().set_param(
            'base_tier_validation.module_base_tier_validation_forward',
            self.module_base_tier_validation_forward)
        self.env['ir.config_parameter'].sudo().set_param(
            'base_tier_validation.module_base_tier_validation_server_action',
            self.module_base_tier_validation_server_action)
        self.env['ir.config_parameter'].sudo().set_param(
            'base_tier_validation.module_base_tier_validation_report',
            self.module_base_tier_validation_report)
        return res

    @api.model
    def get_values(self):
        res = super().get_values()
        res.update(
            module_base_tier_validation_formula=self.env['ir.config_parameter'].sudo().get_param(
                'base_tier_validation.module_base_tier_validation_formula', default=False),
            module_base_tier_validation_forward=self.env['ir.config_parameter'].sudo().get_param(
                'base_tier_validation.module_base_tier_validation_forward', default=False),
            module_base_tier_validation_server_action=self.env['ir.config_parameter'].sudo().get_param(
                'base_tier_validation.module_base_tier_validation_server_action', default=False),
            module_base_tier_validation_report=self.env['ir.config_parameter'].sudo().get_param(
                'base_tier_validation.module_base_tier_validation_report', default=False),
        )
        return res
