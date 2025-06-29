#!/usr/bin/env python3
"""
Universal Workshop ERP - Performance Testing Suite
Load testing for authentication and session management using Locust
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add Frappe to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../apps/frappe'))

from locust import HttpUser, task, between, events
from locust.runners import MasterRunner, WorkerRunner
import frappe
from frappe.auth import LoginManager
import random
import string
import uuid


class UniversalWorkshopUser(HttpUser):
    """
    Simulate realistic user behavior for Universal Workshop ERP
    """
    wait_time = between(1, 5)  # Wait 1-5 seconds between requests
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auth_token = None
        self.session_data = {}
        self.user_role = None
        self.test_metrics = {
            'login_attempts': 0,
            'successful_logins': 0,
            'failed_logins': 0,
            'session_requests': 0,
            'navigation_requests': 0
        }
    
    def on_start(self):
        """Initialize user session"""
        self.authenticate_user()
    
    def on_stop(self):
        """Cleanup user session"""
        self.logout_user()
        self.log_test_metrics()
    
    def authenticate_user(self):
        """Perform user authentication"""
        # Simulate different user types
        user_types = [
            {'username': 'workshop_admin', 'role': 'Workshop Admin'},
            {'username': 'technician', 'role': 'Technician'},
            {'username': 'customer_service', 'role': 'Customer Service'},
            {'username': 'inventory_manager', 'role': 'Inventory Manager'},
            {'username': 'workshop_owner', 'role': 'Workshop Owner'}
        ]
        
        # Select random user type for this session
        selected_user = random.choice(user_types)
        self.user_role = selected_user['role']
        
        # Generate unique test user credentials
        test_username = f"test_{selected_user['username']}_{random.randint(1000, 9999)}"
        test_password = f"test_password_{random.randint(1000, 9999)}"
        
        self.test_metrics['login_attempts'] += 1
        
        start_time = time.time()
        
        try:
            # First, get login page to simulate real user behavior
            login_page_response = self.client.get("/login")
            
            if login_page_response.status_code == 200:
                # Extract CSRF token if present
                csrf_token = self.extract_csrf_token(login_page_response.text)
                
                # Prepare login data
                login_data = {
                    'cmd': 'login',
                    'usr': test_username,
                    'pwd': test_password
                }
                
                if csrf_token:
                    login_data['csrf_token'] = csrf_token
                
                # Perform login request
                login_response = self.client.post(
                    "/api/method/login",
                    data=login_data,
                    headers={
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                )
                
                auth_latency = time.time() - start_time
                
                if login_response.status_code == 200:
                    try:
                        response_data = login_response.json()
                        if response_data.get('message') == 'Logged In':
                            self.auth_token = login_response.cookies.get('sid')
                            self.test_metrics['successful_logins'] += 1
                            
                            # Log successful authentication
                            events.request.fire(
                                request_type="AUTH",
                                name="user_login_success",
                                response_time=auth_latency * 1000,
                                response_length=len(login_response.content),
                                context={
                                    'user_role': self.user_role,
                                    'auth_latency': auth_latency
                                }
                            )
                            
                            print(f"✅ User authenticated: {self.user_role} (latency: {auth_latency:.3f}s)")
                            return True
                            
                    except json.JSONDecodeError:
                        pass
                
                self.test_metrics['failed_logins'] += 1
                
                # Log failed authentication
                events.request.fire(
                    request_type="AUTH",
                    name="user_login_failure",
                    response_time=auth_latency * 1000,
                    response_length=len(login_response.content) if login_response else 0,
                    exception=Exception(f"Login failed for {self.user_role}")
                )
                
                print(f"❌ Authentication failed: {self.user_role} (status: {login_response.status_code})")
                
        except Exception as e:
            self.test_metrics['failed_logins'] += 1
            auth_latency = time.time() - start_time
            
            events.request.fire(
                request_type="AUTH",
                name="user_login_error",
                response_time=auth_latency * 1000,
                response_length=0,
                exception=e
            )
            
            print(f"💥 Authentication error: {self.user_role} - {str(e)}")
        
        return False
    
    def extract_csrf_token(self, html_content):
        """Extract CSRF token from HTML content"""
        import re
        csrf_pattern = r'name="csrf_token" value="([^"]+)"'
        match = re.search(csrf_pattern, html_content)
        return match.group(1) if match else None
    
    def logout_user(self):
        """Perform user logout"""
        if self.auth_token:
            try:
                logout_response = self.client.post("/api/method/logout")
                print(f"🚪 User logged out: {self.user_role}")
            except Exception as e:
                print(f"⚠️  Logout error: {e}")
    
    @task(10)
    def navigate_dashboard(self):
        """Simulate dashboard navigation"""
        if not self.auth_token:
            return
        
        self.test_metrics['navigation_requests'] += 1
        
        # Simulate different dashboard views based on user role
        dashboard_endpoints = {
            'Workshop Admin': ['/app/desk', '/app/workshop-dashboard', '/app/reports'],
            'Technician': ['/app/desk', '/app/work-order', '/app/task'],
            'Customer Service': ['/app/desk', '/app/customer', '/app/quotation'],
            'Inventory Manager': ['/app/desk', '/app/item', '/app/stock-ledger'],
            'Workshop Owner': ['/app/desk', '/app/dashboard-view', '/app/reports']
        }
        
        endpoints = dashboard_endpoints.get(self.user_role, ['/app/desk'])
        endpoint = random.choice(endpoints)
        
        start_time = time.time()
        
        try:
            response = self.client.get(
                endpoint,
                headers={'Authorization': f'token {self.auth_token}'}
            )
            
            navigation_time = time.time() - start_time
            
            events.request.fire(
                request_type="NAV",
                name=f"dashboard_{self.user_role.lower().replace(' ', '_')}",
                response_time=navigation_time * 1000,
                response_length=len(response.content),
                context={
                    'endpoint': endpoint,
                    'user_role': self.user_role
                }
            )
            
        except Exception as e:
            navigation_time = time.time() - start_time
            events.request.fire(
                request_type="NAV",
                name=f"dashboard_{self.user_role.lower().replace(' ', '_')}_error",
                response_time=navigation_time * 1000,
                response_length=0,
                exception=e
            )
    
    @task(5)
    def api_requests(self):
        """Simulate API requests"""
        if not self.auth_token:
            return
        
        self.test_metrics['session_requests'] += 1
        
        # Common API endpoints
        api_endpoints = [
            '/api/method/frappe.desk.form.load.getdoc',
            '/api/method/frappe.client.get_list',
            '/api/method/frappe.desk.reportview.get',
            '/api/resource/User',
            '/api/resource/Customer'
        ]
        
        endpoint = random.choice(api_endpoints)
        
        start_time = time.time()
        
        try:
            response = self.client.get(
                endpoint,
                headers={
                    'Authorization': f'token {self.auth_token}',
                    'Content-Type': 'application/json'
                }
            )
            
            api_time = time.time() - start_time
            
            events.request.fire(
                request_type="API",
                name=f"api_request_{self.user_role.lower().replace(' ', '_')}",
                response_time=api_time * 1000,
                response_length=len(response.content),
                context={
                    'endpoint': endpoint,
                    'user_role': self.user_role
                }
            )
            
        except Exception as e:
            api_time = time.time() - start_time
            events.request.fire(
                request_type="API",
                name=f"api_request_{self.user_role.lower().replace(' ', '_')}_error",
                response_time=api_time * 1000,
                response_length=0,
                exception=e
            )
    
    @task(3)
    def session_validation(self):
        """Test session persistence and validation"""
        if not self.auth_token:
            return
        
        start_time = time.time()
        
        try:
            response = self.client.get(
                '/api/method/frappe.auth.get_logged_user',
                headers={'Authorization': f'token {self.auth_token}'}
            )
            
            session_time = time.time() - start_time
            
            if response.status_code == 200:
                events.request.fire(
                    request_type="SESSION",
                    name="session_validation_success",
                    response_time=session_time * 1000,
                    response_length=len(response.content),
                    context={'user_role': self.user_role}
                )
            else:
                # Session invalid, try to re-authenticate
                self.auth_token = None
                self.authenticate_user()
                
        except Exception as e:
            session_time = time.time() - start_time
            events.request.fire(
                request_type="SESSION",
                name="session_validation_error",
                response_time=session_time * 1000,
                response_length=0,
                exception=e
            )
    
    def log_test_metrics(self):
        """Log test metrics for this user"""
        metrics_summary = {
            'user_id': self.user_role,
            'timestamp': datetime.now().isoformat(),
            'metrics': self.test_metrics,
            'success_rate': (
                self.test_metrics['successful_logins'] / max(self.test_metrics['login_attempts'], 1)
            ) * 100
        }
        
        print(f"📊 User {self.user_role} metrics: {json.dumps(metrics_summary, indent=2)}")


# Performance monitoring event handlers
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts"""
    print("🚀 Universal Workshop Performance Test Started")
    print(f"Target: {environment.host}")
    print(f"Users: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'Unknown'}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops"""
    print("🏁 Universal Workshop Performance Test Completed")
    
    # Generate performance report
    generate_performance_report(environment)


def generate_performance_report(environment):
    """Generate comprehensive performance report"""
    stats = environment.runner.stats
    
    report = {
        'test_summary': {
            'timestamp': datetime.now().isoformat(),
            'duration': stats.total.get_response_time_percentile(0.95),
            'total_requests': stats.total.num_requests,
            'total_failures': stats.total.num_failures,
            'average_response_time': stats.total.avg_response_time,
            'min_response_time': stats.total.min_response_time,
            'max_response_time': stats.total.max_response_time
        },
        'authentication_metrics': {},
        'performance_percentiles': {
            '50th': stats.total.get_response_time_percentile(0.5),
            '75th': stats.total.get_response_time_percentile(0.75),
            '90th': stats.total.get_response_time_percentile(0.9),
            '95th': stats.total.get_response_time_percentile(0.95),
            '99th': stats.total.get_response_time_percentile(0.99)
        },
        'request_breakdown': {}
    }
    
    # Breakdown by request type
    for stat in stats.entries.values():
        request_type = stat.name.split('_')[0] if '_' in stat.name else 'other'
        
        if request_type not in report['request_breakdown']:
            report['request_breakdown'][request_type] = {
                'count': 0,
                'avg_response_time': 0,
                'failure_rate': 0
            }
        
        report['request_breakdown'][request_type]['count'] += stat.num_requests
        report['request_breakdown'][request_type]['avg_response_time'] = stat.avg_response_time
        report['request_breakdown'][request_type]['failure_rate'] = (
            stat.num_failures / max(stat.num_requests, 1) * 100
        )
    
    # Save report to file
    report_dir = Path('test_results/performance')
    report_dir.mkdir(parents=True, exist_ok=True)
    
    report_file = report_dir / f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"📊 Performance report saved: {report_file}")
    
    # Print summary
    print("\n🎯 PERFORMANCE TEST SUMMARY")
    print("=" * 50)
    print(f"Total Requests: {report['test_summary']['total_requests']}")
    print(f"Total Failures: {report['test_summary']['total_failures']}")
    print(f"Average Response Time: {report['test_summary']['average_response_time']:.2f}ms")
    print(f"95th Percentile: {report['performance_percentiles']['95th']:.2f}ms")
    print(f"99th Percentile: {report['performance_percentiles']['99th']:.2f}ms")
    
    if report['test_summary']['total_requests'] > 0:
        failure_rate = (report['test_summary']['total_failures'] / report['test_summary']['total_requests']) * 100
        print(f"Failure Rate: {failure_rate:.2f}%")
        
        if failure_rate < 1:
            print("✅ Performance test PASSED (< 1% failure rate)")
        elif failure_rate < 5:
            print("⚠️  Performance test WARNING (1-5% failure rate)")
        else:
            print("❌ Performance test FAILED (> 5% failure rate)")


if __name__ == "__main__":
    print("Universal Workshop ERP - Performance Testing Suite")
    print("Use with: locust -f performance_test_suite.py --host=http://localhost:8000")
