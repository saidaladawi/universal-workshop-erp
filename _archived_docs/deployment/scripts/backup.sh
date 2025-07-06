#!/bin/bash
# Universal Workshop ERP Backup Script
# Creates comprehensive backups of database, files, and configuration

set -e

# Configuration
PROJECT_ROOT="/home/said/frappe-dev/frappe-bench"
BACKUP_ROOT="/var/backups/workshop-erp"
SITE_NAME="universal.local"
RETENTION_DAYS=30
LOG_FILE="/var/log/workshop-backup.log"

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

# Check prerequisites
check_prerequisites() {
    log_step "Checking prerequisites..."
    
    # Check if running as correct user
    if [ "$USER" != "frappe" ] && [ "$USER" != "root" ]; then
        log_warning "Not running as frappe or root user. Current user: $USER"
    fi
    
    # Check if bench is available
    if ! command -v bench &> /dev/null; then
        log_error "Bench command not found"
        exit 1
    fi
    
    # Check if project directory exists
    if [ ! -d "$PROJECT_ROOT" ]; then
        log_error "Project root directory not found: $PROJECT_ROOT"
        exit 1
    fi
    
    # Check if site exists
    if [ ! -d "$PROJECT_ROOT/sites/$SITE_NAME" ]; then
        log_error "Site directory not found: $PROJECT_ROOT/sites/$SITE_NAME"
        exit 1
    fi
    
    # Create backup directory
    mkdir -p "$BACKUP_ROOT"
    
    # Check available disk space
    AVAILABLE_SPACE=$(df "$BACKUP_ROOT" | awk 'NR==2 {print $4}')
    REQUIRED_SPACE=2097152  # 2GB in KB
    
    if [ "$AVAILABLE_SPACE" -lt "$REQUIRED_SPACE" ]; then
        log_warning "Low disk space. Available: ${AVAILABLE_SPACE}KB, Recommended: ${REQUIRED_SPACE}KB"
    fi
    
    log_info "Prerequisites check completed"
}

# Create database backup
create_database_backup() {
    log_step "Creating database backup..."
    
    cd "$PROJECT_ROOT"
    
    BACKUP_TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
    DB_BACKUP_DIR="$BACKUP_ROOT/database_$BACKUP_TIMESTAMP"
    
    mkdir -p "$DB_BACKUP_DIR"
    
    # Create Frappe backup with files
    log_info "Creating Frappe database backup with files..."
    if bench --site "$SITE_NAME" backup --with-files; then
        log_info "Database backup created successfully"
        
        # Copy backup files to our backup directory
        SITE_BACKUP_DIR="$PROJECT_ROOT/sites/$SITE_NAME/private/backups"
        if [ -d "$SITE_BACKUP_DIR" ]; then
            # Get the latest backup files
            LATEST_DB_BACKUP=$(ls -t "$SITE_BACKUP_DIR"/*.sql.gz 2>/dev/null | head -1)
            LATEST_FILES_BACKUP=$(ls -t "$SITE_BACKUP_DIR"/*-files.tar 2>/dev/null | head -1)
            LATEST_PRIVATE_BACKUP=$(ls -t "$SITE_BACKUP_DIR"/*-private-files.tar 2>/dev/null | head -1)
            
            if [ -n "$LATEST_DB_BACKUP" ]; then
                cp "$LATEST_DB_BACKUP" "$DB_BACKUP_DIR/"
                log_info "Database backup copied: $(basename "$LATEST_DB_BACKUP")"
            fi
            
            if [ -n "$LATEST_FILES_BACKUP" ]; then
                cp "$LATEST_FILES_BACKUP" "$DB_BACKUP_DIR/"
                log_info "Public files backup copied: $(basename "$LATEST_FILES_BACKUP")"
            fi
            
            if [ -n "$LATEST_PRIVATE_BACKUP" ]; then
                cp "$LATEST_PRIVATE_BACKUP" "$DB_BACKUP_DIR/"
                log_info "Private files backup copied: $(basename "$LATEST_PRIVATE_BACKUP")"
            fi
        fi
    else
        log_error "Database backup failed"
        return 1
    fi
    
    echo "$DB_BACKUP_DIR" > /tmp/latest_db_backup_path
    log_info "Database backup completed: $DB_BACKUP_DIR"
}

# Create configuration backup
create_config_backup() {
    log_step "Creating configuration backup..."
    
    BACKUP_TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
    CONFIG_BACKUP_DIR="$BACKUP_ROOT/config_$BACKUP_TIMESTAMP"
    
    mkdir -p "$CONFIG_BACKUP_DIR"
    
    cd "$PROJECT_ROOT"
    
    # Backup site configuration
    log_info "Backing up site configuration..."
    if [ -f "sites/common_site_config.json" ]; then
        cp "sites/common_site_config.json" "$CONFIG_BACKUP_DIR/"
    fi
    
    if [ -f "sites/$SITE_NAME/site_config.json" ]; then
        cp "sites/$SITE_NAME/site_config.json" "$CONFIG_BACKUP_DIR/"
    fi
    
    # Backup system configuration
    log_info "Backing up system configuration..."
    if [ -d "config" ]; then
        cp -r config "$CONFIG_BACKUP_DIR/"
    fi
    
    # Backup deployment configuration
    if [ -d "deployment" ]; then
        cp -r deployment "$CONFIG_BACKUP_DIR/"
    fi
    
    # Backup app configurations
    log_info "Backing up app configurations..."
    if [ -d "apps/universal_workshop" ]; then
        mkdir -p "$CONFIG_BACKUP_DIR/apps"
        cp -r "apps/universal_workshop" "$CONFIG_BACKUP_DIR/apps/"
    fi
    
    # Create system info file
    log_info "Creating system information file..."
    cat > "$CONFIG_BACKUP_DIR/system_info.txt" << EOF
Backup Date: $(date)
System: $(uname -a)
User: $(whoami)
Frappe Version: $(bench version)
Site: $SITE_NAME
Project Root: $PROJECT_ROOT
Backup Location: $CONFIG_BACKUP_DIR
EOF
    
    # List installed apps
    log_info "Recording installed apps..."
    bench --site "$SITE_NAME" list-apps > "$CONFIG_BACKUP_DIR/installed_apps.txt" 2>/dev/null || true
    
    echo "$CONFIG_BACKUP_DIR" > /tmp/latest_config_backup_path
    log_info "Configuration backup completed: $CONFIG_BACKUP_DIR"
}

# Create application code backup
create_code_backup() {
    log_step "Creating application code backup..."
    
    BACKUP_TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
    CODE_BACKUP_DIR="$BACKUP_ROOT/code_$BACKUP_TIMESTAMP"
    
    mkdir -p "$CODE_BACKUP_DIR"
    
    cd "$PROJECT_ROOT"
    
    # Backup Universal Workshop app
    log_info "Backing up Universal Workshop application code..."
    if [ -d "apps/universal_workshop" ]; then
        tar -czf "$CODE_BACKUP_DIR/universal_workshop_$BACKUP_TIMESTAMP.tar.gz" \
            --exclude="*.pyc" \
            --exclude="__pycache__" \
            --exclude=".git" \
            --exclude="node_modules" \
            "apps/universal_workshop"
        log_info "Universal Workshop app backup created"
    fi
    
    # Backup custom modifications to Frappe/ERPNext (if any)
    log_info "Backing up custom modifications..."
    if [ -d "apps/frappe/frappe/custom" ]; then
        tar -czf "$CODE_BACKUP_DIR/frappe_custom_$BACKUP_TIMESTAMP.tar.gz" \
            "apps/frappe/frappe/custom" 2>/dev/null || true
    fi
    
    if [ -d "apps/erpnext/erpnext/custom" ]; then
        tar -czf "$CODE_BACKUP_DIR/erpnext_custom_$BACKUP_TIMESTAMP.tar.gz" \
            "apps/erpnext/erpnext/custom" 2>/dev/null || true
    fi
    
    # Backup patches
    log_info "Backing up patches..."
    if [ -f "patches.txt" ]; then
        cp "patches.txt" "$CODE_BACKUP_DIR/"
    fi
    
    echo "$CODE_BACKUP_DIR" > /tmp/latest_code_backup_path
    log_info "Application code backup completed: $CODE_BACKUP_DIR"
}

# Create logs backup
create_logs_backup() {
    log_step "Creating logs backup..."
    
    BACKUP_TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
    LOGS_BACKUP_DIR="$BACKUP_ROOT/logs_$BACKUP_TIMESTAMP"
    
    mkdir -p "$LOGS_BACKUP_DIR"
    
    # Backup Frappe logs
    log_info "Backing up Frappe logs..."
    if [ -d "$PROJECT_ROOT/logs" ]; then
        cp -r "$PROJECT_ROOT/logs" "$LOGS_BACKUP_DIR/frappe_logs"
    fi
    
    # Backup system logs
    log_info "Backing up system logs..."
    if [ -d "/var/log" ]; then
        mkdir -p "$LOGS_BACKUP_DIR/system_logs"
        
        # Copy relevant log files
        for log_file in workshop-*.log frappe*.log nginx/*.log; do
            if [ -f "/var/log/$log_file" ]; then
                cp "/var/log/$log_file" "$LOGS_BACKUP_DIR/system_logs/" 2>/dev/null || true
            fi
        done
    fi
    
    # Backup application logs
    log_info "Backing up application logs..."
    if [ -d "$PROJECT_ROOT/sites/$SITE_NAME/logs" ]; then
        cp -r "$PROJECT_ROOT/sites/$SITE_NAME/logs" "$LOGS_BACKUP_DIR/site_logs"
    fi
    
    echo "$LOGS_BACKUP_DIR" > /tmp/latest_logs_backup_path
    log_info "Logs backup completed: $LOGS_BACKUP_DIR"
}

# Create comprehensive backup
create_comprehensive_backup() {
    log_step "Creating comprehensive backup..."
    
    BACKUP_TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
    COMPREHENSIVE_BACKUP_DIR="$BACKUP_ROOT/comprehensive_$BACKUP_TIMESTAMP"
    
    mkdir -p "$COMPREHENSIVE_BACKUP_DIR"
    
    # Run all backup types
    create_database_backup
    create_config_backup
    create_code_backup
    create_logs_backup
    
    # Copy all backups to comprehensive directory
    log_info "Consolidating backups..."
    
    if [ -f /tmp/latest_db_backup_path ]; then
        DB_BACKUP_PATH=$(cat /tmp/latest_db_backup_path)
        if [ -d "$DB_BACKUP_PATH" ]; then
            cp -r "$DB_BACKUP_PATH" "$COMPREHENSIVE_BACKUP_DIR/database"
        fi
    fi
    
    if [ -f /tmp/latest_config_backup_path ]; then
        CONFIG_BACKUP_PATH=$(cat /tmp/latest_config_backup_path)
        if [ -d "$CONFIG_BACKUP_PATH" ]; then
            cp -r "$CONFIG_BACKUP_PATH" "$COMPREHENSIVE_BACKUP_DIR/config"
        fi
    fi
    
    if [ -f /tmp/latest_code_backup_path ]; then
        CODE_BACKUP_PATH=$(cat /tmp/latest_code_backup_path)
        if [ -d "$CODE_BACKUP_PATH" ]; then
            cp -r "$CODE_BACKUP_PATH" "$COMPREHENSIVE_BACKUP_DIR/code"
        fi
    fi
    
    if [ -f /tmp/latest_logs_backup_path ]; then
        LOGS_BACKUP_PATH=$(cat /tmp/latest_logs_backup_path)
        if [ -d "$LOGS_BACKUP_PATH" ]; then
            cp -r "$LOGS_BACKUP_PATH" "$COMPREHENSIVE_BACKUP_DIR/logs"
        fi
    fi
    
    # Create backup manifest
    log_info "Creating backup manifest..."
    cat > "$COMPREHENSIVE_BACKUP_DIR/backup_manifest.txt" << EOF
Universal Workshop ERP Comprehensive Backup
==========================================

Backup Date: $(date)
Backup Type: Comprehensive
Site: $SITE_NAME
Project Root: $PROJECT_ROOT

Components Included:
- Database backup with files
- Site and system configuration
- Application source code
- System and application logs

Backup Structure:
- database/     : Database and file backups
- config/       : Configuration files
- code/         : Application source code
- logs/         : System and application logs

Restore Instructions:
1. Use database backup files with 'bench restore' command
2. Restore configuration files to appropriate locations
3. Extract code backups to apps directory
4. Review logs for troubleshooting if needed

Generated by: Universal Workshop ERP Backup Script
EOF
    
    # Calculate backup size
    BACKUP_SIZE=$(du -sh "$COMPREHENSIVE_BACKUP_DIR" | cut -f1)
    log_info "Comprehensive backup completed: $COMPREHENSIVE_BACKUP_DIR (Size: $BACKUP_SIZE)"
    
    echo "$COMPREHENSIVE_BACKUP_DIR" > /tmp/latest_comprehensive_backup_path
}

# Clean old backups
cleanup_old_backups() {
    log_step "Cleaning up old backups..."
    
    if [ -d "$BACKUP_ROOT" ]; then
        # Remove backups older than retention period
        log_info "Removing backups older than $RETENTION_DAYS days..."
        find "$BACKUP_ROOT" -type d -name "*_[0-9]*" -mtime +$RETENTION_DAYS -exec rm -rf {} \; 2>/dev/null || true
        
        # Remove temporary files
        rm -f /tmp/latest_*_backup_path 2>/dev/null || true
        
        # Show remaining backups
        REMAINING_BACKUPS=$(find "$BACKUP_ROOT" -type d -name "*_[0-9]*" | wc -l)
        log_info "Cleanup completed. Remaining backups: $REMAINING_BACKUPS"
    fi
}

# Verify backup integrity
verify_backup() {
    log_step "Verifying backup integrity..."
    
    if [ -f /tmp/latest_comprehensive_backup_path ]; then
        BACKUP_PATH=$(cat /tmp/latest_comprehensive_backup_path)
        
        if [ -d "$BACKUP_PATH" ]; then
            # Check if backup directory exists and has content
            if [ "$(ls -A "$BACKUP_PATH" 2>/dev/null)" ]; then
                log_info "Backup directory exists and has content"
                
                # Check database backup
                if [ -d "$BACKUP_PATH/database" ] && [ "$(ls -A "$BACKUP_PATH/database" 2>/dev/null)" ]; then
                    log_info "Database backup verified"
                else
                    log_warning "Database backup verification failed"
                fi
                
                # Check configuration backup
                if [ -d "$BACKUP_PATH/config" ] && [ "$(ls -A "$BACKUP_PATH/config" 2>/dev/null)" ]; then
                    log_info "Configuration backup verified"
                else
                    log_warning "Configuration backup verification failed"
                fi
                
                # Check manifest file
                if [ -f "$BACKUP_PATH/backup_manifest.txt" ]; then
                    log_info "Backup manifest verified"
                else
                    log_warning "Backup manifest missing"
                fi
                
                log_info "Backup verification completed"
                return 0
            else
                log_error "Backup directory is empty"
                return 1
            fi
        else
            log_error "Backup directory not found: $BACKUP_PATH"
            return 1
        fi
    else
        log_error "No backup path found for verification"
        return 1
    fi
}

# Main backup function
main() {
    local backup_type=${1:-comprehensive}
    
    log_info "Starting Universal Workshop ERP backup (Type: $backup_type)"
    
    check_prerequisites
    
    case "$backup_type" in
        "database"|"db")
            create_database_backup
            ;;
        "config"|"configuration")
            create_config_backup
            ;;
        "code"|"application")
            create_code_backup
            ;;
        "logs")
            create_logs_backup
            ;;
        "comprehensive"|"full"|"all")
            create_comprehensive_backup
            ;;
        *)
            log_error "Unknown backup type: $backup_type"
            echo "Valid types: database, config, code, logs, comprehensive"
            exit 1
            ;;
    esac
    
    verify_backup
    cleanup_old_backups
    
    log_info "Backup process completed successfully!"
    
    if [ -f /tmp/latest_comprehensive_backup_path ]; then
        FINAL_BACKUP_PATH=$(cat /tmp/latest_comprehensive_backup_path)
        log_info "Final backup location: $FINAL_BACKUP_PATH"
    fi
}

# Usage information
usage() {
    echo "Usage: $0 [backup_type]"
    echo "Backup Types:"
    echo "  database      - Database and files only"
    echo "  config        - Configuration files only"
    echo "  code          - Application source code only"
    echo "  logs          - System and application logs only"
    echo "  comprehensive - All components (default)"
    echo ""
    echo "Examples:"
    echo "  $0                    # Comprehensive backup"
    echo "  $0 database           # Database backup only"
    echo "  $0 comprehensive      # Full backup"
    exit 1
}

# Check arguments
if [ $# -gt 1 ]; then
    usage
fi

# Run main function
main "$@"
