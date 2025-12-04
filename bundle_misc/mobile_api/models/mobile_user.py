from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
import uuid
import datetime

_logger = logging.getLogger(__name__)

class MobileUser(models.Model):
    _name = 'mobile.user'
    _description = 'Mobile App User'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Name', related='user_id.name', readonly=True)
    user_id = fields.Many2one(
        'res.users', 
        string='User', 
        required=True, 
        ondelete='cascade',
        domain=[('share', '=', False)]
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        groups='base.group_multi_company',
        help='Company this user belongs to'
    )
    active = fields.Boolean(default=True)
    last_login = fields.Datetime(string='Last Login')
    device_id = fields.Char(string='Device ID')
    device_name = fields.Char(string='Device Name')
    device_model = fields.Char(string='Device Model')
    platform = fields.Selection([
        ('android', 'Android'),
        ('ios', 'iOS'),
    ], string='Platform')
    app_version = fields.Char(string='App Version')
    fcm_token = fields.Char(string='FCM Token', help='Firebase Cloud Messaging token for push notifications')
    api_key = fields.Char(string='API Key', readonly=True, copy=False, groups='base.group_system')
    token_expiry = fields.Datetime(string='Token Expiry', readonly=True, copy=False, groups='base.group_system')
    
    _sql_constraints = [
        ('user_id_uniq', 'unique(user_id)', 'A user can only be registered once for mobile access!'),
    ]
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'api_key' not in vals or not vals['api_key']:
                vals['api_key'] = str(uuid.uuid4())
                vals['token_expiry'] = fields.Datetime.now() + datetime.timedelta(days=30)
        return super(MobileUser, self).create(vals_list)
    
    def generate_new_api_key(self):
        for record in self:
            record.write({
                'api_key': str(uuid.uuid4()),
                'token_expiry': fields.Datetime.now() + datetime.timedelta(days=30)
            })
        return True
    
    def _update_last_login(self):
        self.ensure_one()
        return self.write({'last_login': fields.Datetime.now()})
    
    def check_token_validity(self):
        self.ensure_one()
        if not self.api_key or not self.token_expiry:
            return False
        if self.token_expiry < fields.Datetime.now():
            return False
        return True
    
    def extend_token_validity(self, days=30):
        self.ensure_one()
        if not self.check_token_validity():
            return self.generate_new_api_key()
        self.token_expiry = fields.Datetime.now() + datetime.timedelta(days=days)
        return True
    
    @api.model
    def _cron_cleanup_expired_tokens(self):
        expired_users = self.search([
            ('token_expiry', '<', fields.Datetime.now()),
            ('api_key', '!=', False)
        ])
        if expired_users:
            _logger.info(f"Cleaning up {len(expired_users)} expired mobile user tokens")
            expired_users.write({'api_key': False, 'token_expiry': False})
        return True


class ResUsers(models.Model):
    _inherit = 'res.users'
    
    mobile_user_ids = fields.One2many('mobile.user', 'user_id', string='Mobile Devices')
    mobile_user_count = fields.Integer(compute='_compute_mobile_user_count', string='Mobile Devices Count')
    
    @api.depends('mobile_user_ids')
    def _compute_mobile_user_count(self):
        for user in self:
            user.mobile_user_count = len(user.mobile_user_ids)
