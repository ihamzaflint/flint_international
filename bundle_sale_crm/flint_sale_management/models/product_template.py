from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.template'

    is_recruitment_service = fields.Boolean(string='Is Recruitment Service')

    def write(self, vals):
        res = super(ProductProduct, self).write(vals)
        if 'is_recruitment_service' in vals:
            self.product_variant_ids.is_recruitment_service = vals['is_recruitment_service']
        return res
