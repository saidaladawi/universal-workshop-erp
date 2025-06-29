#!/bin/bash
# Universal Workshop ERP - Installation and Setup Script
# Author: Said Al-Adawi
# Version: 3.0-Professional

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly WHITE='\033[1;37m'
readonly NC='\033[0m'

print_header() {
    echo -e "${PURPLE}================================================================${NC}"
    echo -e "${WHITE}  Universal Workshop ERP - Setup & Installation${NC}"
    echo -e "${PURPLE}================================================================${NC}"
    echo ""
}

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case "$level" in
        "ERROR")   echo -e "${RED}❌ [$timestamp] ERROR: $message${NC}" ;;
        "WARNING") echo -e "${YELLOW}⚠️  [$timestamp] WARNING: $message${NC}" ;;
        "INFO")    echo -e "${BLUE}ℹ️  [$timestamp] INFO: $message${NC}" ;;
        "SUCCESS") echo -e "${GREEN}✅ [$timestamp] SUCCESS: $message${NC}" ;;
    esac
}

check_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt-get >/dev/null 2>&1; then
            echo "ubuntu"
        elif command -v yum >/dev/null 2>&1; then
            echo "centos"
        else
            echo "linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "unknown"
    fi
}

install_dependencies() {
    local os_type=$(check_os)
    
    log "INFO" "Detected OS: $os_type"
    log "INFO" "Installing required dependencies..."
    
    local packages=("jq" "openssl")
    
    case "$os_type" in
        "ubuntu")
            sudo apt-get update
            sudo apt-get install -y "${packages[@]}" coreutils
            ;;
        "centos")
            sudo yum install -y "${packages[@]}" coreutils
            ;;
        "macos")
            if ! command -v brew >/dev/null 2>&1; then
                log "ERROR" "Homebrew is required for macOS. Install from https://brew.sh"
                return 1
            fi
            brew install "${packages[@]}"
            ;;
        *)
            log "WARNING" "Unknown OS. Please install manually: ${packages[*]}"
            ;;
    esac
    
    log "SUCCESS" "Dependencies installed"
}

setup_directories() {
    log "INFO" "Setting up directory structure..."
    
    local dirs=(
        "$SCRIPT_DIR/licenses"
        "$SCRIPT_DIR/logs"
        "$SCRIPT_DIR/backups"
        "$SCRIPT_DIR/client_data"
        "$SCRIPT_DIR/templates"
        "$SCRIPT_DIR/reports"
    )
    
    for dir in "${dirs[@]}"; do
        mkdir -p "$dir"
        log "INFO" "Created directory: $dir"
    done
    
    log "SUCCESS" "Directory structure created"
}

set_permissions() {
    log "INFO" "Setting file permissions..."
    
    # Make scripts executable
    local scripts=(
        "generate_license_pro.sh"
        "client_manager.sh"
        "environment_check.sh"
    )
    
    for script in "${scripts[@]}"; do
        if [[ -f "$SCRIPT_DIR/$script" ]]; then
            chmod +x "$SCRIPT_DIR/$script"
            log "INFO" "Made executable: $script"
        fi
    done
    
    # Set directory permissions
    chmod 755 "$SCRIPT_DIR"/{licenses,logs,backups,client_data} 2>/dev/null || true
    
    log "SUCCESS" "Permissions set"
}

create_config_file() {
    local config_file="$SCRIPT_DIR/config.json"
    
    if [[ -f "$config_file" ]]; then
        log "INFO" "Configuration file already exists"
        return 0
    fi
    
    log "INFO" "Creating configuration file..."
    
    cat > "$config_file" << 'EOF'
{
  "version": "3.0-Professional",
  "installation_date": "",
  "default_license_type": "professional",
  "auto_backup": true,
  "backup_retention_days": 30,
  "log_level": "INFO",
  "security": {
    "require_confirmation": true,
    "validate_client_id": true,
    "auto_generate_ids": true
  },
  "paths": {
    "licenses_dir": "./licenses",
    "logs_dir": "./logs",
    "backups_dir": "./backups",
    "client_data_dir": "./client_data"
  },
  "license_types": {
    "trial": {
      "duration_days": 30,
      "max_users": 5,
      "features": ["workshop_management", "basic_inventory"]
    },
    "basic": {
      "duration_days": 0,
      "max_users": 5,
      "features": ["workshop_management", "basic_inventory"]
    },
    "professional": {
      "duration_days": 0,
      "max_users": 25,
      "features": ["workshop_management", "inventory", "scrap_management", "reports"]
    },
    "enterprise": {
      "duration_days": 0,
      "max_users": 100,
      "features": ["workshop_management", "inventory", "scrap_management", "reports", "api_access", "advanced_analytics"]
    },
    "unlimited": {
      "duration_days": 0,
      "max_users": 999,
      "features": ["workshop_management", "inventory", "scrap_management", "reports", "api_access", "advanced_analytics", "custom_modules"]
    }
  }
}
EOF
    
    # Update installation date
    local timestamp=$(date -Iseconds)
    local updated_config=$(jq ".installation_date = \"$timestamp\"" "$config_file")
    echo "$updated_config" > "$config_file"
    
    log "SUCCESS" "Configuration file created: $config_file"
}

create_readme() {
    local readme_file="$SCRIPT_DIR/README.md"
    
    log "INFO" "Creating README file..."
    
    cat > "$readme_file" << 'EOF'
# Universal Workshop ERP - Client Deployment Scripts

This directory contains professional-grade scripts for managing Universal Workshop ERP licenses and client deployments.

## 📁 Directory Structure

```
client_deployment/
├── generate_license_pro.sh    # Professional license generator
├── client_manager.sh          # Interactive client management
├── environment_check.sh       # Environment validation
├── setup.sh                   # Installation script
├── config.json                # Configuration file
├── README.md                  # This file
├── licenses/                  # Generated license files
├── logs/                      # Operation logs
├── backups/                   # Automatic backups
├── client_data/               # Client database
├── templates/                 # License templates
└── reports/                   # Generated reports
```

## 🚀 Quick Start

1. **Install Dependencies:**
   ```bash
   ./setup.sh --install-deps
   ```

2. **Check Environment:**
   ```bash
   ./generate_license_pro.sh --check
   ```

3. **Interactive Client Management:**
   ```bash
   ./client_manager.sh
   ```

4. **Generate License (Command Line):**
   ```bash
   ./generate_license_pro.sh "Client Name" CLIENT-ID professional
   ```

## 📝 License Types

| Type | Duration | Users | Features |
|------|----------|-------|----------|
| trial | 30 days | 5 | Basic testing |
| basic | Permanent | 5 | Basic features |
| professional | Permanent | 25 | Advanced features |
| enterprise | Permanent | 100 | Full features |
| unlimited | Permanent | 999 | All features + custom |

## 🔧 Usage Examples

### Command Line License Generation
```bash
# Trial license for testing
./generate_license_pro.sh "Test Workshop" TEST-001 trial

# Professional license
./generate_license_pro.sh "Alfarsi Workshop" ALFARSI-001 professional

# Enterprise license
./generate_license_pro.sh "Gulf Auto Center" GULF-002 enterprise

# Dry run (preview only)
./generate_license_pro.sh "Preview Client" PREVIEW-001 basic --dry-run
```

### Interactive Management
```bash
# Start interactive client manager
./client_manager.sh

# Available options:
# 1. Add new client
# 2. Generate license for existing client
# 3. List all clients
# 4. Search clients
# 5. Client management tools
```

### Validation and Maintenance
```bash
# Validate existing license
./generate_license_pro.sh --validate licenses/client_license.json

# List all generated licenses
./generate_license_pro.sh --list-licenses

# Create backup
./generate_license_pro.sh --backup

# Rollback to previous backup
./generate_license_pro.sh --rollback
```

## 🔐 Security Features

- **Cryptographic signatures** using SHA-256 and MD5
- **Secure license keys** generated with OpenSSL
- **Tamper detection** for license files
- **Automatic backups** before modifications
- **Client ID validation** and auto-generation
- **Input sanitization** and validation

## 📊 Generated Files

For each client, the following files are generated:

1. **`client_license.json`** - Main license file for system activation
2. **`client_info.txt`** - Human-readable license information
3. **`client_certificate.pdf`** - Official license certificate (if available)

## 🛠️ Maintenance

### Logs
- All operations are logged to `logs/license_generation.log`
- Log levels: ERROR, WARNING, INFO, SUCCESS, DEBUG

### Backups
- Automatic backups before overwriting licenses
- Full backup archives in `backups/` directory
- Configurable retention period (default: 30 days)

### Configuration
- System settings in `config.json`
- Customizable license types and features
- Adjustable security and validation settings

## 🔧 Troubleshooting

### Common Issues

1. **Missing dependencies:**
   ```bash
   ./setup.sh --install-deps
   ```

2. **Permission errors:**
   ```bash
   ./setup.sh --fix-permissions
   ```

3. **Environment check:**
   ```bash
   ./environment_check.sh
   ```

### Support

For technical support or questions:
- Check logs in `logs/` directory
- Run environment check
- Validate existing licenses
- Review configuration settings

## 📄 License

Universal Workshop ERP - Professional License Management
Copyright (c) 2025 Said Al-Adawi
EOF
    
    log "SUCCESS" "README file created: $readme_file"
}

validate_installation() {
    log "INFO" "Validating installation..."
    
    # Check required tools
    local required_tools=("jq" "sha256sum" "md5sum" "openssl")
    local missing_tools=()
    
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            missing_tools+=("$tool")
        fi
    done
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log "ERROR" "Missing tools: ${missing_tools[*]}"
        return 1
    fi
    
    # Check scripts
    local scripts=("generate_license_pro.sh" "client_manager.sh")
    for script in "${scripts[@]}"; do
        if [[ ! -x "$SCRIPT_DIR/$script" ]]; then
            log "ERROR" "Script not executable: $script"
            return 1
        fi
    done
    
    # Test license generation
    if ! "$SCRIPT_DIR/generate_license_pro.sh" "Test Client" TEST-VALIDATION trial --dry-run >/dev/null 2>&1; then
        log "ERROR" "License generation test failed"
        return 1
    fi
    
    log "SUCCESS" "Installation validation passed"
    return 0
}

show_usage() {
    cat << 'EOF'
Universal Workshop ERP - Setup & Installation

USAGE:
    ./setup.sh [OPTIONS]

OPTIONS:
    --install-deps      Install system dependencies
    --setup-dirs        Create directory structure
    --fix-permissions   Fix file and directory permissions
    --create-config     Create configuration file
    --validate          Validate installation
    --full-install      Complete installation (all above)
    --help              Show this help message

EXAMPLES:
    ./setup.sh --full-install    # Complete setup
    ./setup.sh --install-deps    # Install dependencies only
    ./setup.sh --validate        # Check installation

REQUIREMENTS:
    - Linux, macOS, or compatible Unix system
    - sudo access for dependency installation
    - Internet connection for package downloads

EOF
}

main() {
    local install_deps=false
    local setup_dirs=false
    local fix_permissions=false
    local create_config=false
    local validate=false
    local full_install=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --install-deps)
                install_deps=true
                shift
                ;;
            --setup-dirs)
                setup_dirs=true
                shift
                ;;
            --fix-permissions)
                fix_permissions=true
                shift
                ;;
            --create-config)
                create_config=true
                shift
                ;;
            --validate)
                validate=true
                shift
                ;;
            --full-install)
                full_install=true
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                log "ERROR" "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # If no options provided, show usage
    if [[ "$install_deps" == false && "$setup_dirs" == false && "$fix_permissions" == false && 
          "$create_config" == false && "$validate" == false && "$full_install" == false ]]; then
        show_usage
        exit 0
    fi
    
    print_header
    
    # Full installation
    if [[ "$full_install" == true ]]; then
        install_deps=true
        setup_dirs=true
        fix_permissions=true
        create_config=true
        validate=true
    fi
    
    # Execute requested operations
    if [[ "$install_deps" == true ]]; then
        install_dependencies
    fi
    
    if [[ "$setup_dirs" == true ]]; then
        setup_directories
    fi
    
    if [[ "$fix_permissions" == true ]]; then
        set_permissions
    fi
    
    if [[ "$create_config" == true ]]; then
        create_config_file
    fi
    
    # Always create README if doing setup
    if [[ "$setup_dirs" == true || "$full_install" == true ]]; then
        create_readme
    fi
    
    if [[ "$validate" == true ]]; then
        validate_installation
    fi
    
    echo ""
    log "SUCCESS" "Setup completed successfully!"
    echo ""
    echo -e "${CYAN}Next steps:${NC}"
    echo -e "  1. Run: ${WHITE}./environment_check.sh${NC} to verify environment"
    echo -e "  2. Run: ${WHITE}./client_manager.sh${NC} for interactive management"
    echo -e "  3. Or use: ${WHITE}./generate_license_pro.sh --help${NC} for command line usage"
    echo ""
}

# Execute main function with all arguments
main "$@"
