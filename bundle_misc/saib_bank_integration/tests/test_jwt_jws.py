#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key, 
    Encoding, 
    PrivateFormat, 
    NoEncryption
)

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
_logger = logging.getLogger(__name__)

class JWSSigner:
    ALGORITHM = "RS256"
    
    # [sanjay-techvoot] Initialize signer: accept PEM text, normalize, and load RSA private key.
    # Raises ValueError if the key cannot be loaded or validated.
    def __init__(self, private_key_pem):
        """Initialize JWS signer with PEM private key"""
        try:
            # Ensure we're working with a string
            if isinstance(private_key_pem, bytes):
                private_key_pem = private_key_pem.decode('utf-8')
            
            # Get private key from PEM format
            self.private_key = self._get_private_key_from_pem(private_key_pem)
            _logger.info("Successfully loaded and validated RSA key")
            
        except Exception as e:
            _logger.error(f"Failed to initialize JWS signer: {str(e)}")
            raise ValueError(f"Failed to initialize JWS signer: {str(e)}")
    
    # [sanjay-techvoot] Parse and load an RSA private key from a PEM string.
    # Returns an RSAPrivateKey or raises an exception on parse/format errors.
    def _get_private_key_from_pem(self, private_key_pem):
        """Extract and validate private key from PEM format"""
        try:
            # Load the private key
            private_key = load_pem_private_key(
                private_key_pem.encode('utf-8'),
                password=None
            )
            
            # Validate that it's an RSA key
            if not isinstance(private_key, rsa.RSAPrivateKey):
                raise ValueError("The provided key is not an RSA private key")
                
            return private_key
            
        except Exception as e:
            _logger.error(f"Failed to process private key: {str(e)}")
            raise
    
    # [sanjay-techvoot] Create a full JWS token (header.payload.signature) for the payload.
    # Normalizes payload, base64url-encodes parts, signs with RSA (PKCS1v15+SHA256) and returns token.
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
        
        # Encode payload based on its type
        if isinstance(payload, dict):
            # Convert dict to JSON string with consistent formatting
            payload_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
            _logger.info(f"Payload JSON for JWS: {payload_json}")
            payload_encoded = self._encode_base64_url(payload_json)
        elif isinstance(payload, str):
            try:
                # Try to parse as JSON to validate
                json_obj = json.loads(payload)
                payload_json = json.dumps(json_obj, sort_keys=True, separators=(',', ':'))
                payload_encoded = self._encode_base64_url(payload_json)
            except json.JSONDecodeError:
                # Not a JSON string, encode as is
                payload_encoded = self._encode_base64_url(payload)
        elif isinstance(payload, bytes):
            payload_encoded = self._encode_base64_url(payload)
        else:
            # For any other type, convert to string and then encode
            payload_str = str(payload)
            payload_encoded = self._encode_base64_url(payload_str)
        
        # Create unsigned token
        unsigned_token = f"{header}.{payload_encoded}"
        
        # Sign the token
        signature = self._sign_with_private_key(unsigned_token)
        
        # Return the complete JWS token
        full_token = f"{unsigned_token}.{signature}"
        _logger.info(f"Full JWS token: {full_token}")
        return full_token
    
    # [sanjay-techvoot] Create a detached JWS (header..signature) for the payload.
    # Normalizes payload consistently and returns a signature without embedding the payload.
    def create_detached_jws(self, payload):
        """Create a detached JWS signature for the given payload
        
        Args:
            payload: The payload to sign (dict, str, or bytes)
            
        Returns:
            str: The detached JWS signature in the format header..signature
        """
        # Normalize the payload based on its type
        if isinstance(payload, dict):
            # Convert dict to JSON string with consistent formatting
            normalized_payload = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        elif isinstance(payload, str):
            # Check if it's a JSON string
            try:
                # Try to parse as JSON
                json_obj = json.loads(payload)
                normalized_payload = json.dumps(json_obj, sort_keys=True, separators=(',', ':'))
            except json.JSONDecodeError:
                # Not JSON, use as is
                normalized_payload = payload
        elif isinstance(payload, bytes):
            # Try to decode as UTF-8
            try:
                decoded = payload.decode('utf-8')
                try:
                    # Check if it's JSON
                    json_obj = json.loads(decoded)
                    normalized_payload = json.dumps(json_obj, sort_keys=True, separators=(',', ':'))
                except json.JSONDecodeError:
                    # Not JSON, use decoded string
                    normalized_payload = decoded
            except UnicodeDecodeError:
                # Not UTF-8, keep as bytes
                normalized_payload = payload
        else:
            # For other types, convert to string
            normalized_payload = str(payload)
        
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
    
    # [sanjay-techvoot] Sign a UTF-8 string with the RSA private key using PKCS1v15 + SHA256.
    # Returns the signature encoded as base64url (no padding).
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
            
            # Encode the signature as base64url
            return self._encode_base64_url(signature)
            
        except Exception as e:
            _logger.error(f"Error signing data: {str(e)}")
            raise
    
    # [sanjay-techvoot] Encode bytes or string to base64url (URL-safe) and strip '=' padding.
    # Used for encoding JWS header, payload, and signature consistently.
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
            
        # Encode as base64 and convert to string
        encoded = base64.b64encode(data).decode('utf-8')
        
        # Convert to base64url format by replacing characters
        encoded = encoded.replace('+', '-').replace('/', '_')
        
        # Remove padding
        encoded = encoded.rstrip('=')
        
        return encoded


# [sanjay-techvoot] Local test runner: generate a test RSA key, create signer, and exercise methods.
# Logs generated full and detached JWS tokens and performs basic format validations.
def test_jws_signature():
    """Test the JWS signature generation to match the JavaScript implementation"""
    # Generate a new RSA key pair for testing
    _logger.info("Generating a new RSA key pair for testing...")
    private_key_obj = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    
    # Serialize to PEM format
    private_key = private_key_obj.private_bytes(
        encoding=Encoding.PEM,
        format=PrivateFormat.PKCS8,
        encryption_algorithm=NoEncryption()
    ).decode('utf-8')
    
    _logger.info("Generated test private key successfully")

    # Create a JWS signer with the private key
    signer = JWSSigner(private_key)

    # Test with a sample payload (matching the JavaScript example)
    _logger.info("Testing with payload similar to JavaScript example...")
    payload = {"request": {"body": {"raw": "test"}}}
    
    # Test the generate_jws method
    _logger.info("Testing generate_jws method...")
    jws_token = signer.generate_jws(payload)
    _logger.info(f"Generated JWS token: {jws_token}")
    
    # Split the token to verify its components
    parts = jws_token.split('.')
    if len(parts) != 3:
        _logger.error(f"Invalid JWS token format: expected 3 parts, got {len(parts)}")
        return
    
    # Test the create_detached_jws method
    _logger.info("\nTesting create_detached_jws method...")
    detached_jws = signer.create_detached_jws(payload)
    _logger.info(f"Generated detached JWS: {detached_jws}")
    
    # Split the detached token to verify its components
    detached_parts = detached_jws.split('..')
    if len(detached_parts) != 2:
        _logger.error(f"Invalid detached JWS format: expected 2 parts separated by '..' got {len(detached_parts)}")
        return
    
    _logger.info("JWS signature tests completed successfully!")


if __name__ == "__main__":
    test_jws_signature()
