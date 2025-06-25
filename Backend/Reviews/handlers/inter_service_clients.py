# api/inter_service_clients.py
import requests
import logging
from .config import (
    AUTHENTICATION_SERVICE_URL,
    SUBMISSION_SERVICE_URL,
    ASSIGNMENT_SERVICE_URL,
    DEFAULT_REQUEST_TIMEOUT
)

logger = logging.getLogger(__name__) # MODIFICA: Assicurati che sia __name__

def _make_request(method: str, url: str, headers: dict = None, params: dict = None, json_data: dict = None, service_name: str = "External") -> requests.Response | None:
    """Helper generico per fare richieste HTTP e gestire errori comuni."""
    if not url or not url.startswith("http"): 
        logger.error(f"Invalid or missing URL for {service_name} Service: {url}")
        return None
    try:
        # Rimuovi la stampa di json_data se può contenere dati sensibili o essere troppo verboso in produzione
        logger.debug(f"Calling {service_name} Service: {method.upper()} {url} with params {params}") # Rimosso json_data dal log per brevità
        response = requests.request(
            method,
            url,
            headers=headers,
            params=params,
            json=json_data,
            timeout=DEFAULT_REQUEST_TIMEOUT
        )
        # Gestisci 404 separatamente per non sollevare eccezione inutilmente se è un "not found" atteso
        if response.status_code == 404:
            logger.info(f"{service_name} Service: Resource not found for {method.upper()} {url} (404). Response: {response.text[:200]}")
            return response # Restituisci l'oggetto response anche per 404
            
        response.raise_for_status() # Solleva HTTPError per altri 4xx/5xx
        return response
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"{service_name} Service: HTTP error for {method.upper()} {url}: {http_err.response.status_code} - {http_err.response.text[:500]}") # Limita lunghezza errore
    except requests.exceptions.Timeout:
        logger.error(f"{service_name} Service: Timeout for {method.upper()} {url}.")
    except requests.exceptions.ConnectionError: 
        logger.error(f"{service_name} Service: Connection error for {method.upper()} {url}.")
    except requests.exceptions.RequestException as req_err: 
        logger.error(f"{service_name} Service: RequestException for {method.upper()} {url}: {req_err}")
    except Exception as e: 
        logger.error(f"{service_name} Service: Unexpected error for {method.upper()} {url}: {e}", exc_info=True) # NUOVO LOG: exc_info=True
    return None

def get_assignment_details_api(assignment_id: str, jwt_token: str) -> dict | None:
    """Recupera i dettagli di un assignment dal servizio Assignment."""
    if not ASSIGNMENT_SERVICE_URL: 
        logger.error("ASSIGNMENT_SERVICE_URL is not configured.") # NUOVO LOG
        return None 
    
    headers = {"Authorization": f"Bearer {jwt_token}"}
    url = f"{ASSIGNMENT_SERVICE_URL}/assignments/{assignment_id}" 
    
    response = _make_request("GET", url, headers=headers, service_name="Assignment")
    if response and response.status_code == 200:
        try:
            return response.json()
        except ValueError: 
            logger.error(f"Failed to decode JSON from Assignment Service for assignment {assignment_id}. Response text: {response.text[:200]}")
    elif response and response.status_code == 404: # Già loggato da _make_request
        pass
    return None

def get_submission_details_by_id_api(submission_id: str, jwt_token: str) -> dict | None:
    """Recupera i dettagli di una sottomissione (incluso autore) dal servizio Submission."""
    if not SUBMISSION_SERVICE_URL: 
        logger.error("SUBMISSION_SERVICE_URL is not configured.") # NUOVO LOG
        return None
    headers = {"Authorization": f"Bearer {jwt_token}"}
    url = f"{SUBMISSION_SERVICE_URL}/submissions/{submission_id}" 
    
    response = _make_request("GET", url, headers=headers, service_name="Submission")
    if response and response.status_code == 200:
        try:
            return response.json() 
        except ValueError:
            logger.error(f"Failed to decode JSON from Submission Service for submission {submission_id}. Response text: {response.text[:200]}")
    elif response and response.status_code == 404: # Già loggato
        pass
    return None

def get_all_submissions_for_assignment_api(assignment_id: str, jwt_token: str) -> list | None:
    """Recupera tutte le sottomissioni per un assignment dal servizio Submission."""
    if not SUBMISSION_SERVICE_URL: 
        logger.error("SUBMISSION_SERVICE_URL is not configured.") # NUOVO LOG
        return None
    headers = {"Authorization": f"Bearer {jwt_token}"}
    url = f"{SUBMISSION_SERVICE_URL}/submissions/assignment/{assignment_id}"
    
    response = _make_request("GET", url, headers=headers, service_name="Submission (all for assignment)")
    if response and response.status_code == 200:
        try:
            return response.json() 
        except ValueError:
            logger.error(f"Failed to decode JSON from Submission Service for all submissions of {assignment_id}. Response text: {response.text[:200]}")
    elif response and response.status_code == 404: 
        logger.info(f"No submissions found (404) for assignment {assignment_id} from Submission Service.")
        return [] 
    return None 

def get_own_profile_api(jwt_token: str) -> dict | None:
    """Recupera il profilo dell'utente autenticato (proprietario del token) da Auth Service."""
    if not AUTHENTICATION_SERVICE_URL: 
        logger.error("AUTHENTICATION_SERVICE_URL is not configured for get_own_profile_api.") # NUOVO LOG
        return None
    
    headers = {"Authorization": f"Bearer {jwt_token}"}
    url = f"{AUTHENTICATION_SERVICE_URL}/auth/users/me"
    
    response = _make_request("GET", url, headers=headers, service_name="Authentication (own profile)")
    if response and response.status_code == 200:
        try:
            return response.json()
        except ValueError:
            logger.error(f"Failed to decode JSON from Authentication Service ({url}). Response text: {response.text[:200]}")
    return None

def get_user_details_api(user_serial_number: str, jwt_token: str, requester_token_info: dict) -> dict | None:
    """Recupera i dettagli di un utente specifico. Usa /me se possibile, altrimenti /students per insegnanti."""
    if not AUTHENTICATION_SERVICE_URL: 
        logger.error("AUTHENTICATION_SERVICE_URL is not configured for get_user_details_api.") # NUOVO LOG
        return None

    if not requester_token_info:
        logger.error("get_user_details_api called without requester_token_info.")
        return None

    # Controlla se stiamo chiedendo i dettagli dell'utente che fa la richiesta
    if requester_token_info.get('user_id') == user_serial_number:
        logger.debug(f"Fetching own profile for {user_serial_number} via get_own_profile_api.")
        return get_own_profile_api(jwt_token)

    # Se il richiedente è un docente, può provare a cercare lo studente nella lista /students
    if requester_token_info.get('role') == 'teacher':
        logger.debug(f"Teacher ({requester_token_info.get('user_id')}) fetching details for student {user_serial_number} via /auth/users/students.")
        headers = {"Authorization": f"Bearer {jwt_token}"}
        url = f"{AUTHENTICATION_SERVICE_URL}/auth/users/students" 
        
        response = _make_request("GET", url, headers=headers, service_name="Authentication (all students)")
        if response and response.status_code == 200:
            try:
                students_data = response.json()
                if not isinstance(students_data, list): # NUOVO CONTROLLO
                    logger.error(f"Expected a list from /auth/users/students, got {type(students_data)}. Response: {response.text[:200]}")
                    return None
                for student_details in students_data:
                    if isinstance(student_details, dict) and student_details.get('serialNumber') == user_serial_number: # NUOVO CONTROLLO
                        logger.debug(f"Found student {user_serial_number} in /auth/users/students list.")
                        return student_details 
                logger.info(f"User {user_serial_number} not found in /auth/users/students list (called by teacher).")
            except ValueError:
                logger.error(f"Failed to decode JSON response from Authentication Service ({url}). Response text: {response.text[:200]}")
        elif response and response.status_code == 403:
             logger.warning(f"get_user_details_api: Teacher token lacks permission for {url} or other 403 reason.")
        return None 

    logger.warning(f"get_user_details_api: No direct method to fetch details for {user_serial_number} by requester {requester_token_info.get('user_id')} with role '{requester_token_info.get('role')}'.")
    return None