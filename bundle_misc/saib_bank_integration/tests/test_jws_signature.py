#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import sys
import os
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.serialization import load_pem_private_key

# Set up standalone JWSSigner class without Odoo dependencies
class JWSSigner:
    ALGORITHM = "RS256"
    SIGNING_ALGORITHM = "SHA256withRSA"
    
    # [sanjay-techvoot] Initialize signer: validate input PEM text and load RSA private key.
    # Raises ValueError on invalid or non-RSA keys.
    def __init__(self, private_key_pem):
        """Initialize JWS signer with PEM private key"""
        try:
            # Ensure we're working with a string
            if isinstance(private_key_pem, bytes):
                private_key_pem = private_key_pem.decode('utf-8')
                
            # Handle potential escaped newlines in the key
            if '\n' in private_key_pem:
                print("Detected escaped newlines in private key, converting to actual newlines")
                private_key_pem = private_key_pem.replace('\n', '\n')
            
            # Get private key from PEM format
            self.private_key = self._get_private_key_from_pem(private_key_pem)
            print("Successfully loaded and validated RSA key")
            
        except Exception as e:
            print(f"Failed to initialize JWS signer: {str(e)}")
            raise ValueError(f"Failed to initialize JWS signer: {str(e)}")
    
    # [sanjay-techvoot] Parse and load an RSA private key from a PEM string.
    # Returns an RSAPrivateKey object or raises on parse/format errors.
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
            print(f"Failed to process private key: {str(e)}")
            raise
    
    # [sanjay-techvoot] Create a full JWS (header.payload.signature) for the given payload.
    # Normalizes payload, base64url-encodes parts, signs with the RSA key and returns token.
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
        print(f"Generating JWS for payload type: {type(payload)}")
        
        # Encode payload based on its type
        if isinstance(payload, dict):
            # Convert dict to JSON string with consistent formatting
            payload_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
            print(f"Payload JSON for JWS: {payload_json}")
            payload_encoded = self._encode_base64_url(payload_json)
        elif isinstance(payload, str):
            # The string might already be a JSON string
            try:
                # Try to parse as JSON to validate
                json_obj = json.loads(payload)
                # If it's a dict or list, it was a JSON string
                if isinstance(json_obj, (dict, list)):
                    print(f"Using JSON string as-is for JWS: {payload}")
                    payload_encoded = self._encode_base64_url(payload)
                else:
                    # It's a JSON primitive (number, boolean, null)
                    # Encode as a JSON string literal
                    payload_json = json.dumps(payload)
                    print(f"Encoding JSON primitive as string: {payload_json}")
                    payload_encoded = self._encode_base64_url(payload_json)
            except json.JSONDecodeError:
                # Not a JSON string, encode as a JSON string literal
                payload_json = json.dumps(payload)
                print(f"Encoding non-JSON string: {payload_json}")
                payload_encoded = self._encode_base64_url(payload_json)
        elif isinstance(payload, bytes):
            # Try to decode as UTF-8 first
            try:
                decoded = payload.decode('utf-8')
                print(f"Decoded bytes to string: {decoded[:100]}...")
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
                print("Encoding binary data directly")
                payload_encoded = self._encode_base64_url(payload)
        else:
            # For any other type, convert to string and then encode
            payload_str = str(payload)
            payload_json = json.dumps(payload_str)
            print(f"Encoding other type as string: {payload_json}")
            payload_encoded = self._encode_base64_url(payload_json)
        
        # Create unsigned token
        unsigned_token = f"{header}.{payload_encoded}"
        
        # Sign the token
        signature = self._sign_with_private_key(unsigned_token)
        
        # Return the complete JWS token
        full_token = f"{unsigned_token}.{signature}"
        print(f"Full JWS token: {full_token}")
        return full_token
    
    # [sanjay-techvoot] Create a detached JWS signature (header..signature) for a payload.
    # Normalizes payload consistently and produces a signature without embedding the payload.
    def create_detached_jws(self, payload):
        """Create a detached JWS signature for the given payload
        
        Args:
            payload: The payload to sign (dict, str, or bytes)
            
        Returns:
            str: The detached JWS signature in the format header..signature
        """
        # Log the payload type for debugging
        print(f"Creating detached JWS for payload type: {type(payload)}")
        
        # Normalize the payload based on its type
        if isinstance(payload, dict):
            # Convert dict to JSON string with consistent formatting
            normalized_payload = json.dumps(payload, sort_keys=True, separators=(',', ':'))
            print(f"Normalized dict to JSON: {normalized_payload}")
        elif isinstance(payload, str):
            # Check if it's a JSON string
            try:
                # Try to parse as JSON
                json_obj = json.loads(payload)
                normalized_payload = json.dumps(json_obj, sort_keys=True, separators=(',', ':'))
                print(f"Normalized JSON string: {normalized_payload}")
            except json.JSONDecodeError:
                # Not JSON, use as is
                normalized_payload = payload
                print(f"Using string as-is: {normalized_payload[:100]}...")
        elif isinstance(payload, bytes):
            # Try to decode as UTF-8
            try:
                decoded = payload.decode('utf-8')
                try:
                    # Check if it's JSON
                    json_obj = json.loads(decoded)
                    normalized_payload = json.dumps(json_obj, sort_keys=True, separators=(',', ':'))
                    print(f"Converted bytes to normalized JSON string: {normalized_payload}")
                except json.JSONDecodeError:
                    # Not JSON, use decoded string
                    normalized_payload = decoded
                    print(f"Converted bytes to string (not JSON): {normalized_payload[:100]}...")
            except UnicodeDecodeError:
                # Not UTF-8, keep as bytes
                normalized_payload = payload
                print("Payload is binary data, using as-is")
        else:
            # For other types, convert to string
            normalized_payload = str(payload)
            print(f"Converted other type to string: {normalized_payload[:100]}...")
        
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
        print(f"Detached JWS: {detached_jws}")
        print(f"Full JWS would be: {header}.{payload_encoded}.{signature}")
        
        return detached_jws
    
    # [sanjay-techvoot] Sign the provided string data with the loaded RSA private key (PKCS1v15 + SHA256).
    # Returns the signature encoded as base64url; raises on signing errors.
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
            print(f"Error signing data: {str(e)}")
            raise
    
    # [sanjay-techvoot] Encode bytes or string to base64url (URL-safe) without padding.
    # Ensures consistent encoding used for JWS header/payload/signature.
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

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
_logger = logging.getLogger(__name__)

# [sanjay-techvoot] Local test function that runs example signing flows using the test key.
# Demonstrates generate_jws and create_detached_jws, logs results and basic validations.
def test_jws_signature():
    """
    Test the JWS signature generation to match the JavaScript implementation
    """
    # Sample private key (for testing only - DO NOT use in production)
    private_key = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VJTUt9Us8cKj
MzEfYyjiWA4R4/M2bS1GB4t7NXp98C3SC6dVMvDuictGeurT8jNbvJZHtCSuYEvu
NMoSfm76oqFvAp8Gy0iz5sxjZmSnXyCdPEovGhLa0VzMaQ8s+CLOyS56YyCFGeJZ
agU5TzgQARQE/3/ayNjLpDq8yR6ggmgPH1OxqQZoRWW6R0LmqLj5O0BXESEKx5P/
hQvwdXlPGJr6/QgGJT4KAg8yBrtg8+coZS7rQWTMPEpv5CLVBRLXnBS3x+FRcnZz
t1Ou9FPuLuC5ZLENI0sMJl8jXOKYHaHF3P1q7wOLmUyCg2xLIQUXLk+Fj2geYbb6
JOhjMuOhAgMBAAECggEAQxURhs1v3D0wgx27ywO3zeoJmGmD6DM+N+5jkZOPEBS6
AxNAAfFMPe9TvU5AOKb5B/Pd6WoTtj7LWu+TH5hWNuDG8CSrJO8Uf7v7ujKcrR/V
0wLS4UlthVCaKLs2Uy+q3dEUmY+8XK3Js/BYpR+jk2lOlTv0T25tHmTA+gooXK1N
Wr/JYOx9AGcVo7KuF9gZOUHQXpR/T2hXbyd8/jFJ5usj+dY/CpQpvym+2kkIWqOz
dJfMOYlsWFzOkQ5c6I2Ot5OEb9uXmPbO9aiXrZ1A8SA1/J4nqHJQBk1iUFMwpji0
YBD67qX4D9wxOw5jSEkmUstxHPzjc0JxA41nJJxACQKBgQDuROadWAhNUTJUWK3J
cOKfGPhfR5j4Yy8jQkw9VsGtIHFHWgYFQXABY1VvvOzuY8Iw3BJeI/bYtQMX3/O9
aAB5QVg5+Hc7eWLFzG/PXL/QkxKYFJmV/DW61wMigIlaMxD2s4h5GG4omuKdPJZK
M9xt2O9+5NAhAP3zYiGkaVUbKQKBgQDJR1L3d4JXHMDGlsUHYPRDITqH0cM0GHLw
iux4S3hcIh6Ka2JDYJhEEsjCq5y8C7H/lLRNvw1QzZCEBEm5nDcZEzU7UYydsEpx
4ZbkBNl+/J5KYdVKNJXBA5FUtFrxn8jGcqnItLTZP9laIRwUjyxdX7hCPPdZLGVS
dZCJC8z7aQKBgQCQWrO4PaQQIZ/ZPi8/f2dDp1HAqdJcyLQTSkHPUZUKfIVRLZbK
xNPPWPr87ntbr1grYd+B0K9yYmvsRX5jP2VUjy3nEB7wjNR5OJJ31uojGkP1oQE0
dJtOcRLRXqYJKKoJKlHmGHwxIxc9R5L3ThLP7vZjgR6QYjnm4RZ79ERwCQKBgGnv
nCUXH3hbxXJYvHiMmCkgEbVPSNV94/JjH5Vv9D4jKsxDrY8NGw+1nOSFstYMc1+F
xKWXpzrQjQlnuAZY/B7Ozx2YZkO4yqKi/1+/38mSqwZVYCHnHQVLV2oaYOBVwmwt
QFFk8nRE/H+LRVgQT3LIk2PNrEAix1cPHFYDm315AoGAMdDQ9JXFkXDLxPqRyR1e
TqxQmfBhDn8ZQH1FVi9jw4TCXFbLMFXyKbEfP9ARk4lMO0wicMA6Y5e4AxELJP0Q
Hxq+b8wZk76nMYLOXEAq4LwUzrLfZ1pVYLZ/RNbzf5g7xpLEa6YR4ULZ1PnD1Xxq
QVlyjYH5nCiGZ9QrcGgLbO4=
-----END PRIVATE KEY-----"""

    # Create a JWS signer with the private key
    signer = JWSSigner(private_key)

    # Test with a sample payload (matching the JavaScript example)
    header = {
        "alg": "RS256",
        "typ": "JWT"
    }
    
    payload = json.loads('{"request":{"body":{"raw":"test"}}')
    
    # Test the generate_jws method
    _logger.info("Testing generate_jws method...")
    
    # Convert header and payload to strings for comparison
    header_str = json.dumps(header, separators=(',', ':'))
    payload_str = json.dumps(payload, separators=(',', ':'))
    
    # Log the header and payload that will be used
    _logger.info(f"Header: {header_str}")
    _logger.info(f"Payload: {payload_str}")
    
    # Generate the JWS token
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
