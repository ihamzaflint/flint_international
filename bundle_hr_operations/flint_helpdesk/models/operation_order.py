from odoo import api, fields, models


class GovernmentOrderWithoutPayment(models.Model):
    _inherit = 'operation.order'


    helpdesk_type_id = fields.Many2one('helpdesk.ticket.type', string="Service Category")