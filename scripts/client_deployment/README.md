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
