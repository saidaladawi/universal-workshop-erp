#!/bin/bash
# Universal Workshop ERP - Professional License Generator
# Author: Said Al-Adawi
# Version: 3.0-Professional
# Usage: ./generate_license.sh [CLIENT_NAME] [CLIENT_ID] [LICENSE_TYPE]

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# =============================================================================
# CONFIGURATION AND CONSTANTS
# =============================================================================

readonly SCRIPT_VERSION="3.0-Professional"
readonly SCRIPT_NAME="Universal Workshop License Generator"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly LICENSES_DIR="${SCRIPT_DIR}/licenses"
readonly BACKUPS_DIR="${SCRIPT_DIR}/backups"
readonly LOGS_DIR="${SCRIPT_DIR}/logs"
readonly LOG_FILE="${LOGS_DIR}/license_generation.log"

# License types and configurations
declare -A LICENSE_CONFIGS=(
    ["trial"]="5 [\"workshop_management\",\"basic_inventory\"] 30"
    ["basic"]="5 [\"workshop_management\",\"basic_inventory\"] 0"
    ["professional"]="25 [\"workshop_management\",\"inventory\",\"scrap_management\",\"reports\"] 0"
    ["enterprise"]="100 [\"workshop_management\",\"inventory\",\"scrap_management\",\"reports\",\"api_access\",\"advanced_analytics\"] 0"
    ["unlimited"]="999 [\"workshop_management\",\"inventory\",\"scrap_management\",\"reports\",\"api_access\",\"advanced_analytics\",\"custom_modules\"] 0"
)

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly WHITE='\033[1;37m'
readonly NC='\033[0m' # No Color

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Ensure logs directory exists
    mkdir -p "$LOGS_DIR"
    
    # Write to log file
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
    
    # Also output to console based on level
    case "$level" in
        "ERROR")   echo -e "${RED}❌ ERROR: $message${NC}" ;;
        "WARNING") echo -e "${YELLOW}⚠️  WARNING: $message${NC}" ;;
        "INFO")    echo -e "${BLUE}ℹ️  INFO: $message${NC}" ;;
        "SUCCESS") echo -e "${GREEN}✅ SUCCESS: $message${NC}" ;;
        "DEBUG")   echo -e "${PURPLE}🔍 DEBUG: $message${NC}" ;;
    esac
}

print_header() {
    echo -e "${PURPLE}================================================================${NC}"
    echo -e "${WHITE}  $SCRIPT_NAME v$SCRIPT_VERSION${NC}"
    echo -e "${PURPLE}================================================================${NC}"
    echo ""
}

print_section() {
    echo -e "\n${CYAN}🔧 $1${NC}"
    echo "----------------------------------------"
}

show_usage() {
    cat << 'EOF'
🔐 Universal Workshop ERP - Professional License Generator

USAGE:
    ./generate_license.sh [CLIENT_NAME] [CLIENT_ID] [LICENSE_TYPE]

EXAMPLES:
    ./generate_license.sh "Alfarsi Workshop" ALFARSI-001 professional
    ./generate_license.sh "Gulf Auto Center" GULF-002 enterprise
    ./generate_license.sh "Test Workshop" TEST-001 trial

LICENSE TYPES:
    trial        - 30 days, 5 users, basic features (for testing)
    basic        - Permanent, 5 users, basic features
    professional - Permanent, 25 users, advanced features
    enterprise   - Permanent, 100 users, full features
    unlimited    - Permanent, 999 users, all features + custom modules

OPTIONS:
    --dry-run           Preview what would be generated (no files created)
    --help             Show this help message
    --check            Check environment and dependencies
    --list-licenses    List all generated licenses
    --validate FILE    Validate an existing license file
    --backup           Create backup of existing licenses
    --rollback         Rollback to previous backup

ENVIRONMENT:
    The script requires: jq, sha256sum, md5sum, openssl
    All dependencies will be checked automatically.

GENERATED FILES:
    licenses/[CLIENT]_license.json    - Main license file
    licenses/[CLIENT]_info.txt        - Human-readable info
    licenses/[CLIENT]_certificate.pdf - License certificate (if available)
    logs/license_generation.log       - Operation logs
    backups/                          - Automatic backups

EXAMPLES OF CLIENT NAMES:
    English: "Alfarsi Automotive Workshop"
    Arabic supported via environment variables (see documentation)

EOF
}

# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

validate_environment() {
    log "INFO" "Checking environment and dependencies..."
    
    local missing_tools=()
    local required_tools=("jq" "sha256sum" "md5sum" "date" "openssl")
    
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            missing_tools+=("$tool")
        fi
    done
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log "ERROR" "Missing required tools: ${missing_tools[*]}"
        echo -e "${RED}To install missing tools:${NC}"
        echo "  Ubuntu/Debian: sudo apt-get install ${missing_tools[*]}"
        echo "  CentOS/RHEL:   sudo yum install ${missing_tools[*]}"
        echo "  MacOS:         brew install ${missing_tools[*]}"
        return 1
    fi
    
    log "SUCCESS" "All required tools are available"
    return 0
}

validate_inputs() {
    local client_name="$1"
    local client_id="$2"
    local license_type="$3"
    
    # Validate client name
    if [[ -z "$client_name" ]]; then
        log "ERROR" "Client name is required"
        return 1
    fi
    
    if [[ ${#client_name} -lt 3 ]]; then
        log "ERROR" "Client name must be at least 3 characters long"
        return 1
    fi
    
    if [[ ${#client_name} -gt 100 ]]; then
        log "ERROR" "Client name must be less than 100 characters"
        return 1
    fi
    
    # Validate client ID
    if [[ -z "$client_id" ]]; then
        log "ERROR" "Client ID is required"
        return 1
    fi
    
    if [[ ! "$client_id" =~ ^[A-Z0-9-]+$ ]]; then
        log "ERROR" "Client ID must contain only uppercase letters, numbers, and hyphens"
        return 1
    fi
    
    # Validate license type
    if [[ ! "${LICENSE_CONFIGS[$license_type]+isset}" ]]; then
        log "ERROR" "Invalid license type: $license_type"
        echo -e "${YELLOW}Available types: ${!LICENSE_CONFIGS[*]}${NC}"
        return 1
    fi
    
    log "SUCCESS" "Input validation passed"
    return 0
}

check_existing_license() {
    local client_name="$1"
    local client_id="$2"
    
    local safe_name="${client_name// /_}"
    local license_file="$LICENSES_DIR/${safe_name}_license.json"
    
    if [[ -f "$license_file" ]]; then
        log "WARNING" "License already exists for client: $client_name"
        echo -e "${YELLOW}Existing license found: $license_file${NC}"
        echo -e "${YELLOW}Do you want to overwrite it? (y/N):${NC} "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            log "INFO" "Operation cancelled by user"
            return 1
        fi
        
        # Create backup before overwriting
        create_backup "$license_file"
    fi
    
    return 0
}

# =============================================================================
# BACKUP AND ROLLBACK FUNCTIONS
# =============================================================================

create_backup() {
    local file_to_backup="$1"
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    
    mkdir -p "$BACKUPS_DIR"
    
    if [[ -f "$file_to_backup" ]]; then
        local backup_file="$BACKUPS_DIR/$(basename "$file_to_backup")_$timestamp"
        cp "$file_to_backup" "$backup_file"
        log "INFO" "Backup created: $backup_file"
    fi
}

create_full_backup() {
    log "INFO" "Creating full backup of licenses directory..."
    
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_archive="$BACKUPS_DIR/licenses_backup_$timestamp.tar.gz"
    
    mkdir -p "$BACKUPS_DIR"
    
    if [[ -d "$LICENSES_DIR" ]]; then
        tar -czf "$backup_archive" -C "$(dirname "$LICENSES_DIR")" "$(basename "$LICENSES_DIR")"
        log "SUCCESS" "Full backup created: $backup_archive"
        echo -e "${GREEN}Backup archive: $backup_archive${NC}"
    else
        log "WARNING" "No licenses directory found to backup"
    fi
}

rollback_from_backup() {
    log "INFO" "Available backups:"
    
    if [[ ! -d "$BACKUPS_DIR" ]] || [[ -z "$(ls -A "$BACKUPS_DIR" 2>/dev/null)" ]]; then
        log "ERROR" "No backups available"
        return 1
    fi
    
    local backups=($(ls -t "$BACKUPS_DIR"/licenses_backup_*.tar.gz 2>/dev/null))
    
    if [[ ${#backups[@]} -eq 0 ]]; then
        log "ERROR" "No backup archives found"
        return 1
    fi
    
    echo -e "${CYAN}Available backup archives:${NC}"
    for i in "${!backups[@]}"; do
        echo "  $((i+1)). $(basename "${backups[$i]}")"
    done
    
    echo -e "${YELLOW}Select backup to restore (1-${#backups[@]}):${NC} "
    read -r selection
    
    if [[ ! "$selection" =~ ^[0-9]+$ ]] || [[ "$selection" -lt 1 ]] || [[ "$selection" -gt ${#backups[@]} ]]; then
        log "ERROR" "Invalid selection"
        return 1
    fi
    
    local selected_backup="${backups[$((selection-1))]}"
    
    echo -e "${RED}WARNING: This will replace all current licenses!${NC}"
    echo -e "${YELLOW}Continue with rollback? (y/N):${NC} "
    read -r confirm
    
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        log "INFO" "Rollback cancelled"
        return 1
    fi
    
    # Create backup of current state before rollback
    create_full_backup
    
    # Remove current licenses directory
    rm -rf "$LICENSES_DIR"
    
    # Extract backup
    tar -xzf "$selected_backup" -C "$(dirname "$LICENSES_DIR")"
    
    log "SUCCESS" "Rollback completed from: $(basename "$selected_backup")"
}

# =============================================================================
# LICENSE GENERATION FUNCTIONS
# =============================================================================

generate_license_data() {
    local client_name="$1"
    local client_id="$2"
    local license_type="$3"
    
    # Parse license configuration
    local config="${LICENSE_CONFIGS[$license_type]}"
    local max_users=$(echo "$config" | cut -d' ' -f1)
    local features=$(echo "$config" | cut -d' ' -f2)
    local trial_days=$(echo "$config" | cut -d' ' -f3)
    
    # Generate dates
    local issue_date=$(date -Iseconds)
    local expiry_date
    local is_permanent
    
    if [[ "$trial_days" -eq 0 ]]; then
        expiry_date=$(date -d "+100 years" -Iseconds)
        is_permanent=true
    else
        expiry_date=$(date -d "+${trial_days} days" -Iseconds)
        is_permanent=false
    fi
    
    local support_until=$(date -d "+1 year" -Iseconds)
    
    # Generate cryptographic signatures
    local signature_data="${client_id}${issue_date}"
    local signature=$(echo -n "$signature_data" | sha256sum | cut -d' ' -f1)
    
    local hash_data="${client_name}${client_id}${license_type}"
    local hash_value=$(echo -n "$hash_data" | md5sum | cut -d' ' -f1)
    
    # Generate secure license key
    local license_key=$(openssl rand -hex 32)
    
    # Create license JSON
    cat << EOF
{
  "license_data": {
    "client_name": "$client_name",
    "client_id": "$client_id",
    "license_type": "$license_type",
    "license_key": "$license_key",
    "max_users": $max_users,
    "features": $features,
    "issue_date": "$issue_date",
    "expiry_date": "$expiry_date",
    "is_permanent": $is_permanent,
    "trial_days": $trial_days,
    "version": "2.0",
    "support_until": "$support_until"
  },
  "security": {
    "signature": "$signature",
    "hash": "$hash_value",
    "algorithm": "SHA256-MD5",
    "key_version": "v2.0"
  },
  "metadata": {
    "created_by": "$(whoami)",
    "created_on": "$(hostname)",
    "created_at": "$issue_date",
    "script_version": "$SCRIPT_VERSION",
    "generator": "$SCRIPT_NAME"
  }
}
EOF
}

create_license_info() {
    local client_name="$1"
    local client_id="$2"
    local license_type="$3"
    local license_file="$4"
    
    # Parse license configuration
    local config="${LICENSE_CONFIGS[$license_type]}"
    local max_users=$(echo "$config" | cut -d' ' -f1)
    local features=$(echo "$config" | cut -d' ' -f2)
    local trial_days=$(echo "$config" | cut -d' ' -f3)
    
    local issue_date=$(date -Iseconds)
    local support_until=$(date -d "+1 year" -Iseconds)
    
    cat << EOF
================================================================
UNIVERSAL WORKSHOP ERP - LICENSE CERTIFICATE
================================================================

Client Information:
  Name: $client_name
  ID: $client_id
  License Type: $license_type

License Details:
  Maximum Users: $max_users
  Trial Period: $(if [[ $trial_days -eq 0 ]]; then echo "Permanent License"; else echo "$trial_days days"; fi)
  Issue Date: $(date -d "$issue_date" '+%Y-%m-%d %H:%M:%S UTC')
  Expiry Date: $(if [[ $trial_days -eq 0 ]]; then echo "Never (Permanent)"; else date -d "$issue_date +$trial_days days" '+%Y-%m-%d %H:%M:%S UTC'; fi)
  Support Until: $(date -d "$support_until" '+%Y-%m-%d %H:%M:%S UTC')

Features Included:
$(echo "$features" | jq -r '.[]' | sed 's/^/  - /')

Technical Information:
  License File: $license_file
  Script Version: $SCRIPT_VERSION
  Generated By: $(whoami)@$(hostname)
  Generation Time: $(date '+%Y-%m-%d %H:%M:%S UTC')

Security:
  Signature: $(echo -n "${client_id}${issue_date}" | sha256sum | cut -d' ' -f1)
  Hash: $(echo -n "${client_name}${client_id}${license_type}" | md5sum | cut -d' ' -f1)
  Algorithm: SHA256-MD5

================================================================
This license is valid only for the specified client and cannot
be transferred or modified without authorization.
================================================================
EOF
}

# =============================================================================
# MAIN GENERATION FUNCTION
# =============================================================================

generate_license() {
    local client_name="$1"
    local client_id="$2"
    local license_type="$3"
    local dry_run="$4"
    
    print_section "License Generation Process"
    
    # Validate inputs
    if ! validate_inputs "$client_name" "$client_id" "$license_type"; then
        return 1
    fi
    
    # Create safe filename
    local safe_name="${client_name// /_}"
    safe_name="${safe_name//[^a-zA-Z0-9_-]/}"  # Remove special characters
    
    local license_file="$LICENSES_DIR/${safe_name}_license.json"
    local info_file="$LICENSES_DIR/${safe_name}_info.txt"
    
    log "INFO" "Generating license for: $client_name ($client_id)"
    log "INFO" "License type: $license_type"
    
    if [[ "$dry_run" == "true" ]]; then
        log "INFO" "DRY RUN MODE - No files will be created"
        echo -e "${YELLOW}📋 Preview of license data:${NC}"
        echo ""
        echo "Client Name: $client_name"
        echo "Client ID: $client_id"
        echo "License Type: $license_type"
        echo "License File: $license_file"
        echo "Info File: $info_file"
        echo ""
        echo -e "${CYAN}Sample JSON structure:${NC}"
        generate_license_data "$client_name" "$client_id" "$license_type" | jq .
        return 0
    fi
    
    # Check for existing licenses
    if ! check_existing_license "$client_name" "$client_id"; then
        return 1
    fi
    
    # Create directories
    mkdir -p "$LICENSES_DIR" "$LOGS_DIR" "$BACKUPS_DIR"
    
    # Generate license file
    log "INFO" "Creating license file: $license_file"
    if ! generate_license_data "$client_name" "$client_id" "$license_type" > "$license_file"; then
        log "ERROR" "Failed to create license file"
        return 1
    fi
    
    # Validate generated JSON
    if ! jq empty "$license_file" 2>/dev/null; then
        log "ERROR" "Generated license file is not valid JSON"
        rm -f "$license_file"
        return 1
    fi
    
    # Generate info file
    log "INFO" "Creating info file: $info_file"
    if ! create_license_info "$client_name" "$client_id" "$license_type" "$license_file" > "$info_file"; then
        log "ERROR" "Failed to create info file"
        return 1
    fi
    
    # Set appropriate permissions
    chmod 644 "$license_file" "$info_file"
    
    log "SUCCESS" "License generated successfully"
    
    # Display summary
    echo ""
    echo -e "${GREEN}✅ License Generation Complete${NC}"
    echo "----------------------------------------"
    echo -e "📄 License File: ${BLUE}$license_file${NC}"
    echo -e "📋 Info File: ${BLUE}$info_file${NC}"
    echo ""
    echo -e "${CYAN}📊 License Summary:${NC}"
    echo "  Client: $client_name"
    echo "  ID: $client_id"
    echo "  Type: $license_type"
    
    # Parse and display configuration
    local config="${LICENSE_CONFIGS[$license_type]}"
    local max_users=$(echo "$config" | cut -d' ' -f1)
    local trial_days=$(echo "$config" | cut -d' ' -f3)
    
    echo "  Max Users: $max_users"
    echo "  Duration: $(if [[ $trial_days -eq 0 ]]; then echo "Permanent"; else echo "$trial_days days"; fi)"
    echo ""
    echo -e "${GREEN}🚀 Next Steps:${NC}"
    echo "  1. Copy license file to client installation"
    echo "  2. Provide info file to client for reference"
    echo "  3. Keep backup of generated files"
}

# =============================================================================
# ADDITIONAL UTILITY FUNCTIONS
# =============================================================================

list_licenses() {
    print_section "Generated Licenses"
    
    if [[ ! -d "$LICENSES_DIR" ]] || [[ -z "$(ls -A "$LICENSES_DIR" 2>/dev/null)" ]]; then
        log "INFO" "No licenses found"
        return 0
    fi
    
    local license_files=("$LICENSES_DIR"/*_license.json)
    
    if [[ ! -e "${license_files[0]}" ]]; then
        log "INFO" "No license files found"
        return 0
    fi
    
    echo -e "${CYAN}Found licenses:${NC}"
    echo ""
    
    for license_file in "${license_files[@]}"; do
        if [[ -f "$license_file" ]]; then
            local client_name=$(jq -r '.license_data.client_name' "$license_file" 2>/dev/null || echo "Unknown")
            local client_id=$(jq -r '.license_data.client_id' "$license_file" 2>/dev/null || echo "Unknown")
            local license_type=$(jq -r '.license_data.license_type' "$license_file" 2>/dev/null || echo "Unknown")
            local created=$(jq -r '.metadata.created_at' "$license_file" 2>/dev/null || echo "Unknown")
            
            echo -e "📄 ${GREEN}$(basename "$license_file")${NC}"
            echo "   Client: $client_name"
            echo "   ID: $client_id"
            echo "   Type: $license_type"
            echo "   Created: $created"
            echo ""
        fi
    done
}

validate_license_file() {
    local license_file="$1"
    
    if [[ ! -f "$license_file" ]]; then
        log "ERROR" "License file not found: $license_file"
        return 1
    fi
    
    log "INFO" "Validating license file: $license_file"
    
    # Check JSON validity
    if ! jq empty "$license_file" 2>/dev/null; then
        log "ERROR" "Invalid JSON format"
        return 1
    fi
    
    # Check required fields
    local required_fields=("license_data.client_name" "license_data.client_id" "license_data.license_type")
    
    for field in "${required_fields[@]}"; do
        if [[ "$(jq -r ".$field" "$license_file" 2>/dev/null)" == "null" ]]; then
            log "ERROR" "Missing required field: $field"
            return 1
        fi
    done
    
    # Validate signatures
    local client_name=$(jq -r '.license_data.client_name' "$license_file")
    local client_id=$(jq -r '.license_data.client_id' "$license_file")
    local license_type=$(jq -r '.license_data.license_type' "$license_file")
    local issue_date=$(jq -r '.license_data.issue_date' "$license_file")
    
    local stored_signature=$(jq -r '.security.signature' "$license_file")
    local stored_hash=$(jq -r '.security.hash' "$license_file")
    
    local expected_signature=$(echo -n "${client_id}${issue_date}" | sha256sum | cut -d' ' -f1)
    local expected_hash=$(echo -n "${client_name}${client_id}${license_type}" | md5sum | cut -d' ' -f1)
    
    if [[ "$stored_signature" != "$expected_signature" ]]; then
        log "ERROR" "Invalid signature - license may be tampered"
        return 1
    fi
    
    if [[ "$stored_hash" != "$expected_hash" ]]; then
        log "ERROR" "Invalid hash - license may be tampered"
        return 1
    fi
    
    log "SUCCESS" "License file is valid"
    
    # Display license info
    echo -e "\n${CYAN}License Information:${NC}"
    echo "  Client: $client_name"
    echo "  ID: $client_id"
    echo "  Type: $license_type"
    echo "  Issue Date: $issue_date"
    echo "  Expiry: $(jq -r '.license_data.expiry_date' "$license_file")"
    echo "  Permanent: $(jq -r '.license_data.is_permanent' "$license_file")"
    
    return 0
}

# =============================================================================
# MAIN FUNCTION
# =============================================================================

main() {
    local client_name=""
    local client_id=""
    local license_type="professional"
    local dry_run="false"
    local command=""
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                dry_run="true"
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            --check)
                command="check"
                shift
                ;;
            --list-licenses)
                command="list"
                shift
                ;;
            --validate)
                command="validate"
                shift
                if [[ $# -gt 0 ]]; then
                    license_file_to_validate="$1"
                    shift
                else
                    log "ERROR" "--validate requires a file path"
                    exit 1
                fi
                ;;
            --backup)
                command="backup"
                shift
                ;;
            --rollback)
                command="rollback"
                shift
                ;;
            -*)
                log "ERROR" "Unknown option: $1"
                show_usage
                exit 1
                ;;
            *)
                if [[ -z "$client_name" ]]; then
                    client_name="$1"
                elif [[ -z "$client_id" ]]; then
                    client_id="$1"
                elif [[ -z "$license_type" ]] || [[ "$license_type" == "professional" ]]; then
                    license_type="$1"
                else
                    log "ERROR" "Too many arguments"
                    show_usage
                    exit 1
                fi
                shift
                ;;
        esac
    done
    
    print_header
    
    # Execute commands
    case "$command" in
        "check")
            validate_environment
            exit $?
            ;;
        "list")
            list_licenses
            exit $?
            ;;
        "validate")
            validate_license_file "$license_file_to_validate"
            exit $?
            ;;
        "backup")
            create_full_backup
            exit $?
            ;;
        "rollback")
            rollback_from_backup
            exit $?
            ;;
        "")
            # Main license generation
            ;;
        *)
            log "ERROR" "Unknown command: $command"
            exit 1
            ;;
    esac
    
    # Validate environment first
    if ! validate_environment; then
        exit 1
    fi
    
    # Auto-generate client ID if not provided
    if [[ -z "$client_id" && -n "$client_name" ]]; then
        # Create ID from client name + date
        local base_id="${client_name// /-}"
        base_id="${base_id//[^a-zA-Z0-9-]/}"  # Remove special characters
        base_id=$(echo "$base_id" | tr '[:lower:]' '[:upper:]')
        client_id="${base_id}-$(date +%Y%m%d)"
        log "INFO" "Auto-generated client ID: $client_id"
    fi
    
    # Check if we have required parameters
    if [[ -z "$client_name" ]]; then
        log "ERROR" "Client name is required"
        echo ""
        show_usage
        exit 1
    fi
    
    # Generate the license
    if ! generate_license "$client_name" "$client_id" "$license_type" "$dry_run"; then
        log "ERROR" "License generation failed"
        exit 1
    fi
    
    log "SUCCESS" "Script completed successfully"
}

# =============================================================================
# SCRIPT EXECUTION
# =============================================================================

# Only run main if script is executed directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
