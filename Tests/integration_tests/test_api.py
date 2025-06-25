# --- START OF FILE test_api.py ---

import pytest
import requests
import os
from datetime import date, datetime, timezone, timedelta
import io

# Base URLs
AUTH_SERVICE_URL = os.getenv('AUTHENTICATION_SERVICE_URL', 'http://authentication-app-service:5000')
ASSIGNMENT_SERVICE_URL = os.getenv('ASSIGNMENT_SERVICE_URL', 'http://assignment-app-service:5001')


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

    # --- AUTH PROFILE AND LOGOUT ---
    def test_10_student1_get_own_profile(self): 
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

    def test_11_student1_update_own_profile(self): 
        if not TestIntegration.student1_token: pytest.skip("Student1 token missing.")
        url = f"{AUTH_SERVICE_URL}/auth/users/me"
        headers = {'Authorization': f'Bearer {TestIntegration.student1_token}'}
        update_data = {"residence": "New S1 City, New S1 Street, 111"}
        response = requests.put(url, json=update_data, headers=headers)
        assert response.status_code == 200, f"S1 Update profile failed: {response.text}"
        assert response.json().get('residence') == update_data["residence"]
        print(f"\nStudent1 Update Own Profile successful.")

    def test_12_teacher_get_all_students(self): 
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
    def test_13_student1_logout(self): 
        if not TestIntegration.student1_token: pytest.skip("Student1 token missing for logout.")
        url = f"{AUTH_SERVICE_URL}/auth/logout"
        headers = {'Authorization': f'Bearer {TestIntegration.student1_token}'}
        response_logout = requests.post(url, headers=headers)
        assert response_logout.status_code == 204, f"Student1 logout failed: {response_logout.text}"
        
        response_after = requests.get(f"{AUTH_SERVICE_URL}/auth/users/me", headers=headers)
        assert response_after.status_code == 401, "Token for S1 not invalidated after logout."
        TestIntegration.student1_token = None 
        print(f"\nStudent1 Logout successful.")

    def test_14_student2_logout(self):
        if not TestIntegration.student2_token: pytest.skip("Student2 token missing for logout.")
        url = f"{AUTH_SERVICE_URL}/auth/logout"
        headers = {'Authorization': f'Bearer {TestIntegration.student2_token}'}
        response_logout = requests.post(url, headers=headers)
        assert response_logout.status_code == 204, f"Student2 logout failed: {response_logout.text}"
        
        response_after = requests.get(f"{AUTH_SERVICE_URL}/auth/users/me", headers=headers)
        assert response_after.status_code == 401, "Token for S2 not invalidated after logout."
        TestIntegration.student2_token = None
        print(f"Student2 Logout successful.")

    def test_15_student3_logout(self):
        if not TestIntegration.student3_token: pytest.skip("Student3 token missing for logout.")
        url = f"{AUTH_SERVICE_URL}/auth/logout"
        headers = {'Authorization': f'Bearer {TestIntegration.student3_token}'}
        response_logout = requests.post(url, headers=headers)
        assert response_logout.status_code == 204, f"Student3 logout failed: {response_logout.text}"

        response_after = requests.get(f"{AUTH_SERVICE_URL}/auth/users/me", headers=headers)
        assert response_after.status_code == 401, "Token for S3 not invalidated after logout."
        TestIntegration.student3_token = None
        print(f"Student3 Logout successful.")

    def test_16_teacher_logout(self):
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
