# Load Testing and Performance Benchmarking

This directory contains comprehensive load testing tools and scenarios for the Universal Workshop ERP system.

## Tools Included

### 1. Locust Load Testing (`locust_workshop_tests.py`)
- Python-based event-driven load testing
- Realistic workshop user scenarios
- Real-time monitoring via web UI

### 2. JMeter Test Plans (`jmeter/`)
- GUI-based test plans for different scenarios
- Workshop workflow simulation
- Detailed reporting and analysis

### 3. Artillery Test Scripts (`artillery/`)
- Lightweight JavaScript/YAML-based scenarios
- High-concurrency API testing
- CI/CD integration ready

### 4. Custom Performance Testing (`performance_tests.py`)
- Database stress testing
- Background job queue testing
- System resource monitoring

## Usage

### Quick Start with Locust
```bash
# Install dependencies
pip install locust requests

# Run load test
locust -f locust_workshop_tests.py --host=http://localhost:8000

# Open web UI at http://localhost:8089
```

### Running JMeter Tests
```bash
# GUI mode
jmeter -t jmeter/workshop_load_test.jmx

# Command line mode
jmeter -n -t jmeter/workshop_load_test.jmx -l results.jtl
```

### Artillery Tests
```bash
# Install Artillery
npm install -g artillery

# Run test
artillery run artillery/api_load_test.yml
```

## Test Scenarios

1. **Customer Registration & Booking Flow**
   - Concurrent customer registrations
   - Appointment booking stress test
   - Vehicle registration load

2. **Technician Workflow Simulation**
   - Job status updates
   - Parts inventory updates
   - Photo uploads and reports

3. **Administrative Operations**
   - Report generation under load
   - Invoice processing
   - Inventory management

4. **Database Stress Testing**
   - Concurrent read/write operations
   - Background job queue stress
   - Cache performance validation

## Performance Metrics

- Response time (average, 95th percentile, max)
- Throughput (requests/second)
- Error rate and failure analysis
- Database query performance
- Background job processing times
- System resource utilization

## Monitoring

The tests include comprehensive monitoring of:
- CPU and memory usage
- Database connection pools
- Redis cache performance
- Background worker queues
- Network I/O and disk usage
