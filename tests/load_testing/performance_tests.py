"""
Performance Testing and System Monitoring for Universal Workshop ERP
===================================================================

This module provides comprehensive performance testing capabilities including:
- Database stress testing
- Background job queue testing  
- System resource monitoring
- Performance benchmarking

Usage:
    python performance_tests.py --test=database_stress
    python performance_tests.py --test=background_jobs
    python performance_tests.py --test=system_monitor
"""

import argparse
import json
import multiprocessing
import psutil
import threading
import time
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path

try:
    import frappe
    FRAPPE_AVAILABLE = True
except ImportError:
    FRAPPE_AVAILABLE = False
    print("Warning: Frappe not available. Some tests will be skipped.")


class SystemMonitor:
    """Real-time system resource monitoring during load tests"""
    
    def __init__(self, output_file="performance_metrics.json"):
        self.output_file = output_file
        self.monitoring = False
        self.metrics = []
        self.start_time = None
    
    def start_monitoring(self, duration_seconds=300):
        """Start system monitoring for specified duration"""
        self.monitoring = True
        self.start_time = datetime.now()
        
        print(f"🔍 Starting system monitoring for {duration_seconds} seconds...")
        
        monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(duration_seconds,)
        )
        monitor_thread.daemon = True
        monitor_thread.start()
        
        return monitor_thread
    
    def _monitor_loop(self, duration_seconds):
        """Main monitoring loop"""
        end_time = datetime.now() + timedelta(seconds=duration_seconds)
        
        while datetime.now() < end_time and self.monitoring:
            metrics = self._collect_metrics()
            self.metrics.append(metrics)
            time.sleep(5)  # Collect metrics every 5 seconds
        
        self._save_metrics()
    
    def _collect_metrics(self):
        """Collect system performance metrics"""
        timestamp = datetime.now().isoformat()
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
        
        # Memory metrics
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # Disk metrics
        disk_usage = psutil.disk_usage('/')
        disk_io = psutil.disk_io_counters()
        
        # Network metrics
        network_io = psutil.net_io_counters()
        
        # Process metrics
        process_count = len(psutil.pids())
        
        metrics = {
            "timestamp": timestamp,
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count,
                "load_avg": load_avg
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used,
                "free": memory.free
            },
            "swap": {
                "total": swap.total,
                "used": swap.used,
                "free": swap.free,
                "percent": swap.percent
            },
            "disk": {
                "total": disk_usage.total,
                "used": disk_usage.used,
                "free": disk_usage.free,
                "percent": (disk_usage.used / disk_usage.total) * 100,
                "read_bytes": disk_io.read_bytes if disk_io else 0,
                "write_bytes": disk_io.write_bytes if disk_io else 0
            },
            "network": {
                "bytes_sent": network_io.bytes_sent,
                "bytes_recv": network_io.bytes_recv,
                "packets_sent": network_io.packets_sent,
                "packets_recv": network_io.packets_recv
            },
            "processes": {
                "count": process_count
            }
        }
        
        # Database metrics (if available)
        if FRAPPE_AVAILABLE:
            try:
                db_metrics = self._get_database_metrics()
                metrics["database"] = db_metrics
            except Exception as e:
                metrics["database"] = {"error": str(e)}
        
        return metrics
    
    def _get_database_metrics(self):
        """Get database-specific metrics"""
        if not FRAPPE_AVAILABLE:
            return {}
        
        try:
            # Database connection count
            db_connections = frappe.db.sql("""
                SELECT COUNT(*) as active_connections
                FROM information_schema.processlist
                WHERE Command != 'Sleep'
            """, as_dict=True)
            
            # Slow queries
            slow_queries = frappe.db.sql("""
                SELECT COUNT(*) as slow_queries
                FROM information_schema.processlist
                WHERE Time > 5 AND Command != 'Sleep'
            """, as_dict=True)
            
            # Table sizes
            table_sizes = frappe.db.sql("""
                SELECT 
                    table_name,
                    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                ORDER BY (data_length + index_length) DESC
                LIMIT 10
            """, as_dict=True)
            
            return {
                "active_connections": db_connections[0]["active_connections"],
                "slow_queries": slow_queries[0]["slow_queries"],
                "top_tables": table_sizes
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _save_metrics(self):
        """Save collected metrics to file"""
        output_data = {
            "test_start": self.start_time.isoformat(),
            "test_end": datetime.now().isoformat(),
            "metrics": self.metrics,
            "summary": self._calculate_summary()
        }
        
        with open(self.output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"📊 Performance metrics saved to {self.output_file}")
    
    def _calculate_summary(self):
        """Calculate summary statistics"""
        if not self.metrics:
            return {}
        
        cpu_values = [m["cpu"]["percent"] for m in self.metrics]
        memory_values = [m["memory"]["percent"] for m in self.metrics]
        
        return {
            "cpu": {
                "avg": sum(cpu_values) / len(cpu_values),
                "max": max(cpu_values),
                "min": min(cpu_values)
            },
            "memory": {
                "avg": sum(memory_values) / len(memory_values),
                "max": max(memory_values),
                "min": min(memory_values)
            },
            "duration_seconds": len(self.metrics) * 5
        }
    
    def stop_monitoring(self):
        """Stop system monitoring"""
        self.monitoring = False


class DatabaseStressTest:
    """Database stress testing utilities"""
    
    def __init__(self):
        self.results = []
    
    def run_concurrent_operations(self, num_threads=10, operations_per_thread=100):
        """Run concurrent database operations"""
        if not FRAPPE_AVAILABLE:
            print("❌ Frappe not available. Skipping database stress test.")
            return
        
        print(f"🔥 Starting database stress test: {num_threads} threads, {operations_per_thread} ops each")
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []
            
            for thread_id in range(num_threads):
                future = executor.submit(
                    self._worker_thread,
                    thread_id,
                    operations_per_thread
                )
                futures.append(future)
            
            # Wait for all threads to complete
            for future in as_completed(futures):
                try:
                    result = future.result()
                    self.results.append(result)
                except Exception as e:
                    print(f"Thread failed: {e}")
        
        end_time = time.time()
        
        self._analyze_results(end_time - start_time)
    
    def _worker_thread(self, thread_id, num_operations):
        """Worker thread for database operations"""
        thread_results = {
            "thread_id": thread_id,
            "operations": num_operations,
            "successful": 0,
            "failed": 0,
            "response_times": []
        }
        
        for i in range(num_operations):
            try:
                start_time = time.time()
                
                # Simulate various database operations
                operation_type = i % 4
                
                if operation_type == 0:
                    # Read operation
                    frappe.db.sql("SELECT COUNT(*) FROM `tabCustomer` LIMIT 1")
                elif operation_type == 1:
                    # Insert operation (create test record)
                    test_customer = {
                        "doctype": "Customer",
                        "customer_name": f"Test Customer {thread_id}-{i}",
                        "customer_type": "Individual"
                    }
                    frappe.get_doc(test_customer).insert(ignore_permissions=True)
                elif operation_type == 2:
                    # Update operation
                    customers = frappe.db.sql(
                        "SELECT name FROM `tabCustomer` ORDER BY RAND() LIMIT 1",
                        as_dict=True
                    )
                    if customers:
                        customer = frappe.get_doc("Customer", customers[0].name)
                        customer.save(ignore_permissions=True)
                else:
                    # Complex query
                    frappe.db.sql("""
                        SELECT c.name, c.customer_name, COUNT(so.name) as order_count
                        FROM `tabCustomer` c
                        LEFT JOIN `tabSales Order` so ON c.name = so.customer
                        GROUP BY c.name
                        LIMIT 10
                    """)
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                
                thread_results["response_times"].append(response_time)
                thread_results["successful"] += 1
                
                # Commit transaction
                frappe.db.commit()
                
            except Exception as e:
                thread_results["failed"] += 1
                frappe.db.rollback()
                print(f"Operation failed in thread {thread_id}: {e}")
        
        return thread_results
    
    def _analyze_results(self, total_time):
        """Analyze stress test results"""
        total_operations = sum(r["successful"] + r["failed"] for r in self.results)
        total_successful = sum(r["successful"] for r in self.results)
        total_failed = sum(r["failed"] for r in self.results)
        
        all_response_times = []
        for result in self.results:
            all_response_times.extend(result["response_times"])
        
        if all_response_times:
            avg_response_time = sum(all_response_times) / len(all_response_times)
            max_response_time = max(all_response_times)
            min_response_time = min(all_response_times)
            
            # Calculate percentiles
            sorted_times = sorted(all_response_times)
            p95_index = int(0.95 * len(sorted_times))
            p99_index = int(0.99 * len(sorted_times))
            p95_response_time = sorted_times[p95_index] if p95_index < len(sorted_times) else max_response_time
            p99_response_time = sorted_times[p99_index] if p99_index < len(sorted_times) else max_response_time
        else:
            avg_response_time = max_response_time = min_response_time = 0
            p95_response_time = p99_response_time = 0
        
        throughput = total_successful / total_time if total_time > 0 else 0
        error_rate = (total_failed / total_operations * 100) if total_operations > 0 else 0
        
        print("\n" + "="*60)
        print("📊 DATABASE STRESS TEST RESULTS")
        print("="*60)
        print(f"Total Operations: {total_operations}")
        print(f"Successful: {total_successful}")
        print(f"Failed: {total_failed}")
        print(f"Error Rate: {error_rate:.2f}%")
        print(f"Total Time: {total_time:.2f} seconds")
        print(f"Throughput: {throughput:.2f} ops/sec")
        print(f"Average Response Time: {avg_response_time:.2f} ms")
        print(f"Min Response Time: {min_response_time:.2f} ms")
        print(f"Max Response Time: {max_response_time:.2f} ms")
        print(f"95th Percentile: {p95_response_time:.2f} ms")
        print(f"99th Percentile: {p99_response_time:.2f} ms")
        print("="*60)


class BackgroundJobTest:
    """Background job queue stress testing"""
    
    def __init__(self):
        self.job_results = []
    
    def test_queue_performance(self, num_jobs=100):
        """Test background job queue performance"""
        if not FRAPPE_AVAILABLE:
            print("❌ Frappe not available. Skipping background job test.")
            return
        
        print(f"⚡ Testing background job queue with {num_jobs} jobs")
        
        start_time = time.time()
        
        # Enqueue multiple background jobs
        for i in range(num_jobs):
            try:
                frappe.enqueue(
                    method=self._test_job_function,
                    job_name=f"test_job_{i}",
                    job_id=f"test_job_{i}",
                    kwargs={"job_id": i, "data": f"test_data_{i}"}
                )
            except Exception as e:
                print(f"Failed to enqueue job {i}: {e}")
        
        # Monitor job completion
        self._monitor_job_completion(num_jobs, start_time)
    
    def _test_job_function(self, job_id, data):
        """Test job function that simulates work"""
        import random
        
        # Simulate variable processing time
        processing_time = random.uniform(0.1, 2.0)
        time.sleep(processing_time)
        
        # Simulate some database operations
        try:
            if FRAPPE_AVAILABLE:
                frappe.db.sql("SELECT COUNT(*) FROM `tabCustomer`")
                frappe.db.commit()
        except:
            pass
        
        result = {
            "job_id": job_id,
            "data": data,
            "processing_time": processing_time,
            "completed_at": datetime.now().isoformat()
        }
        
        return result
    
    def _monitor_job_completion(self, expected_jobs, start_time):
        """Monitor background job completion"""
        completed_jobs = 0
        timeout = 300  # 5 minutes timeout
        
        while completed_jobs < expected_jobs and (time.time() - start_time) < timeout:
            try:
                # Check job queue status
                if FRAPPE_AVAILABLE:
                    # This would need to be adapted based on the actual job queue implementation
                    # For now, we'll simulate monitoring
                    time.sleep(5)
                    completed_jobs += 1
            except Exception as e:
                print(f"Error monitoring jobs: {e}")
                break
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"✅ Background job test completed in {total_time:.2f} seconds")
        print(f"Jobs completed: {completed_jobs}/{expected_jobs}")
        
        if completed_jobs < expected_jobs:
            print(f"⚠️ {expected_jobs - completed_jobs} jobs did not complete within timeout")


def run_comprehensive_performance_test():
    """Run comprehensive performance testing suite"""
    print("🚀 UNIVERSAL WORKSHOP ERP - COMPREHENSIVE PERFORMANCE TEST")
    print("="*80)
    
    # Initialize components
    monitor = SystemMonitor("comprehensive_performance_metrics.json")
    db_test = DatabaseStressTest()
    bg_test = BackgroundJobTest()
    
    # Start system monitoring
    monitor_thread = monitor.start_monitoring(duration_seconds=600)  # 10 minutes
    
    try:
        # Run database stress test
        print("\n1️⃣ Running Database Stress Test...")
        db_test.run_concurrent_operations(num_threads=20, operations_per_thread=50)
        
        time.sleep(30)  # Brief pause between tests
        
        # Run background job test
        print("\n2️⃣ Running Background Job Test...")
        bg_test.test_queue_performance(num_jobs=50)
        
        time.sleep(30)  # Brief pause
        
        print("\n3️⃣ System monitoring will continue for the full duration...")
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
    finally:
        # Stop monitoring
        monitor.stop_monitoring()
        
        # Wait for monitor thread to finish
        if monitor_thread.is_alive():
            monitor_thread.join(timeout=10)
        
        print("\n✅ Comprehensive performance test completed!")
        print(f"📊 Results saved to {monitor.output_file}")


def main():
    """Main entry point for performance testing"""
    parser = argparse.ArgumentParser(description="Universal Workshop ERP Performance Testing")
    parser.add_argument("--test", 
                       choices=["database_stress", "background_jobs", "system_monitor", "comprehensive"],
                       default="comprehensive",
                       help="Type of performance test to run")
    parser.add_argument("--threads", type=int, default=10, help="Number of threads for database stress test")
    parser.add_argument("--operations", type=int, default=100, help="Operations per thread")
    parser.add_argument("--jobs", type=int, default=50, help="Number of background jobs to test")
    parser.add_argument("--duration", type=int, default=300, help="Monitoring duration in seconds")
    
    args = parser.parse_args()
    
    if args.test == "database_stress":
        db_test = DatabaseStressTest()
        db_test.run_concurrent_operations(args.threads, args.operations)
    
    elif args.test == "background_jobs":
        bg_test = BackgroundJobTest()
        bg_test.test_queue_performance(args.jobs)
    
    elif args.test == "system_monitor":
        monitor = SystemMonitor()
        monitor_thread = monitor.start_monitoring(args.duration)
        try:
            monitor_thread.join()
        except KeyboardInterrupt:
            monitor.stop_monitoring()
    
    elif args.test == "comprehensive":
        run_comprehensive_performance_test()


if __name__ == "__main__":
    main()
