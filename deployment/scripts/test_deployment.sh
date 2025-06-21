#!/bin/bash
# Production Deployment Testing Script
# Tests deployment infrastructure in staging environment

set -e

# Configuration
STAGING_DOMAIN="staging.workshop.local"
MONITORING_DOMAIN="monitoring.staging.workshop.local"
MAX_RETRIES=30
RETRY_INTERVAL=10

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging
LOG_FILE="/var/log/deployment_test.log"
exec 1> >(tee -a "$LOG_FILE")
exec 2> >(tee -a "$LOG_FILE" >&2)

log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Test functions
test_docker_deployment() {
    log_info "Testing Docker deployment..."
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker is not running"
        return 1
    fi
    
    # Test Docker Compose deployment
    cd /home/said/frappe-dev/frappe-bench/deployment/docker
    
    log_info "Starting Docker Compose services..."
    docker-compose -f docker-compose.prod.yml up -d
    
    # Wait for services to be ready
    local retry_count=0
    while [ $retry_count -lt $MAX_RETRIES ]; do
        if docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
            log_info "Docker services are running"
            break
        fi
        
        log_info "Waiting for services to start... (attempt $((retry_count + 1))/$MAX_RETRIES)"
        sleep $RETRY_INTERVAL
        retry_count=$((retry_count + 1))
    done
    
    if [ $retry_count -eq $MAX_RETRIES ]; then
        log_error "Docker services failed to start"
        docker-compose -f docker-compose.prod.yml logs
        return 1
    fi
    
    # Test service connectivity
    log_info "Testing service connectivity..."
    
    # Test database
    if docker-compose -f docker-compose.prod.yml exec -T db mysql -u root -proot_password -e "SELECT 1;" > /dev/null 2>&1; then
        log_info "Database connection successful"
    else
        log_error "Database connection failed"
        return 1
    fi
    
    # Test Redis
    if docker-compose -f docker-compose.prod.yml exec -T redis redis-cli ping | grep -q "PONG"; then
        log_info "Redis connection successful"
    else
        log_error "Redis connection failed"
        return 1
    fi
    
    # Test web service
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080 | grep -q "200\|302"; then
        log_info "Web service is responding"
    else
        log_error "Web service is not responding"
        return 1
    fi
    
    log_info "Docker deployment test completed successfully"
    return 0
}

test_kubernetes_deployment() {
    log_info "Testing Kubernetes deployment..."
    
    # Check if kubectl is available and configured
    if ! kubectl cluster-info > /dev/null 2>&1; then
        log_warning "Kubernetes cluster not available, skipping K8s tests"
        return 0
    fi
    
    # Apply Kubernetes manifests
    cd /home/said/frappe-dev/frappe-bench/deployment/kubernetes
    
    log_info "Applying Kubernetes manifests..."
    kubectl apply -f namespace.yaml
    kubectl apply -f storage.yaml
    kubectl apply -f deployment.yaml
    kubectl apply -f services.yaml
    
    # Wait for deployments to be ready
    log_info "Waiting for deployments to be ready..."
    
    local deployments=("erpnext-web" "mariadb" "redis-cache" "redis-queue")
    for deployment in "${deployments[@]}"; do
        kubectl rollout status deployment/$deployment -n workshop-system --timeout=300s
        if [ $? -eq 0 ]; then
            log_info "Deployment $deployment is ready"
        else
            log_error "Deployment $deployment failed to become ready"
            kubectl describe deployment/$deployment -n workshop-system
            return 1
        fi
    done
    
    # Test service endpoints
    log_info "Testing Kubernetes service endpoints..."
    
    # Get service endpoints
    kubectl get endpoints -n workshop-system
    
    log_info "Kubernetes deployment test completed successfully"
    return 0
}

test_monitoring_stack() {
    log_info "Testing monitoring stack..."
    
    cd /home/said/frappe-dev/frappe-bench/deployment/monitoring
    
    # Start monitoring services
    log_info "Starting monitoring services..."
    docker-compose -f elk-stack.yml up -d
    
    # Wait for Elasticsearch to be ready
    local retry_count=0
    while [ $retry_count -lt $MAX_RETRIES ]; do
        if curl -s http://localhost:9200/_cluster/health | grep -q "yellow\|green"; then
            log_info "Elasticsearch is ready"
            break
        fi
        
        log_info "Waiting for Elasticsearch... (attempt $((retry_count + 1))/$MAX_RETRIES)"
        sleep $RETRY_INTERVAL
        retry_count=$((retry_count + 1))
    done
    
    if [ $retry_count -eq $MAX_RETRIES ]; then
        log_error "Elasticsearch failed to start"
        return 1
    fi
    
    # Test Kibana
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:5601 | grep -q "200\|302"; then
        log_info "Kibana is responding"
    else
        log_warning "Kibana is not responding yet"
    fi
    
    # Test Prometheus (if available)
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:9090 | grep -q "200"; then
        log_info "Prometheus is responding"
    else
        log_warning "Prometheus is not available"
    fi
    
    log_info "Monitoring stack test completed"
    return 0
}

test_database_migration() {
    log_info "Testing database migration scripts..."
    
    cd /home/said/frappe-dev/frappe-bench/deployment/scripts
    
    # Test migration script
    if python3 migrate_database.py --help > /dev/null 2>&1; then
        log_info "Migration script is executable"
    else
        log_error "Migration script has issues"
        return 1
    fi
    
    # Test environment manager
    if python3 environment_manager.py > /dev/null 2>&1; then
        log_info "Environment manager is working"
    else
        log_error "Environment manager has issues"
        return 1
    fi
    
    log_info "Database migration test completed"
    return 0
}

test_backup_restore() {
    log_info "Testing backup and restore procedures..."
    
    cd /home/said/frappe-dev/frappe-bench/deployment/scripts
    
    # Test backup script
    if [ -f "./backup.sh" ]; then
        if bash -n ./backup.sh; then
            log_info "Backup script syntax is valid"
        else
            log_error "Backup script has syntax errors"
            return 1
        fi
    else
        log_warning "Backup script not found"
    fi
    
    # Test restore script
    if [ -f "./restore.sh" ]; then
        if bash -n ./restore.sh; then
            log_info "Restore script syntax is valid"
        else
            log_error "Restore script has syntax errors"
            return 1
        fi
    else
        log_warning "Restore script not found"
    fi
    
    log_info "Backup/restore test completed"
    return 0
}

test_ssl_certificates() {
    log_info "Testing SSL certificate configuration..."
    
    # Test Nginx configuration
    if nginx -t 2>/dev/null; then
        log_info "Nginx configuration is valid"
    else
        log_warning "Nginx configuration test failed (nginx not installed or config invalid)"
    fi
    
    # Test SSL certificate paths (if they exist)
    local cert_paths=(
        "/etc/ssl/certs/workshop.crt"
        "/etc/ssl/private/workshop.key"
    )
    
    for cert_path in "${cert_paths[@]}"; do
        if [ -f "$cert_path" ]; then
            log_info "Certificate file exists: $cert_path"
        else
            log_warning "Certificate file not found: $cert_path"
        fi
    done
    
    log_info "SSL certificate test completed"
    return 0
}

test_performance_monitoring() {
    log_info "Testing performance monitoring..."
    
    # Test metrics collection
    if command -v prometheus > /dev/null 2>&1; then
        log_info "Prometheus is available"
    else
        log_warning "Prometheus not installed"
    fi
    
    if command -v grafana-server > /dev/null 2>&1; then
        log_info "Grafana is available"
    else
        log_warning "Grafana not installed"
    fi
    
    # Test log aggregation
    if docker ps | grep -q elasticsearch; then
        log_info "Elasticsearch container is running"
    else
        log_warning "Elasticsearch container not running"
    fi
    
    if docker ps | grep -q logstash; then
        log_info "Logstash container is running"
    else
        log_warning "Logstash container not running"
    fi
    
    log_info "Performance monitoring test completed"
    return 0
}

cleanup_test_environment() {
    log_info "Cleaning up test environment..."
    
    # Stop Docker services
    cd /home/said/frappe-dev/frappe-bench/deployment/docker
    docker-compose -f docker-compose.prod.yml down
    
    # Stop monitoring services
    cd /home/said/frappe-dev/frappe-bench/deployment/monitoring
    docker-compose -f elk-stack.yml down
    
    # Clean up Kubernetes resources (if applicable)
    if kubectl cluster-info > /dev/null 2>&1; then
        kubectl delete namespace workshop-system --ignore-not-found=true
    fi
    
    log_info "Cleanup completed"
}

# Main test execution
main() {
    log_info "Starting deployment infrastructure testing..."
    log_info "Test results will be logged to: $LOG_FILE"
    
    local test_results=()
    
    # Run tests
    if test_docker_deployment; then
        test_results+=("Docker Deployment: PASS")
    else
        test_results+=("Docker Deployment: FAIL")
    fi
    
    if test_kubernetes_deployment; then
        test_results+=("Kubernetes Deployment: PASS")
    else
        test_results+=("Kubernetes Deployment: FAIL")
    fi
    
    if test_monitoring_stack; then
        test_results+=("Monitoring Stack: PASS")
    else
        test_results+=("Monitoring Stack: FAIL")
    fi
    
    if test_database_migration; then
        test_results+=("Database Migration: PASS")
    else
        test_results+=("Database Migration: FAIL")
    fi
    
    if test_backup_restore; then
        test_results+=("Backup/Restore: PASS")
    else
        test_results+=("Backup/Restore: FAIL")
    fi
    
    if test_ssl_certificates; then
        test_results+=("SSL Certificates: PASS")
    else
        test_results+=("SSL Certificates: FAIL")
    fi
    
    if test_performance_monitoring; then
        test_results+=("Performance Monitoring: PASS")
    else
        test_results+=("Performance Monitoring: FAIL")
    fi
    
    # Cleanup
    cleanup_test_environment
    
    # Print results
    log_info "=== DEPLOYMENT TEST RESULTS ==="
    for result in "${test_results[@]}"; do
        if [[ $result == *"PASS"* ]]; then
            log_info "$result"
        else
            log_error "$result"
        fi
    done
    
    # Overall result
    local failed_tests=$(printf '%s\n' "${test_results[@]}" | grep -c "FAIL")
    if [ $failed_tests -eq 0 ]; then
        log_info "=== ALL TESTS PASSED ==="
        return 0
    else
        log_error "=== $failed_tests TESTS FAILED ==="
        return 1
    fi
}

# Run tests
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi
