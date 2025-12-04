import json
import logging
import werkzeug.exceptions
import werkzeug.wrappers
import datetime
import random
import string

from odoo import http, fields, _
from odoo.http import request
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.addons.auth_signup.models.res_users import SignupError

from .main import MobileAPIController, validate_token, rate_limit

_logger = logging.getLogger(__name__)

class MobileAuthController(MobileAPIController):
    """Controller for authentication-related endpoints"""
    
    @http.route('/api/mobile/auth/login', type='json', auth='none', methods=['POST'], csrf=False)
    @rate_limit
    def login(self):
        """Authenticate user and return session token"""
        data = request.jsonrequest
        login = data.get('login')
        password = data.get('password')
        device_info = data.get('device_info', {})
        
        if not login or not password:
            return self._json_response({'error': 'Login and password are required'}, status=400)
        
        try:
            # Authenticate using Odoo's built-in authentication
            uid = request.session.authenticate(request.session.db, login, password)
            if not uid:
                return self._json_response({'error': 'Authentication failed'}, status=401)
            
            user = request.env['res.users'].sudo().browse(uid)
            company = self._get_company_from_request()
            
            # Find or create mobile user record
            mobile_user = request.env['mobile.user'].sudo().search([
                ('user_id', '=', uid),
                ('device_id', '=', device_info.get('device_id', ''))
            ], limit=1)
            
            if not mobile_user:
                # Create new mobile user record
                mobile_user = request.env['mobile.user'].sudo().create({
                    'user_id': uid,
                    'company_id': company.id,
                    'device_id': device_info.get('device_id', ''),
                    'device_name': device_info.get('device_name', ''),
                    'device_model': device_info.get('device_model', ''),
                    'platform': device_info.get('platform', ''),
                    'app_version': device_info.get('app_version', ''),
                    'fcm_token': device_info.get('fcm_token', ''),
                })
            else:
                # Update existing mobile user record
                mobile_user.sudo().write({
                    'last_login': fields.Datetime.now(),
                    'device_name': device_info.get('device_name', mobile_user.device_name),
                    'device_model': device_info.get('device_model', mobile_user.device_model),
                    'platform': device_info.get('platform', mobile_user.platform),
                    'app_version': device_info.get('app_version', mobile_user.app_version),
                    'fcm_token': device_info.get('fcm_token', mobile_user.fcm_token),
                    'company_id': company.id,
                })
                
                # Generate new API key if expired
                if not mobile_user.check_token_validity():
                    mobile_user.generate_new_api_key()
            
            # Return user info and token
            return self._json_response({
                'user': {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'company_id': company.id,
                    'company_name': company.name,
                    'lang': user.lang,
                    'tz': user.tz,
                    'image': user.image_1920.decode('utf-8') if user.image_1920 else False,
                },
                'token': mobile_user.api_key,
                'token_expiry': mobile_user.token_expiry.isoformat() if mobile_user.token_expiry else False,
            })
            
        except Exception as e:
            return self._handle_exception(e)
    
    @http.route('/api/mobile/auth/logout', type='http', auth='none', methods=['POST'], csrf=False)
    @validate_token
    def logout(self):
        """Invalidate user session token"""
        try:
            if hasattr(request, 'mobile_user') and request.mobile_user:
                request.mobile_user.sudo().write({
                    'api_key': False,
                    'token_expiry': False,
                    'fcm_token': False,
                })
            return self._json_response({'success': True})
        except Exception as e:
            return self._handle_exception(e)
    
    @http.route('/api/mobile/auth/password/reset', type='json', auth='none', methods=['POST'], csrf=False)
    @rate_limit
    def reset_password(self):
        """Trigger password reset workflow"""
        data = request.jsonrequest
        login = data.get('login')
        
        if not login:
            return self._json_response({'error': 'Login is required'}, status=400)
        
        try:
            # Find user by login
            user = request.env['res.users'].sudo().search([
                ('login', '=', login),
                ('active', '=', True)
            ], limit=1)
            
            if not user:
                # Don't reveal if user exists or not for security
                return self._json_response({
                    'success': True,
                    'message': 'If your email is registered, you will receive a password reset link'
                })
            
            # Trigger password reset using Odoo's built-in mechanism
            user.with_context(create_user=True).action_reset_password()
            
            return self._json_response({
                'success': True,
                'message': 'If your email is registered, you will receive a password reset link'
            })
            
        except Exception as e:
            return self._handle_exception(e)
    
    @http.route('/api/mobile/auth/password/change', type='json', auth='none', methods=['POST'], csrf=False)
    @validate_token
    def change_password(self):
        """Change user password"""
        data = request.jsonrequest
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        
        if not old_password or not new_password:
            return self._json_response({
                'error': 'Old password and new password are required'
            }, status=400)
        
        try:
            user = request.env.user
            
            # Verify old password
            try:
                request.env['res.users'].sudo().check(user.login, old_password)
            except AccessError:
                return self._json_response({'error': 'Old password is incorrect'}, status=400)
            
            # Change password
            user.write({'password': new_password})
            
            return self._json_response({
                'success': True,
                'message': 'Password changed successfully'
            })
            
        except Exception as e:
            return self._handle_exception(e)
    
    @http.route('/api/mobile/auth/check', type='http', auth='none', methods=['GET'], csrf=False)
    @validate_token
    def check_auth(self):
        """Check if token is valid and return user info"""
        try:
            user = request.env.user
            company = self._get_company_from_request()
            
            return self._json_response({
                'user': {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'company_id': company.id,
                    'company_name': company.name,
                    'lang': user.lang,
                    'tz': user.tz,
                },
                'token_expiry': request.mobile_user.token_expiry.isoformat() if request.mobile_user.token_expiry else False,
            })
            
        except Exception as e:
            return self._handle_exception(e)
