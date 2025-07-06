# Copyright (c) 2025, Said Al-Adowi and contributors
# For license information, please see license.txt

"""
Browser Launcher and Redirect Module
Handles automatic browser opening and navigation to onboarding wizard
"""

import os
import sys
import webbrowser
import subprocess
import platform
from pathlib import Path
import frappe
from frappe import _


class BrowserLauncher:
    """Launch browser and navigate to onboarding wizard"""
    
    def __init__(self, site_url="http://localhost:8000"):
        self.site_url = site_url.rstrip('/')
        self.system = platform.system().lower()
    
    def launch_onboarding_wizard(self):
        """Open browser and navigate directly to onboarding wizard"""
        
        # Check if setup is already complete
        setup_complete = frappe.db.get_default("setup_complete")
        if setup_complete == "1":
            onboarding_url = f"{self.site_url}/app"
            frappe.log_error(f"Setup already complete, redirecting to main app: {onboarding_url}")
        else:
            onboarding_url = f"{self.site_url}/onboarding"
            frappe.log_error(f"Starting onboarding wizard: {onboarding_url}")
        
        success = self._open_browser(onboarding_url)
        
        if success:
            print(f"✅ Browser opened: {onboarding_url}")
            return True
        else:
            print(f"❌ Failed to open browser. Please navigate manually to: {onboarding_url}")
            return False
    
    def _open_browser(self, url):
        """Open browser using platform-specific methods"""
        
        try:
            if self.system == 'windows':
                return self._open_windows_browser(url)
            elif self.system == 'darwin':  # macOS
                return self._open_macos_browser(url)
            else:  # Linux and others
                return self._open_linux_browser(url)
        except Exception as e:
            frappe.log_error(f"Error opening browser: {e}")
            return False
    
    def _open_windows_browser(self, url):
        """Open browser on Windows"""
        try:
            # Try to use default browser
            os.startfile(url)
            return True
        except:
            # Fallback to webbrowser module
            return webbrowser.open(url)
    
    def _open_macos_browser(self, url):
        """Open browser on macOS"""
        try:
            subprocess.run(['open', url], check=True)
            return True
        except:
            return webbrowser.open(url)
    
    def _open_linux_browser(self, url):
        """Open browser on Linux"""
        try:
            subprocess.run(['xdg-open', url], check=True)
            return True
        except:
            return webbrowser.open(url)
    
    def create_auto_launch_script(self, output_dir="./scripts"):
        """Create auto-launch script for post-installation"""
        
        Path(output_dir).mkdir(exist_ok=True)
        
        if self.system == 'windows':
            script_content = self._create_windows_launch_script()
            script_path = Path(output_dir) / "launch_workshop.bat"
        else:
            script_content = self._create_unix_launch_script()
            script_path = Path(output_dir) / "launch_workshop.sh"
        
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        if self.system != 'windows':
            os.chmod(script_path, 0o755)  # Make executable
        
        print(f"✅ Auto-launch script created: {script_path}")
        return str(script_path)
    
    def _create_windows_launch_script(self):
        """Create Windows batch script for auto-launch"""
        return f"""@echo off
echo Starting Universal Workshop ERP...
echo.

REM Wait for services to start
timeout /t 5 /nobreak >nul

REM Check if site is accessible
ping -n 1 127.0.0.1 >nul
if errorlevel 1 (
    echo Error: Unable to connect to local server
    pause
    exit /b 1
)

REM Open browser to onboarding wizard
echo Opening Universal Workshop in your browser...
start "" "{self.site_url}/onboarding"

echo.
echo Universal Workshop is now starting in your browser.
echo If the browser doesn't open automatically, please visit:
echo {self.site_url}/onboarding
echo.
echo Press any key to close this window...
pause >nul
"""
    
    def _create_unix_launch_script(self):
        """Create Unix shell script for auto-launch"""
        return f"""#!/bin/bash

echo "Starting Universal Workshop ERP..."
echo

# Wait for services to start
sleep 5

# Check if site is accessible
if ! curl -s --connect-timeout 5 "{self.site_url}" > /dev/null; then
    echo "Error: Unable to connect to Universal Workshop server"
    echo "Please ensure the server is running and try again."
    exit 1
fi

# Open browser to onboarding wizard
echo "Opening Universal Workshop in your browser..."

if command -v xdg-open > /dev/null; then
    xdg-open "{self.site_url}/onboarding"
elif command -v open > /dev/null; then
    open "{self.site_url}/onboarding"
else
    echo "Please open your browser and navigate to:"
    echo "{self.site_url}/onboarding"
fi

echo
echo "Universal Workshop is now starting in your browser."
echo "If the browser doesn't open automatically, please visit:"
echo "{self.site_url}/onboarding"
"""


class InstallationRedirectManager:
    """Manage post-installation redirect and setup completion"""
    
    @staticmethod
    def setup_post_install_redirect():
        """Configure system to redirect to onboarding after installation"""
        
        try:
            # Check if this is first installation
            setup_complete = frappe.db.get_default("setup_complete")
            
            if setup_complete != "1":
                # Set redirect flag for boot session
                frappe.db.set_default("require_onboarding", "1")
                frappe.db.set_default("onboarding_redirect", "1")
                frappe.db.commit()
                
                print("✅ Post-installation redirect configured")
                return True
            else:
                print("ℹ️  Setup already complete, no redirect needed")
                return False
                
        except Exception as e:
            frappe.log_error(f"Error setting up post-install redirect: {e}")
            return False
    
    @staticmethod
    def handle_onboarding_completion(workshop_code):
        """Handle completion of onboarding wizard"""
        
        try:
            # Mark setup as complete
            frappe.db.set_default("setup_complete", "1")
            frappe.db.set_default("require_onboarding", "0")
            frappe.db.set_default("onboarding_redirect", "0")
            
            # Set home page to main dashboard
            frappe.db.set_default("home_page", "/app/workspace/Workshop%20Management")
            
            frappe.db.commit()
            
            # Return redirect URL
            redirect_url = "/app/workspace/Workshop%20Management"
            
            print(f"✅ Onboarding completed for workshop: {workshop_code}")
            print(f"🏠 Home page set to: {redirect_url}")
            
            return {
                "success": True,
                "redirect_url": redirect_url,
                "message": _("Welcome to Universal Workshop! Your system is now ready to use.")
            }
            
        except Exception as e:
            frappe.log_error(f"Error handling onboarding completion: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Utility functions for hooks and API calls
def launch_browser_to_onboarding(site_url="http://localhost:8000"):
    """Utility function to launch browser - can be called from hooks"""
    launcher = BrowserLauncher(site_url)
    return launcher.launch_onboarding_wizard()


def create_launch_script(site_url="http://localhost:8000", output_dir="./scripts"):
    """Utility function to create launch script"""
    launcher = BrowserLauncher(site_url)
    return launcher.create_auto_launch_script(output_dir)


@frappe.whitelist()
def complete_onboarding_and_redirect(workshop_code):
    """API endpoint to complete onboarding and get redirect URL"""
    return InstallationRedirectManager.handle_onboarding_completion(workshop_code)


@frappe.whitelist()
def get_post_install_status():
    """Check if post-installation setup is required"""
    setup_complete = frappe.db.get_default("setup_complete")
    require_onboarding = frappe.db.get_default("require_onboarding")
    
    return {
        "setup_complete": setup_complete == "1",
        "require_onboarding": require_onboarding == "1",
        "onboarding_url": "/onboarding" if require_onboarding == "1" else "/app"
    }