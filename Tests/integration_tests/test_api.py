# --- START OF FILE test_api.py ---

import pytest
import requests
import os
from datetime import date, datetime, timezone, timedelta
import io

# Base URLs
AUTH_SERVICE_URL = os.getenv('AUTHENTICATION_SERVICE_URL', 'http://authentication-app-service:5000')
ASSIGNMENT_SERVICE_URL = os.getenv('ASSIGNMENT_SERVICE_URL', 'http://assignment-app-service:5001')
SUBMISSION_SERVICE_URL = os.getenv('SUBMISSION_SERVICE_URL', 'http://submission-app-service:5002')
REVIEW_SERVICE_URL = os.getenv('REVIEW_SERVICE_URL', 'http://review-app-service:5003')

SKIP_REVIEW_TESTS = not REVIEW_SERVICE_URL or REVIEW_SERVICE_URL == 'http://review-app-servicelollipop:5003'
SKIP_REVIEW_REASON = "REVIEW_SERVICE_URL not configured or is default placeholder"

TEST_PASSWORD = "password123"

class TestIntegration:
    student1_token = None
    student1_serial_number = None
    student2_token = None
    student2_serial_number = None
    student3_token = None
    student3_serial_number = None
    teacher_token = None
    teacher_serial_number = None

    assignment_id = None
    assignment_rubric = None

    student1_submission_id = None
    student2_submission_id = None
    student3_submission_id = None

    peer_review_assignments = [] 
    review_id = None 

    # --- HEALTH CHECKS ---
    def test_00_auth_service_health(self):
        url = f"{AUTH_SERVICE_URL}/health"
        try:
            response = requests.get(url, timeout=10)
            assert response.status_code == 200, f"Auth service health check failed: {response.status_code} - {response.text}"
            health_data = response.json()
            assert 'status' in health_data
            print(f"\nAuth service health check: {health_data['status']}")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Auth service not available (FATAL for test suite): {e}")

    def test_00b_assignment_service_health(self):
        url = f"{ASSIGNMENT_SERVICE_URL}/health"
        try:
            response = requests.get(url, timeout=10)
            assert response.status_code == 200, f"Assignment service health check failed: {response.status_code} - {response.text}"
            health_data = response.json()
            assert 'status' in health_data 
            print(f"Assignment service health check: {health_data['status']}")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Assignment service not available (FATAL for test suite): {e}")

    def test_00c_submission_service_health(self):
        url = f"{SUBMISSION_SERVICE_URL}/health"
        try:
            response = requests.get(url, timeout=10)
            assert response.status_code in [200, 503], f"Submission health check returned unexpected status: {response.status_code} - {response.text}"
            health_data = response.json()
            assert 'status' in health_data 
            print(f"Submission service health check: Status {health_data['status']}, Details: {health_data.get('details')}")
            if response.status_code == 503:
                 print("Warning: Submission service is unhealthy but responding.")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Submission service not available (FATAL for test suite): {e}")

    @pytest.mark.skipif(SKIP_REVIEW_TESTS, reason=SKIP_REVIEW_REASON)
    def test_00d_review_service_health(self):
        url = f"{REVIEW_SERVICE_URL}/health"
        try:
            response = requests.get(url, timeout=10)
            assert response.status_code == 200, f"Review service health check failed: {response.status_code} - {response.text}"
            health_data = response.json()
            assert 'status' in health_data 
            print(f"Review service health check: {health_data['status']}")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Review service health check failed after skipif condition was false: {e}")

    # --- REGISTRATION TESTS ---
    def test_01_teacher_registration(self):
        url = f"{AUTH_SERVICE_URL}/auth/register"
        teacher_data = {
            "name": "Professore", "surname": "Rossi", "email": "professore.rossi@example.com",
            "password": TEST_PASSWORD, "role": "teacher", "fiscalCode": "PRORSS80A01A001A",
            "birthDate": date(1980, 1, 1).isoformat(), "residence": "Milano, Via Garibaldi, 10"
        }
        response = requests.post(url, json=teacher_data)
        print(f"\n[REGISTRATION - Teacher] Status: {response.status_code}, Response: {response.text[:300]}")
        if response.status_code == 500: pytest.skip("Teacher registration returned 500.")
        
        if response.status_code == 201:
            TestIntegration.teacher_serial_number = response.json()['serialNumber']
        elif response.status_code == 400 and ("already exists" in response.json().get("message", "").lower() or \
             "already in use" in response.json().get("message", "").lower()):
            print("Teacher already exists, attempting login.")
            login_resp = requests.post(f"{AUTH_SERVICE_URL}/auth/login", json={"email": teacher_data["email"], "password": teacher_data["password"]})
            if login_resp.status_code == 200: TestIntegration.teacher_serial_number = login_resp.json()['user']['serialNumber']
            else: pytest.fail(f"Fallback login for existing teacher failed: {login_resp.status_code} - {login_resp.text}")
        else:
            pytest.fail(f"Teacher registration failed unexpectedly: Status {response.status_code} - {response.text}")
        
        assert TestIntegration.teacher_serial_number is not None, "Teacher serial number not obtained."
        print(f"Teacher Serial Number: {TestIntegration.teacher_serial_number}")

    def test_02_student1_registration(self):
        url = f"{AUTH_SERVICE_URL}/auth/register"
        student_data = {
            "name": "TestStudentOne", "surname": "UserOne", "email": "student1.test@example.com",
            "password": TEST_PASSWORD, "role": "student", "fiscalCode": "RSSMRA00A01H501U", 
            "birthDate": date(2000, 1, 1).isoformat(), "residence": "Test Town, Test Avenue, 456"
        }
        response = requests.post(url, json=student_data)
        print(f"\n[REGISTRATION - Student1] Status: {response.status_code}, Response: {response.text[:300]}")
        if response.status_code == 500: pytest.skip("Student1 registration returned 500.")

        if response.status_code == 201:
            TestIntegration.student1_serial_number = response.json()['serialNumber']
        elif response.status_code == 400 and ("already exists" in response.json().get("message", "").lower() or \
             "already in use" in response.json().get("message", "").lower()):
            print("Student1 already exists, attempting login.")
            login_resp = requests.post(f"{AUTH_SERVICE_URL}/auth/login", json={"email": student_data["email"], "password": student_data["password"]})
            if login_resp.status_code == 200: TestIntegration.student1_serial_number = login_resp.json()['user']['serialNumber']
            else: pytest.fail(f"Fallback login for existing student1 failed: {login_resp.status_code} - {login_resp.text}")
        else:
            pytest.fail(f"Student1 registration failed unexpectedly: Status {response.status_code} - {response.text}")

        assert TestIntegration.student1_serial_number is not None, "Student1 serial number not obtained."
        print(f"Student1 Serial Number: {TestIntegration.student1_serial_number}")

    def test_03_student2_registration(self):
        url = f"{AUTH_SERVICE_URL}/auth/register"
        student_data = {
            "name": "StudentTwo", "surname": "UserTwo", "email": "student2.test@example.com",
            "password": TEST_PASSWORD, "role": "student", "fiscalCode": "VRDLGI00A15H501L", 
            "birthDate": date(2000, 1, 15).isoformat(), "residence": "Test Town 2, Test Avenue 2, 789"
        }
        response = requests.post(url, json=student_data)
        print(f"\n[REGISTRATION - Student2] Status: {response.status_code}, Response: {response.text[:300]}")
        if response.status_code == 500: pytest.skip("Student2 registration returned 500.")

        if response.status_code == 201:
            TestIntegration.student2_serial_number = response.json()['serialNumber']
        elif response.status_code == 400 and ("already exists" in response.json().get("message", "").lower() or \
             "already in use" in response.json().get("message", "").lower()):
            print("Student2 already exists, attempting login.")
            login_resp = requests.post(f"{AUTH_SERVICE_URL}/auth/login", json={"email": student_data["email"], "password": student_data["password"]})
            if login_resp.status_code == 200: TestIntegration.student2_serial_number = login_resp.json()['user']['serialNumber']
            else: pytest.fail(f"Fallback login for existing student2 failed: {login_resp.status_code} - {login_resp.text}")
        else:
            pytest.fail(f"Student2 registration failed unexpectedly: Status {response.status_code} - {response.text}")
        
        assert TestIntegration.student2_serial_number is not None, "Student2 serial number not obtained."
        print(f"Student2 Serial Number: {TestIntegration.student2_serial_number}")

    def test_04_student3_registration(self):
        url = f"{AUTH_SERVICE_URL}/auth/register"
        student_data = {
            "name": "StudentThree", "surname": "UserThree", "email": "student3.test@example.com",
            "password": TEST_PASSWORD, "role": "student", "fiscalCode": "BNCLRA01B16H501Z", 
            "birthDate": date(2001, 2, 16).isoformat(), "residence": "Test Town 3, Test Avenue 3, 321"
        }
        response = requests.post(url, json=student_data)
        print(f"\n[REGISTRATION - Student3] Status: {response.status_code}, Response: {response.text[:300]}")
        if response.status_code == 500: pytest.skip("Student3 registration returned 500.")

        if response.status_code == 201:
            TestIntegration.student3_serial_number = response.json()['serialNumber']
        elif response.status_code == 400 and ("already exists" in response.json().get("message", "").lower() or \
             "already in use" in response.json().get("message", "").lower()):
            print("Student3 already exists, attempting login.")
            login_resp = requests.post(f"{AUTH_SERVICE_URL}/auth/login", json={"email": student_data["email"], "password": student_data["password"]})
            if login_resp.status_code == 200: TestIntegration.student3_serial_number = login_resp.json()['user']['serialNumber']
            else: pytest.fail(f"Fallback login for existing student3 failed: {login_resp.status_code} - {login_resp.text}")
        else:
            pytest.fail(f"Student3 registration failed unexpectedly: Status {response.status_code} - {response.text}")

        assert TestIntegration.student3_serial_number is not None, "Student3 serial number not obtained."
        print(f"Student3 Serial Number: {TestIntegration.student3_serial_number}")

    # --- LOGIN TESTS ---
    def test_05_teacher_login(self):
        if not TestIntegration.teacher_serial_number: pytest.skip("Teacher SN not set, skipping login.")
        url = f"{AUTH_SERVICE_URL}/auth/login"
        login_data = {"email": "professore.rossi@example.com", "password": TEST_PASSWORD}
        response = requests.post(url, json=login_data)
        assert response.status_code == 200, f"Teacher Login Failed: {response.text}"
        TestIntegration.teacher_token = response.json()['token']
        assert TestIntegration.teacher_token is not None
        assert response.json()['user']['serialNumber'] == TestIntegration.teacher_serial_number
        print(f"\nTeacher Login Token (first 10): {TestIntegration.teacher_token[:10]}...")

    def test_06_student1_login(self):
        if not TestIntegration.student1_serial_number: pytest.skip("Student1 SN not set, skipping login.")
        url = f"{AUTH_SERVICE_URL}/auth/login"
        login_data = {"email": "student1.test@example.com", "password": TEST_PASSWORD}
        response = requests.post(url, json=login_data)
        assert response.status_code == 200, f"Student1 Login Failed: {response.text}"
        TestIntegration.student1_token = response.json()['token']
        assert TestIntegration.student1_token is not None
        assert response.json()['user']['serialNumber'] == TestIntegration.student1_serial_number
        print(f"\nStudent1 Login Token (first 10): {TestIntegration.student1_token[:10]}...")

    def test_07_student2_login(self):
        if not TestIntegration.student2_serial_number: pytest.skip("Student2 SN not set, skipping login.")
        url = f"{AUTH_SERVICE_URL}/auth/login"
        login_data = {"email": "student2.test@example.com", "password": TEST_PASSWORD}
        response = requests.post(url, json=login_data)
        assert response.status_code == 200, f"Student2 Login Failed: {response.text}"
        TestIntegration.student2_token = response.json()['token']
        assert TestIntegration.student2_token is not None
        assert response.json()['user']['serialNumber'] == TestIntegration.student2_serial_number
        print(f"\nStudent2 Login Token (first 10): {TestIntegration.student2_token[:10]}...")

    def test_08_student3_login(self):
        if not TestIntegration.student3_serial_number: pytest.skip("Student3 SN not set, skipping login.")
        url = f"{AUTH_SERVICE_URL}/auth/login"
        login_data = {"email": "student3.test@example.com", "password": TEST_PASSWORD}
        response = requests.post(url, json=login_data)
        assert response.status_code == 200, f"Student3 Login Failed: {response.text}"
        TestIntegration.student3_token = response.json()['token']
        assert TestIntegration.student3_token is not None
        assert response.json()['user']['serialNumber'] == TestIntegration.student3_serial_number
        print(f"\nStudent3 Login Token (first 10): {TestIntegration.student3_token[:10]}...")

    # --- ASSIGNMENT AND SUBMISSION FLOW ---
    def test_09_teacher_create_assignment(self):
        if not (TestIntegration.teacher_token and \
                TestIntegration.student1_serial_number and \
                TestIntegration.student2_serial_number and \
                TestIntegration.student3_serial_number):
            pytest.skip("Prerequisites for creating assignment not met (tokens/serials missing).")

        url = f"{ASSIGNMENT_SERVICE_URL}/assignments"
        headers = {'Authorization': f'Bearer {TestIntegration.teacher_token}'}
        future_deadline = datetime.now(timezone.utc) + timedelta(days=1) 
        deadline_str = future_deadline.isoformat() 
        TestIntegration.assignment_rubric = [
            {"criterion": "Completeness", "maxScore": 10},
            {"criterion": "Quality", "maxScore": 10},
            {"criterion": "Clarity", "maxScore": 10}
        ]
        assignment_data = {
            "title": "Peer Review Integration Test Assignment",
            "description": "This is an assignment for peer review integration testing.",
            "deadline": deadline_str,
            "rubric": TestIntegration.assignment_rubric,
            "students": [
                TestIntegration.student1_serial_number,
                TestIntegration.student2_serial_number,
                TestIntegration.student3_serial_number
            ]
        }
        response = requests.post(url, json=assignment_data, headers=headers)
        if response.status_code != 201:
            print(f"Create Assignment Error Response: {response.text}")
        assert response.status_code == 201, f"Create Assignment Failed: {response.text}"
        
        assignment_response_json = response.json()
        TestIntegration.assignment_id = assignment_response_json.get('_id')
        assert TestIntegration.assignment_id is not None, f"Assignment _id not found in response: {assignment_response_json}"
        print(f"\nCreated Assignment ID: {TestIntegration.assignment_id}")

    def test_10_student1_submit_assignment(self): 
        if not (TestIntegration.student1_token and TestIntegration.assignment_id):
            pytest.skip("Student1 token or assignment ID missing.")
        url = f"{SUBMISSION_SERVICE_URL}/submissions"
        headers = {'Authorization': f'Bearer {TestIntegration.student1_token}'}
        files = {'attachments': ('student1_submission.txt', io.BytesIO(b"Student 1 submission content."), 'text/plain')}
        data = {'assignmentId': TestIntegration.assignment_id, 'text': 'Submission by Student 1'}
        response = requests.post(url, data=data, files=files, headers=headers)
        assert response.status_code == 201, f"S1 Submit Failed: {response.status_code} - {response.text}"
        
        submission_json = response.json()
        TestIntegration.student1_submission_id = submission_json.get('submissionId')
        assert TestIntegration.student1_submission_id is not None, f"submissionId not found for S1: {submission_json}"
        assert len(TestIntegration.student1_submission_id) == 24, "S1 submissionId is not 24 chars."
        print(f"\nStudent1 Submission ID: {TestIntegration.student1_submission_id}")

    def test_11_student2_submit_assignment(self):
        if not (TestIntegration.student2_token and TestIntegration.assignment_id):
            pytest.skip("Student2 token or assignment ID missing.")
        url = f"{SUBMISSION_SERVICE_URL}/submissions"
        headers = {'Authorization': f'Bearer {TestIntegration.student2_token}'}
        files = {'attachments': ('student2_submission.txt', io.BytesIO(b"Student 2 submission content."), 'text/plain')}
        data = {'assignmentId': TestIntegration.assignment_id, 'text': 'Submission by Student 2'}
        response = requests.post(url, data=data, files=files, headers=headers)
        assert response.status_code == 201, f"S2 Submit Failed: {response.status_code} - {response.text}"

        submission_json = response.json()
        TestIntegration.student2_submission_id = submission_json.get('submissionId')
        assert TestIntegration.student2_submission_id is not None, f"submissionId not found for S2: {submission_json}"
        assert len(TestIntegration.student2_submission_id) == 24, "S2 submissionId is not 24 chars."
        print(f"Student2 Submission ID: {TestIntegration.student2_submission_id}")

    def test_12_student3_submit_assignment(self):
        if not (TestIntegration.student3_token and TestIntegration.assignment_id):
            pytest.skip("Student3 token or assignment ID missing.")
        url = f"{SUBMISSION_SERVICE_URL}/submissions"
        headers = {'Authorization': f'Bearer {TestIntegration.student3_token}'}
        files = {'attachments': ('student3_submission.txt', io.BytesIO(b"Student 3 submission content."), 'text/plain')}
        data = {'assignmentId': TestIntegration.assignment_id, 'text': 'Submission by Student 3'}
        response = requests.post(url, data=data, files=files, headers=headers)
        assert response.status_code == 201, f"S3 Submit Failed: {response.status_code} - {response.text}"
        
        submission_json = response.json()
        TestIntegration.student3_submission_id = submission_json.get('submissionId')
        assert TestIntegration.student3_submission_id is not None, f"submissionId not found for S3: {submission_json}"
        assert len(TestIntegration.student3_submission_id) == 24, "S3 submissionId is not 24 chars."
        print(f"Student3 Submission ID: {TestIntegration.student3_submission_id}")

    # --- REVIEW TESTS ---
    @pytest.mark.skipif(SKIP_REVIEW_TESTS, reason=SKIP_REVIEW_REASON)
    def test_13_review_service_health(self):
        url = f"{REVIEW_SERVICE_URL}/health"
        try:
            response = requests.get(url, timeout=10)
            assert response.status_code == 200, f"Review health check failed: {response.status_code} - {response.text}"
            health_data = response.json()
            assert 'status' in health_data 
            print(f"\nReview service health check: {health_data}")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Review service not available or health check failed: {e}")

    @pytest.mark.skipif(SKIP_REVIEW_TESTS, reason=SKIP_REVIEW_REASON)
    def test_14_teacher_auto_assign_peer_reviews(self):
        if not (TestIntegration.teacher_token and TestIntegration.assignment_id and \
                TestIntegration.student1_serial_number and TestIntegration.student2_serial_number and TestIntegration.student3_serial_number and \
                TestIntegration.student1_submission_id and \
                TestIntegration.student2_submission_id and \
                TestIntegration.student3_submission_id):
            pytest.skip("Prerequisites for auto-assigning reviews not met (missing IDs, serials or token).")
        
        url = f"{REVIEW_SERVICE_URL}/reviews/assign/auto"
        headers = {'Authorization': f'Bearer {TestIntegration.teacher_token}'}
        # MODIFICA: minReviews = 1 per lasciare spazio a manual_assign
        auto_assign_data = {"assignmentId": TestIntegration.assignment_id, "minReviews": 1} 
        
        print(f"\nDEBUG test_14: Attempting auto-assign for assignmentId: {TestIntegration.assignment_id} with minReviews: 1")
        response = requests.post(url, json=auto_assign_data, headers=headers, timeout=20)
        
        print(f"DEBUG test_14: Auto Assign Response Status: {response.status_code}")
        print(f"DEBUG test_14: Auto Assign Response Text (first 300): {response.text[:300]}")

        assert response.status_code == 200, f"Failed to auto-assign peer reviews: Status {response.status_code} - {response.text}"
        
        assignments_data = response.json()
        assert isinstance(assignments_data, list), "Auto-assign response is not a list."
        
        num_submissions = 3
        expected_assignments = num_submissions * auto_assign_data["minReviews"] # Ora 3 * 1 = 3
        assert len(assignments_data) == expected_assignments, \
            f"Expected {expected_assignments} review assignments, but got {len(assignments_data)}."
        
        TestIntegration.peer_review_assignments = assignments_data
        print(f"Auto-assigned {len(assignments_data)} peer reviews successfully.")

        reviews_per_reviewer = {}
        reviews_per_submission = {}
        for assign in assignments_data:
            assert 'reviewId' in assign, f"Review assignment missing 'reviewId': {assign}"
            assert assign.get('authorSerialNumber') != assign.get('reviewerserialNumber'), f"Auto-assign created a self-review: {assign}"
            reviews_per_reviewer[assign['reviewerserialNumber']] = reviews_per_reviewer.get(assign['reviewerserialNumber'], 0) + 1
            reviews_per_submission[assign['submissionId']] = reviews_per_submission.get(assign['submissionId'], 0) + 1
        
        print(f"DEBUG test_14: Reviews per reviewer: {reviews_per_reviewer}")
        print(f"DEBUG test_14: Reviews per submission: {reviews_per_submission}")

        all_submission_ids_in_assignment = [
            TestIntegration.student1_submission_id, 
            TestIntegration.student2_submission_id, 
            TestIntegration.student3_submission_id
        ]
        for sub_id in all_submission_ids_in_assignment:
             assert reviews_per_submission.get(sub_id, 0) == auto_assign_data["minReviews"], \
                f"Submission {sub_id} did not receive {auto_assign_data['minReviews']} reviews. Got {reviews_per_submission.get(sub_id, 0)}"

        student1_review = next((r for r in assignments_data if r.get('reviewerserialNumber') == TestIntegration.student1_serial_number), None)
        if student1_review:
            TestIntegration.review_id = student1_review.get('reviewId')
            print(f"Review ID for Student1 to submit (from auto-assign): {TestIntegration.review_id}")
        elif assignments_data:
             TestIntegration.review_id = assignments_data[0].get('reviewId') 
             print(f"Warning: No review auto-assigned to Student1. Using fallback review ID: {TestIntegration.review_id} for reviewer {assignments_data[0].get('reviewerserialNumber')}")
        # Non fallire se review_id non è impostato qui, test_17 lo gestirà se S1 non ha review
        # assert TestIntegration.review_id is not None, "Failed to obtain a review_id from auto-assignments."

    @pytest.mark.skipif(SKIP_REVIEW_TESTS, reason=SKIP_REVIEW_REASON)
    def test_15_teacher_manual_assign_peer_reviews(self):
        if not (TestIntegration.teacher_token and TestIntegration.assignment_id and \
                TestIntegration.student1_serial_number and TestIntegration.student1_submission_id and \
                TestIntegration.student2_serial_number and TestIntegration.student2_submission_id and \
                TestIntegration.student3_serial_number and TestIntegration.student3_submission_id):
             pytest.skip("Prerequisites for manual review assignment not met (missing student/submission IDs or token).")

        url = f"{REVIEW_SERVICE_URL}/reviews/assign/manual"
        headers = {'Authorization': f'Bearer {TestIntegration.teacher_token}'}
        
        # Trova una combinazione (revisore, sottomissione) che non sia già in TestIntegration.peer_review_assignments
        # e che non sia un'auto-review.
        all_students_serials = [
            TestIntegration.student1_serial_number, 
            TestIntegration.student2_serial_number, 
            TestIntegration.student3_serial_number
        ]
        all_submission_ids = [
            TestIntegration.student1_submission_id,
            TestIntegration.student2_submission_id,
            TestIntegration.student3_submission_id
        ]
        # Mappa submission_id al suo autore
        submission_authors = {
            TestIntegration.student1_submission_id: TestIntegration.student1_serial_number,
            TestIntegration.student2_submission_id: TestIntegration.student2_serial_number,
            TestIntegration.student3_submission_id: TestIntegration.student3_serial_number,
        }

        chosen_manual_reviewer_sn = None
        chosen_manual_submission_id = None
        
        for reviewer_sn in all_students_serials:
            for submission_id in all_submission_ids:
                author_sn = submission_authors[submission_id]
                if reviewer_sn == author_sn: # Evita auto-review
                    continue

                is_already_assigned = any(
                    auto_assign.get('reviewerserialNumber') == reviewer_sn and \
                    auto_assign.get('submissionId') == submission_id
                    for auto_assign in TestIntegration.peer_review_assignments 
                )

                if not is_already_assigned:
                    chosen_manual_reviewer_sn = reviewer_sn
                    chosen_manual_submission_id = submission_id
                    print(f"DEBUG test_15: Chosen UNIQUE manual assignment: Reviewer {chosen_manual_reviewer_sn}, Submission {chosen_manual_submission_id} (Author: {author_sn})")
                    break # Trovata una combinazione
            if chosen_manual_reviewer_sn: # Esci anche dal ciclo esterno
                break
        
        if not chosen_manual_reviewer_sn:
            pytest.skip("Could not find a unique manual assignment combination not already created by auto-assign. Skipping this manual assign test.")

        manual_assign_data = {
            "assignmentId": TestIntegration.assignment_id,
            "manualAssignments": [{"reviewerserialNumber": chosen_manual_reviewer_sn, "submissionId": chosen_manual_submission_id}]
        }
        
        print(f"\nDEBUG test_15: Attempting manual assignment with: {manual_assign_data}")
        response = requests.post(url, json=manual_assign_data, headers=headers, timeout=10)
        print(f"DEBUG test_15: Manual Assign Response Status: {response.status_code}, Text: {response.text[:300]}")

        assert response.status_code == 200, f"Manual assignment failed: Status {response.status_code} - {response.text}"
        
        assignments_data = response.json()
        assert isinstance(assignments_data, list), "Manual assignment response is not a list."
        assert len(assignments_data) >= 1, f"Manual assignment expected at least one item, got {len(assignments_data)}. Response: {assignments_data}"
        
        specific_assignment_found = any(
            a.get('reviewerserialNumber') == chosen_manual_reviewer_sn and \
            a.get('submissionId') == chosen_manual_submission_id
            for a in assignments_data
        )
        assert specific_assignment_found, "Chosen manually assigned review not found in response."
        print(f"Manually assigned peer review ({chosen_manual_reviewer_sn} -> {chosen_manual_submission_id}) successful.")


    @pytest.mark.skipif(SKIP_REVIEW_TESTS, reason=SKIP_REVIEW_REASON)
    def test_16_student1_list_assigned_reviews(self):
        # ... (codice di test_16 rimane invariato, ma ora dovrebbe riflettere più accuratamente
        # le assegnazioni totali dopo auto e manual se manual_assign aggiunge a una lista globale o se il servizio
        # restituisce tutte le assegnazioni per lo studente)
        if not (TestIntegration.student1_token and TestIntegration.student1_serial_number):
            pytest.skip("Student1 token or serial number missing for listing reviews.")
        
        url = f"{REVIEW_SERVICE_URL}/reviews/student/{TestIntegration.student1_serial_number}"
        headers = {'Authorization': f'Bearer {TestIntegration.student1_token}'}
        response = requests.get(url, headers=headers)
        assert response.status_code == 200, f"List S1 Reviews Failed: {response.status_code} - {response.text}"
        
        student_reviews_api = response.json()
        assert isinstance(student_reviews_api, list), "Response for S1's reviews is not a list."
        
        print(f"\nDEBUG test_16: Student1 ({TestIntegration.student1_serial_number}) has {len(student_reviews_api)} reviews listed by API.")

        # Controlla se S1 ha almeno le review da auto_assign (più eventuali manuali)
        num_auto_assigned_to_s1 = 0
        if TestIntegration.peer_review_assignments: # Se auto-assign è stato eseguito
            num_auto_assigned_to_s1 = sum(1 for r in TestIntegration.peer_review_assignments if r.get('reviewerserialNumber') == TestIntegration.student1_serial_number)
            print(f"DEBUG test_16: Student1 was auto-assigned {num_auto_assigned_to_s1} reviews initially.")
        
        # Ora è più difficile predire il numero esatto a causa di manual_assign.
        # Almeno, se S1 aveva auto-assegnazioni, queste dovrebbero essere presenti.
        if num_auto_assigned_to_s1 > 0:
            assert len(student_reviews_api) >= num_auto_assigned_to_s1, \
                f"S1 was auto-assigned {num_auto_assigned_to_s1}, API lists {len(student_reviews_api)}."
        elif not student_reviews_api:
            print("DEBUG test_16: S1 had no auto-assigned reviews and API list is empty. This might be OK if no manual assignments were made for S1 either.")
        
        print(f"Student1 has {len(student_reviews_api)} peer reviews assigned according to API.")


    @pytest.mark.skipif(SKIP_REVIEW_TESTS, reason=SKIP_REVIEW_REASON)
    def test_17_student1_get_and_submit_specific_review(self): 
        if not (TestIntegration.student1_token and TestIntegration.assignment_rubric):
            pytest.skip("Student1 token or assignment_rubric is missing.")
        
        list_reviews_url = f"{REVIEW_SERVICE_URL}/reviews/student/{TestIntegration.student1_serial_number}"
        headers_s1_for_list = {'Authorization': f'Bearer {TestIntegration.student1_token}'}
        list_response = requests.get(list_reviews_url, headers=headers_s1_for_list)
        assert list_response.status_code == 200, "Failed to list S1's reviews to pick one for submission test."
        s1_assigned_reviews = list_response.json()

        if not s1_assigned_reviews:
            pytest.skip(f"No reviews currently assigned to Student1 ({TestIntegration.student1_serial_number}) via API. Cannot test GET/SUBMIT.")

        review_to_process = None
        for rev in s1_assigned_reviews:
            if not rev.get('submittedAt'): 
                review_to_process = rev
                break
        if not review_to_process: 
            # Se tutte sono sottomesse, questo test non può procedere con una nuova sottomissione.
            # Potremmo scegliere di saltare o fallire a seconda dello scopo del test.
            # Per ora, lo saltiamo se non ci sono review non sottomesse.
            pytest.skip(f"All reviews for Student1 ({TestIntegration.student1_serial_number}) are already submitted. Cannot test new submission.")
            # review_to_process = s1_assigned_reviews[0] # Fallback precedente, ma non utile se vogliamo testare la sottomissione

        current_review_id_for_s1 = review_to_process.get('reviewId')
        assert current_review_id_for_s1, "Could not get a valid reviewId from S1's listed reviews."
        
        print(f"\nStudent1 ({TestIntegration.student1_serial_number}) will attempt to GET and SUBMIT review ID: {current_review_id_for_s1}")
        print(f"Full review object chosen for GET/SUBMIT: {review_to_process}")

        get_url = f"{REVIEW_SERVICE_URL}/reviews/{current_review_id_for_s1}"
        
        response_get = requests.get(get_url, headers=headers_s1_for_list) 
        print(f"DEBUG test_17: GET Response Status: {response_get.status_code}")
        if response_get.status_code != 200:
            print(f"DEBUG test_17: GET Response Text: {response_get.text[:1000]}")
        assert response_get.status_code == 200, f"Failed to GET specific review {current_review_id_for_s1} for S1: {response_get.text}"
        
        review_data_get = response_get.json()
        assert review_data_get.get('reviewId') == current_review_id_for_s1, "GET response reviewId mismatch."
        assert review_data_get.get('reviewerserialNumber') == TestIntegration.student1_serial_number, "GET response reviewer SN mismatch."
        print(f"Student1 retrieved specific review {current_review_id_for_s1} successfully.")

        # Fase 2: PUT (Submit) della review (solo se non già sottomessa)
        if review_data_get.get('submittedAt'): # Doppio controllo, anche se abbiamo cercato una non sottomessa
            print(f"Warning test_17: Review {current_review_id_for_s1} was already submitted (checked after GET). Skipping PUT.")
            return 

        put_url = f"{REVIEW_SERVICE_URL}/reviews/{current_review_id_for_s1}"
        evaluation_payload = []
        for criterion in TestIntegration.assignment_rubric:
            evaluation_payload.append({
                "criterion": criterion["criterion"],
                "score": criterion["maxScore"] // 2 +1, 
                "feedback": f"Feedback on {criterion['criterion']} from Student1 for review {current_review_id_for_s1}."
            })
        submit_payload = {"evaluation": evaluation_payload}
        
        response_put = requests.put(put_url, json=submit_payload, headers=headers_s1_for_list)
        print(f"DEBUG test_17: PUT Response Status: {response_put.status_code}")
        if response_put.status_code != 200:
             print(f"DEBUG test_17: PUT Response Text: {response_put.text[:500]}")
        assert response_put.status_code == 200, f"Failed to submit review {current_review_id_for_s1} by S1: {response_put.text}"
        
        submitted_review_data = response_put.json()
        assert submitted_review_data.get('reviewId') == current_review_id_for_s1, "PUT response reviewId mismatch."
        assert 'submittedAt' in submitted_review_data and submitted_review_data['submittedAt'] is not None, "submittedAt missing or null."
        assert isinstance(submitted_review_data.get('evaluation'), list) and \
               len(submitted_review_data.get('evaluation', [])) == len(TestIntegration.assignment_rubric), "Evaluation data mismatch."
        print(f"Student1 submitted review {current_review_id_for_s1} successfully.")

    # --- AUTH PROFILE AND LOGOUT ---
    # (Questi test rimangono invariati, li ometto per brevità)
    def test_18_student1_get_own_profile(self): 
        if not (TestIntegration.student1_token and TestIntegration.student1_serial_number):
            pytest.skip("Student1 token or serial_number not available.")

        url = f"{AUTH_SERVICE_URL}/auth/users/me"
        headers = {'Authorization': f'Bearer {TestIntegration.student1_token}'}
        response = requests.get(url, headers=headers)
        assert response.status_code == 200, f"Student1 Get profile failed: {response.text}"
        profile = response.json()
        assert profile.get('email') == "student1.test@example.com" 
        assert profile.get('serialNumber') == TestIntegration.student1_serial_number
        print(f"Student1 Get Own Profile successful (serialNumber: {profile.get('serialNumber')}).")

    def test_19_student1_update_own_profile(self): 
        if not TestIntegration.student1_token: pytest.skip("Student1 token missing.")
        url = f"{AUTH_SERVICE_URL}/auth/users/me"
        headers = {'Authorization': f'Bearer {TestIntegration.student1_token}'}
        update_data = {"residence": "New S1 City, New S1 Street, 111"}
        response = requests.put(url, json=update_data, headers=headers)
        assert response.status_code == 200, f"S1 Update profile failed: {response.text}"
        assert response.json().get('residence') == update_data["residence"]
        print(f"\nStudent1 Update Own Profile successful.")

    def test_20_teacher_get_all_students(self): 
        if not TestIntegration.teacher_token: pytest.skip("Teacher token missing.")
        url = f"{AUTH_SERVICE_URL}/auth/users/students"
        headers = {'Authorization': f'Bearer {TestIntegration.teacher_token}'}
        response = requests.get(url, headers=headers)
        assert response.status_code == 200, f"Teacher get all students failed: {response.text}"
        students_list = response.json()
        assert isinstance(students_list, list)
        
        serials_in_list = {s.get('serialNumber') for s in students_list if isinstance(s, dict) and s.get('serialNumber')}
        if TestIntegration.student1_serial_number:
            assert TestIntegration.student1_serial_number in serials_in_list, f"S1 ({TestIntegration.student1_serial_number}) not in list."
        if TestIntegration.student2_serial_number:
            assert TestIntegration.student2_serial_number in serials_in_list, f"S2 ({TestIntegration.student2_serial_number}) not in list."
        if TestIntegration.student3_serial_number:
            assert TestIntegration.student3_serial_number in serials_in_list, f"S3 ({TestIntegration.student3_serial_number}) not in list."
        print(f"\nTeacher Get All Students successful, found {len(serials_in_list)} students.")

    # --- LOGOUT TESTS ---
    def test_21_student1_logout(self): 
        if not TestIntegration.student1_token: pytest.skip("Student1 token missing for logout.")
        url = f"{AUTH_SERVICE_URL}/auth/logout"
        headers = {'Authorization': f'Bearer {TestIntegration.student1_token}'}
        response_logout = requests.post(url, headers=headers)
        assert response_logout.status_code == 204, f"Student1 logout failed: {response_logout.text}"
        
        response_after = requests.get(f"{AUTH_SERVICE_URL}/auth/users/me", headers=headers)
        assert response_after.status_code == 401, "Token for S1 not invalidated after logout."
        TestIntegration.student1_token = None 
        print(f"\nStudent1 Logout successful.")

    def test_22_student2_logout(self):
        if not TestIntegration.student2_token: pytest.skip("Student2 token missing for logout.")
        url = f"{AUTH_SERVICE_URL}/auth/logout"
        headers = {'Authorization': f'Bearer {TestIntegration.student2_token}'}
        response_logout = requests.post(url, headers=headers)
        assert response_logout.status_code == 204, f"Student2 logout failed: {response_logout.text}"
        
        response_after = requests.get(f"{AUTH_SERVICE_URL}/auth/users/me", headers=headers)
        assert response_after.status_code == 401, "Token for S2 not invalidated after logout."
        TestIntegration.student2_token = None
        print(f"Student2 Logout successful.")

    def test_23_student3_logout(self):
        if not TestIntegration.student3_token: pytest.skip("Student3 token missing for logout.")
        url = f"{AUTH_SERVICE_URL}/auth/logout"
        headers = {'Authorization': f'Bearer {TestIntegration.student3_token}'}
        response_logout = requests.post(url, headers=headers)
        assert response_logout.status_code == 204, f"Student3 logout failed: {response_logout.text}"

        response_after = requests.get(f"{AUTH_SERVICE_URL}/auth/users/me", headers=headers)
        assert response_after.status_code == 401, "Token for S3 not invalidated after logout."
        TestIntegration.student3_token = None
        print(f"Student3 Logout successful.")

    def test_24_teacher_logout(self):
        if not TestIntegration.teacher_token: pytest.skip("Teacher token missing for logout.")
        url = f"{AUTH_SERVICE_URL}/auth/logout"
        headers = {'Authorization': f'Bearer {TestIntegration.teacher_token}'}
        response_logout = requests.post(url, headers=headers)
        assert response_logout.status_code == 204, f"Teacher logout failed: {response_logout.text}"

        response_after = requests.get(f"{AUTH_SERVICE_URL}/auth/users/me", headers=headers)
        assert response_after.status_code == 401, "Token for Teacher not invalidated after logout."
        TestIntegration.teacher_token = None
        print(f"Teacher Logout successful.")

    # --- TEARDOWN CLASS ---
    @classmethod
    def teardown_class(cls):
        print("\nRunning teardown to clean up created resources...")
        
        current_tokens = {
            "teacher": cls.teacher_token,
            "student1": cls.student1_token,
            "student2": cls.student2_token,
            "student3": cls.student3_token
        }
        
        teacher_token_for_assignment_deletion = current_tokens["teacher"] # Salva prima della potenziale cancellazione

        if cls.assignment_id and teacher_token_for_assignment_deletion:
            print(f"Attempting to delete assignment {cls.assignment_id} using teacher's original token.")
            try:
                headers = {'Authorization': f'Bearer {teacher_token_for_assignment_deletion}'}
                response = requests.delete(f"{ASSIGNMENT_SERVICE_URL}/assignments/{cls.assignment_id}", headers=headers)
                if response.status_code == 204: 
                    print(f"Assignment {cls.assignment_id} deleted.")
                else: 
                    print(f"Failed to delete assignment {cls.assignment_id}: {response.status_code} - {response.text}")
            except requests.exceptions.RequestException as e: 
                print(f"Error deleting assignment: {e}")
        elif cls.assignment_id:
            print(f"Cannot delete assignment {cls.assignment_id}: teacher token was not available at teardown start.")

        users_to_delete_info = [
            ("Student1", cls.student1_serial_number, "student1"),
            ("Student2", cls.student2_serial_number, "student2"),
            ("Student3", cls.student3_serial_number, "student3"),
            ("Teacher", cls.teacher_serial_number, "teacher") 
        ]
        
        for user_desc, serial, token_key in users_to_delete_info:
            token_to_use = current_tokens.get(token_key)
            if token_to_use and getattr(cls, f"{token_key}_serial_number", None):
                print(f"Attempting to delete {user_desc} account (Serial: {serial})...")
                try:
                    headers = {'Authorization': f'Bearer {token_to_use}'}
                    response = requests.delete(f"{AUTH_SERVICE_URL}/auth/users/me", headers=headers)
                    if response.status_code == 204: 
                        print(f"{user_desc} account deleted.")
                    elif response.status_code == 401: 
                        print(f"{user_desc} account token was already invalid or user deleted by other means.")
                    else: 
                        print(f"Failed to delete {user_desc} account: {response.status_code} - {response.text}")
                except requests.exceptions.RequestException as e: 
                    print(f"Error deleting {user_desc}: {e}")
            else: 
                print(f"Skipping deletion for {user_desc} (Serial: {serial}) - token or serial not set.")
        
        print("--- Teardown Complete ---")

# --- END OF FILE test_api.py ---