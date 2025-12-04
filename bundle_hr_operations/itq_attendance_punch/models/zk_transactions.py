import sys
from odoo import api, fields, models, _
import logging
import requests
import json
from urllib.parse import urljoin, urlencode
from datetime import datetime
import pytz
from odoo.exceptions import ValidationError
_logger = logging.getLogger(__name__)


LOGIN_URL = '/jwt-api-token-auth/'
TRANSACTIONS_URL = '/iclock/api/transactions/'
MAX_RECORDS = sys.maxsize


class ZKTransaction(models.Model):
    _name = 'itq.attendance.punch'
    _description = 'Attendance Punch'
    _rec_name = 'employee_name'

    zk_id = fields.Integer(string='ZK ID')
    employee_name = fields.Char()
    emp_code = fields.Char('Employee Code')
    punch_time = fields.Datetime()
    punch_state = fields.Char()
    transfer = fields.Boolean(default=False, readonly=True)
    incorrect = fields.Boolean(default=False, readonly=True)
    error = fields.Text('Error', readonly=True)
    punch_log_id = fields.Many2one(comodel_name="punch.import.history", string="Punch Import History", required=False, )
    machine_id = fields.Many2one(comodel_name="itq.attendance.punch.config", string="Machine ID", required=False, )

    _sql_constraints = [
        ('unique_zk_id', 'UNIQUE(zk_id)', 'zk_id must be unique')
    ]

    @api.model
    def set_default_finger_machine(self):
        self.sudo().search([('machine_id', '=', False)]).write({'machine_id': self.env.ref('itq_attendance_punch.itq_attendance_default_fp').id})

    def generate_attendance_punch_manual(self):
        self.with_context(generate_zk_punch_import=True).get_transaction()

    def _get_attendance_from_date(self, machine=None):
        if machine:
            self.flush(['punch_time'])
            self._cr.execute("select max(punch_time) from itq_attendance_punch")
            zk_start_date = machine.zk_start_date
            zk_last_action_date = machine.zk_last_action_date
            # max_punch_time = self._cr.fetchone()
            start_time = zk_last_action_date or zk_start_date
            if start_time:
                return start_time
            else:
                return False
        return False

    def _generate_punch_imported_log(self, start_time=None, end_time=None, records=None, machine=None):
        if records and machine:
            machine.sudo().write({'zk_last_action_date': fields.Datetime.now()})
            import_vals = {
                'user_id': self.env.user.id,
                'text': "Data Imported Successfully",
                'zk_action_date': fields.Datetime.now(),
                'zk_action_type': machine.zk_action_type,
                'date_from': start_time,
                'date_to': end_time,
                'count': len(records),
                'machine_id': machine.id,
            }
            log_id = self.env['punch.import.history'].sudo().create(import_vals)
            records.sudo().write({'punch_log_id': log_id.id})

    def get_transaction(self, count=MAX_RECORDS):
        machines = self.env['itq.attendance.punch.config'].sudo().search([])
        for machine in machines:
            token = self._get_login_token(machine=machine)
            if token:
                url = machine.zk_machine_ip
                if not url:
                    continue
                if machine.zk_action_type == 'manual' and not self.env.context.get('generate_zk_punch_import', False):
                    continue
                if self.env.context.get('generate_zk_punch_import', False) and len(machines.filtered(lambda m: m.zk_action_type == 'manual')) < 1:
                    next_date_action = self.env.ref('itq_attendance_punch.ir_cron_zkt_transactions').nextcall
                    raise ValidationError(_("You can't import Attendance Punch Manual, will imported Automatic at %s")%next_date_action)
                start_time = self._get_attendance_from_date(machine=machine)
                if not start_time:
                    continue
                if not url.startswith('http'):
                    url = 'http://' + url
                url = urljoin(url, TRANSACTIONS_URL)

                end_time = fields.Datetime.now()
                # TODO: we should get records in patch
                params = {
                    'start_time': start_time,
                    'end_time': end_time,
                    'page_size': count,
                }
                url += '?%s' % urlencode(params)
                self._get_transaction(token, url, machine, start_time, end_time)

    def _get_transaction(self, token, url, machine=None, start_time=None, end_time=None):
        if machine:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'JWT %s' % token,
            }
            try:
                _logger.info('requesting  %s from %s to %s' % (url, start_time, end_time))
                response = requests.get(url, headers=headers)
                json_response = response.json()
                next_page = json_response.get('next')
                count = json_response.get('count', 0)
                print('count:- ', count)
                transaction_fields = ['id', 'emp_code', 'employee_name', 'punch_time', 'punch_state']
                vals = self.parse_response(json_response.get('data', []), transaction_fields)
                vals[0]['employee_name'] = self.env['hr.employee'].search([('zk_emp_code', '=', vals[0]['emp_code'])]).name
                records = self._insert_transactions(vals, machine=machine)
                self._generate_punch_imported_log(start_time=start_time, end_time=end_time, records=records, machine=machine)
                # if next_page:
                #     self._get_transaction(token, next_page)
            except Exception as e:
                _logger.warning('fail to request %s' % url)
                _logger.warning(e)

    def _insert_transactions(self, transactions, machine=None):
        if machine:
            # TODO: insert them via sql instead?
            records = self.sudo().create(transactions)
            records.sudo().write({'machine_id': machine.id})
            _logger.info('created (%s) punch time records', len(records))
            return records
        return False

    @api.model
    def parse_response(self, response_data, transaction_fields):
        parsed_records = []
        for rec in response_data:
            user_punch_time = rec.pop('punch_time')
            user_punch_time = fields.Datetime.from_string(user_punch_time)
            user_punch_time = pytz.timezone(self.env.context['tz']).localize(user_punch_time)
            utc_punch_time = user_punch_time.astimezone(pytz.UTC)
            rec['punch_time'] = utc_punch_time.replace(tzinfo=None)
            parsed_records.append({'zk_id' if f == 'id' else f: rec.get(f) for f in transaction_fields})
        return parsed_records

    @api.model
    def _get_login_token(self, machine=None):
        if machine:
            try:
                url = machine.zk_machine_ip
                zk_username = machine.zk_username
                zk_password = machine.zk_password
                if not (url and zk_password and zk_username):
                    _logger.warning('Could not find ZK tech device settings')
                    return False
                if not url.startswith('http'):
                    url = 'http://' + url
                url = urljoin(url, LOGIN_URL)
                headers = {
                    'Content-Type': 'application/json'
                }
                data = {
                    'username': zk_username,
                    'password': zk_password,
                }
                response = requests.post(url, data=json.dumps(data), headers=headers)
                return response.json()['token']
            except Exception as e:
                _logger.warning('fail to request %s' % url)
                _logger.warning(e)
                return False
        return False
