from odoo import models, fields, api, _
from odoo.exceptions import AccessError, ValidationError, UserError
import requests
import json
from odoo.http import request
import logging
_logger = logging.getLogger(__name__)
from odoo import http
import socket
import os



class CompanyInherit(models.Model):
    _inherit = "res.company"

    user = fields.Char(string="UserName")
    password = fields.Char(string="Password")


    def show_popup(self, title, message, sticky=True, type='danger'):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _(title),
                'message': _(message),
                'type': type,
                'sticky': sticky,
                'next': {
                    'type': 'ir.actions.act_window_close'
                }
            }
        }

    def _get_api_credentials_client(self):
        # settings = self.env['ir.config_parameter']
        # mg_user_name = settings.sudo().get_param('era_muqeem_client.user_name')
        # mg_user_password = settings.sudo().get_param('era_muqeem_client.user_pass')
        current_company= self.env.company
        mg_user_name =current_company.user
        mg_user_password = current_company.password



        return mg_user_name, mg_user_password


    def era_call_muqeem(self, data, url_send_muqeem,  user_name, user_password):
        url = 'https://app.era.net.sa/muqeem/call'


        # request = http.request if hasattr(http, 'request') else None
        server_domain = request.httprequest.host_url if request else None
        if not server_domain:
            server_domain = os.getenv('ODOO_SERVER_DOMAIN', 'default.domain.com')
        params = {
            'data': data,
            'url_send_muqeem': url_send_muqeem,
            'user_name': user_name,
            'user_password': user_password,
            'server_domain': server_domain,
        }
        _logger.info('Domain: %s', params['server_domain'])

        payload = json.dumps({
            'jsonrpc': '2.0',
            'params': params
        })
        headers = {
            'Content-Type': 'application/json',
        }
        response = requests.post(url, headers=headers, data=payload)

        if response.status_code == 200:
            result = response.json()

            if result.get('error'):
                _logger.info('error result: %s', result)
                _logger.info('error: %s', result.get('error'))

                raise ValidationError(_(' Invalid Username or Password or connection timeout' ))

            elif result.get('result'):
               response=result.get('result')

               _logger.info('Success result: %s', result)
               _logger.info('Success result: %s', response)

               return response
        else:
            _logger.error('Failed to call muqeem service, status code: %s, response: %s', response.status_code,

                          response.text)
            if response.status_code == 500:
                raise ValidationError(_('Failed to call muqeem service'))

            if response.status_code == 403:
                raise ValidationError(_('Please check your subscription with Era Group  info@era.net.sa'))


            return {
                'status': 'error',
                'message': 'Failed to call muqeem service'
            }