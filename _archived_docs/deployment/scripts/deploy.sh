#!/bin/bash
# Universal Workshop ERP Production Deployment Script
# Automated deployment for production environment

set -e

# Configuration
DEPLOYMENT_ENV=${1:-production}
PROJECT_ROOT="/home/said/frappe-dev/frappe-bench"
BACKUP_DIR="/var/backups/workshop-erp"
LOG_FILE="/var/log/workshop-deployment.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
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

log_step() {
    echo -e "${BLUE}[STEP]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Pre-deployment checks
pre_deployment_checks() {
    log_step "Running pre-deployment checks..."
    
    # Check if running as correct user
    if [ "$USER" != "frappe" ]; then
        log_warning "Not running as frappe user. Current user: $USER"
    fi
    
    # Check disk space
    AVAILABLE_SPACE=$(df /home/said/frappe-dev/frappe-bench | awk 'NR==2 {print $4}')
    REQUIRED_SPACE=1048576  # 1GB in KB
    
    if [ "$AVAILABLE_SPACE" -lt "$REQUIRED_SPACE" ]; then
        log_error "Insufficient disk space. Available: ${AVAILABLE_SPACE}KB, Required: ${REQUIRED_SPACE}KB"
        exit 1
    fi
    
    # Check if site is accessible
    if ! curl -s -o /dev/null -w "%{http_code}" http://localhost:8000 | grep -q "200\|302"; then
        log_error "Site is not accessible at localhost:8000"
        exit 1
    fi
    
    # Check database connectivity
    cd "$PROJECT_ROOT"
    if ! bench --site universal.local execute "frappe.db.sql('SELECT 1')" > /dev/null 2>&1; then
        log_error "Database connectivity check failed"
        exit 1
    fi
    
    log_info "Pre-deployment checks completed successfully"
}

# Create backup before deployment
create_backup() {
    log_step "Creating pre-deployment backup..."
    
    mkdir -p "$BACKUP_DIR"
    BACKUP_TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
    BACKUP_PATH="$BACKUP_DIR/workshop_backup_$BACKUP_TIMESTAMP"
    
    cd "$PROJECT_ROOT"
    
    # Database backup
    log_info "Creating database backup..."
    bench --site universal.local backup --with-files
    
    # Copy backup files to backup directory
    SITE_BACKUP_DIR="$PROJECT_ROOT/sites/universal.local/private/backups"
    if [ -d "$SITE_BACKUP_DIR" ]; then
        cp -r "$SITE_BACKUP_DIR" "$BACKUP_PATH"
        log_info "Backup created at: $BACKUP_PATH"
    else
        log_error "Backup directory not found: $SITE_BACKUP_DIR"
        exit 1
    fi
    
    # Create system backup
    log_info "Creating system configuration backup..."
    tar -czf "$BACKUP_PATH/system_config_$BACKUP_TIMESTAMP.tar.gz" \
        sites/common_site_config.json \
        sites/universal.local/site_config.json \
        config/ || true
    
    echo "$BACKUP_PATH" > /tmp/latest_backup_path
    log_info "Backup completed successfully"
}

# Update codebase
update_codebase() {
    log_step "Updating codebase..."
    
    cd "$PROJECT_ROOT"
    
    # Pull latest changes
    log_info "Pulling latest changes from repository..."
    bench update --no-backup --reset
    
    # Install/update apps
    log_info "Installing Universal Workshop app..."
    if ! bench --site universal.local install-app universal_workshop; then
        log_warning "App already installed, attempting to migrate..."
        bench --site universal.local migrate
    fi
    
    log_info "Codebase update completed"
}

# Run database migrations
run_migrations() {
    log_step "Running database migrations..."
    
    cd "$PROJECT_ROOT"
    
    # Run migrations
    log_info "Executing database migrations..."
    bench --site universal.local migrate
    
    # Clear cache
    log_info "Clearing cache..."
    bench --site universal.local clear-cache
    
    log_info "Database migrations completed"
}

# Update system configuration
update_configuration() {
    log_step "Updating system configuration..."
    
    cd "$PROJECT_ROOT"
    
    # Set production configuration
    log_info "Setting production configuration..."
    
    # Enable scheduler
    bench --site universal.local enable-scheduler
    
    # Set maintenance mode off
    bench --site universal.local set-maintenance-mode off
    
    # Set production configuration
    if [ "$DEPLOYMENT_ENV" = "production" ]; then
        # Production-specific settings
        bench --site universal.local set-config developer_mode 0
        bench --site universal.local set-config server_script_enabled 0
        bench --site universal.local set-config allow_tests 0
        
        # Arabic language settings
        bench --site universal.local set-config default_language ar
        bench --site universal.local set-config time_zone "Asia/Muscat"
        
        # Performance settings
        bench --site universal.local set-config background_workers 2
        bench --site universal.local set-config gunicorn_workers 4
    fi
    
    log_info "Configuration update completed"
}

# Setup production services
setup_production() {
    log_step "Setting up production services..."
    
    cd "$PROJECT_ROOT"
    
    if [ "$DEPLOYMENT_ENV" = "production" ]; then
        log_info "Configuring production services..."
        
        # Setup production
        sudo bench setup production frappe
        
        # Setup nginx
        bench setup nginx
        
        # Setup supervisor
        bench setup supervisor
        
        # Restart all services
        sudo supervisorctl restart all
        
        # Enable and start nginx
        sudo systemctl enable nginx
        sudo systemctl restart nginx
        
        log_info "Production services setup completed"
    else
        log_info "Skipping production setup for $DEPLOYMENT_ENV environment"
    fi
}

# Run post-deployment tests
run_post_deployment_tests() {
    log_step "Running post-deployment tests..."
    
    cd "$PROJECT_ROOT"
    
    # Test site accessibility
    log_info "Testing site accessibility..."
    if curl -s -o /dev/null -w "%{http_code}" http://localhost | grep -q "200\|302"; then
        log_info "Site is accessible"
    else
        log_error "Site accessibility test failed"
        return 1
    fi
    
    # Test database connectivity
    log_info "Testing database connectivity..."
    if bench --site universal.local execute "frappe.db.sql('SELECT 1')" > /dev/null 2>&1; then
        log_info "Database connectivity test passed"
    else
        log_error "Database connectivity test failed"
        return 1
    fi
    
    # Test Arabic localization
    log_info "Testing Arabic localization..."
    if bench --site universal.local execute "frappe.get_all('Language', filters={'language_code': 'ar'})" | grep -q "ar"; then
        log_info "Arabic localization test passed"
    else
        log_warning "Arabic localization test failed"
    fi
    
    # Run basic API test
    log_info "Testing API endpoints..."
    if curl -s http://localhost/api/method/ping | grep -q "pong"; then
        log_info "API test passed"
    else
        log_warning "API test failed"
    fi
    
    log_info "Post-deployment tests completed"
}

# Cleanup and finalization
cleanup() {
    log_step "Performing cleanup and finalization..."
    
    cd "$PROJECT_ROOT"
    
    # Clear cache one more time
    bench --site universal.local clear-cache
    
    # Restart services
    if [ "$DEPLOYMENT_ENV" = "production" ]; then
        sudo supervisorctl restart all
    else
        bench restart
    fi
    
    # Clean up temporary files
    find /tmp -name "workshop_*" -mtime +1 -delete 2>/dev/null || true
    
    log_info "Cleanup completed"
}

# Rollback function
rollback_deployment() {
    log_error "Deployment failed. Initiating rollback..."
    
    if [ -f /tmp/latest_backup_path ]; then
        BACKUP_PATH=$(cat /tmp/latest_backup_path)
        log_info "Rolling back to backup: $BACKUP_PATH"
        
        cd "$PROJECT_ROOT"
        
        # Restore database
        if [ -d "$BACKUP_PATH" ]; then
            LATEST_DB_BACKUP=$(ls -t "$BACKUP_PATH"/*.sql.gz 2>/dev/null | head -1)
            if [ -n "$LATEST_DB_BACKUP" ]; then
                log_info "Restoring database from: $LATEST_DB_BACKUP"
                bench --site universal.local restore "$LATEST_DB_BACKUP" --with-public-files --with-private-files
            fi
        fi
        
        # Restart services
        bench restart
        
        log_info "Rollback completed"
    else
        log_error "No backup path found for rollback"
    fi
}

# Main deployment function
main() {
    log_info "Starting Universal Workshop ERP deployment (Environment: $DEPLOYMENT_ENV)"
    
    # Set trap for rollback on failure
    trap rollback_deployment ERR
    
    # Execute deployment steps
    pre_deployment_checks
    create_backup
    update_codebase
    run_migrations
    update_configuration
    
    if [ "$DEPLOYMENT_ENV" = "production" ]; then
        setup_production
    fi
    
    run_post_deployment_tests
    cleanup
    
    # Remove rollback trap
    trap - ERR
    
    log_info "Deployment completed successfully!"
    log_info "Universal Workshop ERP is now running in $DEPLOYMENT_ENV mode"
    
    if [ "$DEPLOYMENT_ENV" = "production" ]; then
        log_info "Production URL: http://$(hostname -I | awk '{print $1}')"
        log_info "Admin login: Administrator"
        log_info "Please change default passwords and review security settings"
    fi
}

# Usage information
usage() {
    echo "Usage: $0 [environment]"
    echo "Environments: development, staging, production"
    echo "Example: $0 production"
    exit 1
}

# Check arguments
if [ $# -gt 1 ]; then
    usage
fi

# Run main function
main "$@"
