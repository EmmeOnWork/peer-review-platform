import jwt
import os
import requests
import logging
import time
from functools import wraps
from flask import request, jsonify

# Configuration for fetching the public key from the Authentication service
ASSIGNMENT_SERVICE_URL = os.getenv('ASSIGNMENT_SERVICE_URL')
AUTHENTICATION_SERVICE_URL = os.getenv('AUTHENTICATION_SERVICE_URL')
PUBLIC_KEY_URL = f"{AUTHENTICATION_SERVICE_URL}/auth/public_key"

JWT_ALGORITHM = 'RS256' # Should match the algorithm used in Authentication service

_public_key_cache = {"key": None, "last_fetch_time": 0, "lock": False}
CACHE_DURATION_SECONDS = 600 # Cache public key for 10 minutes

logging.basicConfig(level=logging.INFO) # Configure logging

def get_public_key_from_auth_service():
    """Fetches the public key from the Authentication service and caches it."""
    current_time = time.time()
    # Basic lock to prevent multiple concurrent fetches if cache is stale
    if _public_key_cache["lock"] and (current_time - _public_key_cache["last_fetch_time"] < 10):
        logging.info("Public key fetch already in progress, waiting briefly.")
        time.sleep(0.5) # Wait briefly for other thread to finish
        if _public_key_cache["key"]:
             return _public_key_cache["key"]

    if not _public_key_cache["key"] or \
       (current_time - _public_key_cache["last_fetch_time"] > CACHE_DURATION_SECONDS):
        try:
            _public_key_cache["lock"] = True
            logging.info(f"Fetching public key from {PUBLIC_KEY_URL}")
            response = requests.get(PUBLIC_KEY_URL, timeout=5) # Added timeout
            response.raise_for_status() # Raises an HTTPError for bad responses (4XX or 5XX)
            _public_key_cache["key"] = response.text
            _public_key_cache["last_fetch_time"] = current_time
            logging.info("Public key fetched and cached successfully.")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching public key from {PUBLIC_KEY_URL}: {e}")
            # If a cached key exists, return it to maintain service availability for a while
            if _public_key_cache["key"]:
                logging.warning("Returning stale public key due to fetch error.")
                return _public_key_cache["key"]
            return None # Critical failure if no key ever fetched
        finally:
            _public_key_cache["lock"] = False
    return _public_key_cache["key"]

def decode_token(token):
    """
    Decodes the JWT token using the public key from the Authentication service.
    This function is called by Connexion for endpoints secured with bearerAuth.
    """
    public_key_pem = get_public_key_from_auth_service()
    
    if not public_key_pem:
        logging.error("Public key not available. Cannot validate token.")
        return None # Or raise an appropriate exception for Connexion
    
    logging.info(f"Attempting to decode token. Public key (first 50 chars): {public_key_pem[:50]}...")
    logging.info(f"Token (first 50 chars): {token[:50]}...")
    logging.info(f"Algorithm expected: {JWT_ALGORITHM}")

    try:
        decoded_token = jwt.decode(token, public_key_pem, algorithms=[JWT_ALGORITHM])
        # Ensure the token contains the necessary user identifier, e.g., 'user_id' or 'sub'
        # This structure should match what your Authentication service puts in the token payload
        if 'user_id' in decoded_token and 'role' in decoded_token:
            return decoded_token # This dict will be available as `token_info` in handlers
        else:
            logging.warning(f"Token is missing 'user_id' or 'role': {decoded_token}")
            return None
    except jwt.ExpiredSignatureError:
        logging.warning("Token has expired.")
        return None
    except jwt.InvalidTokenError as e:
        logging.warning(f"Invalid token: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error decoding token: {e}")
        return None

# (Optional) Decorator, if needed outside Connexion's direct handling
def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        token_info = None
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            token_info = decode_token(token)
        
        if not token_info:
            return jsonify({'message': 'Token is invalid, missing, or expired'}), 401
        
        # Pass token_info to the handler, or store in flask.g if preferred
        # For Connexion, this is usually handled by `x-bearerInfoFunc` automatically
        return f(*args, **kwargs, token_info=token_info) # Example of passing it
    return decorated_function