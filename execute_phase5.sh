#!/bin/bash
#
# Phase 5: Professional Testing & Validation Execution Script
# Universal Workshop ERP Refactoring Project
#
# This script executes Phase 5 testing with professional standards:
# - Comprehensive safety checks
# - Professional logging
# - Stakeholder notifications
# - Decision support framework
#

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# ===========================================
# CONFIGURATION & CONSTANTS
# ===========================================

PHASE="Phase 5: Testing & Validation"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="phase5_execution_${TIMESTAMP}.log"
PYTHON_SCRIPT="phase5_testing_validation.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# ===========================================
# UTILITY FUNCTIONS
# ===========================================

log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        "INFO")  echo -e "${BLUE}[${timestamp}] INFO: ${message}${NC}" | tee -a "$LOG_FILE" ;;
        "SUCCESS") echo -e "${GREEN}[${timestamp}] SUCCESS: ${message}${NC}" | tee -a "$LOG_FILE" ;;
        "WARNING") echo -e "${YELLOW}[${timestamp}] WARNING: ${message}${NC}" | tee -a "$LOG_FILE" ;;
        "ERROR") echo -e "${RED}[${timestamp}] ERROR: ${message}${NC}" | tee -a "$LOG_FILE" ;;
        "CRITICAL") echo -e "${PURPLE}[${timestamp}] CRITICAL: ${message}${NC}" | tee -a "$LOG_FILE" ;;
    esac
}

print_header() {
    echo -e "${WHITE}"
    echo "================================================================================"
    echo "  $1"
    echo "================================================================================"
    echo -e "${NC}"
}

print_section() {
    echo -e "${CYAN}"
    echo "--- $1 ---"
    echo -e "${NC}"
}

# ===========================================
# SAFETY CHECK FUNCTIONS
# ===========================================

check_prerequisites() {
    log "INFO" "🔍 Checking Phase 5 prerequisites..."
    
    # Check if we're in the right directory
    if [[ ! -d "apps/universal_workshop" ]]; then
        log "ERROR" "Not in frappe-bench directory. Please run from bench root."
        return 1
    fi
    
    # Check if Phase 4 completion markers exist
    local phase4_markers=(
        "phase4_asset_migration_report.json"
        "phase4_hooks_update_report.json"
        "PHASE4_COMPLETION_SUMMARY.md"
    )
    
    local missing_markers=()
    for marker in "${phase4_markers[@]}"; do
        if [[ ! -f "$marker" ]]; then
            missing_markers+=("$marker")
        fi
    done
    
    if [[ ${#missing_markers[@]} -gt 0 ]]; then
        log "WARNING" "Some Phase 4 completion markers missing: ${missing_markers[*]}"
        log "WARNING" "This may indicate Phase 4 is not complete. Proceed with caution."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log "INFO" "Phase 5 execution cancelled by user."
            return 1
        fi
    fi
    
    # Check if Python script exists
    if [[ ! -f "$PYTHON_SCRIPT" ]]; then
        log "ERROR" "Phase 5 testing script not found: $PYTHON_SCRIPT"
        return 1
    fi
    
    # Check Python availability
    if ! command -v python3 &> /dev/null; then
        log "ERROR" "Python3 not found. Required for Phase 5 testing."
        return 1
    fi
    
    # Check Git availability
    if ! command -v git &> /dev/null; then
        log "WARNING" "Git not found. Safety checkpoints will not be created."
    fi
    
    log "SUCCESS" "✅ Prerequisites check completed"
    return 0
}

create_execution_environment() {
    log "INFO" "🏗️ Setting up Phase 5 execution environment..."
    
    # Create logs directory if it doesn't exist
    mkdir -p logs
    
    # Set up Python path
    export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH:-}"
    
    # Create backup directory for this execution
    local backup_dir="phase5_backup_${TIMESTAMP}"
    mkdir -p "$backup_dir"
    
    log "SUCCESS" "✅ Execution environment ready"
    return 0
}

create_pre_execution_backup() {
    log "INFO" "💾 Creating pre-execution safety backup..."
    
    # Git checkpoint
    if command -v git &> /dev/null; then
        local git_tag="phase5-pre-execution-${TIMESTAMP}"
        if git tag "$git_tag" 2>/dev/null; then
            log "SUCCESS" "Git checkpoint created: $git_tag"
        else
            log "WARNING" "Could not create git checkpoint"
        fi
    fi
    
    # File system backup of critical files
    local backup_files=(
        "apps/universal_workshop/universal_workshop/hooks.py"
        "test_refactoring_safety.py"
    )
    
    local backup_dir="phase5_backup_${TIMESTAMP}"
    for file in "${backup_files[@]}"; do
        if [[ -f "$file" ]]; then
            local backup_path="$backup_dir/$(basename "$file")"
            cp "$file" "$backup_path"
            log "INFO" "Backed up: $file -> $backup_path"
        fi
    done
    
    log "SUCCESS" "✅ Pre-execution backup completed"
    return 0
}

# ===========================================
# EXECUTION FUNCTIONS
# ===========================================

display_execution_plan() {
    print_header "PHASE 5: TESTING & VALIDATION EXECUTION PLAN"
    
    cat << EOF
📋 EXECUTION OVERVIEW:
   Phase: Testing & Validation
   Risk Level: LOW (Validation only)
   Duration: Estimated 15-30 minutes
   Approach: Comprehensive automated testing

🧪 TEST CATEGORIES:
   1. Critical Tests (MUST PASS)
      - Directory Structure Integrity
      - Python Import Integrity  
      - Hooks File Integrity
   
   2. Important Tests (SHOULD PASS)
      - Frontend Asset Accessibility
      - DocType Accessibility
      - Database Connectivity
   
   3. Performance Tests
      - Import Performance
      - File Access Performance
   
   4. Data Integrity Tests
      - No Duplicate Files
      - Migration Completeness
   
   5. Functionality Tests
      - Critical User Workflows
      - API Endpoints Structure
      - Build Process

🎯 SUCCESS CRITERIA:
   ✅ All critical tests must pass
   ✅ No critical failures detected
   ✅ Overall success rate > 80%
   ✅ System builds successfully

⚠️ FAILURE HANDLING:
   - Critical failures will halt execution
   - Non-critical failures will be logged
   - Rollback procedures available if needed

EOF

    echo
    read -p "Ready to proceed with Phase 5 execution? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "INFO" "Phase 5 execution cancelled by user."
        return 1
    fi
    
    return 0
}

execute_phase5_testing() {
    print_section "EXECUTING PHASE 5 TESTING"
    
    log "INFO" "🚀 Starting Phase 5: Testing & Validation..."
    log "INFO" "Execution started at: $(date)"
    
    # Execute the Python testing script
    local start_time=$(date +%s)
    local exit_code=0
    
    log "INFO" "Running comprehensive testing suite..."
    
    # Run the Python script with proper error handling
    if python3 "$PYTHON_SCRIPT" 2>&1 | tee -a "$LOG_FILE"; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        log "SUCCESS" "✅ Phase 5 testing completed successfully in ${duration}s"
        exit_code=0
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        log "ERROR" "❌ Phase 5 testing failed after ${duration}s"
        exit_code=1
    fi
    
    return $exit_code
}

analyze_test_results() {
    print_section "ANALYZING TEST RESULTS"
    
    log "INFO" "📊 Analyzing Phase 5 test results..."
    
    # Check if report file exists
    local report_file="phase5_testing_report.json"
    if [[ ! -f "$report_file" ]]; then
        log "ERROR" "Test report not found: $report_file"
        return 1
    fi
    
    # Parse JSON report (basic parsing with grep/sed)
    local overall_status=$(grep -o '"overall_status": "[^"]*"' "$report_file" | cut -d'"' -f4)
    local success_rate=$(grep -o '"success_rate_percentage": [0-9.]*' "$report_file" | cut -d':' -f2 | tr -d ' ')
    local total_tests=$(grep -o '"total_tests": [0-9]*' "$report_file" | cut -d':' -f2 | tr -d ' ')
    local passed_tests=$(grep -o '"passed_tests": [0-9]*' "$report_file" | cut -d':' -f2 | tr -d ' ')
    local failed_tests=$(grep -o '"failed_tests": [0-9]*' "$report_file" | cut -d':' -f2 | tr -d ' ')
    
    # Display results
    log "INFO" "Overall Status: $overall_status"
    log "INFO" "Success Rate: ${success_rate}%"
    log "INFO" "Tests: $passed_tests passed, $failed_tests failed out of $total_tests total"
    
    # Determine recommendation
    case "$overall_status" in
        "SUCCESS")
            log "SUCCESS" "🎉 EXCELLENT: All tests passed! Ready for Phase 6."
            return 0
            ;;
        "SUCCESS_WITH_WARNINGS")
            log "WARNING" "⚠️ GOOD: Tests passed with warnings. Review before Phase 6."
            return 0
            ;;
        "FAILURE")
            log "ERROR" "❌ ISSUES: Some tests failed. Fix issues before Phase 6."
            return 1
            ;;
        "CRITICAL_FAILURE")
            log "CRITICAL" "🚨 CRITICAL: Critical failures detected. Immediate action required."
            return 2
            ;;
        *)
            log "WARNING" "Unknown status: $overall_status"
            return 1
            ;;
    esac
}

provide_recommendations() {
    print_section "RECOMMENDATIONS & NEXT STEPS"
    
    local report_file="phase5_testing_report.json"
    
    if [[ -f "$report_file" ]]; then
        log "INFO" "📋 Based on test results:"
        
        # Extract recommendations from JSON (basic parsing)
        if grep -q '"recommendations"' "$report_file"; then
            log "INFO" "Recommendations from test report:"
            grep -A 10 '"recommendations"' "$report_file" | grep -o '"[^"]*"' | grep -v 'recommendations' | head -5 | while read -r rec; do
                clean_rec=$(echo "$rec" | sed 's/"//g')
                log "INFO" "  - $clean_rec"
            done
        fi
        
        # Extract next steps
        if grep -q '"next_steps"' "$report_file"; then
            log "INFO" "Next steps:"
            grep -A 10 '"next_steps"' "$report_file" | grep -o '"[^"]*"' | grep -v 'next_steps' | head -5 | while read -r step; do
                clean_step=$(echo "$step" | sed 's/"//g')
                log "INFO" "  - $clean_step"
            done
        fi
    fi
    
    # General recommendations
    log "INFO" "📁 Generated files:"
    log "INFO" "  - Test Report: $report_file"
    log "INFO" "  - Test Log: phase5_testing_validation.log"
    log "INFO" "  - Execution Log: $LOG_FILE"
    
    log "INFO" "🔍 For detailed analysis, review the JSON report file."
}

create_completion_checkpoint() {
    log "INFO" "🏁 Creating Phase 5 completion checkpoint..."
    
    # Git checkpoint
    if command -v git &> /dev/null; then
        local git_tag="phase5-execution-complete-${TIMESTAMP}"
        if git tag "$git_tag" 2>/dev/null; then
            log "SUCCESS" "Completion checkpoint created: $git_tag"
        else
            log "WARNING" "Could not create completion checkpoint"
        fi
    fi
    
    # Create completion marker file
    cat > "PHASE5_EXECUTION_COMPLETE_${TIMESTAMP}.md" << EOF
# Phase 5: Testing & Validation - Execution Complete

**Execution Date:** $(date)
**Execution ID:** ${TIMESTAMP}
**Status:** COMPLETED

## Files Generated:
- Test Report: phase5_testing_report.json
- Test Log: phase5_testing_validation.log  
- Execution Log: ${LOG_FILE}

## Git Checkpoints:
- Pre-execution: phase5-pre-execution-${TIMESTAMP}
- Post-execution: phase5-execution-complete-${TIMESTAMP}

## Next Steps:
Review test results and proceed to Phase 6 if appropriate.
EOF
    
    log "SUCCESS" "✅ Phase 5 execution completed and documented"
}

# ===========================================
# ERROR HANDLING & CLEANUP
# ===========================================

cleanup_on_exit() {
    local exit_code=$?
    
    if [[ $exit_code -ne 0 ]]; then
        log "ERROR" "Phase 5 execution failed with exit code: $exit_code"
        log "INFO" "Check logs for details: $LOG_FILE"
    fi
    
    # Always create some form of completion marker
    echo "Phase 5 execution finished at $(date) with exit code $exit_code" >> "$LOG_FILE"
}

handle_interrupt() {
    log "WARNING" "🛑 Phase 5 execution interrupted by user"
    log "INFO" "Cleaning up and exiting..."
    exit 130
}

# ===========================================
# MAIN EXECUTION FLOW
# ===========================================

main() {
    # Set up signal handlers
    trap cleanup_on_exit EXIT
    trap handle_interrupt INT TERM
    
    print_header "PHASE 5: PROFESSIONAL TESTING & VALIDATION"
    
    log "INFO" "Phase 5 execution started at: $(date)"
    log "INFO" "Execution ID: $TIMESTAMP"
    
    # Execute main workflow
    if ! check_prerequisites; then
        log "ERROR" "Prerequisites check failed"
        return 1
    fi
    
    if ! create_execution_environment; then
        log "ERROR" "Environment setup failed"
        return 1
    fi
    
    if ! create_pre_execution_backup; then
        log "ERROR" "Backup creation failed"
        return 1
    fi
    
    if ! display_execution_plan; then
        log "INFO" "Execution cancelled by user"
        return 1
    fi
    
    if ! execute_phase5_testing; then
        log "ERROR" "Phase 5 testing failed"
        return 1
    fi
    
    local analysis_result=0
    if ! analyze_test_results; then
        analysis_result=$?
        log "WARNING" "Test result analysis indicated issues (code: $analysis_result)"
    fi
    
    provide_recommendations
    create_completion_checkpoint
    
    # Final status
    case $analysis_result in
        0)
            print_header "🎉 PHASE 5 COMPLETED SUCCESSFULLY"
            log "SUCCESS" "Phase 5: Testing & Validation completed successfully!"
            log "SUCCESS" "System validated and ready for Phase 6: Cleanup & Optimization"
            ;;
        1)
            print_header "⚠️ PHASE 5 COMPLETED WITH ISSUES"
            log "WARNING" "Phase 5 completed but issues were detected"
            log "WARNING" "Review test results before proceeding to Phase 6"
            ;;
        2)
            print_header "🚨 PHASE 5 COMPLETED WITH CRITICAL ISSUES"
            log "CRITICAL" "Critical issues detected during Phase 5"
            log "CRITICAL" "DO NOT proceed to Phase 6 until issues are resolved"
            ;;
    esac
    
    return $analysis_result
}

# Execute main function
main "$@"
