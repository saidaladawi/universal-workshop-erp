# Universal Workshop ERP - Installation Guide

## System Requirements

### Minimum Requirements
- **Operating System:** Ubuntu 20.04+ / CentOS 8+ / Windows 10+ / macOS 11+
- **Python:** 3.8 or higher
- **Node.js:** 14.0 or higher
- **Database:** MariaDB 10.3+ or MySQL 8.0+
- **Memory:** 4GB RAM minimum, 8GB recommended
- **Storage:** 20GB free disk space
- **Network:** Internet connection for installation and updates

### Recommended Requirements
- **Operating System:** Ubuntu 22.04 LTS
- **Python:** 3.11
- **Node.js:** 18.0
- **Database:** MariaDB 10.11
- **Memory:** 16GB RAM
- **Storage:** 50GB SSD
- **CPU:** 4+ cores

## Quick Installation

### One-Command Installation (Linux/macOS)
```bash
curl -fsSL https://github.com/saidaladawi/universal-workshop-erp/releases/latest/download/install.sh | bash
```

### Docker Installation (All Platforms)
```bash
git clone https://github.com/saidaladawi/universal-workshop-erp.git
cd universal-workshop-erp
docker-compose up -d
```

### Windows Installation
1. Download `install.bat` from the latest release
2. Run as Administrator
3. Follow the installation prompts

## Manual Installation

### Step 1: System Preparation

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nodejs npm mariadb-server redis-server
```

#### CentOS/RHEL
```bash
sudo dnf update
sudo dnf install -y python3 python3-pip nodejs npm mariadb-server redis
```

#### Windows
1. Install Python 3.8+ from python.org
2. Install Node.js 14+ from nodejs.org
3. Install MariaDB from mariadb.org
4. Install Redis from redis.io

### Step 2: Database Setup

#### MariaDB Configuration
```bash
sudo mysql_secure_installation
sudo mysql -u root -p
```

```sql
CREATE DATABASE workshop_erp CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'workshop_user'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON workshop_erp.* TO 'workshop_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### Step 3: Frappe Bench Installation

```bash
# Install bench
pip3 install frappe-bench

# Initialize bench
bench init --frappe-branch version-15 frappe-bench
cd frappe-bench

# Create site
bench new-site workshop.local --db-name workshop_erp --db-user workshop_user --db-password your_secure_password

# Set site as default
bench use workshop.local
```

### Step 4: ERPNext Installation

```bash
# Get ERPNext
bench get-app --branch version-15 erpnext

# Install ERPNext
bench --site workshop.local install-app erpnext
```

### Step 5: Universal Workshop App Installation

```bash
# Get Universal Workshop app
bench get-app https://github.com/saidaladawi/universal-workshop-erp.git

# Install Universal Workshop app
bench --site workshop.local install-app universal_workshop
```

### Step 6: Configuration

```bash
# Enable developer mode (optional)
bench --site workshop.local set-config developer_mode 1

# Set maintenance mode off
bench --site workshop.local set-maintenance-mode off

# Start services
bench start
```

## Configuration

### Site Configuration
Edit `sites/workshop.local/site_config.json`:

```json
{
  "db_name": "workshop_erp",
  "db_password": "your_secure_password",
  "db_user": "workshop_user",
  "developer_mode": 0,
  "maintenance_mode": 0,
  "lang": "ar",
  "time_zone": "Asia/Muscat",
  "currency": "OMR",
  "country": "Oman",
  "auto_email_reports": 1,
  "scheduler_enabled": 1
}
```

### Environment Variables
Create `.env` file:

```bash
# Database
DB_HOST=localhost
DB_PORT=3306
DB_NAME=workshop_erp
DB_USER=workshop_user
DB_PASSWORD=your_secure_password

# Redis
REDIS_CACHE_HOST=localhost
REDIS_CACHE_PORT=6379
REDIS_QUEUE_HOST=localhost
REDIS_QUEUE_PORT=6380

# Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=1
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password

# Security
ENCRYPTION_KEY=your_32_character_encryption_key
```

## Production Deployment

### Using Docker Compose

1. Clone the repository:
```bash
git clone https://github.com/saidaladawi/universal-workshop-erp.git
cd universal-workshop-erp
```

2. Configure environment:
```bash
cp .env.production.example .env.production
# Edit .env.production with your settings
```

3. Deploy:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Using Kubernetes

1. Apply manifests:
```bash
kubectl apply -f deployment/kubernetes/namespace.yaml
kubectl apply -f deployment/kubernetes/storage.yaml
kubectl apply -f deployment/kubernetes/deployment.yaml
kubectl apply -f deployment/kubernetes/services.yaml
```

2. Configure ingress and SSL certificates as needed.

## Updates and Maintenance

### Automatic Updates
```bash
# Update to latest version
./scripts/update.sh

# Update to specific version
./scripts/update.sh v2.1.0
```

### Manual Updates
```bash
cd frappe-bench
bench update --reset
bench --site workshop.local migrate
bench restart
```

### Backup and Restore

#### Create Backup
```bash
bench --site workshop.local backup
```

#### Restore Backup
```bash
bench --site workshop.local restore backup_file.sql.gz
```

## Troubleshooting

### Common Issues

#### Database Connection Error
- Check database credentials in site_config.json
- Ensure MariaDB is running: `sudo systemctl status mariadb`
- Test connection: `mysql -u workshop_user -p workshop_erp`

#### Permission Errors
- Fix file permissions: `sudo chown -R $USER:$USER frappe-bench`
- Reset permissions: `bench setup socketio`

#### Port Conflicts
- Change port in `sites/common_site_config.json`
- Default ports: 8000 (web), 9000 (socketio)

#### Memory Issues
- Increase virtual memory: `sudo sysctl vm.max_map_count=262144`
- Add swap space if needed

### Performance Optimization

#### Database Optimization
```sql
-- Add indexes for better performance
ALTER TABLE `tabCustomer` ADD INDEX `idx_customer_name` (`customer_name`);
ALTER TABLE `tabItem` ADD INDEX `idx_item_code` (`item_code`);
```

#### Redis Configuration
Edit `/etc/redis/redis.conf`:
```
maxmemory 2gb
maxmemory-policy allkeys-lru
```

### Log Files
- Frappe logs: `logs/frappe.log`
- Error logs: `logs/error.log`
- Nginx logs: `/var/log/nginx/`

## Security

### SSL Certificate Setup
```bash
# Using Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### Firewall Configuration
```bash
sudo ufw enable
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
```

### Regular Security Updates
```bash
# Update system packages
sudo apt update && sudo apt upgrade

# Update Frappe/ERPNext
bench update
```

## Support

### Community Support
- GitHub Issues: https://github.com/saidaladawi/universal-workshop-erp/issues
- Discussions: https://github.com/saidaladawi/universal-workshop-erp/discussions
- ERPNext Community: https://discuss.erpnext.com

### Documentation
- User Manual: `/docs/en/user-manual.md`
- API Documentation: `/docs/en/api-documentation.md`
- Developer Guide: `/docs/en/developer-guide.md`

### Professional Support
For enterprise support and customization services, contact:
- Email: support@workshop-erp.com
- Website: https://workshop-erp.com

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.
