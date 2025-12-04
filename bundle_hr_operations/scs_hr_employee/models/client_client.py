from odoo import models, fields


class ClientClient(models.Model):
    _name = 'client.client'
    _description = 'Client'

    name = fields.Char("Client")
    code = fields.Char("Code")
