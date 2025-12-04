import json
import logging
import werkzeug.exceptions
import werkzeug.wrappers
import datetime
from functools import wraps

from odoo import http
from odoo.http import request, Response
from odoo.service import security
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)

# Rate limiting configuration
RATE_LIMIT_INTERVAL = 60  # 1 minute
RATE_LIMIT_MAX_CALLS = 30  # 30 calls per minute
RATE_LIMIT_STORAGE = {}  # In-memory storage for rate limiting

def validate_token(func):
    """Decorator to validate API token for authenticated endpoints"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        auth_header = request.httprequest.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return self._json_response(
                {'error': 'Missing or invalid Authorization header'}, 
                status=401
            )
        
        token = auth_header.split(' ')[1]
        mobile_user = request.env['mobile.user'].sudo().search([
            ('api_key', '=', token),
            ('token_expiry', '>=', fields.Datetime.now()),
            ('active', '=', True)
        ], limit=1)
        
        if not mobile_user:
            return self._json_response(
                {'error': 'Invalid or expired token'}, 
                status=401
            )
        
        # Set the authenticated user for this request
        request.uid = mobile_user.user_id.id
        request.mobile_user = mobile_user
        
        # Update last login time
        mobile_user._update_last_login()
        
        # Extend token validity
        mobile_user.extend_token_validity()
        
        return func(self, *args, **kwargs)
    return wrapper

def rate_limit(func):
    """Decorator to apply rate limiting to API endpoints"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        client_ip = request.httprequest.remote_addr
        endpoint = request.httprequest.path
        key = f"{client_ip}:{endpoint}"
        
        current_time = datetime.datetime.now()
        if key in RATE_LIMIT_STORAGE:
            calls, first_call_time = RATE_LIMIT_STORAGE[key]
            
            # Reset counter if interval has passed
            time_diff = (current_time - first_call_time).total_seconds()
            if time_diff > RATE_LIMIT_INTERVAL:
                RATE_LIMIT_STORAGE[key] = (1, current_time)
            else:
                # Increment counter
                calls += 1
                if calls > RATE_LIMIT_MAX_CALLS:
                    return self._json_response(
                        {'error': 'Rate limit exceeded'}, 
                        status=429
                    )
                RATE_LIMIT_STORAGE[key] = (calls, first_call_time)
        else:
            RATE_LIMIT_STORAGE[key] = (1, current_time)
            
        return func(self, *args, **kwargs)
    return wrapper

class MobileAPIController(http.Controller):
    """Base controller for Mobile API endpoints"""
    
    def _json_response(self, data=None, status=200):
        """Helper method to create JSON responses"""
        if data is None:
            data = {}
            
        return Response(
            json.dumps(data),
            status=status,
            headers=[('Content-Type', 'application/json')]
        )
    
    def _get_company_from_request(self):
        """Helper method to get company from request"""
        company_id = request.httprequest.headers.get('X-Company-ID')
        if company_id and company_id.isdigit():
            company = request.env['res.company'].sudo().browse(int(company_id))
            if company.exists():
                return company
        return request.env.company
    
    def _handle_exception(self, exception):
        """Handle exceptions and return appropriate JSON response"""
        if isinstance(exception, AccessError):
            return self._json_response({'error': str(exception)}, status=403)
        elif isinstance(exception, (UserError, ValidationError)):
            return self._json_response({'error': str(exception)}, status=400)
        else:
            _logger.exception("Server error")
            return self._json_response(
                {'error': 'Server error, please try again later'}, 
                status=500
            )
    
    @http.route('/api/mobile/version', type='http', auth='none', methods=['GET'], csrf=False)
    @rate_limit
    def version(self):
        """Return API version information"""
        version_info = {
            'api_version': '1.0',
            'server_version': request.env['ir.module.module'].sudo().search(
                [('name', '=', 'base')], limit=1
            ).installed_version,
            'mobile_api_version': request.env['ir.module.module'].sudo().search(
                [('name', '=', 'mobile_api')], limit=1
            ).installed_version or '1.0',
        }
        return self._json_response(version_info)
    
    @http.route('/api/mobile/server-info', type='http', auth='none', methods=['GET'], csrf=False)
    @rate_limit
    def server_info(self):
        """Return server information for the mobile app"""
        info = {
            'server_timezone': request.env['ir.config_parameter'].sudo().get_param('mobile_api.timezone', 'UTC'),
            'server_datetime': fields.Datetime.now().isoformat(),
            'modules': {
                'helpdesk': bool(request.env['ir.module.module'].sudo().search(
                    [('name', '=', 'helpdesk'), ('state', '=', 'installed')]
                )),
                'crm': bool(request.env['ir.module.module'].sudo().search(
                    [('name', '=', 'crm'), ('state', '=', 'installed')]
                )),
            }
        }
        return self._json_response(info)
