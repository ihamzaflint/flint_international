import json
import logging
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.backends import default_backend

_logger = logging.getLogger(__name__)


class JWSSigner:
    # Constants for JWS signature generation
    ALGORITHM = "RS256"
    SIGNING_ALGORITHM = "SHA256withRSA"  # Equivalent to SHA256 with PKCS1v15 padding in cryptography

    # [sanjay-techvoot] Initialize signer with PEM private key; sets self.private_key or raises on error.
    # Input: private_key_pem (str/bytes).
    def __init__(self, private_key_pem):
        """Initialize JWS signer with PEM private key"""
        try:
            # Ensure we're working with a string
            if isinstance(private_key_pem, bytes):
                private_key_pem = private_key_pem.decode('utf-8')
                
            # Handle potential escaped newlines in the key
            if '\n' in private_key_pem:
                _logger.info("Detected escaped newlines in private key, converting to actual newlines")
                private_key_pem = private_key_pem.replace('\n', '\n')

            # Basic format validation
            if not private_key_pem.startswith('-----BEGIN') or not private_key_pem.endswith('-----'):
                _logger.error("Invalid PEM format: Missing header or footer")
                raise ValueError("Invalid PEM format: Missing header or footer. The key must start with '-----BEGIN' and end with '-----'")

            # Get private key from PEM format
            self.private_key = self._get_private_key_from_pem(private_key_pem)
            _logger.info("Successfully loaded and validated RSA key")
            
        except Exception as e:
            _logger.error(f"Failed to initialize JWS signer: {str(e)}")
            raise ValueError(f"Failed to initialize JWS signer: {str(e)}")
            
    # [sanjay-techvoot] Parse and load RSA private key from PEM text; returns RSAPrivateKey or raises.
    # Input: private_key_pem (str).
    def _get_private_key_from_pem(self, private_key_pem):
        """Extract and validate private key from PEM format"""
        try:
            # Clean up the key content - remove any extra whitespace and ensure proper line breaks
            lines = private_key_pem.strip().splitlines()
            clean_lines = []
            
            # Process header
            if lines and lines[0].startswith('-----BEGIN'):
                clean_lines.append(lines[0])
                _logger.info(f"Key header: {lines[0]}")
            else:
                raise ValueError("Invalid PEM format: Missing BEGIN header")
                
            # Process base64 content
            content_lines = []
            for line in lines[1:-1]:
                line = line.strip()
                if line:
                    # Only validate non-empty lines that aren't headers/footers
                    if not line.startswith('-----'):
                        try:
                            # Try to decode as base64 to validate
                            base64.b64decode(line)
                            clean_lines.append(line)
                            content_lines.append(line)
                        except Exception as e:
                            _logger.error(f"Invalid base64 in key content: {str(e)}")
                            raise ValueError(f"Invalid key content: not valid base64. Error: {str(e)}")
                    else:
                        # Keep other header/footer lines as is
                        clean_lines.append(line)
            
            # Process footer
            if lines and lines[-1].startswith('-----END'):
                clean_lines.append(lines[-1])
                _logger.info(f"Key footer: {lines[-1]}")
            else:
                raise ValueError("Invalid PEM format: Missing END footer")
            
            # Reconstruct the key with proper format
            private_key_pem = '\n'.join(clean_lines)
            
            # Load the private key
            try:
                key = load_pem_private_key(
                    private_key_pem.encode('utf-8'),
                    password=None,
                    backend=default_backend()
                )
            except ValueError as e:
                if "Bad decrypt" in str(e) or "Bad PKCS#8 encryption" in str(e):
                    _logger.error("The private key appears to be encrypted. Please provide an unencrypted key.")
                    raise ValueError("The private key appears to be encrypted. Please provide an unencrypted key.")
                else:
                    _logger.error(f"Error loading private key: {str(e)}")
                    raise ValueError(f"Could not parse the private key: {str(e)}")

            # Verify it's an RSA key
            if not isinstance(key, rsa.RSAPrivateKey):
                _logger.error("Key is not an RSA private key")
                raise ValueError("Key is not an RSA private key. Please ensure you're using an RSA key.")

            # Test key operations
            test_data = b"test"
            try:
                key.sign(
                    test_data,
                    padding.PKCS1v15(),
                    hashes.SHA256()
                )
                _logger.info("Key signature test successful")
            except Exception as e:
                _logger.error(f"Key validation failed: {str(e)}")
                raise ValueError(f"Key validation failed: {str(e)}")
                
            return key
            
        except Exception as e:
            _logger.error(f"Failed to process private key: {str(e)}")
            raise

    # [sanjay-techvoot] Create a compact JWS string (header.payload.signature) for the given payload.
    # Input: payload (dict/str/bytes/other).
    def generate_jws(self, payload):
        """Generate a JWS token for the given payload
        
        Args:
            payload: The payload to sign (dict, str, or bytes)
            
        Returns:
            str: The complete JWS token in the format header.payload.signature
        """
        # Create header JSON with algorithm and type, matching the JavaScript implementation
        header_json = json.dumps({"alg": self.ALGORITHM, "typ": "JWT"}, separators=(',', ':'))
        header = self._encode_base64_url(header_json)
        
        # Log the payload for debugging
        _logger.info(f"Generating JWS for payload type: {type(payload)}")
        
        # Encode payload based on its type
        if isinstance(payload, dict):
            # Convert dict to JSON string with consistent formatting
            payload_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
            _logger.info(f"Payload JSON for JWS: {payload_json}")
            payload_encoded = self._encode_base64_url(payload_json)
        elif isinstance(payload, str):
            # The string might already be a JSON string
            try:
                # Try to parse as JSON to validate
                json_obj = json.loads(payload)
                # If it's a dict or list, it was a JSON string
                if isinstance(json_obj, (dict, list)):
                    _logger.info(f"Using JSON string as-is for JWS: {payload}")
                    payload_encoded = self._encode_base64_url(payload)
                else:
                    # It's a JSON primitive (number, boolean, null)
                    # Encode as a JSON string literal
                    payload_json = json.dumps(payload)
                    _logger.info(f"Encoding JSON primitive as string: {payload_json}")
                    payload_encoded = self._encode_base64_url(payload_json)
            except json.JSONDecodeError:
                # Not a JSON string, encode as a JSON string literal
                payload_json = json.dumps(payload)
                _logger.info(f"Encoding non-JSON string: {payload_json}")
                payload_encoded = self._encode_base64_url(payload_json)
        elif isinstance(payload, bytes):
            # Try to decode as UTF-8 first
            try:
                decoded = payload.decode('utf-8')
                _logger.info(f"Decoded bytes to string: {decoded[:100]}...")
                # Check if it's JSON
                try:
                    json.loads(decoded)
                    # It's a JSON string, use as is
                    payload_encoded = self._encode_base64_url(decoded)
                except json.JSONDecodeError:
                    # Not JSON, encode as string
                    payload_json = json.dumps(decoded)
                    payload_encoded = self._encode_base64_url(payload_json)
            except UnicodeDecodeError:
                # Binary data, directly encode
                _logger.info("Encoding binary data directly")
                payload_encoded = self._encode_base64_url(payload)
        else:
            # For any other type, convert to string and then encode
            payload_str = str(payload)
            payload_json = json.dumps(payload_str)
            _logger.info(f"Encoding other type as string: {payload_json}")
            payload_encoded = self._encode_base64_url(payload_json)
        
        # Create unsigned token
        unsigned_token = f"{header}.{payload_encoded}"
        
        # Sign the token
        signature = self._sign_with_private_key(unsigned_token)
        
        # Return the complete JWS token
        return f"{unsigned_token}.{signature}"
    
    # [sanjay-techvoot] Create a detached JWS (header..signature) for the given payload.
    # Input: payload (dict/str/bytes/other); payload normalized before signing.
    def create_detached_jws(self, payload):
        """Create a detached JWS signature for the given payload
        
        Args:
            payload: The payload to sign (dict, str, or bytes)
            
        Returns:
            str: The detached JWS signature in the format header..signature
        """
        # Log the payload type and content for debugging
        _logger.info(f"Creating detached JWS for payload type: {type(payload)}")
        
        # Normalize the payload to ensure consistent format
        if isinstance(payload, dict):
            _logger.info(f"Payload keys: {list(payload.keys())}")
            # Convert dict to JSON string with consistent formatting
            normalized_payload = json.dumps(payload, sort_keys=True, separators=(',', ':'))
            _logger.info(f"Converted dict to JSON string: {normalized_payload}")
        elif isinstance(payload, str):
            # Check if it's a JSON string
            try:
                # Try to parse and re-stringify to ensure consistent format
                json_obj = json.loads(payload)
                # Only re-stringify if it parsed successfully as JSON
                if isinstance(json_obj, (dict, list)):
                    original = payload
                    normalized_payload = json.dumps(json_obj, sort_keys=True, separators=(',', ':'))
                    _logger.info(f"Normalized JSON string from '{original}' to '{normalized_payload}'")
                else:
                    # JSON primitive, use as is
                    normalized_payload = payload
            except json.JSONDecodeError:
                # Not JSON, keep as is
                normalized_payload = payload
                _logger.info(f"Payload is not JSON, using as-is: {normalized_payload[:100]}...")
        elif isinstance(payload, bytes):
            _logger.info(f"Payload bytes length: {len(payload)}")
            # Try to decode as UTF-8 if it might be a JSON string
            try:
                decoded = payload.decode('utf-8')
                try:
                    # Check if it's JSON
                    json_obj = json.loads(decoded)
                    normalized_payload = json.dumps(json_obj, sort_keys=True, separators=(',', ':'))
                    _logger.info(f"Converted bytes to normalized JSON string: {normalized_payload}")
                except json.JSONDecodeError:
                    # Not JSON, use decoded string
                    normalized_payload = decoded
                    _logger.info(f"Converted bytes to string (not JSON): {normalized_payload[:100]}...")
            except UnicodeDecodeError:
                # Not UTF-8, keep as bytes
                normalized_payload = payload
                _logger.info("Payload is binary data, using as-is")
        else:
            # For other types, convert to string
            normalized_payload = str(payload)
            _logger.info(f"Converted other type to string: {normalized_payload[:100]}...")
        
        # Create header with algorithm and type (JWT style)
        header_json = json.dumps({"alg": self.ALGORITHM, "typ": "JWT"}, separators=(',', ':'))
        header = self._encode_base64_url(header_json)
        
        # For detached signature, we need to sign the payload but not include it in the result
        # First, encode the payload to base64url
        if isinstance(normalized_payload, str):
            payload_bytes = normalized_payload.encode('utf-8')
        else:
            payload_bytes = normalized_payload
            
        payload_encoded = self._encode_base64_url(payload_bytes)
        
        # Create the string to be signed (header.payload)
        unsigned_token = f"{header}.{payload_encoded}"
        
        # Sign the token
        signature = self._sign_with_private_key(unsigned_token)
        
        # Format for detached signature following JWT.io style (header..signature)
        detached_jws = f"{header}..{signature}"
        
        # Log the detached signature and full JWS for debugging
        _logger.info(f"Detached JWS: {detached_jws}")
        _logger.info(f"Full JWS would be: {header}.{payload_encoded}.{signature}")
        
        return detached_jws
        
    # [sanjay-techvoot] Sign the given string (data) with RSA private key and return base64url signature.
    # Input: data (str) — the text to sign (e.g., "header.payload").
    def _sign_with_private_key(self, data):
        """Sign data with the private key
        
        Args:
            data (str): The data to sign
            
        Returns:
            str: Base64URL-encoded signature
        """
        try:
            # Sign the data using SHA256 with PKCS1v15 padding (equivalent to SHA256withRSA in Java)
            signature = self.private_key.sign(
                data.encode('utf-8'),
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            
            # Encode the signature
            return self._encode_base64_url(signature)
            
        except Exception as e:
            _logger.error(f"Error signing data: {str(e)}")
            raise ValueError(f"Error signing data: {str(e)}")

    # [sanjay-techvoot] Encode bytes/string to base64url without '=' padding and return string.
    # Input: data (str/bytes).
    @staticmethod
    def _encode_base64_url(data):
        """Encode data as base64url without padding
        
        Args:
            data: The data to encode (string or bytes)
            
        Returns:
            str: Base64URL-encoded string without padding
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

    # [sanjay-techvoot] Diagnose common PEM key issues and return a short diagnostic dict.
    # Input: private_key_pem (str/bytes); Output: dict with 'valid','issues','recommendations'.
    @staticmethod
    def diagnose_key_issues(private_key_pem):
        """
        Diagnose common issues with private keys and return a detailed report.
        This is a helper method for troubleshooting key problems.
        
        Args:
            private_key_pem (str): The private key in PEM format
            
        Returns:
            dict: A dictionary with diagnostic information
        """
        result = {
            'valid': False,
            'issues': [],
            'format': None,
            'line_count': 0,
            'content_line_count': 0,
            'recommendations': []
        }
        
        try:
            # Basic checks
            if not private_key_pem:
                result['issues'].append('Key is empty')
                result['recommendations'].append('Provide a valid private key')
                return result
                
            # Ensure we're working with a string
            if isinstance(private_key_pem, bytes):
                private_key_pem = private_key_pem.decode('utf-8')
            
            # Check for escaped newlines
            if '\\n' in private_key_pem:
                result['issues'].append('Contains escaped newlines')
                result['recommendations'].append('Replace \\n with actual newlines')
                private_key_pem = private_key_pem.replace('\\n', '\n')
            
            # Check basic format
            lines = private_key_pem.strip().splitlines()
            result['line_count'] = len(lines)
            
            # Check header and footer
            has_header = False
            has_footer = False
            header_type = None
            
            if lines and lines[0].startswith('-----BEGIN'):
                has_header = True
                header_type = lines[0]
                
                # Determine key type
                if 'PRIVATE KEY' in lines[0]:
                    if 'RSA PRIVATE KEY' in lines[0]:
                        result['format'] = 'RSA PRIVATE KEY (PKCS#1)'
                    else:
                        result['format'] = 'PRIVATE KEY (PKCS#8)'
                elif 'CERTIFICATE' in lines[0]:
                    result['format'] = 'CERTIFICATE'
                    result['issues'].append('This is a certificate, not a private key')
                    result['recommendations'].append('Use a private key instead of a certificate')
                elif 'PUBLIC KEY' in lines[0]:
                    result['format'] = 'PUBLIC KEY'
                    result['issues'].append('This is a public key, not a private key')
                    result['recommendations'].append('Use a private key instead of a public key')
                else:
                    result['format'] = f'Unknown ({lines[0]})'
                    result['issues'].append(f'Unknown key format: {lines[0]}')
            else:
                result['issues'].append('Missing BEGIN header')
                result['recommendations'].append('Ensure key starts with -----BEGIN PRIVATE KEY----- or -----BEGIN RSA PRIVATE KEY-----')
            
            if lines and lines[-1].startswith('-----END'):
                has_footer = True
            else:
                result['issues'].append('Missing END footer')
                result['recommendations'].append('Ensure key ends with -----END PRIVATE KEY----- or -----END RSA PRIVATE KEY-----')
            
            # Check content
            content_lines = []
            if has_header and has_footer and len(lines) > 2:
                for line in lines[1:-1]:
                    line = line.strip()
                    if line:
                        try:
                            base64.b64decode(line)
                            content_lines.append(line)
                        except Exception:
                            result['issues'].append(f'Invalid base64 content: "{line[:10]}..."')
                
                result['content_line_count'] = len(content_lines)
                
                if len(content_lines) == 0:
                    result['issues'].append('No valid base64 content found')
                    result['recommendations'].append('Ensure key contains valid base64-encoded content')
            
            # Try loading the key
            if has_header and has_footer and len(content_lines) > 0:
                try:
                    # Reconstruct the key
                    clean_key = '\n'.join([lines[0]] + content_lines + [lines[-1]])
                    
                    # Try to load it
                    key = load_pem_private_key(
                        clean_key.encode('utf-8'),
                        password=None,
                        backend=default_backend()
                    )
                    
                    # Check if it's an RSA key
                    if isinstance(key, rsa.RSAPrivateKey):
                        result['valid'] = True
                    else:
                        result['issues'].append('Not an RSA private key')
                        result['recommendations'].append('Use an RSA private key')
                        
                except ValueError as e:
                    error_msg = str(e)
                    result['issues'].append(f'Key loading error: {error_msg}')
                    
                    if "Bad decrypt" in error_msg or "Bad PKCS#8 encryption" in error_msg:
                        result['issues'].append('Key appears to be encrypted')
                        result['recommendations'].append('Use an unencrypted private key')
                    elif "Could not deserialize key data" in error_msg:
                        result['recommendations'].append('Check key format and ensure all content is included')
                
                except Exception as e:
                    result['issues'].append(f'Unexpected error: {str(e)}')
            
            # Final recommendations
            if not result['valid'] and not result['recommendations']:
                result['recommendations'].append('Ensure key is in PEM format with proper header, content, and footer')
                result['recommendations'].append('Try generating a new RSA private key if problems persist')
            
            return result
            
        except Exception as e:
            result['issues'].append(f'Diagnostic error: {str(e)}')
            return result
