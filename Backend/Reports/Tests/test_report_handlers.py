import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from handlers import report

@pytest.fixture(scope="module")
def app_instance():
    app = Flask(__name__)
    app.config['TESTING'] = True
    yield app

@pytest.fixture(autouse=True)
def setup_mocks(monkeypatch):
    # Default: teacher autenticato
    monkeypatch.setattr(report, "get_auth_header", lambda req: "mocktoken")
    monkeypatch.setattr(report, "decode_token", lambda token: {"role": "teacher", "user_id": "1234567890"})

def test_get_teacher_reports_by_serial_success(app_instance):
    assignment_data = {
        "_id": "ASSIGN1",
        "title": "Test Assignment",
        "rubric": [{"criterion": "Qualità"}, {"criterion": "Completezza"}]
    }
    assignments_data = [assignment_data]
    submissions_data = [
        {"submissionId": "sub1", "studentSerialNumber": "0000000001"},
        {"submissionId": "sub2", "studentSerialNumber": "0000000002"}
    ]
    reviews_data = [
        {
            "submissionId": "sub1",
            "reviewerserialNumber": "0000000003",
            "evaluation": [
                {"criterion": "Qualità", "score": 80, "feedback": "Buono"},
                {"criterion": "Completezza", "score": 90, "feedback": "Ottimo"}
            ],
            "submittedAt": "2024-06-24T10:00:00Z"
        }
    ]

    with app_instance.test_request_context(headers={'Authorization': 'Bearer mocktoken'}):
        with patch("handlers.report.requests.get") as mock_get:
            mock_get.side_effect = [
                MagicMock(status_code=200, json=lambda: assignments_data),  # Assignments
                MagicMock(status_code=200, json=lambda: submissions_data),  # Submissions
                MagicMock(status_code=200, json=lambda: reviews_data),      # Reviews
            ]
            result, status = report.get_teacher_reports_by_serial("1234567890")
    
    assert status == 200
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["assignmentId"] == "ASSIGN1"
    assert result[0]["title"] == "Test Assignment"
    assert isinstance(result[0]["averageScores"], list)
    assert isinstance(result[0]["submissions"], list)
    assert "averageScores" in result[0]["submissions"][0]
    assert isinstance(result[0]["submissions"][0]["averageScores"], list)

def test_get_teacher_reports_by_serial_forbidden(app_instance, monkeypatch):
    # Simula teacher che cerca di accedere ai report di un altro teacher
    monkeypatch.setattr(report, "decode_token", lambda token: {"role": "teacher", "user_id": "0000000001"})
    with app_instance.test_request_context(headers={'Authorization': 'Bearer mocktoken'}):
        result, status = report.get_teacher_reports_by_serial("0000000002")
    assert status == 403
    assert "error" in result

def test_get_teacher_reports_by_serial_empty(app_instance):
    with app_instance.test_request_context(headers={'Authorization': 'Bearer mocktoken'}):
        with patch("handlers.report.requests.get") as mock_get:
            mock_get.return_value = MagicMock(status_code=200, json=lambda: [])
            result, status = report.get_teacher_reports_by_serial("1234567890")
    assert status == 200
    assert result == []

def test_get_student_report_success(app_instance, monkeypatch):
    # Simula studente autenticato
    monkeypatch.setattr(report, "decode_token", lambda token: {"role": "student", "user_id": "0000000001"})
    assignment_data = {
        "title": "Test Assignment",
        "rubric": [{"criterion": "Qualità"}, {"criterion": "Completezza"}]
    }
    submissions_data = [
        {"submissionId": "sub1", "assignmentId": "ASSIGN1", "studentSerialNumber": "0000000001"}
    ]
    reviews_data = [
        {
            "submissionId": "sub1",
            "reviewerserialNumber": "0000000003",
            "evaluation": [
                {"criterion": "Qualità", "score": 80, "feedback": "Buono"},
                {"criterion": "Completezza", "score": 90, "feedback": "Ottimo"}
            ],
            "submittedAt": "2024-06-24T10:00:00Z"
        }
    ]
    with app_instance.test_request_context(headers={'Authorization': 'Bearer mocktoken'}):
        with patch("handlers.report.requests.get") as mock_get:
            mock_get.side_effect = [
                MagicMock(status_code=200, json=lambda: assignment_data),   # Assignment
                MagicMock(status_code=200, json=lambda: submissions_data),  # Submissions/mine
                MagicMock(status_code=200, json=lambda: reviews_data),      # Reviews/assignment
            ]
            result, status = report.get_student_report("0000000001", "ASSIGN1")
    assert status == 200
    assert result["assignmentId"] == "ASSIGN1"
    assert result["submissionId"] == "sub1"
    assert isinstance(result["peerReviews"], list)
    assert result["peerReviews"][0]["reviewerSerialNumber"] == "0000000003"
    assert result["peerReviews"][0]["evaluation"][0]["criterion"] == "Qualità"
    assert result["averageScore"] == pytest.approx(85.0)

def test_get_student_report_forbidden(app_instance, monkeypatch):
    # Simula studente diverso da quello richiesto
    monkeypatch.setattr(report, "decode_token", lambda token: {"role": "student", "user_id": "0000000002"})
    with app_instance.test_request_context(headers={'Authorization': 'Bearer mocktoken'}):
        result, status = report.get_student_report("0000000001", "ASSIGN1")
    assert status == 403
    assert "error" in result

def test_get_student_reports_success(app_instance, monkeypatch):
    monkeypatch.setattr(report, "decode_token", lambda token: {"role": "student", "user_id": "0000000001"})
    assignments_data = [
        {"_id": "ASSIGN1"},
        {"_id": "ASSIGN2"}
    ]
    with app_instance.test_request_context(headers={'Authorization': 'Bearer mocktoken'}):
        with patch("handlers.report.requests.get") as mock_get, \
             patch("handlers.report.get_student_report") as mock_student_report:
            mock_get.return_value = MagicMock(status_code=200, json=lambda: assignments_data)
            mock_student_report.side_effect = [
                ({"assignmentId": "ASSIGN1", "title": "A1", "submissionId": "sub1", "peerReviews": [], "averageScore": 0}, 200),
                ({"assignmentId": "ASSIGN2", "title": "A2", "submissionId": "sub2", "peerReviews": [], "averageScore": 0}, 200)
            ]
            result, status = report.get_student_reports()
    assert status == 200
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["assignmentId"] == "ASSIGN1"

def test_get_student_reports_empty(app_instance, monkeypatch):
    monkeypatch.setattr(report, "decode_token", lambda token: {"role": "student", "user_id": "0000000001"})
    with app_instance.test_request_context(headers={'Authorization': 'Bearer mocktoken'}):
        with patch("handlers.report.requests.get") as mock_get:
            mock_get.return_value = MagicMock(status_code=200, json=lambda: [])
            result, status = report.get_student_reports()
    assert status == 200
    assert result == []

def test_missing_or_invalid_token(app_instance, monkeypatch):
    monkeypatch.setattr(report, "get_auth_header", lambda req: None)
    with app_instance.test_request_context():
        result, status = report.get_teacher_reports_by_serial("1234567890")
    assert status == 401
    assert "error" in result

def test_get_student_submission_reviews_success(app_instance, monkeypatch):
    # Simula studente autenticato
    monkeypatch.setattr(report, "decode_token", lambda token: {"role": "student", "user_id": "0000000001"})
    
    submission_data = {
        "submissionId": "sub1",
        "assignmentId": "ASSIGN1",
        "studentSerialNumber": "0000000001"
    }
    assignment_data = {
        "title": "Test Assignment"
    }
    reviews_data = [
        {
            "submissionId": "sub1",
            "reviewerserialNumber": "0000000003",
            "evaluation": [
                {"criterion": "Qualità", "score": 80, "feedback": "Buono"},
                {"criterion": "Completezza", "score": 90, "feedback": "Ottimo"}
            ],
            "submittedAt": "2024-06-24T10:00:00Z"
        }
    ]
    
    with app_instance.test_request_context(headers={'Authorization': 'Bearer mocktoken'}):
        with patch("handlers.report.requests.get") as mock_get:
            mock_get.side_effect = [
                MagicMock(status_code=200, json=lambda: submission_data),  # Submission
                MagicMock(status_code=200, json=lambda: assignment_data),  # Assignment
                MagicMock(status_code=200, json=lambda: reviews_data),     # Reviews
            ]
            result, status = report.get_student_submission_reviews("0000000001", "sub1")
    
    assert status == 200
    assert result["submissionId"] == "sub1"
    assert result["assignmentId"] == "ASSIGN1"
    assert len(result["reviews"]) == 1
    # Verifica che il reviewerSerialNumber non sia presente
    assert "reviewerSerialNumber" not in result["reviews"][0]
    assert "evaluation" in result["reviews"][0]
    assert "reviewedAt" in result["reviews"][0]
    assert result["averageScore"] == 85.0

def test_get_student_submission_reviews_forbidden(app_instance, monkeypatch):
    # Simula studente che cerca di accedere alle review di un altro studente
    monkeypatch.setattr(report, "decode_token", lambda token: {"role": "student", "user_id": "0000000002"})
    
    with app_instance.test_request_context(headers={'Authorization': 'Bearer mocktoken'}):
        result, status = report.get_student_submission_reviews("0000000001", "sub1")
    
    assert status == 403
    assert "error" in result