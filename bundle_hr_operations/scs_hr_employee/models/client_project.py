from urllib.parse import parse_qs, urlparse

from odoo import models, fields, api, _
import requests
import logging

from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)
API_KEY = "AIzaSyDiTjNtexNREkkQX8ojHJ0_0SENc1swz0s"


class ClientProject(models.Model):
    _name = "client.project"
    _description = "Client Project"

    name = fields.Char("Project Name")
    code = fields.Char("Code")
    partner_id = fields.Many2one("res.partner", string="Client",
                                domain=[('customer_rank', '>', 0)])
    analytic_account_id = fields.Many2one("account.analytic.account",
                                        string="Analytic Account")
    project_location = fields.Char("Project Location")
    project_latitude = fields.Float(string='Project Latitude', digits=(16, 8))
    project_longitude = fields.Float(string='Project Longitude', digits=(16, 8))


    def get_maps_place(self, address):
        if not API_KEY:
            raise UserError(_("Google API key not configured"))
        map_url = f'https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={API_KEY}'

        res = requests.get(map_url)
        data = res.json()

        if data['status'] == 'OK':
            location = data['results'][0]['geometry']['location']
            return location['lat'], location['lng']
        else:
            return None, None

    def get_coordinates(self, url):
        if not API_KEY:
            raise UserError(_("Google API key not configured"))
        parsed_url = urlparse(url)
        if parsed_url.netloc == 'www.google.com':
            maps_link = requests.head(url, allow_redirects=True)
            index = maps_link.url.find("https://www.google.com")
            maps_link = maps_link.url[index:]
            parsed_url = urlparse(maps_link)
            path = parsed_url.path
            # Handle both /place/ and /search/ URLs
            if '@' in path:
                coordinates = path.split("/@")[1].split(",")[:2]  # Get first two elements for lat/long
                lat, long = coordinates[0], coordinates[1]
            elif '/place/' in path:
                url_parts = path.split('/place/')[1]
                address = url_parts.split('/')[0]
                if address:
                    lat, long = self.get_maps_place(address)
                elif '3d' and '4d' in path:
                    lat = path[parsed_url.path.find('3d'):].split('!')[0].replace('3d', '')
                    long = path[parsed_url.path.find('3d'):].split('!')[1].replace('4d', '')
                else:
                    return None
            elif '/search/' in path:
                url_parts = path.split('/search/')[1]
                address = url_parts.split('/')[0]
                if address:
                    lat, long = self.get_maps_place(address)
                else:
                    return None
            else:
                return None
            return lat, long
        else:
            response = requests.head(url, allow_redirects=True)
            redirect_url = response.url
            parsed_url = urlparse(redirect_url)
            query_params = parse_qs(parsed_url.query)
            if parsed_url.netloc in ['maps.google.com', 'www.google.com'] and 'q' in query_params:
                location = query_params['q'][0]
                api_url = 'https://maps.googleapis.com/maps/api/geocode/json'
                params = {
                    'key': API_KEY,
                    'address': location
                }
                try:
                    response = requests.get(api_url, params=params).json()
                    _logger.info("Response url", response)
                except ValidationError:
                    raise ValidationError(_("Invalid response url"))
                if response['status'] == 'OK':
                    latitude = response['results'][0]['geometry']['location']['lat']
                    longitude = response['results'][0]['geometry']['location']['lng']
                    return latitude, longitude
            elif parsed_url.netloc in ['maps.google.com', 'www.google.com'] and 'q' not in query_params:
                maps_link = requests.head(url, allow_redirects=True)
                index = maps_link.url.find("https://www.google.com")
                maps_link = maps_link.url[index:]
                parsed_url = urlparse(maps_link)
                path = parsed_url.path
                url_parts = path.split('/place/')[1]
                address = url_parts.split('/')[0]
                if address:
                    lat, long = self.get_maps_place(address)
                elif '3d' and '4d' in path:
                    lat = path[parsed_url.path.find('3d'):].split('!')[0].replace('3d', '')
                    long = path[parsed_url.path.find('3d'):].split('!')[1].replace('4d', '')
                else:
                    return None
                return lat, long
            return None


    @api.model
    def create(self, vals):
        record = super(ClientProject, self).create(vals)
        if record.project_location:
            coordinates = record.get_coordinates(record.project_location)
            if coordinates:
                latitude, longitude = coordinates
                record.project_latitude = latitude
                record.project_longitude = longitude
        return record

    def write(self, vals):
        res = super(ClientProject, self).write(vals)
        if 'project_location' in vals:
            coordinates = self.get_coordinates(self.project_location)
            if coordinates:
                latitude, longitude = coordinates
                self.project_latitude = latitude
                self.project_longitude = longitude
        return res
