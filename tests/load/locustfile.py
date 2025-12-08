"""
Locust Load Testing
Alternative to k6 for Python-based load testing
"""
from locust import HttpUser, task, between  # type: ignore

class VaultUser(HttpUser):
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Called when a user starts."""
        self.token = "test_token_123"
        self.document_id = "doc_test_123"
    
    @task(3)
    def health_check(self):
        """Health check - most common operation."""
        with self.client.get("/monitoring/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task(2)
    def get_share_bundle(self):
        """Get share bundle - critical path."""
        with self.client.get(f"/vault/share/{self.token}/bundle", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if "proof_type" in data:
                    response.success()
                else:
                    response.failure("Missing proof_type in response")
            elif response.status_code == 429:
                response.failure("Rate limited")
            else:
                response.failure(f"Unexpected status: {response.status_code}")
    
    @task(1)
    def get_metrics(self):
        """Get metrics."""
        with self.client.get("/monitoring/metrics", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Metrics failed: {response.status_code}")
    
    @task(1)
    def security_audit(self):
        """Security audit endpoint."""
        with self.client.get("/security/audit", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Security audit failed: {response.status_code}")

# Run with: locust -f locustfile.py --host=http://localhost:8000
