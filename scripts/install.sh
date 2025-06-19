#!/bin/bash

# Universal Workshop ERP v2.0 Installation Script
# نص تثبيت نظام إدارة الورش الشامل
# 
# Usage: curl -fsSL https://github.com/saidaladawi/universal-workshop-erp/releases/latest/download/install.sh | bash
# أو: ./scripts/install.sh

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
ERPNEXT_BRANCH="version-15"
PYTHON_VERSION="3.10"
REPO_URL="https://github.com/saidaladawi/universal-workshop-erp.git"

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

# Check if running as root
check_root() {
    if [ "$EUID" -eq 0 ]; then
        print_error "Please don't run this script as root" "يرجى عدم تشغيل هذا النص كـ root"
        exit 1
    fi
}

# Check OS compatibility
check_os() {
    print_message "Checking OS compatibility..." "فحص توافق نظام التشغيل..."
    
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    else
        print_error "Cannot detect OS" "لا يمكن اكتشاف نظام التشغيل"
        exit 1
    fi
    
    case $OS in
        "Ubuntu"*)
            if [[ $(echo "$VER >= 20.04" | bc -l 2>/dev/null || echo "0") == "1" ]]; then
                print_message "✓ Ubuntu $VER detected" "✓ تم اكتشاف Ubuntu $VER"
            else
                print_error "Ubuntu 20.04+ required" "يتطلب Ubuntu 20.04 أو أحدث"
                exit 1
            fi
            ;;
        "CentOS"*|"Red Hat"*)
            if [[ $(echo "$VER >= 8" | bc -l 2>/dev/null || echo "0") == "1" ]]; then
                print_message "✓ $OS $VER detected" "✓ تم اكتشاف $OS $VER"
            else
                print_error "CentOS/RHEL 8+ required" "يتطلب CentOS/RHEL 8 أو أحدث"
                exit 1
            fi
            ;;
        *)
            print_warning "Unsupported OS, proceeding anyway" "نظام تشغيل غير مدعوم، سيتم المتابعة"
            ;;
    esac
}

# Install system dependencies
install_dependencies() {
    print_message "Installing system dependencies..." "تثبيت متطلبات النظام..."
    
    # Update package lists
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update -y
        sudo apt-get install -y git python3 python3-dev python3-pip python3-venv \
            nodejs npm mariadb-server mariadb-client redis-server \
            libmysqlclient-dev libffi-dev libssl-dev \
            wkhtmltopdf xvfb libfontconfig curl wget bc \
            fonts-noto-arabic fonts-liberation
    elif command -v yum >/dev/null 2>&1; then
        sudo yum update -y
        sudo yum install -y git python3 python3-devel python3-pip \
            nodejs npm mariadb-server mariadb redis \
            mysql-devel libffi-devel openssl-devel \
            wkhtmltopdf xorg-x11-server-Xvfb fontconfig curl wget bc
    fi
    
    print_message "✓ Dependencies installed" "✓ تم تثبيت المتطلبات"
}

# Configure MariaDB
configure_mariadb() {
    print_message "Configuring MariaDB..." "تكوين MariaDB..."
    
    sudo systemctl start mariadb
    sudo systemctl enable mariadb
    
    # Secure installation
    sudo mysql -e "DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');" 2>/dev/null || true
    sudo mysql -e "DELETE FROM mysql.user WHERE User='';" 2>/dev/null || true
    sudo mysql -e "DELETE FROM mysql.db WHERE Db='test' OR Db='test\_%';" 2>/dev/null || true
    sudo mysql -e "FLUSH PRIVILEGES;" 2>/dev/null || true
    
    # Configure for UTF8MB4 (Arabic support)
    sudo tee /etc/mysql/mariadb.conf.d/99-universal-workshop.cnf > /dev/null <<EOF
[mysqld]
character-set-client-handshake = FALSE
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

[mysql]
default-character-set = utf8mb4
EOF
    
    sudo systemctl restart mariadb
    print_message "✓ MariaDB configured for Arabic support" "✓ تم تكوين MariaDB لدعم العربية"
}

# Install Node.js and Yarn
install_nodejs() {
    print_message "Installing Node.js and Yarn..." "تثبيت Node.js و Yarn..."
    
    # Install Node.js 18 via NodeSource
    if ! command -v node >/dev/null 2>&1; then
        curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
        sudo apt-get install -y nodejs
    fi
    
    # Install Yarn
    if ! command -v yarn >/dev/null 2>&1; then
        sudo npm install -g yarn
    fi
    
    NODE_VERSION=$(node --version 2>/dev/null || echo "not installed")
    print_message "✓ Node.js $NODE_VERSION and Yarn installed" "✓ تم تثبيت Node.js $NODE_VERSION و Yarn"
}

# Create frappe user
create_frappe_user() {
    if ! id "$FRAPPE_USER" &>/dev/null; then
        print_message "Creating frappe user..." "إنشاء مستخدم frappe..."
        sudo adduser --disabled-password --gecos "" $FRAPPE_USER
        sudo usermod -aG sudo $FRAPPE_USER
        print_message "✓ Frappe user created" "✓ تم إنشاء مستخدم frappe"
    else
        print_message "✓ Frappe user already exists" "✓ مستخدم frappe موجود مسبقاً"
    fi
}

# Install Frappe Bench
install_bench() {
    print_message "Installing Frappe Bench..." "تثبيت Frappe Bench..."
    
    # Switch to frappe user
    sudo -u $FRAPPE_USER bash -c "
        cd /home/$FRAPPE_USER
        
        # Install bench if not exists
        if ! command -v bench >/dev/null 2>&1; then
            pip3 install --user frappe-bench
            export PATH=\$HOME/.local/bin:\$PATH
        fi
        
        # Initialize bench if not exists
        if [ ! -d \"$BENCH_NAME\" ]; then
            bench init --frappe-branch $ERPNEXT_BRANCH $BENCH_NAME
        fi
        
        cd $BENCH_NAME
        
        # Get ERPNext if not exists
        if [ ! -d \"apps/erpnext\" ]; then
            bench get-app --branch $ERPNEXT_BRANCH erpnext
        fi
        
        # Get Universal Workshop if not exists
        if [ ! -d \"apps/universal_workshop\" ]; then
            bench get-app $REPO_URL
        fi
    "
    
    print_message "✓ Frappe Bench installed" "✓ تم تثبيت Frappe Bench"
}

# Create new site
create_site() {
    print_message "Creating new site..." "إنشاء موقع جديد..."
    
    sudo -u $FRAPPE_USER bash -c "
        cd /home/$FRAPPE_USER/$BENCH_NAME
        
        # Create site if not exists
        if [ ! -d \"sites/$SITE_NAME\" ]; then
            bench new-site $SITE_NAME --admin-password admin --mariadb-root-password \"\"
        fi
        
        # Install apps
        bench --site $SITE_NAME install-app erpnext
        bench --site $SITE_NAME install-app universal_workshop
        
        # Configure Arabic
        bench --site $SITE_NAME set-config lang ar
        bench --site $SITE_NAME add-to-hosts
        
        # Clear cache
        bench --site $SITE_NAME clear-cache
    "
    
    print_message "✓ Site created: $SITE_NAME" "✓ تم إنشاء الموقع: $SITE_NAME"
}

# Setup production (optional)
setup_production() {
    read -p "$(if [ "$LANG_AR" = true ]; then echo 'إعداد للإنتاج؟ (y/N): '; else echo 'Setup for production? (y/N): '; fi)" -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_message "Setting up production..." "إعداد الإنتاج..."
        
        sudo -u $FRAPPE_USER bash -c "
            cd /home/$FRAPPE_USER/$BENCH_NAME
            sudo bench setup production $FRAPPE_USER
            bench --site $SITE_NAME enable-scheduler
            bench --site $SITE_NAME set-maintenance-mode off
        "
        
        print_message "✓ Production setup complete" "✓ تم إكمال إعداد الإنتاج"
    fi
}

# Main installation function
main() {
    echo
    if [ "$LANG_AR" = true ]; then
        echo "🚗 بدء تثبيت نظام إدارة الورش الشامل v2.0"
        echo "Universal Workshop ERP Installation Starting..."
    else
        echo "🚗 Universal Workshop ERP v2.0 Installation Starting..."
        echo "نظام إدارة الورش الشامل - بدء التثبيت"
    fi
    echo
    
    check_root
    check_os
    install_dependencies
    configure_mariadb
    install_nodejs
    create_frappe_user
    install_bench
    create_site
    setup_production
    
    echo
    print_message "🎉 Installation completed successfully!" "🎉 تم التثبيت بنجاح!"
    print_message "You can access your site at: http://$SITE_NAME:8000" "يمكنك الوصول إلى موقعك على: http://$SITE_NAME:8000"
    print_message "Default credentials: Administrator / admin" "بيانات الدخول الافتراضية: Administrator / admin"
    echo
    print_message "To start the development server:" "لبدء خادم التطوير:"
    print_message "sudo -u $FRAPPE_USER bash -c 'cd /home/$FRAPPE_USER/$BENCH_NAME && bench start'" "sudo -u $FRAPPE_USER bash -c 'cd /home/$FRAPPE_USER/$BENCH_NAME && bench start'"
    echo
}

# Run main function
main "$@"

