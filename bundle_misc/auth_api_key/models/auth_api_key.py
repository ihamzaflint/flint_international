# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import uuid
from odoo import _, api, fields, models, tools
from odoo.exceptions import AccessError, ValidationError
from odoo.tools import consteq


class AuthApiKey(models.Model):
    _name = "auth.api.key"
    _description = "API Key"

    name = fields.Char(required=True)
    key = fields.Char(
        required=True,
        readonly=True,
        copy=False,
        default=lambda self: uuid.uuid4().hex,
        help="""The API key. Enter a dummy value in this field if it is
        obtained from the server environment configuration.""",
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="User",
        required=True,
        default=lambda self: self.env.user,
        help="""The user used to process the requests authenticated by
        the api key""",
    )
    active = fields.Boolean(default=True)
    expiration_date = fields.Datetime(string='Expiration Date')
    company_id = fields.Many2one(
        comodel_name="res.company",
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )

    _sql_constraints = [("key_uniq", "unique(key)", "API Key must be unique!")]

    @api.model
    @api.returns('self', lambda value: value.id)
    def _retrieve_api_key(self, key):
        """Retrieve API key record by key value"""
        return self.sudo().search([
            ('key', '=', key),
            ('active', '=', True)
        ], limit=1)

    def _generate_key(self):
        """Generate a new API key"""
        return uuid.uuid4().hex

    def regenerate_key(self):
        """Regenerate the API key"""
        for record in self:
            record.key = self._generate_key()

    def _get_api_key(self, key):
        """Get API key record by key value"""
        return self.sudo().search([
            ('key', '=', key),
            ('active', '=', True)
        ], limit=1)

    @api.model
    def _retrieve_api_key_id(self, key):
        if not self.env.user.has_group("base.group_system"):
            raise AccessError(_("User is not allowed"))
        api_key = self._get_api_key(key)
        if api_key:
            return api_key.id
        raise ValidationError(_("The key %s is not allowed") % key)

    @api.model
    @tools.ormcache("key")
    def _retrieve_uid_from_api_key(self, key):
        api_key = self.search([('key', '=', key), ('active', '=', True)], limit=1)
        return api_key.user_id.id if api_key else False
    
