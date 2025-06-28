import jwt
import requests
import logging
import os
import base64

# Configura l'URL del servizio di autenticazione (da variabile d'ambiente o fallback)
AUTHENTICATION_SERVICE_URL = os.getenv('AUTHENTICATION_SERVICE_URL', 'http://authentication-app-service:5000')
PUBLIC_KEY_URL = f"{AUTHENTICATION_SERVICE_URL}/auth/public_key"

_public_key_cache = {"key": None, "last_fetch": None}

def get_public_key():
    """Scarica e cache la chiave pubblica per 10 minuti."""
    import time
    now = time.time()
    if (_public_key_cache["key"] is None or
        _public_key_cache["last_fetch"] is None or
        now - _public_key_cache["last_fetch"] > 600):
        logging.debug(f"Fetching public key from {PUBLIC_KEY_URL}")
        resp = requests.get(PUBLIC_KEY_URL)
        resp.raise_for_status()
        _public_key_cache["key"] = resp.text
        _public_key_cache["last_fetch"] = now
    return _public_key_cache["key"]

def decode_token(token):
    """Decodifica e valida il JWT, restituisce il payload o None."""
    try:
        # Decodifica header per debug (opzionale)
        header = token.split('.')[0]
        header_decoded = base64.urlsafe_b64decode(header + '==')
        logging.debug(f"Token header: {header_decoded}")
        public_key = get_public_key()
        payload = jwt.decode(token, public_key, algorithms=['RS256'])
        logging.debug(f"Decoded payload: {payload}")
        return payload
    except jwt.ExpiredSignatureError:
        logging.warning("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logging.error(f"Invalid token: {e}")
        return None

def get_auth_header(request):
    """Estrae il token JWT dall'header Authorization della richiesta Flask."""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    return auth_header.split(' ')[1]