#!/usr/bin/env python3
"""
Universal Workshop - Client Deployment Script
Generates license keys and creates desktop shortcuts for customer deployments
"""

import os
import json
import uuid
import hashlib
import argparse
from datetime import datetime, timedelta
from pathlib import Path


class LicenseGenerator:
    """Generate license keys for Universal Workshop deployments"""
    
    def __init__(self):
        self.license_types = {
            'basic': {'max_users': 5, 'modules': ['workshop_core', 'customer_management']},
            'premium': {'max_users': 15, 'modules': ['workshop_core', 'customer_management', 'financial_operations', 'inventory_management']},
            'enterprise': {'max_users': 50, 'modules': 'all'}
        }
    
    def generate_license(self, workshop_name_en, workshop_name_ar, license_type='basic', 
                        owner_name='', business_license='', email='', valid_months=12):
        """Generate a complete license file for workshop deployment"""
        
        license_id = str(uuid.uuid4()).replace('-', '').upper()[:16]
        issue_date = datetime.now()
        expiry_date = issue_date + timedelta(days=valid_months * 30)
        
        # Generate hardware fingerprint placeholder
        hardware_hash = hashlib.sha256(f"{workshop_name_en}{business_license}".encode()).hexdigest()[:16]
        
        license_data = {
            # License metadata
            "license_id": license_id,
            "license_type": license_type,
            "issue_date": issue_date.isoformat(),
            "expiry_date": expiry_date.isoformat(),
            "status": "active",
            "hardware_fingerprint": hardware_hash,
            
            # Workshop information (extracted by onboarding wizard)
            "workshop_name_en": workshop_name_en,
            "workshop_name_ar": workshop_name_ar,
            "business_license": business_license,
            "owner_name": owner_name,
            "contact_email": email,
            
            # License capabilities
            "max_users": self.license_types[license_type]['max_users'],
            "enabled_modules": self.license_types[license_type]['modules'],
            
            # Deployment info
            "deployment_date": None,  # Set during installation
            "site_url": None,        # Set during installation
            
            # Security
            "license_signature": self._generate_signature(license_id, workshop_name_en, business_license),
            "encryption_key": hashlib.sha256(f"{license_id}{hardware_hash}".encode()).hexdigest()[:32]
        }
        
        return license_data
    
    def _generate_signature(self, license_id, workshop_name, business_license):
        """Generate license signature for validation"""
        signature_data = f"{license_id}{workshop_name}{business_license}UNIVERSAL_WORKSHOP_2025"
        return hashlib.sha256(signature_data.encode()).hexdigest()
    
    def save_license_file(self, license_data, output_dir="./licenses"):
        """Save license to file for deployment"""
        
        # Create licenses directory
        Path(output_dir).mkdir(exist_ok=True)
        
        # Generate filename
        workshop_code = license_data['workshop_name_en'].replace(' ', '_').lower()
        filename = f"workshop_license_{workshop_code}_{license_data['license_id']}.json"
        
        filepath = Path(output_dir) / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(license_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ License generated: {filepath}")
        return str(filepath)


class DesktopShortcutCreator:
    """Create desktop shortcuts for Universal Workshop"""
    
    @staticmethod
    def create_windows_shortcut(site_url, workshop_name, desktop_path=None):
        """Create Windows .url shortcut file"""
        
        if desktop_path is None:
            desktop_path = Path.home() / "Desktop"
        
        shortcut_content = f"""[InternetShortcut]
URL={site_url}
IconFile={site_url}/assets/universal_workshop/images/icon.ico
IconIndex=0
HotKey=0
IDList=
[{{000214A0-0000-0000-C000-000000000046}}]
Prop3=19,11
"""
        
        shortcut_path = desktop_path / f"{workshop_name} - Universal Workshop.url"
        
        with open(shortcut_path, 'w') as f:
            f.write(shortcut_content)
        
        print(f"✅ Windows shortcut created: {shortcut_path}")
        return str(shortcut_path)
    
    @staticmethod
    def create_linux_shortcut(site_url, workshop_name, desktop_path=None):
        """Create Linux .desktop shortcut file"""
        
        if desktop_path is None:
            desktop_path = Path.home() / "Desktop"
        
        shortcut_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name={workshop_name} - Universal Workshop
Comment=Open Universal Workshop ERP System
Exec=xdg-open {site_url}
Icon={site_url}/assets/universal_workshop/images/icon.png
Terminal=false
Categories=Office;Finance;
StartupNotify=true
"""
        
        shortcut_path = desktop_path / f"{workshop_name} Universal Workshop.desktop"
        
        with open(shortcut_path, 'w') as f:
            f.write(shortcut_content)
        
        # Make executable
        os.chmod(shortcut_path, 0o755)
        
        print(f"✅ Linux shortcut created: {shortcut_path}")
        return str(shortcut_path)
    
    @staticmethod
    def create_macos_shortcut(site_url, workshop_name, desktop_path=None):
        """Create macOS .webloc shortcut file"""
        
        if desktop_path is None:
            desktop_path = Path.home() / "Desktop"
        
        shortcut_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>URL</key>
    <string>{site_url}</string>
</dict>
</plist>
"""
        
        shortcut_path = desktop_path / f"{workshop_name} - Universal Workshop.webloc"
        
        with open(shortcut_path, 'w') as f:
            f.write(shortcut_content)
        
        print(f"✅ macOS shortcut created: {shortcut_path}")
        return str(shortcut_path)


class DeploymentManager:
    """Complete deployment workflow manager"""
    
    def __init__(self):
        self.license_generator = LicenseGenerator()
        self.shortcut_creator = DesktopShortcutCreator()
    
    def deploy_customer_site(self, workshop_name_en, workshop_name_ar, owner_name, 
                           business_license, email, license_type='basic', 
                           site_url='http://localhost:8000', create_shortcut=True):
        """Complete customer deployment workflow"""
        
        print(f"🚀 Starting deployment for: {workshop_name_en}")
        print("=" * 60)
        
        # Step 1: Generate license
        print("📄 Generating license...")
        license_data = self.license_generator.generate_license(
            workshop_name_en=workshop_name_en,
            workshop_name_ar=workshop_name_ar,
            license_type=license_type,
            owner_name=owner_name,
            business_license=business_license,
            email=email
        )
        
        # Step 2: Save license file
        license_file = self.license_generator.save_license_file(license_data)
        
        # Step 3: Create desktop shortcut
        if create_shortcut:
            print("🖥️  Creating desktop shortcut...")
            import platform
            system = platform.system().lower()
            
            if system == 'windows':
                shortcut_path = self.shortcut_creator.create_windows_shortcut(site_url, workshop_name_en)
            elif system == 'darwin':  # macOS
                shortcut_path = self.shortcut_creator.create_macos_shortcut(site_url, workshop_name_en)
            else:  # Linux
                shortcut_path = self.shortcut_creator.create_linux_shortcut(site_url, workshop_name_en)
        
        # Step 4: Generate deployment instructions
        self._generate_deployment_instructions(license_data, license_file, site_url)
        
        print("\n" + "=" * 60)
        print("🎉 Deployment package ready!")
        print(f"📋 License ID: {license_data['license_id']}")
        print(f"📁 License File: {license_file}")
        if create_shortcut:
            print(f"🔗 Desktop Shortcut: {shortcut_path}")
        
        return {
            'license_data': license_data,
            'license_file': license_file,
            'shortcut_path': shortcut_path if create_shortcut else None,
            'site_url': site_url
        }
    
    def _generate_deployment_instructions(self, license_data, license_file, site_url):
        """Generate deployment instructions for customer"""
        
        instructions = f"""
# Universal Workshop Deployment Instructions

## Customer Information
- **Workshop Name:** {license_data['workshop_name_en']} / {license_data['workshop_name_ar']}
- **Owner:** {license_data['owner_name']}
- **License Type:** {license_data['license_type'].title()}
- **License ID:** {license_data['license_id']}
- **Valid Until:** {license_data['expiry_date'][:10]}

## Installation Steps

### 1. License Installation
```bash
# Copy license file to bench directory
cp {license_file} /path/to/frappe-bench/licenses/workshop_license.json
```

### 2. Start System
- Open the desktop shortcut: "{license_data['workshop_name_en']} - Universal Workshop"
- Or navigate to: {site_url}

### 3. Onboarding Process
1. **License Verification:** System will automatically detect workshop information
2. **Logo Upload:** Upload your workshop logo or use default
3. **Admin Account:** Create administrator credentials
4. **Access Dashboard:** Login and start using the system

## Technical Support
- Email: support@universalworkshop.om
- Phone: +968 24 123 456
- License ID: {license_data['license_id']}

## Next Steps After Installation
1. Complete onboarding wizard
2. Upload workshop logo and branding
3. Configure workshop settings
4. Add technicians and staff
5. Start managing your workshop operations

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        instructions_file = Path(license_file).parent / "deployment_instructions.md"
        with open(instructions_file, 'w', encoding='utf-8') as f:
            f.write(instructions)
        
        print(f"📖 Instructions generated: {instructions_file}")


def main():
    """Command line interface for client deployment"""
    
    parser = argparse.ArgumentParser(description='Universal Workshop Client Deployment Tool')
    parser.add_argument('--workshop-en', required=True, help='Workshop name in English')
    parser.add_argument('--workshop-ar', required=True, help='Workshop name in Arabic')
    parser.add_argument('--owner', required=True, help='Owner name')
    parser.add_argument('--license-number', required=True, help='Business license number')
    parser.add_argument('--email', required=True, help='Contact email')
    parser.add_argument('--license-type', choices=['basic', 'premium', 'enterprise'], 
                       default='basic', help='License type')
    parser.add_argument('--site-url', default='http://localhost:8000', help='Site URL')
    parser.add_argument('--no-shortcut', action='store_true', help='Skip desktop shortcut creation')
    
    args = parser.parse_args()
    
    # Create deployment manager
    deployment_manager = DeploymentManager()
    
    # Execute deployment
    result = deployment_manager.deploy_customer_site(
        workshop_name_en=args.workshop_en,
        workshop_name_ar=args.workshop_ar,
        owner_name=args.owner,
        business_license=args.license_number,
        email=args.email,
        license_type=args.license_type,
        site_url=args.site_url,
        create_shortcut=not args.no_shortcut
    )
    
    print("\n✅ Deployment completed successfully!")


if __name__ == '__main__':
    main()