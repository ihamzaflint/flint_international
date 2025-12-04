from odoo import api, fields, models, _
import requests
from urllib.parse import urljoin
import logging
import json
from .zk_transactions import LOGIN_URL
from odoo.exceptions import ValidationError
_logger = logging.getLogger(__name__)


class ItqAttendanceFpConfig(models.Model):
    _name = 'itq.attendance.punch.config'
    _inherit = 'mail.thread'
    _rec_name = 'sequence'
    _description = 'New Attendance Punch Setting'

    sequence = fields.Char(string='Sequence', readonly=True, default=_("NEW"))
    zk_machine_ip = fields.Char(string="Server IP", tracking=True, help="Set Server IP with port")
    zk_username = fields.Char(string="Username", tracking=True)
    zk_password = fields.Char(string="Password")
    zk_start_date = fields.Datetime(string="Start Date", tracking=True)
    zk_last_action_date = fields.Datetime(string="Last Action Date", tracking=True)
    zk_last_check_date = fields.Datetime(string="Last Connection Check Date", tracking=True)
    zk_action_type = fields.Selection(string="Data Importing", selection=[('manual', 'Manual'), ('auto', 'Automatic'), ], default='auto', tracking=True)
    check_in_indicators = fields.Char(string="Check-in Indicators", tracking=True)
    check_out_indicators = fields.Char(string="Check-out Indicators", tracking=True)
    connection_state = fields.Selection(string="Connection Status", selection=[('fail', 'Connection Failed'), ('success', 'Connection Succeeded')], tracking=True)

    @api.model
    def create(self, vals):
        res = super(ItqAttendanceFpConfig, self).create(vals)
        res.sequence = self.env['ir.sequence'].next_by_code('itq.attendance.fp.config') or _('New')
        return res

    @api.constrains('zk_machine_ip')
    def _constrain_zk_machine_ip(self):
        for rec in self:
            if self.search_count([('zk_machine_ip', '=', rec.zk_machine_ip)]) > 1:
                raise ValidationError(_("Machine IP must be unique"))

    def check_zk_credentials(self):
        self.ensure_one()
        if self.zk_machine_ip and self.zk_username and self.zk_password:
            try:
                url = self.zk_machine_ip
                if not url.startswith('http'):
                    url = 'http://' + url
                url = urljoin(url, LOGIN_URL)
                headers = {
                    'Content-Type': 'application/json'
                }
                data = {
                    'username': self.zk_username,
                    'password': self.zk_password,
                }
                response = requests.post(url, data=json.dumps(data), headers=headers)
                _logger.info('requesting %s' % url)
                response.json()['token']
                self.connection_state = 'success'
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'type': 'success',
                        'title': _('ZK Connection'),
                        'message': 'connection success',
                        'sticky': False,
                    }
                }
            except Exception as e:
                _logger.warning('fail to request %s' % url)
                _logger.warning(e)
                self.connection_state = 'fail'
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'type': 'danger',
                        'title': _('ZK Connection'),
                        'message': 'connection Failed',
                        'sticky': False,
                    }
                }
            finally:
                self.zk_last_check_date = fields.Datetime.now()



