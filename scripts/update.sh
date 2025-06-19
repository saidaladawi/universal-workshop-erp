#!/bin/bash

# Universal Workshop ERP v2.0 Update Script
# نص تحديث نظام إدارة الورش الشامل
# 
# Usage: ./scripts/update.sh [version]
# استخدام: ./scripts/update.sh [إصدار]

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
FRAPPE_USER="frappe"
BENCH_NAME="frappe-bench"
SITE_NAME="workshop.local"
REPO_URL="https://github.com/saidaladawi/universal-workshop-erp.git"
BACKUP_DIR="/home/$FRAPPE_USER/backups"
TARGET_VERSION="${1:-latest}"

# Language detection
if [ "${LANG:-}" = "ar"* ] || [ "${LC_ALL:-}" = "ar"* ]; then
    LANG_AR=true
else
    LANG_AR=false
fi

# Messages in Arabic and English
print_message() {
    if [ "$LANG_AR" = true ]; then
        echo -e "${GREEN}$2${NC}"
    else
        echo -e "${GREEN}$1${NC}"
    fi
}

print_error() {
    if [ "$LANG_AR" = true ]; then
        echo -e "${RED}خطأ: $2${NC}"
    else
        echo -e "${RED}Error: $1${NC}"
    fi
}

print_warning() {
    if [ "$LANG_AR" = true ]; then
        echo -e "${YELLOW}تحذير: $2${NC}"
    else
        echo -e "${YELLOW}Warning: $1${NC}"
    fi
}

print_info() {
    if [ "$LANG_AR" = true ]; then
        echo -e "${BLUE}معلومة: $2${NC}"
    else
        echo -e "${BLUE}Info: $1${NC}"
    fi
}

# Check if bench exists
check_installation() {
    if [ ! -d "/home/$FRAPPE_USER/$BENCH_NAME" ]; then
        print_error "Universal Workshop ERP not found. Please install first." "نظام الورش الشامل غير موجود. يرجى التثبيت أولاً."
        exit 1
    fi
    
    print_message "✓ Installation found" "✓ تم العثور على التثبيت"
}

# Create backup before update
create_backup() {
    print_message "Creating backup before update..." "إنشاء نسخة احتياطية قبل التحديث..."
    
    # Create backup directory
    sudo -u $FRAPPE_USER mkdir -p $BACKUP_DIR
    
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_FILE="workshop_backup_${TIMESTAMP}"
    
    sudo -u $FRAPPE_USER bash -c "
        cd /home/$FRAPPE_USER/$BENCH_NAME
        
        # Database backup
        bench --site $SITE_NAME backup --with-files
        
        # Copy backup to safe location
        cp -r sites/$SITE_NAME/private/backups/* $BACKUP_DIR/
        
        # Create full site backup
        tar -czf $BACKUP_DIR/${BACKUP_FILE}_full.tar.gz sites/$SITE_NAME/
    "
    
    echo "$BACKUP_DIR/${BACKUP_FILE}_full.tar.gz" > /tmp/workshop_backup_path
    print_message "✓ Backup created: $BACKUP_DIR/${BACKUP_FILE}_full.tar.gz" "✓ تم إنشاء النسخة الاحتياطية: $BACKUP_DIR/${BACKUP_FILE}_full.tar.gz"
}

# Get current version
get_current_version() {
    CURRENT_VERSION=$(sudo -u $FRAPPE_USER bash -c "
        cd /home/$FRAPPE_USER/$BENCH_NAME/apps/universal_workshop
        git describe --tags --abbrev=0 2>/dev/null || echo 'unknown'
    ")
    
    print_info "Current version: $CURRENT_VERSION" "الإصدار الحالي: $CURRENT_VERSION"
}

# Check for updates
check_updates() {
    print_message "Checking for updates..." "فحص التحديثات..."
    
    sudo -u $FRAPPE_USER bash -c "
        cd /home/$FRAPPE_USER/$BENCH_NAME/apps/universal_workshop
        git fetch origin
    "
    
    if [ "$TARGET_VERSION" = "latest" ]; then
        LATEST_VERSION=$(sudo -u $FRAPPE_USER bash -c "
            cd /home/$FRAPPE_USER/$BENCH_NAME/apps/universal_workshop
            git describe --tags \$(git rev-list --tags --max-count=1) 2>/dev/null || echo 'main'
        ")
        TARGET_VERSION=$LATEST_VERSION
    fi
    
    print_info "Target version: $TARGET_VERSION" "الإصدار المستهدف: $TARGET_VERSION"
    
    if [ "$CURRENT_VERSION" = "$TARGET_VERSION" ]; then
        print_message "Already up to date!" "محدّث بالفعل!"
        exit 0
    fi
}

# Stop services
stop_services() {
    print_message "Stopping services..." "إيقاف الخدمات..."
    
    sudo -u $FRAPPE_USER bash -c "
        cd /home/$FRAPPE_USER/$BENCH_NAME
        bench --site $SITE_NAME set-maintenance-mode on 2>/dev/null || true
    " 2>/dev/null || true
    
    # Stop bench processes
    sudo pkill -f "bench" 2>/dev/null || true
    sleep 2
    
    print_message "✓ Services stopped" "✓ تم إيقاف الخدمات"
}

# Update codebase
update_codebase() {
    print_message "Updating Universal Workshop ERP..." "تحديث نظام إدارة الورش الشامل..."
    
    sudo -u $FRAPPE_USER bash -c "
        cd /home/$FRAPPE_USER/$BENCH_NAME
        
        # Update Frappe
        cd apps/frappe
        git pull origin version-15
        
        # Update ERPNext  
        cd ../erpnext
        git pull origin version-15
        
        # Update Universal Workshop
        cd ../universal_workshop
        git fetch origin
        if [ '$TARGET_VERSION' != 'main' ]; then
            git checkout tags/$TARGET_VERSION
        else
            git checkout main
            git pull origin main
        fi
    "
    
    print_message "✓ Codebase updated" "✓ تم تحديث الكود"
}

# Update dependencies
update_dependencies() {
    print_message "Updating dependencies..." "تحديث المتطلبات..."
    
    sudo -u $FRAPPE_USER bash -c "
        cd /home/$FRAPPE_USER/$BENCH_NAME
        
        # Update Python packages
        ./env/bin/pip install --upgrade pip
        ./env/bin/pip install -e apps/frappe
        ./env/bin/pip install -e apps/erpnext
        ./env/bin/pip install -e apps/universal_workshop
        
        # Update Node packages
        yarn install
    "
    
    print_message "✓ Dependencies updated" "✓ تم تحديث المتطلبات"
}

# Run database migrations
run_migrations() {
    print_message "Running database migrations..." "تشغيل ترحيل قاعدة البيانات..."
    
    sudo -u $FRAPPE_USER bash -c "
        cd /home/$FRAPPE_USER/$BENCH_NAME
        
        # Migrate site
        bench --site $SITE_NAME migrate
        
        # Clear cache
        bench --site $SITE_NAME clear-cache
        bench --site $SITE_NAME clear-website-cache
        
        # Build assets
        bench build --apps universal_workshop
    "
    
    print_message "✓ Database migrations completed" "✓ تم إكمال ترحيل قاعدة البيانات"
}

# Start services
start_services() {
    print_message "Starting services..." "بدء الخدمات..."
    
    sudo -u $FRAPPE_USER bash -c "
        cd /home/$FRAPPE_USER/$BENCH_NAME
        bench --site $SITE_NAME set-maintenance-mode off
    "
    
    print_message "✓ Services started" "✓ تم بدء الخدمات"
}

# Verify update
verify_update() {
    print_message "Verifying update..." "التحقق من التحديث..."
    
    NEW_VERSION=$(sudo -u $FRAPPE_USER bash -c "
        cd /home/$FRAPPE_USER/$BENCH_NAME/apps/universal_workshop
        git describe --tags --abbrev=0 2>/dev/null || echo 'main'
    ")
    
    # Test site access
    sudo -u $FRAPPE_USER bash -c "
        cd /home/$FRAPPE_USER/$BENCH_NAME
        timeout 10 bench --site $SITE_NAME doctor || true
    " > /dev/null 2>&1
    
    print_message "✓ Update verified - Version: $NEW_VERSION" "✓ تم التحقق من التحديث - الإصدار: $NEW_VERSION"
}

# Rollback function
rollback() {
    print_error "Update failed. Rolling back..." "فشل التحديث. جارٍ التراجع..."
    
    if [ -f /tmp/workshop_backup_path ]; then
        BACKUP_PATH=$(cat /tmp/workshop_backup_path)
        if [ -f "$BACKUP_PATH" ]; then
            print_message "Restoring from backup..." "استعادة من النسخة الاحتياطية..."
            
            sudo -u $FRAPPE_USER bash -c "
                cd /home/$FRAPPE_USER
                rm -rf $BENCH_NAME/sites/$SITE_NAME
                tar -xzf $BACKUP_PATH -C /
            "
            
            start_services
            print_message "✓ Rollback completed" "✓ تم إكمال التراجع"
        fi
    fi
    
    rm -f /tmp/workshop_backup_path
    exit 1
}

# Main update function
main() {
    echo
    if [ "$LANG_AR" = true ]; then
        echo "🔄 بدء تحديث نظام إدارة الورش الشامل v2.0"
        echo "Universal Workshop ERP Update Starting..."
    else
        echo "🔄 Universal Workshop ERP v2.0 Update Starting..."
        echo "نظام إدارة الورش الشامل - بدء التحديث"
    fi
    echo
    
    # Set up error handling
    trap rollback ERR
    
    check_installation
    get_current_version
    check_updates
    create_backup
    stop_services
    update_codebase
    update_dependencies
    run_migrations
    start_services
    verify_update
    
    # Cleanup
    rm -f /tmp/workshop_backup_path
    
    echo
    print_message "🎉 Update completed successfully!" "🎉 تم التحديث بنجاح!"
    print_message "Updated from $CURRENT_VERSION to $TARGET_VERSION" "تم التحديث من $CURRENT_VERSION إلى $TARGET_VERSION"
    print_message "You can access your site at: http://$SITE_NAME:8000" "يمكنك الوصول إلى موقعك على: http://$SITE_NAME:8000"
    echo
    print_message "To start the server manually:" "لبدء الخادم يدوياً:"
    print_message "sudo -u $FRAPPE_USER bash -c 'cd /home/$FRAPPE_USER/$BENCH_NAME && bench start'" "sudo -u $FRAPPE_USER bash -c 'cd /home/$FRAPPE_USER/$BENCH_NAME && bench start'"
    echo
}

# Run main function
main "$@" 