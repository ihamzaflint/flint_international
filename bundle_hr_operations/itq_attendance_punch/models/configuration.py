import datetime

from odoo import api, fields, models, _
import requests
from urllib.parse import urljoin
import logging
import json
from .zk_transactions import LOGIN_URL
from datetime import datetime
from odoo.exceptions import ValidationError
_logger = logging.getLogger(__name__)


# class ResCompany(models.Model):
#     _inherit = 'res.company'
#
#     zk_start_date = fields.Datetime()
#     zk_last_action_date = fields.Datetime()
#
#     @api.constrains('zk_start_date')
#     def _constrain_zk_start_date(self):
#         for rec in self:
#             if rec.zk_start_date and rec.zk_start_date > datetime.now():
#                 raise ValidationError(_("ZK Start Date Must be less than or equal now"))
#
#
# class ResConfig(models.TransientModel):
#     _inherit = 'res.config.settings'
#
#     zk_machine_ip = fields.Char(config_parameter='zk.machine_ip')
#     zk_username = fields.Char(config_parameter='zk.username')
#     zk_password = fields.Char(config_parameter='zk.password')
#     zk_start_date = fields.Datetime(related='company_id.zk_start_date', readonly=False)
#     zk_last_action_date = fields.Datetime(related='company_id.zk_last_action_date')
#     zk_action_type = fields.Selection(string="Data Importing", selection=[('manual', 'Manual'), ('auto', 'Automatic'), ], default='auto', config_parameter='zk.zk_action_type')
#
#     def check_zk_credentials(self):
#         if self.zk_machine_ip and self.zk_username and self.zk_password:
#             try:
#                 url = self.zk_machine_ip
#                 if not url.startswith('http'):
#                     url = 'http://' + url
#                 url = urljoin(url, LOGIN_URL)
#                 headers = {
#                     'Content-Type': 'application/json'
#                 }
#                 data = {
#                     'username': self.zk_username,
#                     'password': self.zk_password,
#                 }
#                 response = requests.post(url, data=json.dumps(data), headers=headers)
#                 _logger.info('requesting %s' % url)
#                 response.json()['token']
#                 return {
#                     'type': 'ir.actions.client',
#                     'tag': 'display_notification',
#                     'params': {
#                         'type': 'success',
#                         'title': _('ZK Connection'),
#                         'message': 'connection success',
#                         'sticky': False,
#                     }
#                 }
#             except Exception as e:
#                 _logger.warning('fail to request %s' % url)
#                 _logger.warning(e)
#                 return {
#                     'type': 'ir.actions.client',
#                     'tag': 'display_notification',
#                     'params': {
#                         'type': 'danger',
#                         'title': _('ZK Connection'),
#                         'message': 'connection Failed',
#                         'sticky': False,
#                     }
#                 }
