"""
tests/load/locustfile.py
Load test using Locust.
Run: locust -f tests/load/locustfile.py --host=http://localhost:5000

Scenarios:
  - Health check (lightweight)
  - Create conversation + send message
  - Generate budget plan
"""
from locust import HttpUser, task, between
import json


class WanderAIUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Login and get auth token."""
        resp = self.client.post(
            "/api/v1/auth/login",
            json={"email": "loadtest@wanderai.app", "password": "LoadTest1234"},
            name="auth/login",
        )
        if resp.status_code == 200:
            data = resp.json()
            token = data.get("data", {}).get("access_token", "")
            self.headers = {"Authorization": f"Bearer {token}"}
        else:
            self.headers = {}

    @task(3)
    def health_check(self):
        self.client.get("/api/v1/health", name="health")

    @task(2)
    def create_and_chat(self):
        # Create conversation
        resp = self.client.post(
            "/api/v1/conversations",
            json={"context_mode": "general"},
            headers=self.headers,
            name="conversations/create",
        )
        if resp.status_code == 201:
            conv_id = resp.json()["data"]["id"]
            # Send message
            self.client.post(
                f"/api/v1/conversations/{conv_id}/messages",
                json={"message": "What are the best beaches in Thailand?"},
                headers=self.headers,
                name="conversations/send_message",
            )

    @task(1)
    def get_budget(self):
        self.client.post(
            "/api/v1/budget",
            json={"destination": "Tokyo", "days": 7, "travelers": 2, "budget_total": 3000, "travel_style": "mid-range"},
            headers=self.headers,
            name="budget/generate",
        )
