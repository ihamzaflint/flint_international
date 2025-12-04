from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
import requests
import logging
from urllib.parse import urlparse, parse_qs, unquote

_logger = logging.getLogger(__name__)
API_KEY = "AIzaSyDiTjNtexNREkkQX8ojHJ0_0SENc1swz0s"


class HotelLocation(models.Model):
    _name = 'hotel.location'
    _description = 'Hotel Location'
    _rec_name = 'name'

    name = fields.Char(string='Location Name', required=True, compute="_compute_hotel_name", store=True)
    location_link = fields.Char(string='Location Link')
    latitude = fields.Float(string='Latitude', digits=(16, 8), readonly=True)
    longitude = fields.Float(string='Longitude', digits=(16, 8), readonly=True)
    partner_id = fields.Many2one('res.partner', string='Hotel', 
                                domain=[('vendor_type', '=', 'hotel')],
                                required=True)
    address = fields.Char(string='Full Address', compute='_compute_address', store=True)

    @api.depends('location_link')
    def _compute_address(self):
        for record in self:
            if record.location_link:
                try:
                    parsed_url = urlparse(record.location_link)
                    query_params = parse_qs(parsed_url.query)
                    if parsed_url.netloc in ['maps.google.com', 'www.google.com'] and 'q' in query_params:
                        record.address = unquote(query_params['q'][0]).replace('+', ' ')
                    elif parsed_url.netloc in ['maps.google.com', 'www.google.com'] and 'q' not in query_params:
                        path = parsed_url.path
                        if '/place/' in path:
                            url_parts = path.split('/place/')[1]
                            address = url_parts.split('/')[0]
                            record.address = unquote(address).replace('+', ' ').replace('‭', '')
                except Exception as e:
                    _logger.error("Error parsing location link: %s", str(e))
                    record.address = False
            else:
                record.address = False


    def name_get(self):
        result = []
        for location in self:
            name = f"{location.name} ({location.partner_id.name})"
            result.append((location.id, name))
        return result

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
        record = super(HotelLocation, self).create(vals)
        if record.location_link:
            coordinates = record.get_coordinates(record.location_link)
            if coordinates:
                latitude, longitude = coordinates
                record.latitude = latitude
                record.longitude = longitude
        return record

    def write(self, vals):
        res = super(HotelLocation, self).write(vals)
        if 'location_link' in vals:
            coordinates = self.get_coordinates(self.location_link)
            if coordinates:
                latitude, longitude = coordinates
                self.latitude = latitude
                self.longitude = longitude
        return res
    
    @api.depends('partner_id','address')
    def _compute_hotel_name(self):
        for record in self:
            if record.partner_id:
                record.name = record.partner_id.name + ' - ' + (record.address or '')
            else:
                record.name = False