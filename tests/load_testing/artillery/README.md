# Artillery Load Testing for Universal Workshop ERP

This directory contains Artillery test configurations for comprehensive API load testing.

## Test Files

### `api_load_test.yml`
Main load testing configuration with three phases:
- **Warm-up**: 5 users/sec for 60 seconds
- **Load test**: 20 users/sec for 5 minutes  
- **Stress test**: 50 users/sec for 2 minutes

### `test_data.csv`
Realistic test data for Omani customers including:
- Arabic and English names
- Oman mobile numbers (+968)
- Vehicle information
- Service types

## Scenarios

### 1. Customer Registration and Booking Flow (60% weight)
- User login/authentication
- Customer registration with Arabic/English data
- Vehicle registration
- Appointment booking

### 2. Technician Workflow (25% weight)
- Technician login
- View assigned service orders
- Update job status
- Record parts usage

### 3. Administrative Operations (15% weight)
- Admin login
- Generate various reports
- Inventory management
- Purchase order creation
- Invoice processing

## Usage

### Install Artillery
```bash
npm install -g artillery
```

### Run Load Tests
```bash
# Basic load test
artillery run api_load_test.yml

# With custom target
artillery run api_load_test.yml --target http://your-server:8000

# Generate detailed report
artillery run api_load_test.yml --output results.json
artillery report results.json --output report.html

# Quick test (shorter duration)
artillery quick --count 10 --num 50 http://localhost:8000/api/resource/Customer
```

### Environment Variables
```bash
# Set custom configuration
export ARTILLERY_TARGET=http://production-server:8000
export ARTILLERY_PHASES_0_DURATION=120
export ARTILLERY_PHASES_0_ARRIVALRATE=10

artillery run api_load_test.yml
```

## Key Metrics

Artillery reports the following performance metrics:

### Response Time
- Mean response time
- 95th percentile
- 99th percentile
- Maximum response time

### Throughput
- Requests per second
- Scenarios completed per second
- Virtual users active

### Errors
- HTTP error rates (4xx, 5xx)
- Network errors
- Timeout errors

### Custom Metrics
- Authentication success rate
- Database operation performance
- API endpoint specific metrics

## Integration

### CI/CD Pipeline Integration
```yaml
# Example GitHub Actions workflow
- name: Run Load Tests
  run: |
    artillery run tests/load_testing/artillery/api_load_test.yml --output loadtest-results.json
    artillery report loadtest-results.json --output loadtest-report.html
    
- name: Upload Results
  uses: actions/upload-artifact@v3
  with:
    name: load-test-results
    path: |
      loadtest-results.json
      loadtest-report.html
```

### Performance Monitoring
```bash
# Run with system monitoring
artillery run api_load_test.yml & 
PID=$!
iostat -x 1 > system_metrics.log &
wait $PID
```

## Best Practices

1. **Gradual Load Increase**: Use phased approach to avoid overwhelming the system
2. **Realistic Data**: Use production-like test data volumes and patterns
3. **Think Time**: Include realistic delays between user actions
4. **Error Handling**: Monitor and analyze error patterns
5. **Resource Monitoring**: Watch server resources during tests
6. **Baseline Comparison**: Compare results against established baselines

## Troubleshooting

### Common Issues
- **High Error Rates**: Check server logs, reduce load, verify endpoints
- **Slow Response Times**: Monitor database queries, check indexing
- **Memory Issues**: Monitor server RAM, tune application settings
- **Connection Timeouts**: Adjust timeout settings, check network

### Debug Mode
```bash
# Enable detailed logging
DEBUG=http artillery run api_load_test.yml

# Verbose output
artillery run api_load_test.yml --verbose
```
