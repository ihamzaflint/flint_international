import requests
import logging
import uuid
import os
import tempfile
import json
from datetime import datetime
from odoo import models
from odoo.exceptions import UserError
from .jws_signer import JWSSigner
import base64
import json
_logger = logging.getLogger(__name__)


class SaibAPI(models.AbstractModel):
    _name = 'saib.api'
    _description = 'SAIB API Integration'

    # [sanjay-techvoot] Get and validate the configured SAIB base URL.
    # Returns the base URL string without trailing slash or raises UserError.
    def _get_base_url(self):
        """Get and validate the base URL"""
        config = self.env['ir.config_parameter'].sudo()
        base_url = config.get_param('saib_bank_integration.base_url')
        if not base_url or not isinstance(base_url, str):
            raise UserError('SAIB API Base URL is not configured')
        return str(base_url).rstrip('/')

    # [sanjay-techvoot] Read configured client certificate and key files into temp files.
    # Returns paths (cert, key, temp_dir) or raises UserError on failure.
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

    # [sanjay-techvoot] Obtain OAuth token from SAIB using configured credentials and client certs.
    # Returns access_token string or raises UserError on authentication/network errors.
    def _get_token(self):
        """Get authentication token from SAIB"""
        temp_dir = None
        try:
            config = self.env['ir.config_parameter'].sudo()
            url = f"{self._get_base_url()}/b2b/oauth/token"
            
            # Get header credentials
            header_client_id = config.get_param('saib_bank_integration.client_id')
            header_client_secret = config.get_param('saib_bank_integration.client_secret')
            
            # Get data body credentials
            data_client_id = config.get_param('saib_bank_integration.data_client_id')
            data_client_secret = config.get_param('saib_bank_integration.data_client_secret')
            
            username = config.get_param('saib_bank_integration.username')
            password = config.get_param('saib_bank_integration.password')
            
            # Validate required credentials
            if not all([header_client_id, header_client_secret,
                        data_client_id, data_client_secret, username, password]):
                raise UserError('SAIB API credentials are not fully configured')
            
            data = {
                'grant_type': 'password',
                'client_id': data_client_id,
                'client_secret': data_client_secret,
                'username': username,
                'password': password
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'x-saib-client-id': header_client_id,
                'x-saib-client-secret': header_client_secret
            }
            
            # Read certificate and key files
            temp_cert_path, temp_key_path, temp_dir = self._read_cert_files()
            _logger.info(f"Certificate files read: {temp_cert_path}, {temp_key_path}, {temp_dir}")
            # Configure SSL verification and certificates
            verify = True  # Set to False only in development with self-signed certs
            
            response = requests.post(
                url,
                data=data,
                headers=headers,
                verify=verify,
                cert=(temp_cert_path, temp_key_path),
                timeout=30  # 30 seconds timeout
            )
            
            if response.status_code == 401:
                raise UserError('Authentication failed: Invalid credentials')
            elif response.status_code == 403:
                raise UserError('Authentication failed: Access denied')
            
            response.raise_for_status()
            
            token_data = response.json()
            if 'access_token' not in token_data:
                raise UserError('Invalid response from SAIB API: No access token received')
                
            return token_data['access_token']
            
        except requests.exceptions.SSLError as e:
            _logger.error(f"SSL Error while connecting to SAIB: {str(e)}")
            raise UserError(
                'SSL Error while connecting to SAIB API. Please ensure your certificates '
                'are valid and properly formatted.'
            )
        except requests.exceptions.RequestException as e:
            _logger.error(f"Error connecting to SAIB API: {str(e)}")
            raise UserError(f'Error connecting to SAIB API: {str(e)}')
        finally:
            # Clean up temporary directory and files
            if temp_dir and os.path.exists(temp_dir):
                try:
                    for file in os.listdir(temp_dir):
                        os.unlink(os.path.join(temp_dir, file))
                    os.rmdir(temp_dir)
                except OSError as e:
                    _logger.warning(f"Error cleaning up temporary certificate files: {str(e)}")

    # [sanjay-techvoot] Make an API request to SAIB with optional JWS signing of the payload.
    # Returns parsed JSON response or raises UserError on errors.
    def _make_request(self, method, endpoint, data=None):
        """Make request to SAIB API with JWS signature"""
        try:
            token = self._get_token()
            config = self.env['ir.config_parameter'].sudo()
            base_url = self._get_base_url()
            company_code = config.get_param('saib_bank_integration.company_code')
            
            if not company_code:
                raise UserError('SAIB Company Code is not configured')
                
            # Check if the endpoint path is already included in the base URL to avoid duplication
            if 'b2b-rest-sadad-service' in base_url and 'b2b-rest-sadad-service' in endpoint:
                # Extract the base part without the service path
                base_parts = base_url.split('b2b-rest-sadad-service')
                clean_base_url = base_parts[0].rstrip('/')
                # Use the clean base URL with the endpoint
                url = f"{clean_base_url}/{endpoint.lstrip('/')}"
                _logger.info(f"Adjusted URL to avoid path duplication: {url}")
            else:
                url = f"{base_url}/{endpoint.lstrip('/')}"
            
            # Generate JWS signature if data is present
            jws_signature = None
            if data:
                _logger.info(f"Generating JWS signature for payload: {data}")
                private_key = config.get_param('saib_bank_integration.private_key')
                if not private_key:
                    raise UserError('JWS signing private key is not configured in SAIB settings')
                
                try:
                    # Debug logging
                    _logger.info(f"Private key length: {len(private_key)}")
                    
                    # Handle potential escaped newlines in the key
                    if '\\n' in private_key:
                        _logger.info("Detected escaped newlines in private key, converting to actual newlines")
                        private_key = private_key.replace('\\n', '\n')
                    
                    # Log key format for debugging
                    _logger.info(f"Key length before processing: {len(private_key)}")
                    
                    # Ensure proper line breaks for PEM format
                    # First, extract the header, body, and footer
                    lines = private_key.strip().splitlines()
                    _logger.info(f"Number of lines in key: {len(lines)}")
                    
                    header = lines[0] if lines and lines[0].startswith('-----BEGIN') else None
                    footer = lines[-1] if lines and lines[-1].startswith('-----END') else None
                    
                    if not header:
                        _logger.error("Missing BEGIN header in private key")
                        raise ValueError('Private key is missing BEGIN header. It should start with -----BEGIN PRIVATE KEY----- or -----BEGIN RSA PRIVATE KEY-----')
                    
                    if not footer:
                        _logger.error("Missing END footer in private key")
                        raise ValueError('Private key is missing END footer. It should end with -----END PRIVATE KEY----- or -----END RSA PRIVATE KEY-----')
                    
                    _logger.info(f"Key header: {header}")
                    _logger.info(f"Key footer: {footer}")
                    
                    # Extract the base64 content (everything between header and footer)
                    content_lines = []
                    in_content = False
                    for line in lines:
                        line = line.strip()
                        if line == header:
                            in_content = True
                            content_lines.append(line)
                        elif line == footer:
                            in_content = False
                            content_lines.append(line)
                        elif in_content and line:
                            # Validate base64 content
                            try:
                                base64.b64decode(line)
                                content_lines.append(line)
                            except Exception as e:
                                _logger.warning(f"Skipping invalid base64 line in key: {str(e)}")
                    
                    # Ensure we have at least header, some content, and footer
                    if len(content_lines) < 3:
                        _logger.error(f"Incomplete key: only {len(content_lines)} valid lines found")
                        raise ValueError('Private key is incomplete or corrupted. Please ensure it contains a valid header, base64-encoded content, and footer.')
                    
                    # Reconstruct with proper line breaks
                    private_key = '\n'.join(content_lines)
                    
                    # Debug logging after normalization
                    _logger.info(f"Normalized key length: {len(private_key)}")
                    _logger.info(f"Number of content lines: {len(content_lines) - 2}")  # Subtract header and footer
                    
                    # Call the dedicated method to sign the payload
                    # The _sign_payload method returns both the signature and the normalized payload
                    # We need to use the EXACT same normalized payload in the request as was used for signing
                    jws_signature, normalized_data = self._sign_payload(private_key, data)
                    
                    # Store the original data format for logging
                    original_data_format = type(data).__name__
                    
                    # Important: Use the normalized_data returned from _sign_payload
                    # This ensures we're sending exactly what we signed
                    data = normalized_data
                    
                    _logger.info(f"Original data format: {original_data_format}, normalized format: {type(data).__name__}")
                    _logger.info(f"Successfully created JWS signature: {jws_signature}")
                except ValueError as e:
                    _logger.error(f"JWS Signing Error: {str(e)}")
                    raise UserError(
                        f"Error with JWS signing key: {str(e)}\n\n"
                        "Please ensure your private key:\n"
                        "1. Is in valid PEM format\n"
                        "2. Is an RSA private key\n"
                        "3. Is not encrypted (no password protection)\n"
                        "4. Contains the full key data without corruption\n\n"
                        "Common issues:\n"
                        "- Make sure you're not using a public key or certificate\n"
                        "- Ensure all lines of the key are included\n"
                        "- Check that the key is properly formatted with correct line breaks\n"
                        "- Verify the key works with OpenSSL or other tools\n\n"
                        "Example format:\n"
                        "-----BEGIN PRIVATE KEY-----\n"
                        "(your base64 encoded key)\n"
                        "-----END PRIVATE KEY-----\n"
                        "\nOR\n"
                        "-----BEGIN RSA PRIVATE KEY-----\n"
                        "(your base64 encoded key)\n"
                        "-----END RSA PRIVATE KEY-----"
                    )
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'x-idempotency-key': company_code,
                'x-customer-user-agent': company_code,
                'x-fapi-interaction-id': str(uuid.uuid4()),
                'x-fapi-customer-ip-address': config.get_param('saib_bank_integration.customer_ip'),
                'x-saib-client-id': config.get_param('saib_bank_integration.client_id'),
                'x-saib-client-secret': config.get_param('saib_bank_integration.client_secret'),
                'x-fapi-auth-date': datetime.now().strftime('%a, %d %b %Y %H:%M:%S UTC')
            }
            
            # Add JWS signature if present
            if jws_signature:
                _logger.info(f"Adding JWS signature to headers: {jws_signature}")
                headers['x-jws-signature'] = jws_signature
            else:
                _logger.warning("No JWS signature available for this request")
            
            url = f"{config.get_param('saib_bank_integration.base_url')}{endpoint}"
            
            # Get client certificates
            temp_cert_path, temp_key_path, temp_dir = self._read_cert_files()
            _logger.info(f"data: {data}")
            _logger.info(f"headers: {headers}")
            _logger.info(f"url: {url}")
            try:
                # CRITICAL: For JWS signature verification to work, we MUST send the EXACT same string
                # that was used for signing. Since we modified _sign_payload to always return the
                # normalized string, we can use it directly without any further processing.
                request_data = None
                
                if data:
                    # The data variable now contains the exact normalized string from _sign_payload
                    # We must use it directly without any modifications
                    if isinstance(data, str):
                        _logger.info(f"Sending request with normalized string data: {data[:100]}...")
                        request_data = data
                        # Set Content-Type to application/json for the string data
                        headers['Content-Type'] = 'application/json'
                    else:
                        # This should be rare since _sign_payload now returns strings
                        _logger.warning(f"Unexpected non-string data type: {type(data)}")
                        # Convert to string as a fallback
                        request_data = str(data)
                        _logger.info(f"Converted to string: {request_data[:100]}...")
                        headers['Content-Type'] = 'application/json'
                
                # Make the request with the normalized string data
                # Since we're always using the exact string that was signed, we only need the data parameter
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    data=request_data,  # Use data for string payloads (normalized JSON)
                    cert=(temp_cert_path, temp_key_path),
                    verify=True,
                    timeout=30
                )
            finally:
                # Clean up temporary certificate files
                if temp_dir:
                    try:
                        for file in os.listdir(temp_dir):
                            os.unlink(os.path.join(temp_dir, file))
                        os.rmdir(temp_dir)
                    except OSError as e:
                        _logger.warning(f"Error cleaning up temporary certificate files: {str(e)}")
            
            response.raise_for_status()
            
            # Parse JSON response
            try:
                json_response = response.json()
                
                # Log the full response for debugging
                _logger.info(f"SAIB API response: {json_response}")
                
                # Check for API-specific error codes in the response
                if isinstance(json_response, dict):
                    error_code = json_response.get('ErrorCode')
                    error_desc = json_response.get('ErrorDesc')
                    status_code = json_response.get('Data', {}).get('StatusCode')
                    status_detail = json_response.get('Data', {}).get('StatusDetail')
                    
                    if error_code or error_desc:
                        error_message = f"SAIB API Error: {error_desc or 'Unknown error'} (Code: {error_code or 'N/A'})"
                        _logger.error(error_message)
                        raise UserError(error_message)
                    
                    if status_code and status_code != 'OK' and status_detail:
                        error_message = f"SAIB API Status Error: {status_detail} (Code: {status_code})"
                        _logger.error(error_message)
                        raise UserError(error_message)
                
                return json_response
            except ValueError as json_err:
                _logger.error(f"Invalid JSON response from SAIB API: {str(json_err)}\nResponse content: {response.text[:500]}")
                raise UserError(f"Invalid response format from SAIB API: {str(json_err)}")
                
        except requests.exceptions.HTTPError as http_err:
            status_code = getattr(http_err.response, 'status_code', None)
            response_text = getattr(http_err.response, 'text', '')[:500]  # Limit to first 500 chars
            
            error_message = f"SAIB API HTTP Error: {status_code}\nDetails: {str(http_err)}\nResponse: {response_text}"
            _logger.error(error_message)
            raise UserError(f"SAIB API HTTP Error {status_code}: {str(http_err)}")
            
        except requests.exceptions.ConnectionError as conn_err:
            error_message = f"SAIB API Connection Error: {str(conn_err)}"
            _logger.error(error_message)
            raise UserError(f"Cannot connect to SAIB API: {str(conn_err)}")
            
        except requests.exceptions.Timeout as timeout_err:
            error_message = f"SAIB API Timeout Error: {str(timeout_err)}"
            _logger.error(error_message)
            raise UserError(f"SAIB API request timed out: {str(timeout_err)}")
            
        except requests.exceptions.RequestException as req_err:
            error_message = f"SAIB API Request Error: {str(req_err)}"
            _logger.error(error_message)
            raise UserError(f"Error communicating with SAIB API: {str(req_err)}")
            
        except Exception as e:
            error_message = f"SAIB API request failed: {str(e)}"
            _logger.error(error_message)
            raise UserError(f"Failed to communicate with SAIB: {str(e)}")

    # [sanjay-techvoot] Sign the payload with JWS and return (signature, normalized_payload).
    # Handles dict/str/bytes and ensures deterministic normalization before signing.
    def _sign_payload(self, private_key, payload):
        """
        Sign the payload with JWS using the provided private key following JWT.io style
        
        Args:
            private_key: The private key to use for signing
            payload: The payload to sign (dict, str, or bytes)
            
        Returns:
            tuple: (str: The detached JWS signature, normalized_payload: The normalized payload)
        """
        try:
            # Log the original payload type and content
            _logger.info(f"Original payload type: {type(payload)}")
            
            # Normalize the payload consistently regardless of input type
            if isinstance(payload, dict):
                _logger.info(f"Original payload keys: {list(payload.keys())}")
                # Normalize the payload for consistent JSON serialization
                # Use compact JSON format with sorted keys for consistent hashing
                normalized_payload = json.dumps(payload, sort_keys=True, separators=(',', ':'))
                _logger.info(f"Normalized payload: {normalized_payload}")
                # Keep track of the original format for return value
                return_as_dict = True
            elif isinstance(payload, str):
                _logger.info(f"Original payload string length: {len(payload)}")
                # Check if it's a JSON string
                try:
                    # Try to parse as JSON
                    json_obj = json.loads(payload)
                    if isinstance(json_obj, (dict, list)):
                        # Normalize the JSON string
                        normalized_payload = json.dumps(json_obj, sort_keys=True, separators=(',', ':'))
                        _logger.info(f"Normalized JSON string: {normalized_payload}")
                        # Keep track of the original format for return value
                        return_as_dict = isinstance(json_obj, dict)
                    else:
                        # JSON primitive, use as is
                        normalized_payload = payload
                        return_as_dict = False
                except json.JSONDecodeError:
                    # Not JSON, use as is
                    _logger.info("Payload is not JSON, using as-is")
                    normalized_payload = payload
                    return_as_dict = False
            elif isinstance(payload, bytes):
                # Try to decode as UTF-8 if it might be a JSON string
                try:
                    decoded = payload.decode('utf-8')
                    try:
                        # Check if it's JSON
                        json_obj = json.loads(decoded)
                        normalized_payload = json.dumps(json_obj, sort_keys=True, separators=(',', ':'))
                        _logger.info(f"Converted bytes to normalized JSON string: {normalized_payload}")
                        return_as_dict = isinstance(json_obj, dict)
                    except json.JSONDecodeError:
                        # Not JSON, use decoded string
                        normalized_payload = decoded
                        return_as_dict = False
                except UnicodeDecodeError:
                    # Not UTF-8, keep as bytes
                    normalized_payload = payload
                    return_as_dict = False
                    _logger.info("Payload is binary data, using as-is")
            else:
                # For other types, convert to string
                normalized_payload = str(payload)
                return_as_dict = False
                _logger.info(f"Converted other type to string: {normalized_payload[:100]}...")
            
            # Create JWS signer with private key
            signer = JWSSigner(private_key)
            
            # Create detached JWS signature using the normalized payload
            # This will use the JWT.io style implementation
            signature = signer.create_detached_jws(normalized_payload)
            
            # Log the signature for debugging
            _logger.info(f"Generated JWS signature: {signature}")
            
            # CRITICAL: Always return the normalized JSON string that was used for signing
            # This ensures that the exact same string is used for both signing and sending
            # which is required for JWS signature verification
            if isinstance(normalized_payload, str):
                _logger.info(f"Returning normalized string payload of length: {len(normalized_payload)}")
                # Return the signature and the normalized string payload
                return signature, normalized_payload
            else:
                # For non-string payloads, return as is (should be rare)
                _logger.info(f"Returning non-string payload of type: {type(normalized_payload)}")
                return signature, normalized_payload
                
        except Exception as e:
            _logger.error(f"Error signing payload: {e}")
            raise
    
    # [sanjay-techvoot] Diagnose configured private key using JWSSigner diagnostics.
    # Returns a dict with validation results and basic context info.
    def diagnose_private_key(self):
        """
        Diagnose issues with the configured private key and return a detailed report.
        This is a helper method for troubleshooting key problems.
        
        Returns:
            dict: A dictionary with diagnostic information
        """
        self.ensure_one()
        config = self.env['ir.config_parameter'].sudo()
        company = self.env.company
        
        # Get the private key
        private_key = config.get_param('saib_bank_integration.private_key')
        
        if not private_key:
            return {
                'valid': False,
                'issues': ['No private key configured'],
                'recommendations': ['Configure a private key in the SAIB Bank Integration settings']
            }
        
        # Use the diagnostic method from JWSSigner
        result = JWSSigner.diagnose_key_issues(private_key)
        
        # Add additional context
        result['key_length'] = len(private_key)
        result['has_escaped_newlines'] = '\n' in private_key
        
        return result

    # [sanjay-techvoot] Submit a single payment payload to SAIB using the API.
    # Builds the request body from payment record and calls _make_request.
    def submit_single_payment(self, payment):
        """Submit a single payment to SAIB"""
        data = {
            "ConsentId": payment.consent_id or str(uuid.uuid4()),
            "InstructionID": payment.name,
            "TransactionRef": payment.name,
            "PaymentPurpose": payment.payment_purpose,
            "Amount": str(payment.amount),
            "Currency": payment.currency_id.name,
            "ExecutionDate": payment.execution_date.isoformat(),
            "DebtorAccount": {
                "AccountNumber": payment.bank_account_id.acc_number,
                "DebtorName": payment.bank_account_id.partner_id.name,
                "AddressDetails": [
                    payment.bank_account_id.partner_id.street or 'NA',
                    payment.bank_account_id.partner_id.street2 or 'NA',
                    'NA'
                ]
            },
            "CreditorAccount": {
                "AccountNumber": payment.partner_bank_id.acc_number,
                "CreditorName": payment.partner_bank_id.partner_id.name,
                "AddressDetails": [
                    payment.partner_bank_id.partner_id.street or 'NA',
                    payment.partner_bank_id.partner_id.street2 or 'NA',
                    'NA'
                ],
                "AgentID": payment.partner_bank_id.bank_id.bic or 'SIBCSARI',
                "AgentName": payment.partner_bank_id.bank_id.name or 'SIBCSARI'
            }
        }
        
        return self._make_request('POST', '/b2b-rest-payment-service/b2b/payment/single', data)

    # [sanjay-techvoot] Submit a bulk payment payload to SAIB built from bulk_payment record.
    # Aggregates totals and calls _make_request with bulk endpoint.
    def submit_bulk_payment(self, bulk_payment):
        """Submit a bulk payment to SAIB"""
        # Calculate totals
        total_amount = sum(payment.amount for payment in bulk_payment.payment_ids)
        
        data = {
            "instructionID": bulk_payment.name,
            "CreationDateTime": datetime.now().isoformat(),
            "InstructionID": bulk_payment.name,
            "TransactionRef": bulk_payment.name,
            "Currency": bulk_payment.currency_id.name,
            "DebtorAccount": {
                "AccountNumber": bulk_payment.payment_ids[0].bank_account_id.acc_number,
                "DebtorName": bulk_payment.payment_ids[0].bank_account_id.partner_id.name,
                "AddressDetails": [
                    bulk_payment.payment_ids[0].bank_account_id.partner_id.street or 'NA',
                    bulk_payment.payment_ids[0].bank_account_id.partner_id.street2 or 'NA',
                    'NA'
                ]
            },
            "CreditorAccount": {
                "AccountNumber": bulk_payment.payment_ids[0].partner_bank_id.acc_number,
                "CreditorName": bulk_payment.payment_ids[0].partner_bank_id.partner_id.name,
                "AddressDetails": [
                    bulk_payment.payment_ids[0].partner_bank_id.partner_id.street or 'NA',
                    bulk_payment.payment_ids[0].partner_bank_id.partner_id.street2 or 'NA',
                    'NA'
                ],
                "AgentID": bulk_payment.payment_ids[0].partner_bank_id.bank_id.bic or 'SIBCSARI',
                "AgentName": bulk_payment.payment_ids[0].partner_bank_id.bank_id.name
            },
            "ExecutionDate": bulk_payment.payment_date.isoformat(),
            "ChargeAmount": "1",  # Fixed charge amount as per example
            "AmountDebited": f"SAR{total_amount}",
            "AmountCredited": f"SAR{total_amount - 1}",  # Subtracting charge amount
            "TaxAmount": "0"
        }
        
        return self._make_request('POST', '/b2b-rest-bulk-payment-service/b2b/payment/bulk', data)

    # [sanjay-techvoot] Check payment status by calling the enquiry endpoint for the payment.
    # Builds endpoint path based on payment type and calls _make_request.
    def check_payment_status(self, payment):
        """Check the status of a payment"""
        endpoint = f"/b2b-rest-enquiry-service/b2b/payment/{payment.payment_type}/{payment.name}"
        if payment.payment_type == 'single':
            endpoint += f"?instructionID={payment.name}"
        
        return self._make_request('GET', endpoint)
        
    # [sanjay-techvoot] Diagnostic method to test JWS signing across payload types.
    # Returns a dict with signatures and comparisons for debugging.
    def test_jws_signature(self, payload=None):
        """
        Test method to verify JWS signature generation with different payload types.
        This is a diagnostic tool to help troubleshoot signature issues.
        
        Args:
            payload: Optional test payload. If not provided, a test payload will be created.
            
        Returns:
            dict: A dictionary with test results including signatures and normalized payloads
        """
        self.ensure_one()
        config = self.env['ir.config_parameter'].sudo()
        
        # Get the private key
        private_key = config.get_param('saib_bank_integration.private_key')
        if not private_key:
            return {'error': 'No private key configured'}
            
        results = {}
        
        # Create a JWSSigner instance for direct testing
        try:
            signer = JWSSigner(private_key)
            results['signer_info'] = {
                'algorithm': signer.ALGORITHM,
                'private_key_type': str(type(signer.private_key))
            }
        except Exception as e:
            results['signer_error'] = str(e)
            return results
        
        # Test with provided payload or create test payloads
        if payload:
            # Test with the provided payload
            try:
                # First test with our _sign_payload method
                signature, normalized = self._sign_payload(private_key, payload)
                
                # Get the original payload as a string for comparison
                if isinstance(payload, dict):
                    original_str = json.dumps(payload, sort_keys=True, separators=(',', ':'))
                elif isinstance(payload, str):
                    original_str = payload
                elif isinstance(payload, bytes):
                    try:
                        original_str = payload.decode('utf-8')
                    except UnicodeDecodeError:
                        original_str = str(payload)
                else:
                    original_str = str(payload)
                
                # Get the normalized payload as a string for comparison
                if isinstance(normalized, dict):
                    normalized_str = json.dumps(normalized, sort_keys=True, separators=(',', ':'))
                elif isinstance(normalized, str):
                    normalized_str = normalized
                elif isinstance(normalized, bytes):
                    try:
                        normalized_str = normalized.decode('utf-8')
                    except UnicodeDecodeError:
                        normalized_str = str(normalized)
                else:
                    normalized_str = str(normalized)
                
                # Compare original and normalized
                content_match = original_str == normalized_str
                
                # Also test direct JWS creation
                direct_jws = signer.create_detached_jws(original_str)
                
                results['provided_payload'] = {
                    'original_type': str(type(payload)),
                    'original_str': original_str[:100] + '...' if len(original_str) > 100 else original_str,
                    'normalized_type': str(type(normalized)),
                    'normalized_str': normalized_str[:100] + '...' if len(normalized_str) > 100 else normalized_str,
                    'content_match': content_match,
                    'signature_via_sign_payload': signature,
                    'signature_via_direct_jws': direct_jws,
                    'signatures_match': signature == direct_jws
                }
            except Exception as e:
                results['provided_payload'] = {'error': str(e)}
        else:
            # Test with different payload types
            # 1. Dictionary payload - simulating a payment request
            dict_payload = {
                'merchantId': 'TEST_MERCHANT',
                'amount': 100.50,
                'currency': 'SAR',
                'reference': 'TEST_REF_' + str(uuid.uuid4())[:8],
                'description': 'Test Payment',
                'metadata': {
                    'customer': 'Test Customer',
                    'orderId': '12345'
                }
            }
            
            try:
                # Test with _sign_payload
                signature, normalized = self._sign_payload(private_key, dict_payload)
                
                # Convert to strings for comparison
                original_str = json.dumps(dict_payload, sort_keys=True, separators=(',', ':'))
                if isinstance(normalized, dict):
                    normalized_str = json.dumps(normalized, sort_keys=True, separators=(',', ':'))
                else:
                    normalized_str = str(normalized)
                
                # Test direct JWS creation
                direct_jws = signer.create_detached_jws(original_str)
                
                results['dict_payload'] = {
                    'original': dict_payload,
                    'original_str': original_str,
                    'normalized_str': normalized_str,
                    'content_match': original_str == normalized_str,
                    'signature_via_sign_payload': signature,
                    'signature_via_direct_jws': direct_jws,
                    'signatures_match': signature == direct_jws
                }
            except Exception as e:
                results['dict_payload'] = {'error': str(e)}
                
            # 2. JSON string payload with different formatting
            json_string_pretty = json.dumps({'a': 1, 'b': 2}, indent=2)
            json_string_compact = json.dumps({'a': 1, 'b': 2}, separators=(',', ':'))
            
            try:
                # Test with pretty JSON
                signature_pretty, normalized_pretty = self._sign_payload(private_key, json_string_pretty)
                # Test with compact JSON
                signature_compact, normalized_compact = self._sign_payload(private_key, json_string_compact)
                
                # Convert to canonical form for comparison
                normalized_pretty_str = json.dumps(json.loads(json_string_pretty), sort_keys=True, separators=(',', ':'))
                normalized_compact_str = json.dumps(json.loads(json_string_compact), sort_keys=True, separators=(',', ':'))
                
                # Direct JWS with canonical form
                direct_jws = signer.create_detached_jws(normalized_pretty_str)
                
                results['json_string'] = {
                    'pretty_original': json_string_pretty,
                    'compact_original': json_string_compact,
                    'normalized_pretty': normalized_pretty_str,
                    'normalized_compact': normalized_compact_str,
                    'formats_match': normalized_pretty_str == normalized_compact_str,
                    'signature_pretty': signature_pretty,
                    'signature_compact': signature_compact,
                    'signatures_match': signature_pretty == signature_compact,
                    'direct_jws': direct_jws,
                    'direct_jws_matches': direct_jws == signature_pretty and direct_jws == signature_compact
                }
            except Exception as e:
                results['json_string'] = {'error': str(e)}
                
            # 3. Regular string payload
            string_payload = 'This is a test string'
            try:
                signature, normalized = self._sign_payload(private_key, string_payload)
                direct_jws = signer.create_detached_jws(string_payload)
                
                results['string'] = {
                    'original': string_payload,
                    'normalized': normalized,
                    'content_match': string_payload == normalized if isinstance(normalized, str) else False,
                    'signature_via_sign_payload': signature,
                    'signature_via_direct_jws': direct_jws,
                    'signatures_match': signature == direct_jws
                }
            except Exception as e:
                results['string'] = {'error': str(e)}
                
            # 4. Bytes payload
            bytes_payload = b'Test bytes payload'
            try:
                signature, normalized = self._sign_payload(private_key, bytes_payload)
                
                # Try to decode bytes for comparison
                try:
                    bytes_decoded = bytes_payload.decode('utf-8')
                    direct_jws = signer.create_detached_jws(bytes_decoded)
                    content_match = bytes_decoded == normalized if isinstance(normalized, str) else False
                except UnicodeDecodeError:
                    bytes_decoded = str(bytes_payload)
                    direct_jws = "Cannot create direct JWS for binary data"
                    content_match = False
                
                results['bytes'] = {
                    'original': str(bytes_payload),
                    'decoded': bytes_decoded,
                    'normalized': str(normalized) if not isinstance(normalized, str) else normalized,
                    'content_match': content_match,
                    'signature_via_sign_payload': signature,
                    'signature_via_direct_jws': direct_jws,
                    'signatures_match': signature == direct_jws if direct_jws != "Cannot create direct JWS for binary data" else False
                }
            except Exception as e:
                results['bytes'] = {'error': str(e)}
        
        # Add a section to test with a real-world example that matches SAIB API format
        try:
            # Create a payload similar to what would be sent to SAIB API
            saib_payload = {
                "merchantId": "TEST_MERCHANT",
                "amount": 100.00,
                "currency": "SAR",
                "settlementDate": "2023-07-15",
                "paymentReference": "PAY_" + str(uuid.uuid4())[:8],
                "description": "Test payment for SAIB API",
                "callbackUrl": "https://example.com/callback"
            }
            
            # Test with _sign_payload
            signature, normalized = self._sign_payload(private_key, saib_payload)
            
            # Convert to strings for comparison
            original_str = json.dumps(saib_payload, sort_keys=True, separators=(',', ':'))
            if isinstance(normalized, dict):
                normalized_str = json.dumps(normalized, sort_keys=True, separators=(',', ':'))
            else:
                normalized_str = str(normalized)
            
            # Test direct JWS creation
            direct_jws = signer.create_detached_jws(original_str)
            
            # Create a full JWS (non-detached) for comparison
            full_jws = signer.generate_jws(original_str)
            
            # Parse the full JWS to extract header and payload
            jws_parts = full_jws.split('.')
            if len(jws_parts) == 3:
                header_b64, payload_b64, signature_b64 = jws_parts
                
                # Decode the header and payload
                try:
                    header_json = base64.urlsafe_b64decode(header_b64 + '=' * (4 - len(header_b64) % 4)).decode('utf-8')
                    header = json.loads(header_json)
                    
                    payload_json = base64.urlsafe_b64decode(payload_b64 + '=' * (4 - len(payload_b64) % 4)).decode('utf-8')
                    decoded_payload = json.loads(payload_json)
                    
                    # Check if the payload matches our original
                    payload_matches = json.dumps(decoded_payload, sort_keys=True, separators=(',', ':')) == original_str
                except Exception as e:
                    header = {"error": str(e)}
                    decoded_payload = {"error": str(e)}
                    payload_matches = False
            else:
                header = {"error": "Invalid JWS format"}
                decoded_payload = {"error": "Invalid JWS format"}
                payload_matches = False
            
            results['saib_api_example'] = {
                'original': saib_payload,
                'original_str': original_str,
                'normalized_str': normalized_str,
                'content_match': original_str == normalized_str,
                'signature': signature,
                'direct_jws': direct_jws,
                'signatures_match': signature == direct_jws,
                'full_jws': full_jws,
                'jws_header': header,
                'jws_decoded_payload': decoded_payload,
                'jws_payload_matches': payload_matches
            }
        except Exception as e:
            results['saib_api_example'] = {'error': str(e)}
                
        return results
