# api/auth_utils.py
import jwt
import requests
import logging
import os
import time 
import base64 

from .config import AUTHENTICATION_SERVICE_URL, DEFAULT_REQUEST_TIMEOUT

logger = logging.getLogger(__name__) # MODIFICA: Assicurati che sia __name__

if AUTHENTICATION_SERVICE_URL:
    PUBLIC_KEY_URL = f"{AUTHENTICATION_SERVICE_URL}/auth/public_key"
else:
    PUBLIC_KEY_URL = None
    logger.critical("auth_utils: AUTHENTICATION_SERVICE_URL is not set, JWT validation will fail.") # MODIFICA: Log più forte

_public_key_cache = {"key": None, "last_fetch_attempt": 0, "fetch_interval": 300, "lock": False} # fetch_interval in secondi (5 min)

def get_public_key() -> str | None:
    """
    Recupera la chiave pubblica RSA dal servizio di autenticazione, con caching e rate limiting.
    """
    if not PUBLIC_KEY_URL:
        logger.error("Public Key URL is not configured. Cannot fetch public key.")
        return None # Restituisci None se non configurato, decode_token lo gestirà

    now = time.time()
    
    # Controlla se è necessario un nuovo fetch (cache scaduta o mai fetchata)
    if _public_key_cache["key"] and _public_key_cache["last_fetch_attempt"] and \
       (now - _public_key_cache["last_fetch_attempt"] < _public_key_cache["fetch_interval"]):
        logger.debug("Returning cached public key (cache valid).")
        return _public_key_cache["key"]

    if _public_key_cache["lock"]:
        logger.debug("Public key fetch attempt already in progress by another call, using potentially stale cache or waiting briefly.")
        time.sleep(0.1) # Breve attesa
        # Riprova a leggere dalla cache, potrebbe essere stata aggiornata
        if _public_key_cache["key"] and _public_key_cache["last_fetch_attempt"] and \
           (now - _public_key_cache["last_fetch_attempt"] < _public_key_cache["fetch_interval"]):
            return _public_key_cache["key"]
        # Se ancora vecchia, e il lock è ancora lì, potrebbe essere un problema, ma procediamo con cautela
        # o semplicemente restituiamo la chiave vecchia se presente, per evitare troppi fallimenti
        if _public_key_cache["key"]:
             logger.warning("Returning stale public key due to ongoing fetch lock elsewhere.")
             return _public_key_cache["key"]
        # Se non c'è chiave e il lock è attivo da un altro thread, non possiamo fare molto se non aspettare o fallire
        # Per semplicità, se il lock è attivo e la chiave non c'è, segnaliamo un problema.
        logger.error("Public key fetch is locked and no cached key available.")
        return None


    _public_key_cache["lock"] = True
    _public_key_cache["last_fetch_attempt"] = now # Aggiorna il timestamp dell'ultimo tentativo *prima* della chiamata
    
    logger.info(f"Attempting to fetch new public key from {PUBLIC_KEY_URL}")
    try:
        response = requests.get(PUBLIC_KEY_URL, timeout=DEFAULT_REQUEST_TIMEOUT)
        response.raise_for_status()
        
        new_key = response.text
        if not new_key or not new_key.strip().startswith("-----BEGIN PUBLIC KEY-----"): # Controllo base sulla chiave
            logger.error(f"Fetched public key from {PUBLIC_KEY_URL} appears invalid or empty.")
            # Non aggiornare la cache con una chiave invalida, mantieni la vecchia se c'era
            if not _public_key_cache["key"]: # Se non c'era neanche una vecchia chiave
                 _public_key_cache["key"] = None # Assicura che sia None
            # Non sollevare eccezione qui, lascia che decode_token fallisca se la chiave (vecchia o None) non è valida
        else:
            _public_key_cache["key"] = new_key
            logger.info("Fetched and cached new public key successfully.")

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch public key from {PUBLIC_KEY_URL}: {e}")
        # Non invalidare la chiave buona precedente se il fetch fallisce, potrebbe essere un problema temporaneo di rete
        # Ma se non c'era una chiave prima, assicurati che rimanga None.
        if not _public_key_cache["key"]:
            _public_key_cache["key"] = None
    except Exception as e:
        logger.error(f"Unexpected error fetching public key: {e}", exc_info=True) # NUOVO LOG: exc_info=True
        if not _public_key_cache["key"]:
            _public_key_cache["key"] = None
    finally:
        _public_key_cache["lock"] = False
    
    if not _public_key_cache["key"]:
        logger.error(f"Public key is not available from {PUBLIC_KEY_URL} after fetch attempt and no valid cached key exists.")
            
    return _public_key_cache["key"]

def decode_token(token: str) -> dict | None:
    """
    Decodifica un token JWT usando la chiave pubblica recuperata.
    Restituisce il payload del token come dizionario se valido, altrimenti None.
    """
    if not token:
        logger.warning("decode_token called with an empty or None token.")
        return None
    try:
        logger.debug(f"Attempting to decode token (first 20 chars): {token[:20]}...")
        public_key_str = get_public_key() 
        
        if not public_key_str:
            logger.error("Token decoding failed: Public key is not available.")
            return None
            
        payload = jwt.decode(token, public_key_str, algorithms=['RS256'])
        # Non loggare l'intero payload in produzione se contiene dati sensibili
        logger.debug(f"Successfully decoded token. User ID: {payload.get('user_id')}, Role: {payload.get('role')}") 
        
        # Validazione base del payload atteso
        if not isinstance(payload, dict) or 'user_id' not in payload or 'role' not in payload:
            logger.warning(f"Token payload is malformed or missing 'user_id' or 'role'. Keys: {list(payload.keys()) if isinstance(payload, dict) else 'Not a dict'}")
            return None
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.info("Token has expired.")
        return None
    except jwt.InvalidTokenError as e: 
        logger.warning(f"Invalid token during decoding: {e}") # MODIFICA: Log level a warning per tentativi con token invalidi
        return None
    except Exception as e: 
        logger.error(f"Unexpected error decoding token: {e}", exc_info=True) # NUOVO LOG: exc_info=True
        return None