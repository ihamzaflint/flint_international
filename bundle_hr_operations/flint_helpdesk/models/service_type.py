from odoo import fields, models, _


class ServiceType(models.Model):
    _inherit = "service.type"

    helpdesk_type_id = fields.Many2one('helpdesk.ticket.type', string="Service Category")
    logistic_order_type = fields.Selection([
        ('flight', 'Flight'),
        ('hotel', 'Hotel'),
        ('insurance', 'Insurance'),
        ('pick_up_drop_off', 'Pick-up / Drop-Off'),
        ('courier', 'Courier'),
    ], string='Logistic Order Type')
    is_logistics = fields.Boolean(string='Is Logistics', related='helpdesk_type_id.is_logistics', readonly=True)