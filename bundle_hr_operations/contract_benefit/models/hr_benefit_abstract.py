from odoo import models, fields


class ItqHrBenefitBenefitAbstract(models.AbstractModel):
    _name = 'itq.hr.benefit.abstract'
    _inherit = 'mail.thread'
    _description = 'Hr Benefit Abstract'

    benefit_id = fields.Many2one('itq.hr.benefit.integration', required=False,
                                 domain=[("appear_on_contract", '=', True)], ondelete='restrict', tracking=True)
    calculation_type = fields.Selection(related="benefit_id.calculation_type", store=True)
    benefit_value = fields.Float(required=True, tracking=True)
    cap = fields.Float(related='benefit_id.cap')
