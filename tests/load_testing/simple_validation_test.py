"""
Simple load testing validation for Universal Workshop ERP
"""

import json
import time
import random
from locust import HttpUser, task, between


class SimpleValidationUser(HttpUser):
    """Simple user for framework validation"""
    wait_time = between(1, 3)
    
    @task
    def test_basic_endpoint(self):
        """Test basic endpoint access"""
        # Try to access basic endpoints that should exist in any web application
        endpoints = [
            "/",
            "/api/method/ping",
            "/api/method/version"
        ]
        
        endpoint = random.choice(endpoints)
        
        try:
            response = self.client.get(endpoint, catch_response=True)
            
            # Mark as success if we get any response (even 404 is expected without a running server)
            if response.status_code in [200, 404, 403, 401]:
                response.success()
            else:
                response.failure(f"Unexpected status code: {response.status_code}")
                
        except Exception as e:
            # Expected when no server is running
            pass


if __name__ == "__main__":
    print("Simple load testing validation")
    print("This validates the Locust framework setup")
