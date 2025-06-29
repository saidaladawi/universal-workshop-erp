#!/bin/bash
# Quick Test Script for Universal Workshop ERP License System
# Tests all major functionality with sample data

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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
    echo -e "${WHITE}  Universal Workshop ERP - Quick Test Suite${NC}"
    echo -e "${PURPLE}================================================================${NC}"
    echo ""
}

print_section() {
    echo -e "\n${BLUE}🧪 $1${NC}"
    echo "----------------------------------------"
}

print_step() {
    echo -e "${CYAN}  ➤ $1${NC}"
}

print_success() {
    echo -e "${GREEN}  ✅ $1${NC}"
}

print_error() {
    echo -e "${RED}  ❌ $1${NC}"
}

test_environment() {
    print_section "Environment Check"
    
    print_step "Checking required tools..."
    local tools=("jq" "sha256sum" "md5sum" "openssl")
    local all_good=true
    
    for tool in "${tools[@]}"; do
        if command -v "$tool" >/dev/null 2>&1; then
            print_success "$tool is available"
        else
            print_error "$tool is missing"
            all_good=false
        fi
    done
    
    if [[ "$all_good" == true ]]; then
        print_success "All required tools are available"
    fi
}

test_basic_functionality() {
    print_section "Basic Functionality Tests"
    
    print_step "Testing help command..."
    if ./generate_license_pro.sh --help >/dev/null 2>&1; then
        print_success "Help command works"
    else
        print_error "Help command failed"
    fi
    
    print_step "Testing trial license (dry-run)..."
    if ./generate_license_pro.sh "Test Workshop" TEST-001 trial --dry-run; then
        print_success "Trial license dry-run successful"
    else
        print_error "Trial license dry-run failed"
    fi
    
    print_step "Testing professional license generation..."
    if ./generate_license_pro.sh "Professional Workshop" PROF-001 professional; then
        print_success "Professional license created"
        if [[ -f "licenses/Professional_Workshop_license.json" ]]; then
            print_success "License file created successfully"
        fi
    else
        print_error "Professional license creation failed"
    fi
    
    print_step "Testing enterprise license generation..."
    if ./generate_license_pro.sh "Enterprise Corp" ENT-001 enterprise; then
        print_success "Enterprise license created"
    else
        print_error "Enterprise license creation failed"
    fi
}

test_generated_files() {
    print_section "Generated Files Check"
    
    print_step "Checking licenses directory..."
    if [[ -d "licenses" ]]; then
        local license_count=$(find licenses -name "*.json" | wc -l)
        print_success "Licenses directory exists with $license_count license files"
        
        # Show generated files
        find licenses -name "*.json" | while read -r file; do
            print_success "Found: $(basename "$file")"
        done
    else
        print_error "Licenses directory not found"
    fi
    
    print_step "Checking logs directory..."
    if [[ -d "logs" ]]; then
        print_success "Logs directory exists"
        if [[ -f "logs/license_generation.log" ]]; then
            local log_lines=$(wc -l < "logs/license_generation.log")
            print_success "Log file exists with $log_lines entries"
        fi
    else
        print_error "Logs directory not found"
    fi
}

main() {
    print_header
    
    echo -e "${CYAN}🚀 Running comprehensive test suite...${NC}"
    echo ""
    
    test_environment
    test_basic_functionality
    test_generated_files
    
    echo ""
    print_success "Quick test completed!"
    echo ""
    echo -e "${CYAN}📁 Check the following directories for results:${NC}"
    echo -e "  • ${WHITE}licenses/${NC} - Generated license files"
    echo -e "  • ${WHITE}logs/${NC} - Operation logs"
    echo -e "  • ${WHITE}client_data/${NC} - Client information"
    echo ""
    echo -e "${CYAN}🔧 Next steps:${NC}"
    echo -e "  • Run: ${WHITE}./client_manager.sh${NC} for interactive management"
    echo -e "  • Run: ${WHITE}./generate_license_pro.sh --help${NC} for command options"
    echo -e "  • Check: ${WHITE}README.md${NC} for complete documentation"
    echo ""
}

main "$@"
