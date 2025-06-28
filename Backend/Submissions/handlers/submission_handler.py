from flask import jsonify, request as flask_request, Response
import requests
from werkzeug.utils import secure_filename
import uuid
import os
import mimetypes  # Aggiungi questa linea
from minio import Minio
import logging
import flask # For type hinting flask.Request
from bson import ObjectId # For MongoDB ObjectId conversion
from datetime import datetime, timezone
from typing import Optional, List # <<< AGGIUNGI QUESTA RIGA PER OPTIONAL E LIST
from flask import Response, request
from db import get_db, get_minio_client, MINIO_BUCKET_NAME # Assuming db.py sets these up
from models import Submission
# Assuming utils.py contains decode_token and potentially service URLs
# If service URLs are directly from os.environ, load them here:
# e.g., AUTHENTICATION_SERVICE_URL = os.getenv("AUTHENTICATION_SERVICE_URL")
# For this example, I'll assume they are imported via 'from .utils import *' or available globally
from .utils import decode_token # Make sure this matches your project structure
# Define service URLs (ideally from environment variables or a config file)
AUTHENTICATION_SERVICE_URL = os.getenv("AUTHENTICATION_SERVICE_URL", "http://auth-service:5000") # Example
ASSIGNMENT_SERVICE_URL = os.getenv("ASSIGNMENT_SERVICE_URL", "http://assignment-service:5001") # Example
REVIEW_SERVICE_URL = os.getenv("REVIEW_SERVICE_URL", "http://review-app-service:5003")


logger = logging.getLogger(__name__)

def _format_datetime_to_iso_z(dt_obj: Optional[datetime]) -> Optional[str]:
    if dt_obj is None:
        return None
    if not isinstance(dt_obj, datetime): # If it's already a string, try to normalize or return as is
        if isinstance(dt_obj, str):
            if dt_obj.endswith('+00:00'):
                return dt_obj[:-6] + 'Z'
            return dt_obj # Assume it's already in a good format or cannot be processed
        return str(dt_obj) # Fallback for other types

    if dt_obj.tzinfo is None:
        dt_aware = dt_obj.replace(tzinfo=timezone.utc)
    else:
        dt_aware = dt_obj.astimezone(timezone.utc)
    return dt_aware.isoformat().replace('+00:00', 'Z')

def submit_assignment(token_info=None):
    logger.info(f"--- submit_assignment CALLED ---")

    if not token_info:
        logger.error("Token information not found.")
        return jsonify({"error": "Unauthorized", "message": "Token information not found"}), 401

    student_serial_number = token_info.get('user_id')
    if not student_serial_number:
        logger.error("Student serial number (user_id) not found in token.")
        return jsonify({"error": "Unauthorized", "message": "Student serial number not found in token"}), 401
    
    logger.info(f"Authenticated user (student_serial_number from token): {student_serial_number}")

    student_name = "Unknown"
    student_surname = "Unknown"
    if AUTHENTICATION_SERVICE_URL:
        try:
            auth_header = flask_request.headers.get('Authorization')
            headers = {'Authorization': auth_header} if auth_header else {}
            user_profile_url = f"{AUTHENTICATION_SERVICE_URL}/auth/users/me" # Adjust endpoint if needed
            logger.info(f"Fetching student profile from: {user_profile_url}")
            response = requests.get(user_profile_url, headers=headers, timeout=5)
            response.raise_for_status()
            user_data = response.json()
            student_name = user_data.get('name', 'Unknown')
            student_surname = user_data.get('surname', 'Unknown')
            logger.info(f"Successfully fetched student name: {student_name}, surname: {student_surname}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching student profile: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching student profile: {e}", exc_info=True)
    else:
        logger.warning("AUTHENTICATION_SERVICE_URL not configured. Cannot fetch student name/surname.")

    assignment_id_from_form = flask_request.form.get('assignmentId')
    text_content_from_form = flask_request.form.get('text')

    if not assignment_id_from_form:
        logger.error("assignmentId is missing from form data.")
        return jsonify({"error": "Bad Request", "message": "assignmentId is required in form data"}), 400

    if not ASSIGNMENT_SERVICE_URL:
        logger.error("ASSIGNMENT_SERVICE_URL not configured. Cannot verify assignment deadline.")
        return jsonify({"error": "Service Configuration Error", "message": "Assignment service URL not configured"}), 500

    try:
        assignment_details_url = f"{ASSIGNMENT_SERVICE_URL}/assignments/{assignment_id_from_form}"
        auth_header_deadline = flask_request.headers.get('Authorization')
        headers_deadline = {'Authorization': auth_header_deadline} if auth_header_deadline else {}
        logger.info(f"Fetching assignment details from: {assignment_details_url} for deadline check")
        response = requests.get(assignment_details_url, headers=headers_deadline, timeout=10)
        response.raise_for_status()
        assignment_data = response.json()
        deadline_str = assignment_data.get('deadline')

        if not deadline_str:
            logger.error(f"Deadline not found for assignment {assignment_id_from_form}.")
            return jsonify({"error": "Bad Request", "message": "Assignment deadline information missing."}), 400

        if deadline_str.endswith('Z'):
            deadline_str = deadline_str[:-1] + '+00:00'
        
        assignment_deadline = datetime.fromisoformat(deadline_str)
        if assignment_deadline.tzinfo is None:
            assignment_deadline = assignment_deadline.replace(tzinfo=timezone.utc)
        else:
            assignment_deadline = assignment_deadline.astimezone(timezone.utc)
        
        current_time_utc = datetime.now(timezone.utc)

        if current_time_utc > assignment_deadline:
            logger.warning(f"Deadline passed for assignment {assignment_id_from_form}. Deadline: {assignment_deadline.isoformat()}, Current: {current_time_utc.isoformat()}")
            return jsonify({"error": "Forbidden", "message": "The deadline for this assignment has passed."}), 403
        logger.info(f"Deadline check passed for assignment {assignment_id_from_form}.")

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logger.error(f"Assignment {assignment_id_from_form} not found.")
            return jsonify({"error": "Not Found", "message": f"Assignment {assignment_id_from_form} not found."}), 404
        logger.error(f"HTTP error checking deadline: {e}")
        return jsonify({"error": "Service Communication Error", "message": "Could not verify assignment deadline (HTTP error)."}), 503
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error checking deadline: {e}")
        return jsonify({"error": "Service Communication Error", "message": "Could not verify assignment deadline (network error)."}), 503
    except (ValueError, TypeError) as e:
        logger.error(f"Error parsing deadline '{deadline_str}': {e}")
        return jsonify({"error": "Internal Server Error", "message": "Error processing assignment deadline format."}), 500
    except Exception as e:
        logger.error(f"Unexpected error checking deadline: {e}", exc_info=True)
        return jsonify({"error": "Internal Server Error", "message": "Unexpected error checking deadline."}), 500

    uploaded_files = flask_request.files.getlist('attachments')
    attachment_identifiers = []
    minio_client = get_minio_client()
    if not minio_client and uploaded_files:
         logger.error("MinIO client is None but files were submitted.")
         return jsonify({"error": "Service Configuration Error", "message": "File storage service not available."}), 500

    for file_storage in uploaded_files:
        if file_storage and file_storage.filename:
            original_filename = secure_filename(file_storage.filename)
            _, file_extension = os.path.splitext(original_filename)
            object_name = f"submissions/{student_serial_number}/{assignment_id_from_form}/{uuid.uuid4()}{file_extension}"
            try:
                logger.info(f"Uploading '{original_filename}' to MinIO as '{object_name}'")
                # Reset stream position to beginning and read content
                file_storage.stream.seek(0)
                file_content = file_storage.stream.read()
                file_size = len(file_content)
                
                # Create a new BytesIO object with the content
                import io
                file_stream = io.BytesIO(file_content)
                
                minio_client.put_object(
                    MINIO_BUCKET_NAME, object_name, file_stream,
                    length=file_size, content_type=file_storage.content_type
                )
                attachment_identifiers.append(object_name)
                logger.info(f"Successfully uploaded '{object_name}'.")
            except Exception as e:
                logger.error(f"Failed to upload '{original_filename}' to MinIO: {e}", exc_info=True)
                return jsonify({"error": "File Upload Failed", "message": f"Failed to upload: {original_filename}."}), 500
        elif file_storage and not file_storage.filename:
            logger.warning("Received file part without filename. Skipping.")

    db = get_db()
    if db is None:
        logger.error("Database connection failed.")
        return jsonify({"error": "Service Configuration Error", "message": "Database connection failed"}), 500

    new_submission = Submission(
        assignment_id=assignment_id_from_form,
        student_serial_number=student_serial_number,
        text=text_content_from_form,
        attachments=attachment_identifiers,
        student_name=student_name,
        student_surname=student_surname
    )

    try:
        submission_dict = new_submission.to_dict()
        # submittedAt is already a datetime object from to_dict
        result = db.submissions.insert_one(submission_dict)
        inserted_id = result.inserted_id
        logger.info(f"Submission created with ID: {inserted_id}")

        response_data = submission_dict.copy() # Use the dict that was inserted
        response_data['submissionId'] = str(inserted_id)
        response_data['submittedAt'] = _format_datetime_to_iso_z(response_data['submittedAt'])
        
        # Remove internal _id if present from model's dict for response consistency
        if '_id' in response_data: del response_data['_id']


        return jsonify(response_data), 201
    except Exception as e:
        logger.error(f"Failed to create submission in DB: {e}", exc_info=True)
        return jsonify({"error": "Database Operation Failed", "message": "Failed to create submission."}), 500


def get_my_submissions(token_info=None):
    logger.info(f"--- get_my_submissions CALLED ---")
    if not token_info:
        logger.error("Token info not found for get_my_submissions.")
        return jsonify({"error": "Unauthorized", "message": "Token information not found"}), 401
    
    student_serial_number = token_info.get('user_id')
    if not student_serial_number:
        logger.error("Student serial (user_id) not found in token for get_my_submissions.")
        return jsonify({"error": "Unauthorized", "message": "Student serial number not found in token"}), 401

    logger.info(f"Fetching submissions for student: {student_serial_number}")
    db = get_db()
    if db is None:
        logger.error("DB connection failed in get_my_submissions.")
        return jsonify({"error": "Service Configuration Error", "message": "Database connection failed"}), 500

    try:
        submissions_cursor = db.submissions.find({"studentSerialNumber": student_serial_number})
        results = []
        for doc in submissions_cursor:
            doc['submissionId'] = str(doc.pop('_id'))
            doc['submittedAt'] = _format_datetime_to_iso_z(doc.get('submittedAt'))
            results.append(doc)
        logger.info(f"Found {len(results)} submissions for student {student_serial_number}.")
        return jsonify(results), 200
    except Exception as e:
        logger.error(f"Error fetching submissions from DB: {e}", exc_info=True)
        return jsonify({"error": "Database Operation Failed", "message": "Error fetching submissions."}), 500


def get_all_submissions_for_assignment(token_info=None, assignmentId=None):
    logger.info(f"--- get_all_submissions_for_assignment CALLED ---")
    if not assignmentId:
        logger.error("assignmentId path parameter is missing.")
        return jsonify({"error": "Bad Request", "message": "assignmentId is required"}), 400
    
    assignmentId = assignmentId.strip()
    if not assignmentId:
        logger.error("assignmentId is empty after stripping.")
        return jsonify({"error": "Bad Request", "message": "assignmentId is invalid"}), 400

    if not token_info:
        logger.error("Token info not found.")
        return jsonify({"error": "Unauthorized", "message": "Token information not found"}), 401

    user_role = token_info.get('role')
    requesting_teacher_id = token_info.get('user_id')

    if user_role not in ['teacher', 'admin']: # Admins can also view
        logger.warning(f"User {requesting_teacher_id} (role: {user_role}) forbidden from accessing submissions for assignment {assignmentId}.")
        return jsonify({"error": "Forbidden", "message": "User does not have sufficient privileges"}), 403

    logger.info(f"User {requesting_teacher_id} (role: {user_role}) requesting submissions for assignment {assignmentId}.")

    # Teacher specific check for ownership
    if user_role == 'teacher':
        if not ASSIGNMENT_SERVICE_URL:
            logger.error("ASSIGNMENT_SERVICE_URL not configured for ownership check.")
            return jsonify({"error": "Service Configuration Error", "message": "Assignment service URL not configured"}), 500
        try:
            auth_header = flask_request.headers.get('Authorization')
            headers = {'Authorization': auth_header} if auth_header else {}
            assignment_details_url = f"{ASSIGNMENT_SERVICE_URL}/assignments/{assignmentId}"
            logger.info(f"Verifying ownership: GET {assignment_details_url}")
            response = requests.get(assignment_details_url, headers=headers, timeout=10)
            response.raise_for_status()
            assignment_data = response.json()
            assignment_owner_id = assignment_data.get('teacherSerialNumber')

            if assignment_owner_id != requesting_teacher_id:
                logger.warning(f"Teacher {requesting_teacher_id} does not own assignment {assignmentId} (Owner: {assignment_owner_id}).")
                return jsonify({"error": "Forbidden", "message": "Teacher does not own this assignment."}), 403
            logger.info(f"Ownership confirmed for teacher {requesting_teacher_id} on assignment {assignmentId}.")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.error(f"Assignment {assignmentId} not found during ownership check.")
                return jsonify({"error": "Not Found", "message": f"Assignment {assignmentId} not found."}), 404
            logger.error(f"HTTP error during ownership check for {assignmentId}: {e.response.status_code} - {e.response.text}")
            return jsonify({"error": "Service Communication Error", "message": "Could not verify assignment ownership (HTTP error)."}), 503
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during ownership check for {assignmentId}: {e}")
            return jsonify({"error": "Service Communication Error", "message": "Could not verify assignment ownership (network error)."}), 503
        except Exception as e:
            logger.error(f"Unexpected error during ownership verification for {assignmentId}: {e}", exc_info=True)
            return jsonify({"error": "Internal Server Error", "message": "Unexpected error during ownership verification."}), 500

    db = get_db()
    if db is None:
        logger.error("DB connection failed for get_all_submissions_for_assignment.")
        return jsonify({"error": "Service Configuration Error", "message": "Database connection failed"}), 500

    try:
        logger.info(f"Fetching submissions from DB for assignmentId: {assignmentId}")
        submissions_cursor = db.submissions.find({"assignmentId": assignmentId})
        results = []
        for doc in submissions_cursor:
            doc['submissionId'] = str(doc.pop('_id'))
            doc['submittedAt'] = _format_datetime_to_iso_z(doc.get('submittedAt'))
            # Ensure all expected fields are present or have defaults for the list view
            doc.setdefault('studentName', "N/A")
            doc.setdefault('studentSurname', "N/A")
            doc.setdefault('text', None) # Or some indicator if text is too long for summary
            doc.setdefault('attachments', [])
            results.append(doc)
        logger.info(f"Found {len(results)} submissions for assignment {assignmentId}.")
        return jsonify(results), 200
    except Exception as e:
        logger.error(f"Error fetching/processing submissions for {assignmentId}: {e}", exc_info=True)
        return jsonify({"error": "Database Operation Failed", "message": "Error processing submissions."}), 500

# --- MODIFIED FUNCTION to use /submissions/{submissionId} ---
def get_student_submission_for_assignment(token_info=None, submissionId=None):
    logger.info(f"--- get_student_submission_for_assignment (for /submissions/{{submissionId}}) CALLED ---")
    logger.info(f"Request for submissionId: {submissionId}")

    if not token_info:
        logger.error("Token information not found.")
        return jsonify({"error": "Unauthorized", "message": "Token information not found"}), 401

    user_role = token_info.get('role')
    requesting_user_id = token_info.get('user_id')
    logger.info(f"User {requesting_user_id} (role: '{user_role}') requesting submission {submissionId}")

    if not submissionId:
        logger.error("submissionId path parameter is missing.")
        return jsonify({"error": "Bad Request", "message": "submissionId is required"}), 400

    try:
        submission_object_id = ObjectId(submissionId)
    except Exception: # bson.errors.InvalidId
        logger.error(f"Invalid submissionId format: {submissionId}")
        return jsonify({"error": "Bad Request", "message": "Invalid submissionId format"}), 400

    db = get_db()
    if db is None:
        logger.error("Database connection failed.")
        return jsonify({"error": "Service Configuration Error", "message": "Database connection failed"}), 500

    submission_doc = db.submissions.find_one({"_id": submission_object_id})

    if not submission_doc:
        logger.warning(f"Submission {submissionId} not found in database.")
        return jsonify({"error": "Not Found", "message": "Submission not found"}), 404

    logger.info(f"Found submission {submissionId}.")
    
    # Extract assignmentId from the submission for teacher authorization
    assignment_id_from_submission = submission_doc.get('assignmentId')
    if not assignment_id_from_submission:
        logger.error(f"Submission {submissionId} is missing 'assignmentId'. Cannot perform teacher authorization.")
        # This is an internal data consistency issue if it occurs
        return jsonify({"error": "Internal Server Error", "message": "Submission data incomplete (missing assignmentId)"}), 500

    # Authorization Logic
    authorized = False
    submission_student_id = submission_doc.get('studentSerialNumber')

    if user_role == 'student':
        if requesting_user_id == submission_student_id:
            logger.info(f"Student {requesting_user_id} is authorized for their own submission {submissionId}.")
            authorized = True
        else:
            logger.warning(f"Student {requesting_user_id} attempted to access submission {submissionId} belonging to {submission_student_id}.")
    elif user_role == 'teacher':
        if not ASSIGNMENT_SERVICE_URL:
            logger.error("ASSIGNMENT_SERVICE_URL not configured. Cannot verify teacher ownership.")
            return jsonify({"error": "Service Configuration Error", "message": "Assignment service URL not configured"}), 500
        try:
            auth_header = flask_request.headers.get('Authorization')
            headers = {'Authorization': auth_header} if auth_header else {}
            assignment_details_url = f"{ASSIGNMENT_SERVICE_URL}/assignments/{assignment_id_from_submission}"
            logger.info(f"Teacher {requesting_user_id}: Verifying ownership of assignment {assignment_id_from_submission} (from sub {submissionId}) at {assignment_details_url}")
            
            response = requests.get(assignment_details_url, headers=headers, timeout=10)
            response.raise_for_status()
            assignment_data = response.json()
            assignment_owner_id = assignment_data.get('teacherSerialNumber')

            if assignment_owner_id == requesting_user_id:
                logger.info(f"Teacher {requesting_user_id} owns assignment {assignment_id_from_submission}. Authorized for submission {submissionId}.")
                authorized = True
            else:
                logger.warning(f"Teacher {requesting_user_id} does not own assignment {assignment_id_from_submission} (Owner: {assignment_owner_id}).")
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.error(f"Assignment {assignment_id_from_submission} (from submission {submissionId}) not found via Assignment service.")
                # Return 404 for the submission if its related assignment is gone, as auth cannot be completed
                return jsonify({"error": "Not Found", "message": f"Associated assignment {assignment_id_from_submission} not found."}), 404
            logger.error(f"HTTP error verifying assignment ownership for {assignment_id_from_submission}: {e.response.status_code} - {e.response.text}")
            return jsonify({"error": "Service Communication Error", "message": "Could not verify assignment ownership (HTTP error)."}), 503
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error verifying assignment ownership for {assignment_id_from_submission}: {e}")
            return jsonify({"error": "Service Communication Error", "message": "Could not verify assignment ownership (network error)."}), 503
        except Exception as e:
            logger.error(f"Unexpected error verifying assignment ownership for {assignment_id_from_submission}: {e}", exc_info=True)
            return jsonify({"error": "Internal Server Error", "message": "Error verifying assignment ownership."}), 500
            
    elif user_role == 'admin':
        logger.info(f"Admin {requesting_user_id} is authorized for submission {submissionId}.")
        authorized = True

    if not authorized:
        logger.warning(f"User {requesting_user_id} (role: {user_role}) is not authorized to access submission {submissionId}.")
        return jsonify({"error": "Forbidden", "message": "Not authorized to access this submission"}), 403

    # Format and return the submission
    submission_doc['submissionId'] = str(submission_doc.pop('_id'))
    submission_doc['submittedAt'] = _format_datetime_to_iso_z(submission_doc.get('submittedAt'))
    
    logger.info(f"Successfully returning submission {submissionId} to user {requesting_user_id}.")
    return jsonify(submission_doc), 200



def health_check():
    return {"status": "OK"}, 200


def download_attachment(token_info=None, studentId=None, assignmentId=None, filename=None):
    """Download a submission attachment file from MinIO."""
    logger.info(f"--- download_attachment CALLED with studentId: {studentId}, assignmentId: {assignmentId}, filename: {filename} ---")
    
    if not token_info:
        logger.error("Token information not found.")
        return jsonify({"error": "Unauthorized", "message": "Token information not found"}), 401
    
    if not all([studentId, assignmentId, filename]):
        logger.error("Missing required parameters.")
        return jsonify({"error": "Bad Request", "message": "studentId, assignmentId, and filename are required"}), 400
    
    # Construct the full MinIO path
    full_path = f"submissions/{studentId}/{assignmentId}/{filename}"
    
    try:
        # Get MinIO client
        minio_client = get_minio_client()
        if not minio_client:
            logger.error("MinIO client not available.")
            return jsonify({"error": "Internal Server Error", "message": "Storage service unavailable"}), 500
        
        # Verify the file exists and get its info
        try:
            file_stat = minio_client.stat_object(MINIO_BUCKET_NAME, full_path)
        except Exception as e:
            logger.error(f"File not found in MinIO: {full_path}, error: {e}")
            return jsonify({"error": "Not Found", "message": "File not found"}), 404
        
        # Check authorization
        user_id = token_info.get('user_id')
        user_role = token_info.get('role', 'student')
        
        if user_role == 'student':
            # Students can only download their own files
            if user_id != studentId:
                logger.error(f"Student {user_id} trying to access file of student {studentId}")
                return jsonify({"error": "Forbidden", "message": "You can only download your own files"}), 403
        elif user_role == 'teacher':
            # Teachers can download files from assignments they own
            # Check if teacher owns the assignment
            try:
                assignment_response = requests.get(
                    f"{ASSIGNMENT_SERVICE_URL}/assignments/{assignmentId}",
                    headers={"Authorization": f"Bearer {flask_request.headers.get('Authorization', '').replace('Bearer ', '')}"}
                )
                if assignment_response.status_code == 404:
                    logger.error(f"Assignment {assignmentId} not found")
                    return jsonify({"error": "Not Found", "message": "Assignment not found"}), 404
                elif assignment_response.status_code == 403:
                    logger.error(f"Teacher {user_id} not authorized for assignment {assignmentId}")
                    return jsonify({"error": "Forbidden", "message": "You are not authorized to access files from this assignment"}), 403
                elif assignment_response.status_code != 200:
                    logger.error(f"Error checking assignment ownership: {assignment_response.status_code}")
                    return jsonify({"error": "Internal Server Error", "message": "Error verifying assignment access"}), 500
            except requests.RequestException as e:
                logger.error(f"Error connecting to Assignment service: {e}")
                return jsonify({"error": "Service Unavailable", "message": "Assignment service unavailable"}), 503
        # Admin role would have access to all files (no additional checks needed)
        
        # Download the file from MinIO
        try:
            file_data = minio_client.get_object(MINIO_BUCKET_NAME, full_path)
            file_content = file_data.read()
            file_data.close()
        except Exception as e:
            logger.error(f"Error downloading file from MinIO: {e}")
            return jsonify({"error": "Internal Server Error", "message": "Error downloading file"}), 500
        
        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(filename)
        if not mime_type:
            mime_type = 'application/octet-stream'
        
        # Create response with file content - Force octet-stream to match OpenAPI spec
        response = Response(
            file_content,
            mimetype='application/octet-stream',  # Forza questo per rispettare OpenAPI
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Length': str(len(file_content)),
                'Content-Type': 'application/octet-stream'  # Esplicito anche negli headers
            }
        )
        
        logger.info(f"File {full_path} downloaded successfully by user {user_id}")
        return response
        
    except Exception as e:
        logger.error(f"Unexpected error in download_attachment: {e}")
        return jsonify({"error": "Internal Server Error", "message": "An unexpected error occurred"}), 500



def _check_peer_review_authorization(student_serial_number, submission_id, auth_header):
    """
    Verifica se uno studente è autorizzato a vedere una submission per peer review.
    Chiama il servizio Review per verificare se la submission è assegnata allo studente.
    """
    try:
        headers = {'Authorization': auth_header} if auth_header else {}
        reviews_url = f"{REVIEW_SERVICE_URL}/reviews/student/{student_serial_number}"
        logger.info(f"Checking peer review authorization at: {reviews_url}")
        
        response = requests.get(reviews_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        assigned_reviews = response.json()
        
        # Verifica se la submission è tra quelle assegnate per la revisione
        for review in assigned_reviews:
            if review.get('submissionId') == submission_id:
                logger.info(f"Student {student_serial_number} is authorized to review submission {submission_id}")
                return True
        
        logger.warning(f"Student {student_serial_number} is not assigned to review submission {submission_id}")
        return False
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logger.error(f"Student {student_serial_number} not found in review assignments")
            return False
        logger.error(f"HTTP error checking peer review authorization: {e}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error checking peer review authorization: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error checking peer review authorization: {e}")
        raise


def get_submission_for_review(token_info=None, submissionId=None):
    """
    Recupera il contenuto di una submission per peer review.
    Accesso limitato agli studenti assegnati alla revisione.
    """
    logger.info(f"--- get_submission_for_review CALLED with submissionId: {submissionId} ---")
    
    if not token_info:
        logger.error("Token information not found.")
        return jsonify({"error": "Unauthorized", "message": "Token information not found"}), 401
    
    if not submissionId:
        logger.error("submissionId parameter is required.")
        return jsonify({"error": "Bad Request", "message": "submissionId is required"}), 400
    
    # Validazione formato ObjectId
    try:
        ObjectId(submissionId)
    except Exception:
        logger.error(f"Invalid submissionId format: {submissionId}")
        return jsonify({"error": "Bad Request", "message": "Invalid submissionId format"}), 400
    
    student_serial_number = token_info.get('user_id')
    if not student_serial_number:
        logger.error("Student serial number not found in token.")
        return jsonify({"error": "Unauthorized", "message": "Student serial number not found"}), 401
    
    # Verifica autorizzazione tramite servizio Review
    try:
        auth_header = flask_request.headers.get('Authorization')
        if not _check_peer_review_authorization(student_serial_number, submissionId, auth_header):
            return jsonify({"error": "Forbidden", "message": "You are not assigned to review this submission"}), 403
    except requests.exceptions.RequestException:
        return jsonify({"error": "Service Communication Error", "message": "Could not verify review authorization"}), 503
    except Exception as e:
        logger.error(f"Error checking authorization: {e}")
        return jsonify({"error": "Internal Server Error", "message": "Error verifying authorization"}), 500
    
    # Recupera la submission dal database
    db = get_db()
    if db is None:
        logger.error("Database connection failed.")
        return jsonify({"error": "Internal Server Error", "message": "Database connection failed"}), 500
    
    try:
        submission_doc = db.submissions.find_one({"_id": ObjectId(submissionId)})
        if not submission_doc:
            logger.error(f"Submission {submissionId} not found.")
            return jsonify({"error": "Not Found", "message": "Submission not found"}), 404
    except Exception as e:
        logger.error(f"Database error retrieving submission {submissionId}: {e}")
        return jsonify({"error": "Internal Server Error", "message": "Database error"}), 500
    
    # Prepara la risposta per peer review (senza studentId per anonimato)
    minio_client = get_minio_client()
    attachments_metadata = []
    
    for attachment_path in submission_doc.get('attachments', []):
        try:
            # Estrai il filename dall'attachment path
            filename = os.path.basename(attachment_path)
            
            # Ottieni metadati dal MinIO
            if minio_client:
                try:
                    file_stat = minio_client.stat_object(MINIO_BUCKET_NAME, attachment_path)
                    # Cerca di determinare il nome originale dal filename
                    # Il formato è UUID + estensione, quindi usiamo il filename come originalName
                    original_name = filename
                    
                    attachments_metadata.append({
                        "filename": filename,
                        "originalName": original_name,
                        "size": file_stat.size
                    })
                except Exception as e:
                    logger.warning(f"Could not get metadata for attachment {attachment_path}: {e}")
                    # Aggiungi comunque l'attachment con informazioni limitate
                    attachments_metadata.append({
                        "filename": filename,
                        "originalName": filename,
                        "size": 0
                    })
            else:
                # Se MinIO non è disponibile, aggiungi solo il filename
                attachments_metadata.append({
                    "filename": filename,
                    "originalName": filename,
                    "size": 0
                })
        except Exception as e:
            logger.warning(f"Error processing attachment {attachment_path}: {e}")
    
    response_data = {
        "submissionId": submissionId,
        "assignmentId": submission_doc.get('assignmentId'),  # This should be 'assignmentId'
        "text": submission_doc.get('text'),
        "attachments": attachments_metadata,
        "submittedAt": _format_datetime_to_iso_z(submission_doc.get('submittedAt'))
    }
    
    logger.info(f"Successfully returning submission {submissionId} for peer review to student {student_serial_number}")
    return jsonify(response_data), 200


def download_attachment_for_review(token_info=None, submissionId=None, filename=None):
    """
    Download di un allegato per peer review.
    Accesso limitato agli studenti assegnati alla revisione.
    """
    logger.info(f"--- download_attachment_for_review CALLED with submissionId: {submissionId}, filename: {filename} ---")
    
    if not token_info:
        logger.error("Token information not found.")
        return jsonify({"error": "Unauthorized", "message": "Token information not found"}), 401
    
    if not all([submissionId, filename]):
        logger.error("Missing required parameters.")
        return jsonify({"error": "Bad Request", "message": "submissionId and filename are required"}), 400
    
    # Validazione formato ObjectId
    try:
        ObjectId(submissionId)
    except Exception:
        logger.error(f"Invalid submissionId format: {submissionId}")
        return jsonify({"error": "Bad Request", "message": "Invalid submissionId format"}), 400
    
    student_serial_number = token_info.get('user_id')
    if not student_serial_number:
        logger.error("Student serial number not found in token.")
        return jsonify({"error": "Unauthorized", "message": "Student serial number not found"}), 401
    
    # Verifica autorizzazione tramite servizio Review
    try:
        auth_header = flask_request.headers.get('Authorization')
        if not _check_peer_review_authorization(student_serial_number, submissionId, auth_header):
            return jsonify({"error": "Forbidden", "message": "You are not assigned to review this submission"}), 403
    except requests.exceptions.RequestException:
        return jsonify({"error": "Service Communication Error", "message": "Could not verify review authorization"}), 503
    except Exception as e:
        logger.error(f"Error checking authorization: {e}")
        return jsonify({"error": "Internal Server Error", "message": "Error verifying authorization"}), 500
    
    # Recupera la submission per ottenere il path completo dell'attachment
    db = get_db()
    if db is None:
        logger.error("Database connection failed.")
        return jsonify({"error": "Internal Server Error", "message": "Database connection failed"}), 500
    
    try:
        submission_doc = db.submissions.find_one({"_id": ObjectId(submissionId)})
        if not submission_doc:
            logger.error(f"Submission {submissionId} not found.")
            return jsonify({"error": "Not Found", "message": "Submission not found"}), 404
    except Exception as e:
        logger.error(f"Database error retrieving submission {submissionId}: {e}")
        return jsonify({"error": "Internal Server Error", "message": "Database error"}), 500
    
    # Trova il path completo dell'attachment
    attachment_path = None
    for attachment in submission_doc.get('attachments', []):
        if os.path.basename(attachment) == filename:
            attachment_path = attachment
            break
    
    if not attachment_path:
        logger.error(f"Attachment {filename} not found in submission {submissionId}")
        return jsonify({"error": "Not Found", "message": "Attachment not found"}), 404
    
    # Download del file da MinIO
    try:
        minio_client = get_minio_client()
        if not minio_client:
            logger.error("MinIO client not available.")
            return jsonify({"error": "Internal Server Error", "message": "Storage service unavailable"}), 500
        
        # Verifica che il file esista
        try:
            file_stat = minio_client.stat_object(MINIO_BUCKET_NAME, attachment_path)
        except Exception as e:
            logger.error(f"File not found in MinIO: {attachment_path}, error: {e}")
            return jsonify({"error": "Not Found", "message": "File not found"}), 404
        
        # Download del file
        try:
            file_data = minio_client.get_object(MINIO_BUCKET_NAME, attachment_path)
            file_content = file_data.read()
            file_data.close()
        except Exception as e:
            logger.error(f"Error downloading file from MinIO: {e}")
            return jsonify({"error": "Internal Server Error", "message": "Error downloading file"}), 500
        
        # Crea la risposta con il contenuto del file
        response = Response(
            file_content,
            mimetype='application/octet-stream',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Length': str(len(file_content)),
                'Content-Type': 'application/octet-stream'
            }
        )
        
        logger.info(f"File {filename} from submission {submissionId} downloaded successfully for peer review by student {student_serial_number}")
        return response
        
    except Exception as e:
        logger.error(f"Unexpected error in download_attachment_for_review: {e}")
        return jsonify({"error": "Internal Server Error", "message": "An unexpected error occurred"}), 500

