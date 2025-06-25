import sys
import os
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
import uuid # We'll still use uuid for MinIO object names, but not for primary IDs
import io

import pytest
from flask import Flask, jsonify 
from bson import ObjectId
from typing import Optional,List # Add this line

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from handlers import submission_handler 
from models import Submission

@pytest.fixture(scope="module")
def app_instance():
    app = Flask(__name__)
    app.config['TESTING'] = True 
    return app

@pytest.fixture
def client(app_instance):
    return app_instance.test_client()

@pytest.fixture(autouse=True)
def mock_dependencies(monkeypatch):
    mock_db_instance = MagicMock()
    mock_submissions_collection = MagicMock()
    mock_db_instance.submissions = mock_submissions_collection
    
    monkeypatch.setattr(submission_handler, "get_db", MagicMock(return_value=mock_db_instance))

    mock_minio = MagicMock()
    monkeypatch.setattr(submission_handler, "get_minio_client", MagicMock(return_value=mock_minio))
    monkeypatch.setattr(submission_handler, "MINIO_BUCKET_NAME", "test-bucket")

    mock_requests_get = MagicMock()
    monkeypatch.setattr(submission_handler.requests, "get", mock_requests_get)

    monkeypatch.setattr(submission_handler, "ASSIGNMENT_SERVICE_URL", 'http://fake-assignment-service')
    monkeypatch.setattr(submission_handler, "AUTHENTICATION_SERVICE_URL", 'http://fake-auth-service')
    monkeypatch.setattr(submission_handler, "REVIEW_SERVICE_URL", 'http://fake-review-service')  # Add this line
    
    return mock_submissions_collection, mock_minio, mock_requests_get


# --- Dati di Test Comuni ---
def get_valid_token_info(role="student", user_id="1234567890", name="DefaultNameFromToken", surname="DefaultSurnameFromToken"):
    return {"role": role, "user_id": user_id, "name": name, "surname": surname}

# MODIFIED HELPER: assignment_id is now a stringified ObjectId
def get_mock_assignment_details(deadline_offset_days=7, assignment_id: Optional[str] = None, teacherSerialNumber="teacher123"):
    deadline = datetime.now(timezone.utc) + timedelta(days=deadline_offset_days)
    # If assignment_id is not provided, generate a new ObjectId string
    current_assignment_id = assignment_id if assignment_id else str(ObjectId())
    return {
        # "id": current_assignment_id, # Assuming Assignment service might use 'id' or 'assignmentId'
        "assignmentId": current_assignment_id, # This is what Submission service uses for reference
        "title": "Test Assignment",
        "deadline": deadline.isoformat().replace('+00:00', 'Z'),
        "teacherSerialNumber": teacherSerialNumber
    }

def get_mock_user_profile(name="TestStudentName", surname="TestStudentSurname", serialNumber="1234567890", role="student"):
    return {"name": name, "surname": surname}


# --- Test per submit_assignment ---
def test_submit_assignment_success(app_instance, mock_dependencies):
    mock_submissions_collection, mock_minio, mock_requests_get = mock_dependencies
    # assignment_id_form is now a stringified ObjectId
    assignment_id_form = str(ObjectId()) 
    student_user_id = "student001"
    token_info_student = get_valid_token_info(user_id=student_user_id, name="TokenStudName", surname="TokenStudSurname")

    mock_insert_result = MagicMock()
    mock_insert_result.inserted_id = ObjectId() # This is for the submission's _id
    mock_submissions_collection.insert_one.return_value = mock_insert_result

    mock_requests_get.side_effect = [
        MagicMock(status_code=200, json=lambda: get_mock_user_profile(name="ActualStudName", surname="ActualStudSurname")),
        MagicMock(status_code=200, json=lambda: get_mock_assignment_details(assignment_id=assignment_id_form)) # Pass the ObjectId string
    ]

    with app_instance.test_request_context(
        method='POST', path='/submissions',
        headers={'Authorization': f'Bearer student_token_for_{student_user_id}'},
        content_type='multipart/form-data' 
    ):
        mock_form_data = {'assignmentId': assignment_id_form, 'text': 'My submission text'}
        
        mock_file_content = b"dummy file content for PDF"
        mock_file_storage = MagicMock(spec=io.BytesIO)
        mock_file_storage.filename = "test_file.pdf"
        mock_file_storage.stream = io.BytesIO(mock_file_content) 
        mock_file_storage.content_length = len(mock_file_content)
        mock_file_storage.content_type = "application/pdf"
        
        with patch.object(submission_handler.flask_request, 'form', MagicMock(get=lambda key, default=None: mock_form_data.get(key, default))), \
             patch.object(submission_handler.flask_request, 'files', MagicMock(getlist=MagicMock(return_value=[mock_file_storage]))), \
             patch.object(submission_handler.flask_request, 'headers', MagicMock(get=lambda key, default=None: {'Authorization': f'Bearer student_token_for_{student_user_id}'}.get(key, default))):

            response_tuple = submission_handler.submit_assignment(token_info=token_info_student)
            response_data = response_tuple[0].json
            status_code = response_tuple[1]

    assert status_code == 201
    assert response_data["assignmentId"] == assignment_id_form # Expecting ObjectId string
    assert ObjectId.is_valid(response_data["assignmentId"]) # Verify it's a valid ObjectId string format
    assert response_data["studentSerialNumber"] == student_user_id
    assert response_data["text"] == "My submission text"
    assert response_data["studentName"] == "ActualStudName" 
    assert response_data["studentSurname"] == "ActualStudSurname"
    assert response_data["submittedAt"].endswith("Z")
    assert ObjectId.is_valid(response_data["submissionId"]) # submissionId should also be ObjectId string
    
    attachments_list = response_data["attachments"]
    assert len(attachments_list) == 1
    uploaded_object_name = attachments_list[0]
    
    # MinIO path can still use UUID for uniqueness if desired, or be based on ObjectId strings
    # For this example, keeping UUID for the random part of the path for MinIO to avoid clashes if ObjectId strings are too similar in prefixes.
    # Or, you can base the MinIO random part on a new UUID.uuid4() string as before.
    # The important part is that `assignment_id_form` used in the path is now an ObjectId string.
    expected_path_prefix = f"submissions/{student_user_id}/{assignment_id_form}/" 
    assert uploaded_object_name.startswith(expected_path_prefix)
    assert uploaded_object_name.endswith(".pdf") 
    
    mock_minio.put_object.assert_called_once()
    mock_submissions_collection.insert_one.assert_called_once()


def test_submit_assignment_after_deadline(app_instance, mock_dependencies):
    mock_submissions_collection, mock_minio, mock_requests_get = mock_dependencies
    # assignment_id_form is now a stringified ObjectId
    assignment_id_form = str(ObjectId()) 
    student_user_id = "student002"
    token_info_student = get_valid_token_info(user_id=student_user_id)

    mock_requests_get.side_effect = [
        MagicMock(status_code=200, json=lambda: get_mock_user_profile()),
        MagicMock(status_code=200, json=lambda: get_mock_assignment_details(deadline_offset_days=-1, assignment_id=assignment_id_form))
    ]

    with app_instance.test_request_context(
        method='POST', path='/submissions',
        headers={'Authorization': f'Bearer student_token_for_{student_user_id}'},
        content_type='multipart/form-data'
    ):
        mock_form_data = {'assignmentId': assignment_id_form, 'text': 'Late submission'}
        with patch.object(submission_handler.flask_request, 'form', MagicMock(get=lambda key, default=None: mock_form_data.get(key, default))), \
             patch.object(submission_handler.flask_request, 'files', MagicMock(getlist=MagicMock(return_value=[]))), \
             patch.object(submission_handler.flask_request, 'headers', MagicMock(get=lambda key, default=None: {'Authorization': f'Bearer student_token_for_{student_user_id}'}.get(key, default))):
            
            response_obj, status_code = submission_handler.submit_assignment(token_info=token_info_student)

    assert status_code == 403
    assert "deadline for this assignment has passed" in response_obj.json["message"].lower()


# --- Test per get_my_submissions ---
def test_get_my_submissions_success(app_instance, mock_dependencies):
    mock_submissions_collection, _, _ = mock_dependencies
    student_id = "student123"
    token_info = get_valid_token_info(user_id=student_id, name="MyName", surname="MySurname")

    submission_obj_id = ObjectId() 
    assignment_obj_id_str = str(ObjectId()) # assignmentId is now an ObjectId string
    db_submission_doc_for_mock = {
        "_id": submission_obj_id,       
        "assignmentId": assignment_obj_id_str, 
        "studentSerialNumber": student_id, 
        "text": "My work", "attachments": [],
        "submittedAt": datetime.now(timezone.utc),
        "studentName": "MyName", "studentSurname": "MySurname"
    }
    mock_submissions_collection.find.return_value = [db_submission_doc_for_mock.copy()]

    with app_instance.app_context():
        response_obj, status_code = submission_handler.get_my_submissions(token_info=token_info)
        response_data = response_obj.json

    assert status_code == 200
    assert len(response_data) == 1
    submission_in_response = response_data[0]
    assert submission_in_response["studentSerialNumber"] == student_id
    assert submission_in_response["submissionId"] == str(submission_obj_id) 
    assert submission_in_response["assignmentId"] == assignment_obj_id_str
    assert ObjectId.is_valid(submission_in_response["assignmentId"])
    assert submission_in_response["submittedAt"].endswith("Z") 
    mock_submissions_collection.find.assert_called_once_with({"studentSerialNumber": student_id})


# --- Test per get_all_submissions_for_assignment ---
def test_get_all_submissions_for_assignment_success_teacher(app_instance, mock_dependencies):
    mock_submissions_collection, _, mock_requests_get = mock_dependencies
    # assignment_id_param is now a stringified ObjectId
    assignment_id_param = str(ObjectId()) 
    teacher_id = "teacher123"
    token_info_teacher = get_valid_token_info(role="teacher", user_id=teacher_id)

    mock_requests_get.return_value = MagicMock(
        status_code=200, 
        json=lambda: get_mock_assignment_details(assignment_id=assignment_id_param, teacherSerialNumber=teacher_id)
    )

    original_submission_object_id = ObjectId()
    db_submission_doc = {
        "_id": original_submission_object_id, 
        "assignmentId": assignment_id_param, 
        "studentSerialNumber": "student001", "text": "Work 1",
        "submittedAt": datetime.now(timezone.utc),
        "studentName": "S1Name", "studentSurname": "S1Surname"
    }
    mock_submissions_collection.find.return_value = [db_submission_doc.copy()]

    teacher_auth_header_val = f'Bearer teacher_token_for_{teacher_id}'
    with app_instance.test_request_context(
        path=f'/submissions/assignment/{assignment_id_param}',
        headers={'Authorization': teacher_auth_header_val}
    ):
        response_obj, status_code = submission_handler.get_all_submissions_for_assignment(
            token_info=token_info_teacher, 
            assignmentId=assignment_id_param
        )
        response_data = response_obj.json

    assert status_code == 200
    assert len(response_data) == 1
    submission_in_response = response_data[0]
    assert submission_in_response["submissionId"] == str(original_submission_object_id)
    assert submission_in_response["assignmentId"] == assignment_id_param
    assert ObjectId.is_valid(submission_in_response["assignmentId"])
    assert submission_in_response["studentSerialNumber"] == "student001"
    assert submission_in_response["studentName"] == "S1Name"
    assert submission_in_response["studentSurname"] == "S1Surname"
    assert submission_in_response["submittedAt"].endswith("Z")
    
    mock_submissions_collection.find.assert_called_once_with({"assignmentId": assignment_id_param})
    mock_requests_get.assert_called_once_with(
        f"http://fake-assignment-service/assignments/{assignment_id_param}", 
        headers={'Authorization': teacher_auth_header_val}, 
        timeout=10
    )

def test_get_all_submissions_for_assignment_forbidden_student(app_instance, mock_dependencies):
    _, _, mock_requests_get = mock_dependencies
    # assignment_id_param is now a stringified ObjectId
    assignment_id_param = str(ObjectId()) 
    student_id = "student123"
    token_info_student = get_valid_token_info(role="student", user_id=student_id)

    with app_instance.app_context():
        response_obj, status_code = submission_handler.get_all_submissions_for_assignment(
            token_info=token_info_student, 
            assignmentId=assignment_id_param
        )

    assert status_code == 403 
    assert "User does not have sufficient privileges" in response_obj.json["message"]
    mock_requests_get.assert_not_called()


# --- Test per get_student_submission_for_assignment (endpoint /submissions/{submissionId}) ---

def test_get_submission_by_id_success_owner_student(app_instance, mock_dependencies):
    mock_submissions_collection, _, mock_requests_get = mock_dependencies
    submission_id_obj = ObjectId()
    submission_id_str = str(submission_id_obj)
    # assignment_id_from_sub is now a stringified ObjectId
    assignment_id_from_sub = str(ObjectId()) 
    student_id = "student007"
    token_info = get_valid_token_info(role="student", user_id=student_id)

    mock_submission_data_db = {
        "_id": submission_id_obj, 
        "assignmentId": assignment_id_from_sub, 
        "studentSerialNumber": student_id, 
        "text": "My specific work",
        "attachments": ["path/to/file.txt"], 
        "submittedAt": datetime.now(timezone.utc),
        "studentName": "James", 
        "studentSurname": "Bond"
    }
    mock_submissions_collection.find_one.return_value = mock_submission_data_db
    
    with app_instance.app_context():
        response_obj, status_code = submission_handler.get_student_submission_for_assignment(
            token_info=token_info, submissionId=submission_id_str
        )
        response_data = response_obj.json

    assert status_code == 200
    assert response_data["submissionId"] == submission_id_str
    assert response_data["studentSerialNumber"] == student_id
    assert response_data["assignmentId"] == assignment_id_from_sub
    assert ObjectId.is_valid(response_data["assignmentId"])
    assert response_data["text"] == "My specific work"
    assert response_data["submittedAt"].endswith("Z")
    
    mock_submissions_collection.find_one.assert_called_once_with({"_id": submission_id_obj})
    mock_requests_get.assert_not_called()

def test_get_submission_by_id_success_teacher_of_assignment(app_instance, mock_dependencies):
    mock_submissions_collection, _, mock_requests_get = mock_dependencies
    submission_id_obj = ObjectId()
    submission_id_str = str(submission_id_obj)
    # assignment_id_from_sub is now a stringified ObjectId
    assignment_id_from_sub = str(ObjectId()) 
    teacher_id = "teacher001"
    student_submitter_id = "student008"
    token_info_teacher = get_valid_token_info(role="teacher", user_id=teacher_id)
    
    mock_submission_data_db = {
        "_id": submission_id_obj, 
        "assignmentId": assignment_id_from_sub, 
        "studentSerialNumber": student_submitter_id, 
        "text": "Student work for teacher",
        "submittedAt": datetime.now(timezone.utc),
        "studentName": "S8", "studentSurname": "U8"
    }
    mock_submissions_collection.find_one.return_value = mock_submission_data_db

    mock_requests_get.return_value = MagicMock(
        status_code=200, 
        json=lambda: get_mock_assignment_details(assignment_id=assignment_id_from_sub, teacherSerialNumber=teacher_id)
    )
    
    teacher_bearer_token = f'Bearer teacher_token_for_{teacher_id}'
    with app_instance.test_request_context(headers={'Authorization': teacher_bearer_token}):
        response_obj, status_code = submission_handler.get_student_submission_for_assignment(
            token_info=token_info_teacher, submissionId=submission_id_str
        )
        response_data = response_obj.json

    assert status_code == 200
    assert response_data["submissionId"] == submission_id_str
    assert response_data["studentSerialNumber"] == student_submitter_id
    assert response_data["assignmentId"] == assignment_id_from_sub
    assert ObjectId.is_valid(response_data["assignmentId"])
    
    mock_submissions_collection.find_one.assert_called_once_with({"_id": submission_id_obj})
    mock_requests_get.assert_called_once_with(
        f"http://fake-assignment-service/assignments/{assignment_id_from_sub}", 
        headers={'Authorization': teacher_bearer_token}, timeout=10
    )

def test_get_submission_by_id_forbidden_other_student(app_instance, mock_dependencies):
    mock_submissions_collection, _, mock_requests_get = mock_dependencies
    submission_id_obj = ObjectId()
    submission_id_str = str(submission_id_obj)
    # assignment_id_from_sub is now a stringified ObjectId
    assignment_id_from_sub = str(ObjectId()) 
    owner_student_id = "student009"      
    requester_student_id = "student010" 
    token_info_requester = get_valid_token_info(role="student", user_id=requester_student_id)

    mock_submission_data_db = {
        "_id": submission_id_obj, 
        "assignmentId": assignment_id_from_sub, 
        "studentSerialNumber": owner_student_id, 
        "text": "Secret work",
        "submittedAt": datetime.now(timezone.utc)
    }
    mock_submissions_collection.find_one.return_value = mock_submission_data_db

    with app_instance.app_context():
        response_obj, status_code = submission_handler.get_student_submission_for_assignment(
            token_info=token_info_requester, submissionId=submission_id_str
        )

    assert status_code == 403 
    assert "Not authorized to access this submission" in response_obj.json["message"]
    mock_requests_get.assert_not_called()

def test_get_submission_by_id_not_found_in_db(app_instance, mock_dependencies):
    mock_submissions_collection, _, _ = mock_dependencies
    submission_id_str = str(ObjectId())
    token_info = get_valid_token_info(role="student", user_id="any_student")

    mock_submissions_collection.find_one.return_value = None

    with app_instance.app_context():
        response_obj, status_code = submission_handler.get_student_submission_for_assignment(
            token_info=token_info, submissionId=submission_id_str
        )

    assert status_code == 404
    assert "Submission not found" in response_obj.json["message"]

def test_get_submission_by_id_teacher_not_owner_of_assignment(app_instance, mock_dependencies):
    mock_submissions_collection, _, mock_requests_get = mock_dependencies
    submission_id_obj = ObjectId()
    submission_id_str = str(submission_id_obj)
    # assignment_id_from_sub is now a stringified ObjectId
    assignment_id_from_sub = str(ObjectId()) 
    
    actual_assignment_teacher_id = "teacherXYZ"
    requesting_teacher_id = "teacherABC"    
    token_info_requester = get_valid_token_info(role="teacher", user_id=requesting_teacher_id)

    mock_submission_data_db = {
        "_id": submission_id_obj, 
        "assignmentId": assignment_id_from_sub, 
        "studentSerialNumber": "student123", 
        "text": "Some work",
        "submittedAt": datetime.now(timezone.utc)
    }
    mock_submissions_collection.find_one.return_value = mock_submission_data_db

    mock_requests_get.return_value = MagicMock(
        status_code=200, 
        json=lambda: get_mock_assignment_details(assignment_id=assignment_id_from_sub, teacherSerialNumber=actual_assignment_teacher_id)
    )
    
    requester_teacher_token = f'Bearer teacher_token_for_{requesting_teacher_id}'
    with app_instance.test_request_context(headers={'Authorization': requester_teacher_token}):
        response_obj, status_code = submission_handler.get_student_submission_for_assignment(
            token_info=token_info_requester, submissionId=submission_id_str
        )

    assert status_code == 403
    # Message might vary slightly based on exact logic, but this is the expected outcome from handler
    assert "Not authorized to access this submission" in response_obj.json["message"] 
    mock_requests_get.assert_called_once()


def test_get_submission_by_id_assignment_id_missing_in_submission_doc_for_teacher_auth(app_instance, mock_dependencies):
    mock_submissions_collection, _, mock_requests_get = mock_dependencies
    submission_id_obj = ObjectId()
    submission_id_str = str(submission_id_obj)
    teacher_id = "teacher001"
    token_info_teacher = get_valid_token_info(role="teacher", user_id=teacher_id)

    mock_submission_data_db_incomplete = {
        "_id": submission_id_obj,
        # "assignmentId": "missing_assignment_id", # CAMPO MANCANTE
        "studentSerialNumber": "student008",
        "text": "Work with missing assignmentId field",
        "submittedAt": datetime.now(timezone.utc)
    }
    mock_submissions_collection.find_one.return_value = mock_submission_data_db_incomplete

    teacher_bearer_token = f'Bearer teacher_token_for_{teacher_id}'
    with app_instance.test_request_context(headers={'Authorization': teacher_bearer_token}):
        response_obj, status_code = submission_handler.get_student_submission_for_assignment(
            token_info=token_info_teacher, submissionId=submission_id_str
        )

    assert status_code == 500 
    assert "Submission data incomplete (missing assignmentId)" in response_obj.json["message"]
    mock_requests_get.assert_not_called()


# --- Test per get_submission_for_review ---
def test_get_submission_for_review_success(app_instance, mock_dependencies):
    mock_submissions_collection, mock_minio, mock_requests_get = mock_dependencies
    submission_id_obj = ObjectId()
    submission_id_str = str(submission_id_obj)
    assignment_id_str = str(ObjectId())
    student_id = "reviewer123"
    token_info = get_valid_token_info(role="student", user_id=student_id)

    # Mock submission data - FIX: use 'assignmentId' not 'assignment_id'
    mock_submission_data = {
        "_id": submission_id_obj,
        "assignmentId": assignment_id_str,  # Changed from assignment_id
        "studentSerialNumber": "original_student456",
        "text": "This is the submission text",
        "attachments": ["submissions/original_student456/assignment123/file1.pdf"],
        "submittedAt": datetime.now(timezone.utc),
        "studentName": "John",
        "studentSurname": "Doe"
    }
    mock_submissions_collection.find_one.return_value = mock_submission_data

    # Mock MinIO stat_object for attachment metadata
    mock_stat_result = MagicMock()
    mock_stat_result.size = 1024
    mock_minio.stat_object.return_value = mock_stat_result

    # Mock Review service authorization response
    mock_review_response = MagicMock()
    mock_review_response.status_code = 200
    mock_review_response.json.return_value = [
        {
            "submissionId": submission_id_str,
            "assignmentId": assignment_id_str,
            "reviewerSerialNumber": student_id
        }
    ]
    mock_requests_get.return_value = mock_review_response

    # Add request context with Authorization header
    with app_instance.test_request_context(
        path=f'/submissions/for-review/{submission_id_str}',
        headers={'Authorization': f'Bearer token_for_{student_id}'}
    ):
        response_obj, status_code = submission_handler.get_submission_for_review(
            token_info=token_info, submissionId=submission_id_str
        )
        response_data = response_obj.json

    assert status_code == 200
    assert response_data["submissionId"] == submission_id_str
    assert response_data["assignmentId"] == assignment_id_str
    assert "studentSerialNumber" not in response_data  # Should be anonymous
    assert response_data["text"] == "This is the submission text"
    assert len(response_data["attachments"]) == 1
    assert response_data["attachments"][0]["filename"] == "file1.pdf"

def test_download_attachment_for_review_success(app_instance, mock_dependencies):
    mock_submissions_collection, mock_minio, mock_requests_get = mock_dependencies
    submission_id_obj = ObjectId()
    submission_id_str = str(submission_id_obj)
    assignment_id_str = str(ObjectId())
    student_id = "reviewer123"
    filename = "file1.pdf"  # The filename we want to download
    token_info = get_valid_token_info(role="student", user_id=student_id)

    # Mock submission data - FIX: make sure filename matches exactly
    attachment_path = f"submissions/original_student456/{assignment_id_str}/{filename}"  # Use exact filename
    mock_submission_data = {
        "_id": submission_id_obj,
        "assignmentId": assignment_id_str,
        "studentSerialNumber": "original_student456",
        "attachments": [attachment_path]  # Path contains exact filename
    }
    mock_submissions_collection.find_one.return_value = mock_submission_data

    # Mock Review service authorization
    mock_review_response = MagicMock()
    mock_review_response.status_code = 200
    mock_review_response.json.return_value = [
        {"submissionId": submission_id_str, "assignmentId": assignment_id_str, "reviewerSerialNumber": student_id}
    ]
    mock_requests_get.return_value = mock_review_response

    # Mock MinIO stat_object and get_object
    mock_stat_result = MagicMock()
    mock_stat_result.size = 1024
    mock_minio.stat_object.return_value = mock_stat_result
    
    mock_file_data = MagicMock()
    mock_file_data.read.return_value = b"PDF file content"
    mock_minio.get_object.return_value = mock_file_data

    # Add request context with Authorization header
    with app_instance.test_request_context(
        path=f'/submissions/for-review/{submission_id_str}/download/{filename}',
        headers={'Authorization': f'Bearer token_for_{student_id}'}
    ):
        # FIX: Don't unpack - download_attachment_for_review returns Response directly
        response_obj = submission_handler.download_attachment_for_review(
            token_info=token_info, submissionId=submission_id_str, filename=filename
        )

    # FIX: Check response object directly
    assert response_obj.status_code == 200
    assert response_obj.data == b"PDF file content"
    assert response_obj.headers['Content-Disposition'] == f'attachment; filename="{filename}"'
    # FIX: Use the correct bucket name that was set in the test setup
    mock_minio.get_object.assert_called_once_with("test-bucket", attachment_path)