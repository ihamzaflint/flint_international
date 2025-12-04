from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'sale.order'

    user_domain = fields.Many2one('res.users', related='partner_id.employee_id.user_id', string='User Domain', readonly=True,  store=True)
    employee_domain = fields.Many2one('hr.employee', related='partner_id.employee_id', string='Employee Domain', readonly=True,  store=True)
    user_id = fields.Many2one(default=False, domain="[('id', '=', user_domain)]")
    employee_id = fields.Many2one('hr.employee', domain="[('id', '=', employee_domain)]", string='Salesperson')

    @api.onchange('partner_id')
    def onchange_sales_person_partner_id(self):
        self.user_id = self.user_domain.id
        self.employee_id = self.employee_domain.id
