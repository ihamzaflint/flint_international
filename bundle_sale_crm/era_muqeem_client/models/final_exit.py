import json
import requests
from odoo import models, fields, api, _

from odoo.exceptions import AccessError, ValidationError, UserError
from markupsafe import Markup
from  datetime import datetime

from base64 import b64decode


class FinalExit(models.TransientModel):
    _name = "final.exit.wizard"

    employee_id = fields.Many2one('hr.employee', string="Resident")
    iqama_number = fields.Char(related="employee_id.iqama_number", string="Iqama Number", readonly=True, required=True)

    json_data = fields.Char(string='JSON Data', compute='_compute_json_data')

    def convert_to_json(self):
        for record in self:
             data = {
                'iqamaNumber': record.iqama_number,
              }

        json_data = json.dumps(data)
        return json_data

    @api.depends('iqama_number')
    def _compute_json_data(self):
        for record in self:
            record.json_data = record.convert_to_json()



    def final_exit(self):

        company = self.env['res.company'].search([], limit=1)

        json_data = self.json_data
        url_muqeem = '5'
        company = self.env.company
        credentials = company._get_api_credentials_client()
        user_name,user_password = credentials
        response_data = company.era_call_muqeem(json.loads(json_data), url_muqeem,user_name,user_password)
        user = self.env.user.name
        employee_name = self.employee_id.name
        process =_ ("Final Exit Issue")
        current_datetime = datetime.now()
        vals = {
            'name': process,
            'user': user,
            'employee': employee_name,
            'date': current_datetime,

        }
        record = self.env['client.requests'].create(vals)


        statusCode=response_data.get('statusCode')
        if isinstance(response_data, dict):
            if statusCode == 200:
                        datas_main=response_data.get('response_data').get('mainResident')

                        report_data = {
                            'residentName': datas_main.get('residentName'),
                            'iqama_number': datas_main.get('iqama_number'),
                            'passportNumber': datas_main.get('passportNumber'),
                            'nationality': datas_main.get('nationality'),
                            'occupation': datas_main.get('occupation'),
                            'visaNumber': datas_main.get('visaNumber'),
                        }
                        print('report_data',report_data)
                        mess1 = _('Resident Name: {}').format(report_data['residentName'])
                        mess2 = _('Iqama Number: {}').format(report_data['iqama_number'])
                        mess3 = _('Passport Number: {}').format(report_data['passportNumber'])
                        mess4 = _('Nationality: {}').format(report_data['nationality'])
                        mess5 = _('Occupation: {}').format(report_data['occupation'])
                        mess6 = _('Visa Number: {}').format(report_data['visaNumber'])

                        message_body = (
                                _(' Final Exit Visa') +
                                Markup('<br/>\n') +
                                mess1 + Markup('<br/>\n')
                                +
                                mess2 + Markup('<br/>\n') +
                                mess3 + Markup('<br/>\n') +
                                mess4 + Markup('<br/>\n') +
                                mess5 + Markup('<br/>\n') +
                                mess6 + Markup('<br/>\n'))

                        employee = self.employee_id

                        employee.message_post(
                            body=message_body)
                        record.update({'des': _('Success')})

                        return {
                                    'type': 'ir.actions.client',
                                    'tag': 'display_notification',
                                    'params': {
                                        'title': _('Success'),
                                        'message': _('Final Visa Issued has been successed'),
                                        'type': 'success',
                                        'sticky': True,
                                        'next': {
                                            'type': 'ir.actions.act_window_close'
                                        }
                                    }
                                }

            elif statusCode == 500:
                record.update({'des': _('Fail')})

                return company.show_popup(_('Error'), response_data.get('message'))
            elif statusCode == 429:
                record.update({'des': _('Fail')})

                return company.show_popup(_('Error'), response_data.get('message'))

            elif statusCode == 401:
                record.update({'des': _('Fail')})

                return company.show_popup(_('Error'), response_data.get('message'))

            elif statusCode == 400:
                if response_data.get('fieldErrors'):

                    errors = response_data.get('fieldErrors')
                    error_messages = []
                    for error in errors:
                        field = error.get('field')
                        message = error.get('message')
                        error_messages.append(f"{field}: {message}")
                    record.update({'des': _('Fail')})

                    return company.show_popup(_('Error'), '\n'.join(error_messages))
                else:
                    record.update({'des': _('Fail')})

                    return company.show_popup(_('Error'), response_data.get('message'))

