# -*- coding: utf-8 -*-
from odoo import models, fields, _, api


class ItqHrBenefitIntegration(models.Model):
    _inherit = 'itq.hr.benefit.integration'

    is_used = fields.Boolean(compute="check_is_used", compute_sudo=True)

    def check_is_used(self):
        for rec in self:
            rec.is_used = False
            contracts = self.env['hr.contract'].sudo().search(['|', ('valuable_benefit_ids', '!=', False),
                                                               ('non_valuable_benefit_ids', '!=', False)])
            if contracts:
                if contracts.mapped('valuable_benefit_ids').filtered(lambda b: b.benefit_id == rec) or\
                        contracts.mapped('non_valuable_benefit_ids').filtered(
                            lambda b: b.benefit_id == rec):
                    rec.is_used = True

