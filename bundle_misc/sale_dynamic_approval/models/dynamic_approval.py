from odoo import models, api


class DynamicApproval(models.Model):
    _inherit = 'dynamic.approval'

    @api.model
    def _get_approval_validation_model_names(self):
        """ add model sale.order to model options """
        res = super()._get_approval_validation_model_names()
        res.append('sale.order')
        return res
