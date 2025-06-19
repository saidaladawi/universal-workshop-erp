#!/bin/bash

# Universal Workshop ERP v2.0 Docker Entrypoint
# نقطة دخول Docker لنظام إدارة الورش الشامل

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration from environment variables
DB_HOST=${DB_HOST:-mariadb}
DB_PORT=${DB_PORT:-3306}
DB_NAME=${DB_NAME:-universal_workshop}
DB_USER=${DB_USER:-frappe}
DB_PASSWORD=${DB_PASSWORD:-frappe}
REDIS_CACHE_URL=${REDIS_CACHE_URL:-redis://redis_cache:6379}
REDIS_QUEUE_URL=${REDIS_QUEUE_URL:-redis://redis_queue:6379}
SITE_NAME=${SITE_NAME:-workshop.local}
ADMIN_PASSWORD=${ADMIN_PASSWORD:-admin}
LANG=${LANG:-ar}
ENCRYPTION_KEY=${ENCRYPTION_KEY:-}

print_message() {
    echo -e "${GREEN}$1${NC}"
}

print_error() {
    echo -e "${RED}Error: $1${NC}"
}

print_info() {
    echo -e "${BLUE}Info: $1${NC}"
}

# Wait for database
wait_for_db() {
    print_info "Waiting for database at $DB_HOST:$DB_PORT..."
    
    while ! mysqladmin ping -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" --silent; do
        print_info "Database not ready, waiting..."
        sleep 2
    done
    
    print_message "✓ Database is ready"
}

# Wait for Redis
wait_for_redis() {
    print_info "Waiting for Redis services..."
    
    # Extract Redis details from URLs
    REDIS_CACHE_HOST=$(echo $REDIS_CACHE_URL | sed 's|redis://||' | cut -d: -f1)
    REDIS_CACHE_PORT=$(echo $REDIS_CACHE_URL | sed 's|redis://||' | cut -d: -f2)
    
    while ! redis-cli -h "$REDIS_CACHE_HOST" -p "$REDIS_CACHE_PORT" ping > /dev/null 2>&1; do
        print_info "Redis cache not ready, waiting..."
        sleep 2
    done
    
    print_message "✓ Redis services are ready"
}

# Create site if not exists
create_site_if_not_exists() {
    if [ ! -d "sites/$SITE_NAME" ]; then
        print_info "Creating new site: $SITE_NAME"
        
        # Create site
        bench new-site "$SITE_NAME" \
            --admin-password "$ADMIN_PASSWORD" \
            --db-host "$DB_HOST" \
            --db-port "$DB_PORT" \
            --db-name "$DB_NAME" \
            --db-user "$DB_USER" \
            --db-password "$DB_PASSWORD"
        
        # Install ERPNext
        bench --site "$SITE_NAME" install-app erpnext
        
        # Install Universal Workshop if exists
        if [ -d "apps/universal_workshop" ]; then
            bench --site "$SITE_NAME" install-app universal_workshop
        fi
        
        # Configure Arabic language
        bench --site "$SITE_NAME" set-config lang "$LANG"
        
        # Set encryption key if provided
        if [ -n "$ENCRYPTION_KEY" ]; then
            bench --site "$SITE_NAME" set-config encryption_key "$ENCRYPTION_KEY"
        fi
        
        # Add to hosts
        bench --site "$SITE_NAME" add-to-hosts
        
        print_message "✓ Site created and configured"
    else
        print_message "✓ Site already exists: $SITE_NAME"
    fi
}

# Update site configuration
update_site_config() {
    print_info "Updating site configuration..."
    
    # Update common_site_config.json
    cat > sites/common_site_config.json <<EOF
{
    "db_host": "$DB_HOST",
    "db_port": $DB_PORT,
    "redis_cache": "$REDIS_CACHE_URL",
    "redis_queue": "$REDIS_QUEUE_URL",
    "redis_socketio": "$REDIS_QUEUE_URL",
    "socketio_port": 9000,
    "lang": "$LANG",
    "auto_migrate": true,
    "developer_mode": 0,
    "disable_website_cache": false,
    "maintenance_mode": false,
    "allow_cors": "*",
    "cors_origin": "*"
}
EOF
    
    print_message "✓ Site configuration updated"
}

# Setup Arabic localization
setup_arabic_localization() {
    if [ "$LANG" = "ar" ]; then
        print_info "Setting up Arabic localization..."
        
        # Enable Arabic language in the site
        bench --site "$SITE_NAME" execute "
import frappe

# Enable Arabic language
if not frappe.db.exists('Language', 'ar'):
    doc = frappe.new_doc('Language')
    doc.language_code = 'ar'
    doc.language_name = 'العربية'
    doc.enabled = 1
    doc.flag = 'om'
    doc.insert()

# Update system settings
system_settings = frappe.get_single('System Settings')
system_settings.language = 'ar'
system_settings.country = 'Oman'
system_settings.time_zone = 'Asia/Muscat'
system_settings.float_precision = 3
system_settings.currency_precision = 3
system_settings.save()

frappe.db.commit()
print('Arabic localization completed')
        "
        
        print_message "✓ Arabic localization configured"
    fi
}

# Migrate if needed
migrate_if_needed() {
    print_info "Checking for migrations..."
    
    bench --site "$SITE_NAME" migrate
    bench --site "$SITE_NAME" clear-cache
    
    print_message "✓ Migrations completed"
}

# Start services based on command
start_services() {
    case "${1:-bench start}" in
        "bench start")
            print_message "🚗 Starting Universal Workshop ERP v2.0..."
            print_message "نظام إدارة الورش الشامل - جاري البدء..."
            echo
            print_info "Site: http://$SITE_NAME:8000"
            print_info "Admin: Administrator"
            print_info "Password: $ADMIN_PASSWORD"
            print_info "Language: $LANG"
            echo
            exec bench start
            ;;
        "production")
            print_message "🚀 Starting in production mode..."
            exec supervisord -c /etc/supervisor/supervisord.conf
            ;;
        "worker")
            print_message "🔄 Starting background worker..."
            exec bench worker --site "$SITE_NAME"
            ;;
        "scheduler")
            print_message "⏰ Starting scheduler..."
            exec bench schedule --site "$SITE_NAME"
            ;;
        *)
            print_message "🔧 Running custom command: $*"
            exec "$@"
            ;;
    esac
}

# Main function
main() {
    print_message "🐳 Universal Workshop ERP Docker Container Starting..."
    print_message "حاوية Docker لنظام إدارة الورش الشامل"
    echo
    
    # Wait for dependencies
    wait_for_db
    wait_for_redis
    
    # Navigate to bench directory
    cd /home/frappe/frappe-bench
    
    # Setup site
    create_site_if_not_exists
    update_site_config
    setup_arabic_localization
    migrate_if_needed
    
    # Start services
    start_services "$@"
}

# Run main function with all arguments
main "$@" 