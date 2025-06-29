#!/bin/bash
# Universal Workshop ERP - Interactive Client Management
# Author: Said Al-Adawi
# Version: 3.0-Professional

set -euo pipefail

# =============================================================================
# CONFIGURATION
# =============================================================================

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly DATA_DIR="${SCRIPT_DIR}/client_data"
readonly CLIENTS_DB="${DATA_DIR}/clients.json"

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly WHITE='\033[1;37m'
readonly NC='\033[0m'

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

print_header() {
    clear
    echo -e "${PURPLE}================================================================${NC}"
    echo -e "${WHITE}  Universal Workshop ERP - Client Management System${NC}"
    echo -e "${PURPLE}================================================================${NC}"
    echo ""
}

print_menu() {
    echo -e "${CYAN}📋 Main Menu:${NC}"
    echo ""
    echo "  1. 🆕 Add New Client"
    echo "  2. 📝 Generate License for Existing Client"
    echo "  3. 📂 List All Clients"
    echo "  4. 🔍 Search Client"
    echo "  5. ✏️  Edit Client Information"
    echo "  6. 🗑️  Delete Client"
    echo "  7. 📊 Generate Client Report"
    echo "  8. 💾 Backup Client Database"
    echo "  9. 📥 Restore Client Database"
    echo "  10. ⚙️  System Settings"
    echo "  0. 🚪 Exit"
    echo ""
    echo -e "${YELLOW}Select an option (0-10):${NC} "
}

read_input() {
    local prompt="$1"
    local default="$2"
    local required="$3"
    
    while true; do
        echo -ne "${BLUE}$prompt${NC}"
        if [[ -n "$default" ]]; then
            echo -ne " ${YELLOW}[$default]${NC}"
        fi
        echo -ne ": "
        
        read -r input
        
        # Use default if input is empty
        if [[ -z "$input" && -n "$default" ]]; then
            input="$default"
        fi
        
        # Check if required
        if [[ "$required" == "true" && -z "$input" ]]; then
            echo -e "${RED}❌ This field is required${NC}"
            continue
        fi
        
        echo "$input"
        return 0
    done
}

confirm_action() {
    local message="$1"
    echo -e "${YELLOW}$message (y/N):${NC} "
    read -r response
    [[ "$response" =~ ^[Yy]$ ]]
}

# =============================================================================
# CLIENT DATABASE FUNCTIONS
# =============================================================================

initialize_database() {
    mkdir -p "$DATA_DIR"
    
    if [[ ! -f "$CLIENTS_DB" ]]; then
        echo '{"clients": [], "metadata": {"version": "1.0", "created": "'$(date -Iseconds)'"}}' > "$CLIENTS_DB"
    fi
}

add_client_to_db() {
    local client_data="$1"
    
    # Add timestamp and ID if not exists
    local timestamp=$(date -Iseconds)
    local client_with_meta=$(echo "$client_data" | jq ". + {\"created_at\": \"$timestamp\", \"updated_at\": \"$timestamp\"}")
    
    # Add to database
    local updated_db=$(jq ".clients += [$client_with_meta]" "$CLIENTS_DB")
    echo "$updated_db" > "$CLIENTS_DB"
}

get_client_by_id() {
    local client_id="$1"
    jq -r ".clients[] | select(.client_id == \"$client_id\")" "$CLIENTS_DB" 2>/dev/null
}

list_all_clients() {
    jq -r '.clients[]' "$CLIENTS_DB" 2>/dev/null
}

search_clients() {
    local search_term="$1"
    jq -r ".clients[] | select(.client_name // .business_name // .client_id | test(\"$search_term\"; \"i\"))" "$CLIENTS_DB" 2>/dev/null
}

update_client() {
    local client_id="$1"
    local updated_data="$2"
    
    local timestamp=$(date -Iseconds)
    local updated_data_with_timestamp=$(echo "$updated_data" | jq ". + {\"updated_at\": \"$timestamp\"}")
    
    local updated_db=$(jq "(.clients[] | select(.client_id == \"$client_id\")) |= $updated_data_with_timestamp" "$CLIENTS_DB")
    echo "$updated_db" > "$CLIENTS_DB"
}

delete_client() {
    local client_id="$1"
    local updated_db=$(jq ".clients |= map(select(.client_id != \"$client_id\"))" "$CLIENTS_DB")
    echo "$updated_db" > "$CLIENTS_DB"
}

# =============================================================================
# CLIENT MANAGEMENT FUNCTIONS
# =============================================================================

add_new_client() {
    print_header
    echo -e "${GREEN}🆕 Adding New Client${NC}"
    echo "================================"
    echo ""
    
    # Collect client information
    local business_name=$(read_input "Business Name (English)" "" "true")
    local business_name_arabic=$(read_input "Business Name (Arabic)" "" "false")
    local client_id=$(read_input "Client ID" "" "false")
    
    # Auto-generate client ID if not provided
    if [[ -z "$client_id" ]]; then
        local base_id="${business_name// /-}"
        base_id="${base_id//[^a-zA-Z0-9-]/}"
        base_id=$(echo "$base_id" | tr '[:lower:]' '[:upper:]')
        client_id="${base_id}-$(date +%Y%m%d)"
        echo -e "${YELLOW}Auto-generated Client ID: $client_id${NC}"
    fi
    
    # Check if client ID already exists
    if [[ -n "$(get_client_by_id "$client_id")" ]]; then
        echo -e "${RED}❌ Client ID already exists: $client_id${NC}"
        read -p "Press Enter to continue..."
        return 1
    fi
    
    local owner_name=$(read_input "Owner Name (English)" "" "true")
    local owner_name_arabic=$(read_input "Owner Name (Arabic)" "" "false")
    local civil_id=$(read_input "Owner Civil ID (8 digits)" "" "true")
    local phone=$(read_input "Phone Number (+968 XXXXXXXX)" "" "true")
    local email=$(read_input "Email Address" "" "false")
    local commercial_license=$(read_input "Commercial License Number (7 digits)" "" "false")
    local address=$(read_input "Business Address" "" "false")
    local business_type=$(read_input "Business Type" "Automotive Workshop" "false")
    local notes=$(read_input "Additional Notes" "" "false")
    
    # Create client JSON
    local client_json=$(cat << EOF
{
  "client_id": "$client_id",
  "business_name": "$business_name",
  "business_name_arabic": "$business_name_arabic",
  "owner_name": "$owner_name",
  "owner_name_arabic": "$owner_name_arabic",
  "civil_id": "$civil_id",
  "phone": "$phone",
  "email": "$email",
  "commercial_license": "$commercial_license",
  "address": "$address",
  "business_type": "$business_type",
  "notes": "$notes",
  "licenses": []
}
EOF
    )
    
    # Display summary
    echo ""
    echo -e "${CYAN}📋 Client Summary:${NC}"
    echo "  Business: $business_name"
    if [[ -n "$business_name_arabic" ]]; then
        echo "  Business (AR): $business_name_arabic"
    fi
    echo "  Client ID: $client_id"
    echo "  Owner: $owner_name"
    echo "  Civil ID: $civil_id"
    echo "  Phone: $phone"
    if [[ -n "$email" ]]; then
        echo "  Email: $email"
    fi
    echo ""
    
    if confirm_action "Save this client?"; then
        add_client_to_db "$client_json"
        echo -e "${GREEN}✅ Client added successfully!${NC}"
        
        if confirm_action "Generate license for this client now?"; then
            generate_license_for_client "$client_id"
        fi
    else
        echo -e "${YELLOW}❌ Client not saved${NC}"
    fi
    
    read -p "Press Enter to continue..."
}

generate_license_for_client() {
    local client_id="$1"
    
    if [[ -z "$client_id" ]]; then
        print_header
        echo -e "${GREEN}📝 Generate License${NC}"
        echo "========================"
        echo ""
        
        # List available clients
        echo -e "${CYAN}Available clients:${NC}"
        local clients=$(list_all_clients)
        if [[ -z "$clients" ]]; then
            echo -e "${RED}❌ No clients found. Add a client first.${NC}"
            read -p "Press Enter to continue..."
            return 1
        fi
        
        echo "$clients" | jq -r '"  " + .client_id + " - " + .business_name'
        echo ""
        
        client_id=$(read_input "Enter Client ID" "" "true")
    fi
    
    local client_data=$(get_client_by_id "$client_id")
    if [[ -z "$client_data" ]]; then
        echo -e "${RED}❌ Client not found: $client_id${NC}"
        read -p "Press Enter to continue..."
        return 1
    fi
    
    local business_name=$(echo "$client_data" | jq -r '.business_name')
    
    echo ""
    echo -e "${CYAN}Client: $business_name ($client_id)${NC}"
    echo ""
    echo -e "${YELLOW}Available license types:${NC}"
    echo "  1. trial        (30 days, 5 users, basic features)"
    echo "  2. basic        (permanent, 5 users, basic features)"
    echo "  3. professional (permanent, 25 users, advanced features)"
    echo "  4. enterprise   (permanent, 100 users, full features)"
    echo "  5. unlimited    (permanent, 999 users, all features)"
    echo ""
    
    local license_choice=$(read_input "Select license type (1-5)" "3" "true")
    
    local license_type
    case "$license_choice" in
        1) license_type="trial" ;;
        2) license_type="basic" ;;
        3) license_type="professional" ;;
        4) license_type="enterprise" ;;
        5) license_type="unlimited" ;;
        *) 
            echo -e "${RED}❌ Invalid choice${NC}"
            read -p "Press Enter to continue..."
            return 1
            ;;
    esac
    
    echo ""
    echo -e "${CYAN}Generating $license_type license for $business_name...${NC}"
    
    # Call the license generator
    if "$SCRIPT_DIR/generate_license_pro.sh" "$business_name" "$client_id" "$license_type"; then
        # Update client record with license info
        local license_info=$(cat << EOF
{
  "type": "$license_type",
  "generated_at": "$(date -Iseconds)",
  "file": "licenses/${business_name// /_}_license.json"
}
EOF
        )
        
        local updated_client=$(echo "$client_data" | jq ".licenses += [$license_info]")
        update_client "$client_id" "$updated_client"
        
        echo -e "${GREEN}✅ License generated and client record updated!${NC}"
    else
        echo -e "${RED}❌ License generation failed${NC}"
    fi
    
    read -p "Press Enter to continue..."
}

list_clients() {
    print_header
    echo -e "${GREEN}📂 All Clients${NC}"
    echo "=================="
    echo ""
    
    local clients=$(list_all_clients)
    if [[ -z "$clients" ]]; then
        echo -e "${YELLOW}No clients found${NC}"
        read -p "Press Enter to continue..."
        return
    fi
    
    echo -e "${CYAN}Client List:${NC}"
    echo ""
    
    local count=0
    while IFS= read -r client; do
        if [[ -n "$client" ]]; then
            ((count++))
            local business_name=$(echo "$client" | jq -r '.business_name')
            local client_id=$(echo "$client" | jq -r '.client_id')
            local owner_name=$(echo "$client" | jq -r '.owner_name')
            local phone=$(echo "$client" | jq -r '.phone')
            local licenses_count=$(echo "$client" | jq -r '.licenses | length')
            
            echo -e "${WHITE}$count. $business_name${NC}"
            echo "   ID: $client_id"
            echo "   Owner: $owner_name"
            echo "   Phone: $phone"
            echo "   Licenses: $licenses_count"
            echo ""
        fi
    done <<< "$clients"
    
    echo -e "${CYAN}Total clients: $count${NC}"
    read -p "Press Enter to continue..."
}

search_client() {
    print_header
    echo -e "${GREEN}🔍 Search Client${NC}"
    echo "==================="
    echo ""
    
    local search_term=$(read_input "Enter search term (name, ID, etc.)" "" "true")
    
    local results=$(search_clients "$search_term")
    if [[ -z "$results" ]]; then
        echo -e "${YELLOW}No clients found matching: $search_term${NC}"
        read -p "Press Enter to continue..."
        return
    fi
    
    echo -e "${CYAN}Search Results for: $search_term${NC}"
    echo ""
    
    local count=0
    while IFS= read -r client; do
        if [[ -n "$client" ]]; then
            ((count++))
            local business_name=$(echo "$client" | jq -r '.business_name')
            local client_id=$(echo "$client" | jq -r '.client_id')
            local owner_name=$(echo "$client" | jq -r '.owner_name')
            
            echo -e "${WHITE}$count. $business_name${NC}"
            echo "   ID: $client_id"
            echo "   Owner: $owner_name"
            echo ""
        fi
    done <<< "$results"
    
    echo -e "${CYAN}Found $count client(s)${NC}"
    read -p "Press Enter to continue..."
}

# =============================================================================
# MAIN MENU LOOP
# =============================================================================

main_menu() {
    while true; do
        print_header
        print_menu
        
        read -r choice
        
        case "$choice" in
            1) add_new_client ;;
            2) generate_license_for_client "" ;;
            3) list_clients ;;
            4) search_client ;;
            5) echo "Edit client functionality - Coming soon"; read -p "Press Enter..." ;;
            6) echo "Delete client functionality - Coming soon"; read -p "Press Enter..." ;;
            7) echo "Generate report functionality - Coming soon"; read -p "Press Enter..." ;;
            8) echo "Backup functionality - Coming soon"; read -p "Press Enter..." ;;
            9) echo "Restore functionality - Coming soon"; read -p "Press Enter..." ;;
            10) echo "System settings - Coming soon"; read -p "Press Enter..." ;;
            0) 
                echo -e "${GREEN}👋 Goodbye!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}❌ Invalid choice. Please select 0-10.${NC}"
                read -p "Press Enter to continue..."
                ;;
        esac
    done
}

# =============================================================================
# SCRIPT EXECUTION
# =============================================================================

# Check dependencies
if ! command -v jq >/dev/null 2>&1; then
    echo -e "${RED}❌ Error: jq is required but not installed.${NC}"
    echo "Install it with: sudo apt-get install jq"
    exit 1
fi

# Initialize database
initialize_database

# Start main menu
main_menu
