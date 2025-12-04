import json
import logging
import os
import tempfile
import requests
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class SaibApiAuth(models.Model):
    _name = 'saib.api.auth'
    _description = 'SAIB API Authentication'

    name = fields.Char('Name', default='SAIB API Token', readonly=True)
    token = fields.Text('Access Token', readonly=True)
    token_expiry = fields.Datetime('Token Expiry', readonly=True)
    last_refresh = fields.Datetime('Last Refresh', readonly=True)
    active = fields.Boolean('Active', default=True)

    # [sanjay-techvoot] Read client cert and key files into temp files for requests.
    # Returns (cert_path, key_path, temp_dir) or raises UserError.
    def _read_cert_files(self):
        """Read certificate and key files and create temporary files for use with requests"""
        config = self.env['ir.config_parameter'].sudo()
        cert_path = config.get_param('saib_bank_integration.cert_path')
        key_path = config.get_param('saib_bank_integration.key_path')

        if not cert_path or not key_path:
            raise UserError('Certificate paths are not configured')

        if not os.path.isfile(cert_path):
            raise UserError(f'Client certificate file not found at: {cert_path}')
        if not os.path.isfile(key_path):
            raise UserError(f'Client key file not found at: {key_path}')

        try:
            # Create temporary directory to store the certificate files
            temp_dir = tempfile.mkdtemp()
            temp_cert_path = os.path.join(temp_dir, 'client-cert.pem')
            temp_key_path = os.path.join(temp_dir, 'client-key.pem')

            # Read original files and write to temporary files
            with open(cert_path, 'rb') as cert_file:
                cert_data = cert_file.read()
            with open(key_path, 'rb') as key_file:
                key_data = key_file.read()

            # Write to temporary files
            with open(temp_cert_path, 'wb') as temp_cert:
                temp_cert.write(cert_data)
            with open(temp_key_path, 'wb') as temp_key:
                temp_key.write(key_data)

            return temp_cert_path, temp_key_path, temp_dir
        except (IOError, OSError) as e:
            _logger.error(f"Error reading certificate files: {str(e)}")
            raise UserError(f'Error reading certificate files: {str(e)}')
        
    # [sanjay-techvoot] Return cached token if valid, otherwise request a new token from SAIB.
    # Updates token, token_expiry and last_refresh; returns access token string.
    def get_token(self):
        """Get a valid token, either from cache or by requesting a new one"""
        temp_dir = None
        self.ensure_one()
        
        # Check if we have a valid cached token
        if self.token and self.token_expiry and self.token_expiry > fields.Datetime.now():
            return self.token

        # Get configuration
        config = self.env['ir.config_parameter'].sudo()
        base_url = config.get_param('saib_bank_integration.base_url')
        client_id = config.get_param('saib_bank_integration.client_id')
        client_secret = config.get_param('saib_bank_integration.client_secret')
        cert_path = config.get_param('saib_bank_integration.cert_path')
        key_path = config.get_param('saib_bank_integration.key_path')

        if not all([base_url, client_id, client_secret, cert_path, key_path]):
            raise UserError(_('Missing configuration parameters. Please check SAIB API settings.'))

        # Validate certificate paths
        if not os.path.isfile(cert_path):
            raise UserError(_('Client certificate file not found at: %s') % cert_path)
        if not os.path.isfile(key_path):
            raise UserError(_('Client key file not found at: %s') % key_path)

        try:
            # Prepare request
            url = f"{base_url}/auth/token"
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            payload = {
                'client_id': client_id,
                'client_secret': client_secret,
                'grant_type': 'client_credentials'
            }

            # Make request with client certificates
            temp_cert_path, temp_key_path, temp_dir = self._read_cert_files()
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                cert=(temp_cert_path, temp_key_path),
                verify=True,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                token = data.get('access_token')
                expires_in = data.get('expires_in', 3600)  # Default 1 hour if not specified
                
                # Update token information
                self.write({
                    'token': token,
                    'token_expiry': fields.Datetime.now() + timedelta(seconds=expires_in),
                    'last_refresh': fields.Datetime.now()
                })
                
                return token
            else:
                error_msg = f"Failed to get token. Status: {response.status_code}, Response: {response.text}"
                _logger.error(error_msg)
                raise UserError(_(error_msg))

        except requests.exceptions.RequestException as e:
            error_msg = f"Error connecting to SAIB API: {str(e)}"
            _logger.error(error_msg)
            raise UserError(_(error_msg))

    # [sanjay-techvoot] Model method to fetch token from active auth record or create one.
    # Returns token string from the active `saib.api.auth` record.
    @api.model
    def get_valid_token(self):
        """Get a valid token from the active authentication record"""
        auth = self.search([('active', '=', True)], limit=1)
        if not auth:
            auth = self.create({'active': True})
        return auth.get_token()
