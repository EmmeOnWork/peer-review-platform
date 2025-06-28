import os
import random
import uuid
import io
import string
from datetime import date, datetime, timezone, timedelta
from locust import HttpUser, TaskSet, task, between, events
import locust_plugins
import urllib3

# API paths for different services, accessed via an ingress/gateway
AUTH_API_PATH = "/auth/"
ASSIGNMENT_API_PATH = "/assignments"
SUBMISSION_API_PATH = "/submissions"
REVIEW_API_PATH = "/reviews/"
REPORT_API_PATH = "/reports/"

TEST_PASSWORD = "password123"

# Disable SSL warnings for local testing if needed
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Shared State Management ---
class SharedState:
    """Class to hold all shared data between Locust users."""
    def __init__(self):
        self.assignment_ids = []
        self.submission_ids_for_review = {}  # { assignment_id: [submission_id, ...] }
        self.available_student_serials = []

    def clear(self):
        """Reset the state at the start of a new test."""
        self.assignment_ids.clear()
        self.submission_ids_for_review.clear()
        self.available_student_serials.clear()

# Global instance of the shared state
shared_state = SharedState()

# --- Data Pools for User Generation ---
FIRST_NAMES_POOL = ["Mario", "Luigi", "Giovanni", "Paolo", "Maria", "Anna", "Sofia", "Giulia"]
LAST_NAMES_POOL = ["Rossi", "Ferrari", "Russo", "Bianchi", "Romano", "Gallo"]
CITIES_POOL = ["Roma", "Milano", "Napoli", "Torino"]
STREET_TYPES_POOL = ["Via", "Corso", "Piazza", "Viale"]
STREET_NAMES_POOL = ["Garibaldi", "Mazzini", "Roma", "Dante"]

# --- Helper Functions ---
def generate_unique_email(base="user"):
    return f"{base}.{uuid.uuid4().hex[:8]}@locust.example.com"

def _generate_cf_part(text, is_surname=True):
    text = text.upper().replace(" ", "")
    consonants = "".join(filter(lambda x: x in "BCDFGHJKLMNPQRSTVWXYZ", text))
    vowels = "".join(filter(lambda x: x in "AEIOU", text))
    if is_surname:
        return (consonants + vowels + "XXX")[:3]
    else: # name logic
        if len(consonants) >= 4:
            return consonants[0] + consonants[2] + consonants[3]
        return (consonants + vowels + "XXX")[:3]

def generate_improved_fiscal_code(name, surname):
    surname_code = _generate_cf_part(surname, is_surname=True)
    name_code = _generate_cf_part(name, is_surname=False)
    year_val = random.randint(50, 99) if random.choice([True, False]) else random.randint(0, datetime.now().year % 100 - 1)
    year_str = f"{year_val:02d}"
    month_code = random.choice(['A', 'B', 'C', 'D', 'E', 'H', 'L', 'M', 'P', 'R', 'S', 'T'])
    day_val = random.randint(1, 28)
    if random.choice([True, False]): day_val += 40
    day_str = f"{day_val:02d}"
    comune_letter = random.choice(string.ascii_uppercase)
    comune_digits = "".join(random.choices(string.digits, k=3))
    comune_code = comune_letter + comune_digits
    control_char = random.choice(string.ascii_uppercase)
    return f"{surname_code}{name_code}{year_str}{month_code}{day_str}{comune_code}{control_char}"

# --- Base User Behavior ---
class BaseLocustUser(HttpUser):
    abstract = True
    token = None
    serial_number = None
    user_role = None
    user_email = None

    def _register_or_login(self):
        first_name = random.choice(FIRST_NAMES_POOL)
        last_name = random.choice(LAST_NAMES_POOL)
        residence = f"{random.choice(CITIES_POOL)}, {random.choice(STREET_TYPES_POOL)} {random.choice(STREET_NAMES_POOL)}, {random.randint(1, 200)}"
        birth_date_obj = date(random.randint(1960, 2003), random.randint(1, 12), random.randint(1, 28))
        fiscal_code = generate_improved_fiscal_code(first_name, last_name)
        self.user_email = generate_unique_email(f"{first_name}.{last_name}".lower().replace(" ", ""))
        reg_data = {
            "name": first_name, "surname": last_name, "email": self.user_email, "password": TEST_PASSWORD,
            "role": self.user_role, "fiscalCode": fiscal_code, "birthDate": birth_date_obj.isoformat(),
            "residence": residence
        }

        registration_successful = False
        with self.client.post(f"{AUTH_API_PATH}register", json=reg_data, name=f"/{self.user_role}/register", catch_response=True) as response:
            if response.ok:
                self.serial_number = response.json().get('serialNumber')
                if self.user_role == "student" and self.serial_number and self.serial_number not in shared_state.available_student_serials:
                    shared_state.available_student_serials.append(self.serial_number)
                response.success()
                registration_successful = True
            elif response.status_code == 400 and ("already" in response.text.lower()):
                response.success() # Treat "already exists" as a success for login purposes
                registration_successful = True
            else:
                response.failure(f"Registration failed: {response.status_code} - {response.text}")

        if not registration_successful:
            return False

        login_data = {"email": self.user_email, "password": TEST_PASSWORD}
        with self.client.post(f"{AUTH_API_PATH}login", json=login_data, name=f"/{self.user_role}/login", catch_response=True) as response:
            if response.ok:
                login_json = response.json()
                self.token = login_json.get('access_token') or login_json.get('token')
                user_data = login_json.get('user', {})
                if not self.serial_number:
                     self.serial_number = user_data.get('serialNumber')
                     if self.user_role == "student" and self.serial_number and self.serial_number not in shared_state.available_student_serials:
                         shared_state.available_student_serials.append(self.serial_number)
                response.success()
                return True
            else:
                response.failure(f"Login failed for {self.user_email}: {response.status_code} - {response.text}")
                return False

    def on_start(self):
        self.client.verify = False # Disable SSL verification if using self-signed certs
        if not self._register_or_login() or not self.token:
            print(f"Stopping user {self.user_email} due to failed registration/login.")
            self.stop(True)

    def on_stop(self):
        if self.token:
            with self.client.post(f"{AUTH_API_PATH}logout", headers=self.get_auth_headers(), name=f"/{self.user_role}/logout", catch_response=True) as response:
                if response.status_code in [200, 204]: response.success()
                else: response.failure(f"Logout failed: {response.status_code}")
            self.token = None

    def get_auth_headers(self):
        return {'Authorization': f'Bearer {self.token}'} if self.token else None

# --- Teacher User Tasks ---
class TeacherTasks(TaskSet):
    # This rubric is used to create assignments. It must match the one used by students for submissions.
    assignment_rubric = [{"criterion": "Completeness", "maxScore": 10}, {"criterion": "Quality", "maxScore": 10}]

    @task(10)
    def create_assignment(self):
        """Creates a new assignment and adds its ID to the shared state for students to use."""
        headers = self.user.get_auth_headers()
        if not headers: return
        
        # Need at least 3 students to create a meaningful assignment for this test
        potential_students = [s for s in shared_state.available_student_serials]
        if len(potential_students) < 3: return
        
        assignment_data = {
            "title": f"Locust Assignment {uuid.uuid4().hex[:6]}",
            "description": "Automated performance test assignment.",
            "deadline": (datetime.now(timezone.utc) + timedelta(days=random.randint(1, 5))).isoformat(),
            "rubric": self.assignment_rubric,
            "students": random.sample(potential_students, 3)
        }
        
        with self.user.client.post(ASSIGNMENT_API_PATH, json=assignment_data, headers=headers, name="/teacher/create_assignment", catch_response=True) as response:
            if response.ok:
                assignment_id = response.json().get('id') or response.json().get('_id')
                if assignment_id:
                    shared_state.assignment_ids.append(assignment_id)
                    response.success()
                else: response.failure("Create assignment OK but no ID in response")
            else: response.failure(f"Create assignment failed: {response.status_code} - {response.text}")

    @task(5)
    def auto_assign_peer_reviews(self):
        """Picks a random assignment and triggers auto-assignment of peer reviews."""
        headers = self.user.get_auth_headers()
        if not headers or not shared_state.assignment_ids: return

        assignment_id_to_review = random.choice(shared_state.assignment_ids)
        # Check if there are enough submissions for this assignment to make the call meaningful
        submissions_for_assignment = shared_state.submission_ids_for_review.get(assignment_id_to_review, [])
        if len(submissions_for_assignment) < 2: return

        with self.user.client.post(f"{REVIEW_API_PATH}assign/auto", json={"assignmentId": assignment_id_to_review, "minReviews": 1}, headers=headers, name="/teacher/auto_assign_reviews", catch_response=True) as response:
            if response.ok: response.success()
            elif response.status_code in [400, 404]: response.success() # Non-critical failures (e.g., no submissions)
            else: response.failure(f"Auto-assign reviews failed: {response.status_code} - {response.text}")

    @task(3)
    def get_teacher_report(self):
        """Fetches the aggregated report for all assignments created by the teacher."""
        headers = self.user.get_auth_headers()
        if not headers or not self.user.serial_number: return

        with self.user.client.get(f"{REPORT_API_PATH}teacher/{self.user.serial_number}", headers=headers, name="/teacher/get_report", catch_response=True) as response:
            if response.ok: response.success()
            else: response.failure(f"Get teacher report failed: {response.status_code}")

    @task(2)
    def get_own_profile(self):
        headers = self.user.get_auth_headers()
        if not headers: return
        with self.user.client.get(f"{AUTH_API_PATH}users/me", headers=headers, name="/teacher/get_profile", catch_response=True) as response:
            if response.ok: response.success()
            else: response.failure(f"Get teacher profile failed: {response.status_code}")

# --- Student User Tasks ---
class StudentTasks(TaskSet):
    
    # This rubric must be consistent with the one the teacher uses.
    assignment_rubric = [{"criterion": "Completeness", "maxScore": 10}, {"criterion": "Quality", "maxScore": 10}]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Local list to track submissions made by this specific student instance
        self.submitted_ids = []

    @task(10)
    def submit_assignment(self):
        """Submits work for a random assignment available in the shared state."""
        headers = self.user.get_auth_headers()
        if not headers or not self.user.serial_number or not shared_state.assignment_ids: return

        target_assignment_id = random.choice(shared_state.assignment_ids)
        files = {'attachments': (f'student_{self.user.serial_number}_submission.txt', io.BytesIO(b"Locust submission content."), 'text/plain')}
        data = {'assignmentId': target_assignment_id, 'text': f'Submission by {self.user.serial_number}'}

        with self.user.client.post(SUBMISSION_API_PATH, data=data, files=files, headers=headers, name="/student/submit_assignment", catch_response=True) as response:
            if response.ok:
                submission_json = response.json()
                submission_id = submission_json.get('submissionId')
                if submission_id:
                    # Add to global state for teachers to assign reviews
                    if target_assignment_id not in shared_state.submission_ids_for_review:
                        shared_state.submission_ids_for_review[target_assignment_id] = []
                    if submission_id not in shared_state.submission_ids_for_review[target_assignment_id]:
                         shared_state.submission_ids_for_review[target_assignment_id].append(submission_id)
                    # Add to local state for this student to check their report later
                    if submission_id not in self.submitted_ids:
                        self.submitted_ids.append(submission_id)
                    response.success()
                else: response.failure("Submission OK but no submissionId in response")
            elif response.status_code == 400 and "already submitted" in response.text.lower(): response.success()
            elif response.status_code in [403, 404]: response.success() # Non-critical failure (e.g., student not in assignment)
            else: response.failure(f"Submit assignment failed: {response.status_code} - {response.text}")

    @task(5)
    def list_and_submit_assigned_review(self):
        """Lists assigned reviews and submits one that is not yet completed."""
        headers = self.user.get_auth_headers()
        if not headers or not self.user.serial_number: return

        # 1. Get list of assigned reviews
        review_to_process_id = None
        with self.user.client.get(f"{REVIEW_API_PATH}student/{self.user.serial_number}", headers=headers, name="/student/list_reviews", catch_response=True) as response:
            if not response.ok:
                response.failure(f"List student reviews failed: {response.status_code} - {response.text}")
                return
            
            assigned_reviews = response.json()
            if isinstance(assigned_reviews, list) and assigned_reviews:
                unsubmitted = [r for r in assigned_reviews if not r.get('submittedAt')]
                if unsubmitted:
                    review_to_process_id = random.choice(unsubmitted).get('reviewId')
            response.success()
        
        if not review_to_process_id: return

        # 2. Submit the review using the predefined rubric
        evaluation_payload = []
        for criterion in self.assignment_rubric:
            max_score = criterion.get("maxScore", 10)
            score = random.randint(1, max_score)
            evaluation_payload.append({"criterion": criterion.get("criterion"), "score": score, "feedback": "Auto-generated feedback."})
        
        with self.user.client.put(f"{REVIEW_API_PATH}{review_to_process_id}", json={"evaluation": evaluation_payload}, headers=headers, name="/student/submit_review", catch_response=True) as response:
            if response.ok: response.success()
            elif response.status_code == 400 and "already been submitted" in response.text.lower(): response.success()
            else: response.failure(f"Submit review {review_to_process_id} failed: {response.status_code}")

    @task(3)
    def get_submission_report(self):
        """Fetches the anonymous report for one of the student's own submissions."""
        headers = self.user.get_auth_headers()
        if not headers or not self.user.serial_number or not self.submitted_ids: return

        submission_id_to_check = random.choice(self.submitted_ids)
        url = f"{REPORT_API_PATH}student/{self.user.serial_number}/submissions/{submission_id_to_check}"
        with self.user.client.get(url, headers=headers, name="/student/get_submission_report", catch_response=True) as response:
            if response.ok:
                # The response should contain reviews, average score, etc.
                response.success()
            else:
                response.failure(f"Get submission report failed: {response.status_code}")

    @task(2)
    def get_own_profile(self):
        headers = self.user.get_auth_headers()
        if not headers: return
        with self.user.client.get(f"{AUTH_API_PATH}users/me", headers=headers, name="/student/get_profile", catch_response=True) as response:
            if response.ok: response.success()
            else: response.failure(f"Get student profile failed: {response.status_code}")

# --- User Classes ---
class TeacherUser(BaseLocustUser):
    wait_time = between(2, 5)
    user_role = "teacher"
    tasks = [TeacherTasks]
    weight = 1

class StudentUser(BaseLocustUser):
    wait_time = between(1, 3)
    user_role = "student"
    tasks = [StudentTasks]
    weight = 4 # Increased weight as there are typically more students than teachers

# Optional: A simple user to hit the frontend/public endpoints
class FrontendUser(HttpUser):
    wait_time = between(1, 3)
    tasks = [] # Disable default tasks
    
    @task(10)
    def health_check(self):
        # Assuming your gateway exposes a general health check
        self.client.get("/health", name="/health/frontend", verify=False)

    @task(5)
    def load_homepage(self):
        # Assuming the root path serves a frontend
        self.client.get("/", name="GET /", verify=False)

# --- Event Hooks ---
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("--- Locust Test Starting ---")
    shared_state.clear()
    print("Shared state cleared.")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("--- Locust Test Stopping ---")