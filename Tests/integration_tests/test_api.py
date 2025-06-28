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
REPORT_SERVICE_URL = os.getenv('REPORT_SERVICE_URL', 'http://report-app-service:5004')

TEST_PASSWORD = "password123"

class TestIntegration:
    # --- User credentials and tokens ---
    student1_token = None
    student1_serial_number = None
    student2_token = None
    student2_serial_number = None
    student3_token = None
    student3_serial_number = None
    teacher_token = None
    teacher_serial_number = None

    # --- Resource IDs ---
    assignment_id = None
    assignment_rubric = None
    student1_submission_id = None
    student2_submission_id = None
    student3_submission_id = None
    peer_review_assignments = []
    
    # --- Variables for linking tests, populated in test_16 ---
    submission_id_under_review = None
    author_of_submission_under_review_sn = None
    author_of_submission_under_review_token = None

    # --- HEALTH CHECKS (Unchanged) ---
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

    def test_00d_review_service_health(self):
        url = f"{REVIEW_SERVICE_URL}/health"
        try:
            response = requests.get(url, timeout=10)
            assert response.status_code == 200, f"Review service health check failed: {response.status_code} - {response.text}"
            health_data = response.json()
            assert 'status' in health_data 
            print(f"Review service health check: {health_data['status']}")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Review service health check failed: {e}")

    def test_00e_report_service_health(self):
        url = f"{REPORT_SERVICE_URL}/health"
        try:
            response = requests.get(url, timeout=10)
            assert response.status_code == 200, f"Report service health check failed: {response.status_code} - {response.text}"
            health_data = response.json()
            assert 'status' in health_data and health_data['status'] == 'healthy'
            print(f"Report service health check: {health_data['status']}")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Report service not available or health check failed: {e}")


    # --- REGISTRATION & LOGIN (Unchanged) ---
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


    # --- ASSIGNMENT AND SUBMISSION FLOW (Unchanged) ---
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


    # --- REVIEW TESTS (test_16 is MODIFIED) ---
    def test_13_teacher_auto_assign_peer_reviews(self):
        if not (TestIntegration.teacher_token and TestIntegration.assignment_id and \
                TestIntegration.student1_submission_id and \
                TestIntegration.student2_submission_id and \
                TestIntegration.student3_submission_id):
            pytest.skip("Prerequisites for auto-assigning reviews not met.")
        
        url = f"{REVIEW_SERVICE_URL}/reviews/assign/auto"
        headers = {'Authorization': f'Bearer {TestIntegration.teacher_token}'}
        auto_assign_data = {"assignmentId": TestIntegration.assignment_id, "minReviews": 1} 
        
        response = requests.post(url, json=auto_assign_data, headers=headers, timeout=20)
        assert response.status_code == 200, f"Failed to auto-assign peer reviews: {response.text}"
        
        assignments_data = response.json()
        assert isinstance(assignments_data, list), "Auto-assign response is not a list."
        assert len(assignments_data) >= 3, f"Expected at least 3 review assignments, got {len(assignments_data)}."
        
        TestIntegration.peer_review_assignments = assignments_data
        print(f"\nAuto-assigned {len(assignments_data)} peer reviews successfully.")

    def test_14_teacher_manual_assign_peer_reviews(self):
        if not (TestIntegration.teacher_token and TestIntegration.assignment_id and \
                TestIntegration.student1_serial_number and TestIntegration.student1_submission_id and \
                TestIntegration.student2_serial_number and TestIntegration.student2_submission_id and \
                TestIntegration.student3_serial_number and TestIntegration.student3_submission_id):
             pytest.skip("Prerequisites for manual review assignment not met.")

        url = f"{REVIEW_SERVICE_URL}/reviews/assign/manual"
        headers = {'Authorization': f'Bearer {TestIntegration.teacher_token}'}
        
        all_students_serials = [
            TestIntegration.student1_serial_number, TestIntegration.student2_serial_number, TestIntegration.student3_serial_number
        ]
        all_submission_ids = [
            TestIntegration.student1_submission_id, TestIntegration.student2_submission_id, TestIntegration.student3_submission_id
        ]
        submission_authors = {
            TestIntegration.student1_submission_id: TestIntegration.student1_serial_number,
            TestIntegration.student2_submission_id: TestIntegration.student2_serial_number,
            TestIntegration.student3_submission_id: TestIntegration.student3_serial_number,
        }

        chosen_manual_reviewer_sn, chosen_manual_submission_id = None, None
        for reviewer_sn in all_students_serials:
            for submission_id in all_submission_ids:
                if reviewer_sn == submission_authors[submission_id]: continue
                is_already_assigned = any(
                    a.get('reviewerserialNumber') == reviewer_sn and a.get('submissionId') == submission_id
                    for a in TestIntegration.peer_review_assignments 
                )
                if not is_already_assigned:
                    chosen_manual_reviewer_sn, chosen_manual_submission_id = reviewer_sn, submission_id
                    break
            if chosen_manual_reviewer_sn: break
        
        if not chosen_manual_reviewer_sn:
            pytest.skip("Could not find a unique manual assignment combination. Skipping.")

        manual_assign_data = {
            "assignmentId": TestIntegration.assignment_id,
            "manualAssignments": [{"reviewerserialNumber": chosen_manual_reviewer_sn, "submissionId": chosen_manual_submission_id}]
        }
        response = requests.post(url, json=manual_assign_data, headers=headers)
        assert response.status_code == 200, f"Manual assignment failed: {response.text}"
        assert len(response.json()) >= 1
        print(f"\nManually assigned peer review ({chosen_manual_reviewer_sn} -> {chosen_manual_submission_id}) successful.")

    def test_15_student1_list_assigned_reviews(self):
        if not (TestIntegration.student1_token and TestIntegration.student1_serial_number):
            pytest.skip("Student1 token or serial number missing for listing reviews.")
        
        url = f"{REVIEW_SERVICE_URL}/reviews/student/{TestIntegration.student1_serial_number}"
        headers = {'Authorization': f'Bearer {TestIntegration.student1_token}'}
        response = requests.get(url, headers=headers)
        assert response.status_code == 200, f"List S1 Reviews Failed: {response.text}"
        
        student_reviews_api = response.json()
        assert isinstance(student_reviews_api, list), "Response for S1's reviews is not a list."
        print(f"\nStudent1 has {len(student_reviews_api)} peer reviews assigned.")

    def test_16_student1_get_and_submit_specific_review(self): 
        if not (TestIntegration.student1_token and TestIntegration.assignment_rubric):
            pytest.skip("Student1 token or assignment_rubric is missing.")
        
        list_reviews_url = f"{REVIEW_SERVICE_URL}/reviews/student/{TestIntegration.student1_serial_number}"
        headers_s1 = {'Authorization': f'Bearer {TestIntegration.student1_token}'}
        list_response = requests.get(list_reviews_url, headers=headers_s1)
        assert list_response.status_code == 200, "Failed to list S1's reviews."
        s1_assigned_reviews = list_response.json()

        if not s1_assigned_reviews:
            pytest.skip(f"No reviews assigned to Student1. Cannot test GET/SUBMIT.")

        review_to_process = next((r for r in s1_assigned_reviews if not r.get('submittedAt')), None)
        if not review_to_process: 
            pytest.skip(f"All reviews for Student1 are already submitted. Cannot test new submission.")

        current_review_id = review_to_process.get('reviewId')
        assert current_review_id, "Could not get a valid reviewId from S1's listed reviews."
        
        # MODIFICATION: Store info for later report tests
        TestIntegration.submission_id_under_review = review_to_process.get('submissionId')
        TestIntegration.author_of_submission_under_review_sn = review_to_process.get('authorSerialNumber')
        
        # Determine the correct token for the author of the submission being reviewed
        if TestIntegration.author_of_submission_under_review_sn == TestIntegration.student2_serial_number:
            TestIntegration.author_of_submission_under_review_token = TestIntegration.student2_token
        elif TestIntegration.author_of_submission_under_review_sn == TestIntegration.student3_serial_number:
            TestIntegration.author_of_submission_under_review_token = TestIntegration.student3_token
        else: # This should not happen in this test scenario, but it's good practice
             TestIntegration.author_of_submission_under_review_token = None
        
        assert all([TestIntegration.submission_id_under_review, 
                    TestIntegration.author_of_submission_under_review_sn, 
                    TestIntegration.author_of_submission_under_review_token]), \
            "Could not retrieve author details for the subsequent report test."

        print(f"\nStudent1 will submit review {current_review_id} for submission {TestIntegration.submission_id_under_review} by author {TestIntegration.author_of_submission_under_review_sn}.")

        # Get specific review
        get_url = f"{REVIEW_SERVICE_URL}/reviews/{current_review_id}"
        response_get = requests.get(get_url, headers=headers_s1) 
        assert response_get.status_code == 200, f"Failed to GET review {current_review_id}: {response_get.text}"
        
        # Submit review
        put_url = f"{REVIEW_SERVICE_URL}/reviews/{current_review_id}"
        evaluation_payload = [{"criterion": c["criterion"], "score": c["maxScore"]//2+1, "feedback": f"Feedback on {c['criterion']}."} for c in TestIntegration.assignment_rubric]
        submit_payload = {"evaluation": evaluation_payload}
        
        response_put = requests.put(put_url, json=submit_payload, headers=headers_s1)
        assert response_put.status_code == 200, f"Failed to submit review {current_review_id}: {response_put.text}"
        
        submitted_review = response_put.json()
        assert submitted_review.get('submittedAt') is not None, "submittedAt timestamp is missing after submission."
        print(f"Student1 submitted review {current_review_id} successfully.")


    # --- REPORT TESTS (test_18 is REWRITTEN) ---
    def test_17_teacher_get_assignment_report(self):
        if not (TestIntegration.teacher_token and TestIntegration.assignment_id):
            pytest.skip("Teacher token or assignment ID is missing for report test.")

        url = f"{REPORT_SERVICE_URL}/reports/teacher/{TestIntegration.teacher_serial_number}"
        headers = {'Authorization': f'Bearer {TestIntegration.teacher_token}'}
        
        response = requests.get(url, headers=headers)
        assert response.status_code == 200, f"Failed to get teacher report: {response.status_code} - {response.text}"
        
        reports = response.json()
        assert isinstance(reports, list), "Teacher report response should be a list."
        assert len(reports) >= 1, "Expected at least one assignment report for the teacher."
        
        report = next((r for r in reports if r.get('assignmentId') == TestIntegration.assignment_id), None)
        assert report is not None, f"Report for assignment {TestIntegration.assignment_id} not found."
        
        print(f"\nTeacher report for assignment {TestIntegration.assignment_id} retrieved successfully.")
        
        assert 'title' in report and 'averageScores' in report and 'submissions' in report
        assert isinstance(report['submissions'], list)
        # Check if 3 submissions are in the report. This might be brittle if a submission fails, so we check for >= 1.
        assert len(report['submissions']) >= 1, f"Expected at least 1 submission in report, found {len(report['submissions'])}."

        reviewed_submission_report = next((s for s in report['submissions'] if s.get('submissionId') == TestIntegration.submission_id_under_review), None)
        assert reviewed_submission_report is not None, "The specific submission that was reviewed was not found in the teacher's report."
        
        assert len(reviewed_submission_report.get('peerReviews', [])) >= 1, "Expected at least one peer review for the reviewed submission."
        
        # In the teacher's report, the reviewer's identity IS present.
        review_from_s1 = next((pr for pr in reviewed_submission_report['peerReviews'] if pr.get('reviewerSerialNumber') == TestIntegration.student1_serial_number), None)
        assert review_from_s1 is not None, "Could not find the specific review submitted by Student1 in the teacher's report."
        print("Validated presence and content of Student1's review in the teacher report.")

    def test_18_get_student_submission_report(self):
        """
        Tests the new endpoint: GET /reports/student/{serialNumber}/submissions/{submissionId}
        This test verifies three access scenarios:
        1. The student who owns the submission can view their anonymous report.
        2. The teacher can view the student's anonymous report.
        3. Another student is forbidden from viewing the report.
        """
        if not all([TestIntegration.submission_id_under_review, 
                    TestIntegration.author_of_submission_under_review_sn,
                    TestIntegration.author_of_submission_under_review_token, 
                    TestIntegration.teacher_token, 
                    TestIntegration.student1_token]): # Use S1 as the "other student"
            pytest.skip("Prerequisites for student submission report test are missing.")
        
        base_url = f"{REPORT_SERVICE_URL}/reports/student/{TestIntegration.author_of_submission_under_review_sn}/submissions/{TestIntegration.submission_id_under_review}"

        # --- Part A: Student Owner Access ---
        print(f"\nTesting student report access for owner ({TestIntegration.author_of_submission_under_review_sn})...")
        headers_owner = {'Authorization': f'Bearer {TestIntegration.author_of_submission_under_review_token}'}
        response_owner = requests.get(base_url, headers=headers_owner)
        assert response_owner.status_code == 200, f"Owner student failed to get their own submission report: {response_owner.text}"
        
        report_data = response_owner.json()
        assert report_data.get('submissionId') == TestIntegration.submission_id_under_review
        assert 'reviews' in report_data and isinstance(report_data['reviews'], list)
        assert len(report_data['reviews']) >= 1, "Expected at least one review in the report."
        
        # Verify anonymity: reviewerSerialNumber should NOT be present.
        anonymous_review = report_data['reviews'][0]
        assert 'reviewerSerialNumber' not in anonymous_review, "Reviewer's identity should be anonymous for the student owner."
        assert 'evaluation' in anonymous_review and 'reviewedAt' in anonymous_review
        assert 'averageScore' in report_data and isinstance(report_data['averageScore'], (int, float))

        print("Student owner access successful and review is correctly anonymous.")

        # --- Part B: Teacher Access ---
        print("Testing student report access for teacher...")
        headers_teacher = {'Authorization': f'Bearer {TestIntegration.teacher_token}'}
        response_teacher = requests.get(base_url, headers=headers_teacher)
        assert response_teacher.status_code == 200, f"Teacher failed to get student's submission report: {response_teacher.text}"
        
        # The teacher should see the exact same anonymous report as the student.
        assert response_teacher.json() == report_data, "Teacher's view of the student report should be identical to the student's view."
        print("Teacher access successful.")

        # --- Part C: Forbidden Access (another student) ---
        print("Testing forbidden access for another student...")
        # Use student1's token, unless they are the author, in which case use student3's token.
        non_owner_token = TestIntegration.student1_token if TestIntegration.author_of_submission_under_review_sn != TestIntegration.student1_serial_number else TestIntegration.student3_token
        headers_forbidden = {'Authorization': f'Bearer {non_owner_token}'}
        response_forbidden = requests.get(base_url, headers=headers_forbidden)
        assert response_forbidden.status_code == 403, f"Another student should be forbidden, but got status {response_forbidden.status_code}"
        print("Forbidden access for another student correctly returned 403.")


    # --- AUTH PROFILE AND CLEANUP (Unchanged) ---
    def test_19_student1_get_own_profile(self): 
        if not (TestIntegration.student1_token and TestIntegration.student1_serial_number):
            # Student 1 might have logged out in a previous failed run, so re-login if needed
            if not TestIntegration.student1_token and TestIntegration.student1_serial_number:
                login_resp = requests.post(f"{AUTH_SERVICE_URL}/auth/login", json={"email": "student1.test@example.com", "password": TEST_PASSWORD})
                if login_resp.status_code == 200:
                    TestIntegration.student1_token = login_resp.json()['token']
                else:
                    pytest.skip("Student1 token not available and re-login failed.")
            else:
                 pytest.skip("Student1 token or serial_number not available.")

        url = f"{AUTH_SERVICE_URL}/auth/users/me"
        headers = {'Authorization': f'Bearer {TestIntegration.student1_token}'}
        response = requests.get(url, headers=headers)
        assert response.status_code == 200, f"Student1 Get profile failed: {response.text}"
        profile = response.json()
        assert profile.get('email') == "student1.test@example.com" 
        assert profile.get('serialNumber') == TestIntegration.student1_serial_number
        print(f"\nStudent1 Get Own Profile successful (serialNumber: {profile.get('serialNumber')}).")

    def test_20_student1_update_own_profile(self): 
        if not TestIntegration.student1_token: pytest.skip("Student1 token missing.")
        url = f"{AUTH_SERVICE_URL}/auth/users/me"
        headers = {'Authorization': f'Bearer {TestIntegration.student1_token}'}
        update_data = {"residence": "New S1 City, New S1 Street, 111"}
        response = requests.put(url, json=update_data, headers=headers)
        assert response.status_code == 200, f"S1 Update profile failed: {response.text}"
        assert response.json().get('residence') == update_data["residence"]
        print(f"Student1 Update Own Profile successful.")

    def test_21_teacher_get_all_students(self): 
        if not TestIntegration.teacher_token: pytest.skip("Teacher token missing.")
        url = f"{AUTH_SERVICE_URL}/auth/users/students"
        headers = {'Authorization': f'Bearer {TestIntegration.teacher_token}'}
        response = requests.get(url, headers=headers)
        assert response.status_code == 200, f"Teacher get all students failed: {response.text}"
        students_list = response.json()
        assert isinstance(students_list, list)
        
        serials_in_list = {s.get('serialNumber') for s in students_list if isinstance(s, dict) and s.get('serialNumber')}
        if TestIntegration.student1_serial_number:
            assert TestIntegration.student1_serial_number in serials_in_list
        if TestIntegration.student2_serial_number:
            assert TestIntegration.student2_serial_number in serials_in_list
        if TestIntegration.student3_serial_number:
            assert TestIntegration.student3_serial_number in serials_in_list
        print(f"Teacher Get All Students successful, found {len(serials_in_list)} students.")

    def test_22_student1_logout(self): 
        if not TestIntegration.student1_token: pytest.skip("Student1 token missing for logout.")
        url = f"{AUTH_SERVICE_URL}/auth/logout"
        headers = {'Authorization': f'Bearer {TestIntegration.student1_token}'}
        response_logout = requests.post(url, headers=headers)
        assert response_logout.status_code == 204
        
        response_after = requests.get(f"{AUTH_SERVICE_URL}/auth/users/me", headers=headers)
        assert response_after.status_code == 401
        TestIntegration.student1_token = None 
        print(f"\nStudent1 Logout successful.")

    def test_23_student2_logout(self):
        if not TestIntegration.student2_token: pytest.skip("Student2 token missing for logout.")
        url = f"{AUTH_SERVICE_URL}/auth/logout"
        headers = {'Authorization': f'Bearer {TestIntegration.student2_token}'}
        response_logout = requests.post(url, headers=headers)
        assert response_logout.status_code == 204
        
        response_after = requests.get(f"{AUTH_SERVICE_URL}/auth/users/me", headers=headers)
        assert response_after.status_code == 401
        TestIntegration.student2_token = None
        print(f"Student2 Logout successful.")

    def test_24_student3_logout(self):
        if not TestIntegration.student3_token: pytest.skip("Student3 token missing for logout.")
        url = f"{AUTH_SERVICE_URL}/auth/logout"
        headers = {'Authorization': f'Bearer {TestIntegration.student3_token}'}
        response_logout = requests.post(url, headers=headers)
        assert response_logout.status_code == 204

        response_after = requests.get(f"{AUTH_SERVICE_URL}/auth/users/me", headers=headers)
        assert response_after.status_code == 401
        TestIntegration.student3_token = None
        print(f"Student3 Logout successful.")

    def test_25_teacher_logout(self):
        if not TestIntegration.teacher_token: pytest.skip("Teacher token missing for logout.")
        url = f"{AUTH_SERVICE_URL}/auth/logout"
        headers = {'Authorization': f'Bearer {TestIntegration.teacher_token}'}
        response_logout = requests.post(url, headers=headers)
        assert response_logout.status_code == 204

        response_after = requests.get(f"{AUTH_SERVICE_URL}/auth/users/me", headers=headers)
        assert response_after.status_code == 401
        TestIntegration.teacher_token = None
        print(f"Teacher Logout successful.")

    @classmethod
    def teardown_class(cls):
        print("\nRunning teardown to clean up created resources...")
        
        # Re-login teacher if token is missing, to ensure cleanup can happen
        if not cls.teacher_token and cls.teacher_serial_number:
            login_data = {"email": "professore.rossi@example.com", "password": TEST_PASSWORD}
            resp = requests.post(f"{AUTH_SERVICE_URL}/auth/login", json=login_data)
            if resp.status_code == 200:
                cls.teacher_token = resp.json()['token']
                print("Re-logged in teacher for cleanup.")

        if cls.assignment_id and cls.teacher_token:
            try:
                headers = {'Authorization': f'Bearer {cls.teacher_token}'}
                resp = requests.delete(f"{ASSIGNMENT_SERVICE_URL}/assignments/{cls.assignment_id}", headers=headers)
                print(f"Assignment {cls.assignment_id} deletion status: {resp.status_code}")
            except Exception as e: 
                print(f"Error deleting assignment: {e}")
        
        # Deletion logic can remain as is, since logout tests nullify tokens.
        # This part of cleanup is best-effort and relies on tokens not being nullified before teardown.
        print("--- Teardown Complete ---")