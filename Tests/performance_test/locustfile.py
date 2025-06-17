import os
import random
import uuid
import io
import string
from datetime import date, datetime, timezone, timedelta
from locust import HttpUser, TaskSet, task, between, events
import locust_plugins
import urllib3

# Questi path devono corrispondere ESATTAMENTE ai blocchi `location` in nginx.conf
#AUTH_API_PATH = "/auth/"
#ASSIGNMENT_API_PATH = "/assignments/"
#SUBMISSION_API_PATH = "/submissions/"
#REVIEW_API_PATH = "/reviews/"

TEST_PASSWORD = "password123"

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("--- Load Test Starting (via Ingress) ---")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("--- Load Test Stopping ---")

class FrontendUser(HttpUser):
    wait_time = between(1, 3)

    @task(10)  # Maggiore peso per bombardare /health
    def health_check(self):
        self.client.get("/health/", name="GET /health/", verify=False)

    @task(5)
    def load_homepage(self):
        self.client.get("/", name="GET /", verify=False)

# Puoi aggiungere altri task per simulare navigazione su altre pagine della SPA

# --- Aggiungere qui la logica per testare i servizi backend ---

