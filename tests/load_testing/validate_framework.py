#!/usr/bin/env python3
"""
Load Testing Framework Validation and Demo
==========================================

This script validates the comprehensive load testing framework and demonstrates
all available testing capabilities.
"""

import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))


def validate_framework_structure():
    """Validate that all framework components are in place"""
    print("🔍 Validating Load Testing Framework Structure...")
    
    test_dir = Path(__file__).parent
    required_files = [
        "README.md",
        "locust_workshop_tests.py",
        "performance_tests.py",
        "run_load_tests.py",
        "simple_validation_test.py",
        "artillery/api_load_test.yml",
        "artillery/test_data.csv",
        "artillery/README.md",
        "jmeter/README.md"
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = test_dir / file_path
        if not full_path.exists():
            missing_files.append(file_path)
        else:
            print(f"  ✅ {file_path}")
    
    if missing_files:
        print(f"  ❌ Missing files: {', '.join(missing_files)}")
        return False
    
    print("  ✅ All framework components present")
    return True


def validate_dependencies():
    """Validate that required dependencies are available"""
    print("\n📦 Validating Dependencies...")
    
    dependencies = {
        "locust": "pip install locust",
        "psutil": "pip install psutil", 
        "requests": "pip install requests"
    }
    
    missing_deps = []
    for dep, install_cmd in dependencies.items():
        try:
            __import__(dep)
            print(f"  ✅ {dep}")
        except ImportError:
            print(f"  ❌ {dep} - Install with: {install_cmd}")
            missing_deps.append(dep)
    
    # Check external tools
    external_tools = {
        "artillery": "npm install -g artillery",
        "jmeter": "Download from https://jmeter.apache.org/"
    }
    
    for tool, install_info in external_tools.items():
        import subprocess
        try:
            result = subprocess.run([tool, "--version"], capture_output=True, timeout=5)
            if result.returncode == 0:
                print(f"  ✅ {tool}")
            else:
                print(f"  ⚠️ {tool} - {install_info}")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            print(f"  ⚠️ {tool} - {install_info}")
    
    return len(missing_deps) == 0


def demonstrate_performance_monitoring():
    """Demonstrate system performance monitoring"""
    print("\n🔍 Demonstrating Performance Monitoring...")
    
    try:
        from performance_tests import SystemMonitor
        
        monitor = SystemMonitor("demo_metrics.json")
        print("  🚀 Starting 15-second monitoring demo...")
        
        monitor_thread = monitor.start_monitoring(15)
        
        # Simulate some activity
        for i in range(3):
            time.sleep(5)
            print(f"  📊 Monitoring... {(i+1)*5}/15 seconds")
        
        monitor.stop_monitoring()
        monitor_thread.join(timeout=5)
        
        print("  ✅ Performance monitoring demo completed")
        
        # Show sample metrics if file exists
        if Path("demo_metrics.json").exists():
            with open("demo_metrics.json", 'r') as f:
                data = json.load(f)
                if data.get("summary"):
                    summary = data["summary"]
                    print(f"  📈 Average CPU: {summary['cpu']['avg']:.1f}%")
                    print(f"  💾 Average Memory: {summary['memory']['avg']:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Performance monitoring failed: {e}")
        return False


def demonstrate_locust_validation():
    """Demonstrate Locust framework validation"""
    print("\n🐝 Demonstrating Locust Framework...")
    
    try:
        import subprocess
        
        # Run a very short validation test
        cmd = [
            "locust",
            "-f", "simple_validation_test.py",
            "--host", "http://localhost:8000",
            "--users", "3",
            "--spawn-rate", "1",
            "--run-time", "5s",
            "--headless"
        ]
        
        print("  🚀 Running 5-second Locust validation...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("  ✅ Locust framework validation successful")
            # Extract key info from output
            lines = result.stdout.split('\n')
            for line in lines:
                if "Starting Locust" in line or "Shutting down" in line:
                    print(f"  📝 {line.split('/')[-1]}")
            return True
        else:
            print(f"  ❌ Locust validation failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("  ⏰ Locust validation timed out")
        return False
    except FileNotFoundError:
        print("  ❌ Locust not found. Install with: pip install locust")
        return False
    except Exception as e:
        print(f"  ❌ Locust validation error: {e}")
        return False


def display_framework_capabilities():
    """Display comprehensive framework capabilities"""
    print("\n🚀 LOAD TESTING FRAMEWORK CAPABILITIES")
    print("="*60)
    
    capabilities = {
        "🐝 Locust Load Testing": [
            "Python-based event-driven load testing",
            "Realistic workshop user scenarios (Customer, Technician, Admin)",
            "Concurrent user simulation (10-500+ users)",
            "Arabic/English bilingual test data",
            "Real-time monitoring via web UI at http://localhost:8089",
            "Detailed response time and throughput metrics"
        ],
        "🎯 Artillery API Testing": [
            "JavaScript/YAML-based high-concurrency testing",
            "Multi-phase load testing (warm-up, load, stress)",
            "CSV-driven realistic test data",
            "Workshop workflow simulation",
            "CI/CD pipeline integration ready",
            "Comprehensive HTML reports"
        ],
        "📊 Performance Monitoring": [
            "Real-time system resource monitoring",
            "CPU, memory, disk, and network metrics",
            "Database connection and query monitoring",
            "Background job queue performance",
            "Automated report generation",
            "Custom performance benchmarking"
        ],
        "🔧 JMeter Integration": [
            "GUI-based test plan development",
            "Complex workflow scripting",
            "Parameterized test scenarios",
            "Detailed transaction analysis",
            "Plugin ecosystem support",
            "Enterprise-grade reporting"
        ],
        "🎮 Test Orchestration": [
            "Multi-tool test execution",
            "Predefined test profiles (light, medium, heavy, stress)",
            "Comprehensive result aggregation",
            "HTML report generation",
            "Session-based result organization",
            "Command-line automation"
        ]
    }
    
    for category, features in capabilities.items():
        print(f"\n{category}")
        for feature in features:
            print(f"  • {feature}")
    
    print(f"\n📈 TESTING SCENARIOS")
    print("="*30)
    
    scenarios = {
        "Customer Workflows": [
            "Registration with Arabic/English names",
            "Vehicle registration and management",
            "Appointment booking and scheduling",
            "Service history viewing",
            "Invoice and payment processing"
        ],
        "Technician Operations": [
            "Job assignment and status updates",
            "Parts inventory management",
            "Service completion reporting",
            "Photo uploads and documentation",
            "Time tracking and efficiency metrics"
        ],
        "Administrative Tasks": [
            "Report generation under load",
            "Inventory management operations",
            "Purchase order processing",
            "User management and permissions",
            "System configuration updates"
        ],
        "System Integration": [
            "Database stress testing",
            "Background job queue performance",
            "API endpoint load testing",
            "Cache performance validation",
            "Error handling and recovery"
        ]
    }
    
    for category, tests in scenarios.items():
        print(f"\n{category}:")
        for test in tests:
            print(f"  • {test}")


def display_usage_examples():
    """Display usage examples for all tools"""
    print(f"\n💡 USAGE EXAMPLES")
    print("="*50)
    
    examples = {
        "Quick Load Test": [
            "# Light load testing (10 users, 5 minutes)",
            "python run_load_tests.py --profile light",
            "",
            "# Heavy load testing (200 users, 30 minutes)",
            "python run_load_tests.py --profile heavy"
        ],
        "Specific Tools": [
            "# Run only Locust tests",
            "python run_load_tests.py --tools locust",
            "",
            "# Run only performance monitoring",
            "python run_load_tests.py --tools performance --duration 10m"
        ],
        "Custom Configurations": [
            "# Custom target server",
            "python run_load_tests.py --target http://production-server:8000",
            "",
            "# Disable monitoring",
            "python run_load_tests.py --no-monitoring"
        ],
        "Individual Tools": [
            "# Direct Locust execution",
            "locust -f locust_workshop_tests.py --host=http://localhost:8000",
            "",
            "# Artillery API testing",
            "artillery run artillery/api_load_test.yml",
            "",
            "# Performance monitoring only",
            "python performance_tests.py --test=system_monitor --duration=600"
        ]
    }
    
    for category, commands in examples.items():
        print(f"\n{category}:")
        for command in commands:
            if command.startswith("#"):
                print(f"  {command}")
            elif command:
                print(f"    {command}")
            else:
                print()


def main():
    """Main validation and demonstration function"""
    print("🏭 UNIVERSAL WORKSHOP ERP - LOAD TESTING FRAMEWORK")
    print("="*80)
    print("Comprehensive Load Testing and Performance Benchmarking Suite")
    print("="*80)
    
    # Run validation tests
    structure_ok = validate_framework_structure()
    deps_ok = validate_dependencies()
    
    if structure_ok and deps_ok:
        print("\n✅ Framework validation successful! Running demonstrations...")
        
        # Run demonstrations
        perf_ok = demonstrate_performance_monitoring()
        locust_ok = demonstrate_locust_validation()
        
        print(f"\n📊 VALIDATION RESULTS")
        print("="*30)
        print(f"Framework Structure: {'✅ PASS' if structure_ok else '❌ FAIL'}")
        print(f"Dependencies: {'✅ PASS' if deps_ok else '❌ FAIL'}")
        print(f"Performance Monitoring: {'✅ PASS' if perf_ok else '❌ FAIL'}")
        print(f"Locust Framework: {'✅ PASS' if locust_ok else '❌ FAIL'}")
        
        # Display capabilities and usage
        display_framework_capabilities()
        display_usage_examples()
        
        print(f"\n🎯 NEXT STEPS")
        print("="*20)
        print("1. Start your Universal Workshop ERP server")
        print("2. Run load tests: python run_load_tests.py --profile medium")
        print("3. Review results in the generated reports")
        print("4. Optimize based on performance bottlenecks")
        print("5. Repeat testing with different profiles")
        
        success_rate = sum([structure_ok, deps_ok, perf_ok, locust_ok]) / 4 * 100
        print(f"\n🏆 Overall Framework Health: {success_rate:.0f}%")
        
        if success_rate >= 75:
            print("✅ Framework is ready for comprehensive load testing!")
        else:
            print("⚠️ Some components need attention before full testing")
    
    else:
        print("\n❌ Framework validation failed. Please check the issues above.")
        sys.exit(1)
    
    # Cleanup demo files
    demo_files = ["demo_metrics.json"]
    for file in demo_files:
        if Path(file).exists():
            os.remove(file)


if __name__ == "__main__":
    main()
