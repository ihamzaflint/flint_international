from odoo import models, fields


class ClientType(models.Model):
    _name = 'client.type'
    _description = "Client Type"

    name = fields.Char("Client Type")
    code = fields.Char("Code")
