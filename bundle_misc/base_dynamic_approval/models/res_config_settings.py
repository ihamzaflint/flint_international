from odoo import api, fields, models
from odoo.addons.base.models.res_partner import _tz_get


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    email_resource_calendar_id = fields.Many2one(comodel_name='resource.calendar',
                                                 config_parameter='base_dynamic_approval.email_resource_calendar_id',)

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param(
            'base_dynamic_approval.email_resource_calendar_id', self.email_resource_calendar_id.id)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        calendar_value = self.env['ir.config_parameter'].sudo().get_param(
                'base_dynamic_approval.email_resource_calendar_id')
        calendar_value = int(calendar_value) if calendar_value else False
        res.update(
            email_resource_calendar_id=calendar_value
        )
        return res

