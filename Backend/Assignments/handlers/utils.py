import jwt
import requests
import logging
from datetime import datetime, timedelta
import os

JWT_EXP_DELTA_SECONDS = 3600  # 1 ora
# Ensure this is the correct K8s service name and port for your Authentication service
AUTHENTICATION_SERVICE_URL = os.getenv('AUTHENTICATION_SERVICE_URL')
PUBLIC_KEY_URL = f"{AUTHENTICATION_SERVICE_URL}/auth/public_key"

_public_key_cache = {"key": None, "last_fetch": None}

def get_public_key():
    # Scarica e cache la chiave pubblica per 10 minuti
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
        logging.debug(f"Fetched public key: {_public_key_cache['key']}")  # <--- Add this line
    return _public_key_cache["key"]

import base64
import json

def decode_token(token):
    try:
        header = token.split('.')[0]
        header_decoded = base64.urlsafe_b64decode(header + '==')
        logging.debug(f"Token header: {header_decoded}")
        logging.debug(f"Decoding token: {token}")
        public_key = get_public_key()
        payload = jwt.decode(token, public_key, algorithms=['RS256'])
        logging.debug(f"Decoded payload: {payload}")
        if payload and 'user_id' in payload:
            return payload
        return None
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError as e:
        logging.error(f"Invalid token: {e}")  # <--- Add this line for more info
        return None


def get_and_validate_students(student_serial_numbers: list, jwt_token: str):
    """
    Fetches all students from the Authentication service and validates if the given
    student_serial_numbers exist. Requires a teacher's JWT token for the call.

    Args:
        student_serial_numbers (list): A list of student serial numbers to validate.
        jwt_token (str): The JWT token of the authenticated teacher.

    Returns:
        tuple: (bool, str or None)
               - True, None if all students are valid.
               - False, error_message if validation fails or an error occurs.
    """
    if not student_serial_numbers: # No students to validate
        return True, None

    try:
        headers = {"Authorization": f"Bearer {jwt_token}"}
        # This endpoint should be protected and only accessible by teachers in your Authentication service
        response = requests.get(f"{AUTHENTICATION_SERVICE_URL}/auth/users/students", headers=headers)
        response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
        
        existing_students_data = response.json()
        # Assuming the response is a list of dicts, e.g., [{'serialNumber': '...', ...}, ...]
        # Adjust .get('serialNumber') if your Authentication service uses a different field name
        existing_student_serials = {student.get('serialNumber') for student in existing_students_data if student.get('serialNumber')}

        for student_sn in student_serial_numbers:
            if student_sn not in existing_student_serials:
                return False, f"Student with serial number {student_sn} not found"
        
        return True, None  # All students are valid

    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code == 403:
            logging.error(f"Forbidden: Teacher token may not have rights for /users/students: {http_err}")
            return False, "Forbidden: You do not have permission to access student data."
        logging.error(f"HTTP error calling Authentication service for student validation: {http_err}")
        return False, "Error communicating with Authentication service to verify students."
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Request error calling Authentication service for student validation: {req_err}")
        return False, "Could not connect to Authentication service to verify students."
    except Exception as e:
        logging.error(f"Unexpected error during student validation in utils: {e}")
        return False, "An unexpected error occurred while validating students."


def get_teacher_info(jwt_token: str):
    """
    Fetches teacher information (name and surname) from the Authentication service.
    
    Args:
        jwt_token (str): The JWT token of the authenticated teacher.
    
    Returns:
        tuple: (dict or None, str or None)
               - teacher_info dict with 'name' and 'surname' if successful, None if error
               - error_message if an error occurs, None if successful
    """
    try:
        headers = {"Authorization": f"Bearer {jwt_token}"}
        response = requests.get(f"{AUTHENTICATION_SERVICE_URL}/auth/users/me", headers=headers)
        response.raise_for_status()
        
        teacher_data = response.json()
        return {
            'name': teacher_data.get('name'),
            'surname': teacher_data.get('surname')
        }, None
        
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error calling Authentication service for teacher info: {http_err}")
        return None, "Error communicating with Authentication service to get teacher information."
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Request error calling Authentication service for teacher info: {req_err}")
        return None, "Could not connect to Authentication service to get teacher information."
    except Exception as e:
        logging.error(f"Unexpected error during teacher info retrieval: {e}")
        return None, "An unexpected error occurred while retrieving teacher information."