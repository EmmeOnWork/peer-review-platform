# api/config.py
import os
import logging

AUTHENTICATION_SERVICE_URL = os.getenv('AUTHENTICATION_SERVICE_URL')
SUBMISSION_SERVICE_URL = os.getenv('SUBMISSION_SERVICE_URL')
ASSIGNMENT_SERVICE_URL = os.getenv('ASSIGNMENT_SERVICE_URL')
DEFAULT_REQUEST_TIMEOUT = 10
for url_name, url_val in [
    ("AUTHENTICATION_SERVICE_URL", AUTHENTICATION_SERVICE_URL),
    ("SUBMISSION_SERVICE_URL", SUBMISSION_SERVICE_URL),
    ("ASSIGNMENT_SERVICE_URL", ASSIGNMENT_SERVICE_URL),
]:
    if not url_val:
        logging.warning(f"{url_name} environment variable is not set.")