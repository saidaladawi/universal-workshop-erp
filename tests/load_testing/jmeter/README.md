# JMeter Test Plans for Universal Workshop ERP

This directory contains JMeter test plans for comprehensive load testing of the Universal Workshop ERP system.

## Test Plans

### 1. `workshop_api_load_test.jmx`
- Comprehensive API load testing
- Customer, Vehicle, and Appointment workflows
- Configurable user load and ramp-up periods

### 2. `workshop_ui_load_test.jmx`
- Web UI load testing
- Browser-based user interactions
- Form submissions and page navigation

### 3. `workshop_stress_test.jmx`
- High-volume stress testing
- Database connection limits
- System resource exhaustion testing

## Usage

### GUI Mode (Recommended for test development)
```bash
# Open JMeter GUI
jmeter

# Load test plan
File → Open → select .jmx file

# Configure test parameters in Test Plan
# Run test with green play button
```

### Command Line Mode (Recommended for automated testing)
```bash
# Run API load test
jmeter -n -t workshop_api_load_test.jmx -l api_results.jtl -e -o api_report/

# Run UI load test  
jmeter -n -t workshop_ui_load_test.jmx -l ui_results.jtl -e -o ui_report/

# Run stress test
jmeter -n -t workshop_stress_test.jmx -l stress_results.jtl -e -o stress_report/
```

## Configuration

### Test Parameters
- **Number of Threads (Users)**: 1-500
- **Ramp-up Period**: 60-300 seconds
- **Loop Count**: 1-100 iterations
- **Duration**: 5-60 minutes

### Endpoints Tested
- `/api/resource/Customer` (CRUD operations)
- `/api/resource/Vehicle` (CRUD operations)
- `/api/resource/Appointment` (CRUD operations)
- `/api/resource/Service Order` (CRUD operations)
- `/api/resource/Sales Invoice` (CRUD operations)
- `/api/method/login` (Authentication)
- Report generation endpoints

## Results Analysis

JMeter generates comprehensive reports including:
- Response time percentiles
- Throughput (requests/second)
- Error rates and types
- Resource utilization graphs
- Detailed transaction analysis

## Best Practices

1. **Start Small**: Begin with 10-20 users to validate test plans
2. **Realistic Data**: Use production-like test data volumes
3. **Think Time**: Add realistic delays between user actions
4. **Monitor Resources**: Watch server CPU, memory, and database during tests
5. **Baseline Testing**: Establish performance baselines before optimization
