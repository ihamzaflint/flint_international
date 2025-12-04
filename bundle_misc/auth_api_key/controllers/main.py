import functools
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class ValidateToken:
    """Class-based decorator to validate API token for the request"""
    def __init__(self, func):
        self.func = func
        functools.update_wrapper(self, func)

    def __call__(self, *args, **kwargs):
        auth_header = request.httprequest.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return request.make_response(
                '{"status": "error", "message": "Missing or invalid Authorization header"}',
                headers=[('Content-Type', 'application/json')],
                status=401
            )

        token = auth_header.split(' ')[1]
        api_key = request.env['auth.api.key'].sudo().search([
            ('key', '=', token),
            ('active', '=', True)
        ], limit=1)

        if not api_key:
            return request.make_response(
                '{"status": "error", "message": "Invalid API key"}',
                headers=[('Content-Type', 'application/json')],
                status=401
            )

        # Check if key is expired
        if api_key.expiration_date and api_key.expiration_date < http.request.env['auth.api.key'].fields_get()['expiration_date']['now']():
            return request.make_response(
                '{"status": "error", "message": "API key expired"}',
                headers=[('Content-Type', 'application/json')],
                status=401
            )

        # Store API key in request for later use if needed
        request.api_key = api_key
        return self.func(*args, **kwargs)
