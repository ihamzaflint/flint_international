# -*- coding: utf-8 -*-
from odoo import models, fields
import aiohttp
import asyncio
import requests
import logging

import pytz
_logger = logging.getLogger(__name__)

# put POSIX 'Etc/*' entries at the end to avoid confusing users - see bug 1086728
_tzs = [(tz, tz) for tz in sorted(pytz.all_timezones, key=lambda tz: tz if not tz.startswith('Etc/') else 'ZZ' + tz)]


def _tz_get(self):
    return _tzs


client_secret = "8kgIS20RyP2A5cD4CEyUdBVuJ80gLecuYcYJhqSg0jOmpxomnQa8JQQJ99AKACYeBjFvJlTzAAAgAZMP3197"


class Airport(models.Model):
    _name = 'airport.airport'
    _description = 'Airport Information'
    _rec_name = 'name'

    HEADERS = {
        'x-rapidapi-key': "24956eec85msh91de630a921537bp1ffe67jsn8a7a1e6bb516",
        'x-rapidapi-host': "airport-info.p.rapidapi.com"
    }
    name = fields.Char(string='Airport Name')
    iata_code = fields.Char(string='IATA Code', size=3)
    icao_code = fields.Char(string='ICAO Code', size=4)
    country_id = fields.Many2one('res.country', string='Country')
    city = fields.Many2one(
        'res.country.state',
        string="Fed. State", domain="[('country_id', '=?', country_id)]"
    )
    latitude = fields.Float(string='Latitude', digits=(10, 6))
    longitude = fields.Float(string='Longitude', digits=(10, 6))
    elevation = fields.Integer(string='Elevation (feet)')
    timezone = fields.Selection(_tz_get, string='Timezone', default=lambda self: self._context.get('tz'),
                                help="When printing documents and exporting/importing data, time values are computed according to this timezone.\n"
                                     "If the timezone is not set, UTC (Coordinated Universal Time) is used.\n"
                                     "Anywhere else, time values are computed according to the time offset of your web client.")
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('unique_iata', 'unique(iata_code)', 'IATA code must be unique!'),
    ]

    def _process_batch(self, batch_records, session, headers):
        results = []
        for record in batch_records:
            try:
                response = session.get(
                    f"https://airport-info.p.rapidapi.com/airport?iata={record.iata_code}",
                    headers=headers,
                    timeout=5
                )
                if response.ok:
                    data = response.json()
                    # Add data validation
                    required_fields = ['name', 'icao', 'latitude', 'longitude', 'state', 'city', 'country']
                    if all(field in data for field in required_fields):
                        results.append((record, data))
                    else:
                        missing = [f for f in required_fields if f not in data]
                        _logger.error(f"Missing fields for {record.iata_code}: {missing}")
                        _logger.error(f"Received data: {data}")
                else:
                    _logger.error(f"Failed fetch for {record.iata_code}: {response.status_code}")
            except Exception as e:
                _logger.error(f"Error processing {record.iata_code}: {e}")
        return results

    async def _fetch_timezones(self, coords_map, api_key):
        async with aiohttp.ClientSession() as session:
            tasks = []
            for record_id, (lat, lon) in coords_map.items():
                url = (
                    "https://atlas.microsoft.com/timezone/byCoordinates/json?"
                    f"subscription-key={api_key}&"
                    f"api-version=1.0&options=all&query={lat},{lon}"
                )
                tasks.append(self._fetch_single_timezone(session, record_id, url))
            return await asyncio.gather(*tasks)

    async def _fetch_single_timezone(self, session, record_id, url):
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    timezone = data.get('TimeZones', [{}])[0].get('Id')
                    return record_id, timezone
                return record_id, None
        except Exception as e:
            _logger.error(f"Timezone fetch error for {record_id}: {e}")
            return record_id, None

    def action_fetch_airports(self):
        BATCH_SIZE = 50
        headers = {
            'x-rapidapi-key': "24956eec85msh91de630a921537bp1ffe67jsn8a7a1e6bb516",
            'x-rapidapi-host': "airport-info.p.rapidapi.com"
        }
        azure_key = client_secret

        with requests.Session() as session:
            for batch_start in range(0, len(self), BATCH_SIZE):
                batch = self[batch_start:batch_start + BATCH_SIZE]
                airport_results = self._process_batch(batch, session, headers)
                coords_map = {
                    record.id: (data['latitude'], data['longitude'])
                    for record, data in airport_results
                }

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                timezone_results = loop.run_until_complete(self._fetch_timezones(coords_map, azure_key))
                loop.close()

                for record, airport_data in airport_results:
                    timezone = next((tz for rid, tz in timezone_results if rid == record.id), None)
                    if timezone:
                        print(f"airport #####: {airport_data}")
                        print(f"city: {self._find_state_city(airport_data)}")
                        vals = {
                            'name': airport_data['name'],
                            'icao_code': airport_data['icao'],
                            'city': self._find_state_city(airport_data).id,
                            'country_id': self._find_country(airport_data).id,
                            'latitude': airport_data['latitude'],
                            'longitude': airport_data['longitude'],
                            'timezone': timezone,
                        }
                        record.write(vals)

        return True

    def _find_state_city(self, data):
        print(f"state: {data['state']}")
        print(f"city: {data['city']}")
        return self.env['res.country.state'].search([
            '|', '|', ('name', 'ilike', data['state']),
            ('name', 'ilike', data['city']),
            ('name', 'ilike', data['name'])
        ], limit=1)

    def _find_country(self, data):
        return self.env['res.country'].search([
            ('name', '=', data['country'])
        ], limit=1)
