@echo off
setlocal enabledelayedexpansion

REM Universal Workshop ERP v2.0 Windows Installation Script
REM نص تثبيت نظام إدارة الورش الشامل - Windows

echo.
echo 🚗 Universal Workshop ERP v2.0 Installation for Windows
echo نظام إدارة الورش الشامل - تثبيت Windows
echo.

REM Check for Administrator privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ✓ Running with Administrator privileges
) else (
    echo ❌ This script requires Administrator privileges
    echo يتطلب هذا النص صلاحيات المسؤول
    echo Please run as Administrator / يرجى التشغيل كمسؤول
    pause
    exit /b 1
)

REM Configuration
set PYTHON_VERSION=3.10
set NODE_VERSION=18
set SITE_NAME=workshop.local
set ADMIN_PASSWORD=admin

echo 📋 Installing prerequisites...
echo تثبيت المتطلبات الأساسية...

REM Check if Python is installed
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ Python not found. Please install Python 3.10+
    echo Python غير موجود. يرجى تثبيت Python 3.10 أو أحدث
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
) else (
    echo ✓ Python found
)

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ Node.js not found. Please install Node.js 18+
    echo Node.js غير موجود. يرجى تثبيت Node.js 18 أو أحدث
    echo Download from: https://nodejs.org/
    pause
    exit /b 1
) else (
    echo ✓ Node.js found
)

REM Check if Git is installed
git --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ Git not found. Please install Git
    echo Git غير موجود. يرجى تثبيت Git
    echo Download from: https://git-scm.com/download/win
    pause
    exit /b 1
) else (
    echo ✓ Git found
)

echo.
echo 🔧 Installing Universal Workshop ERP...
echo تثبيت نظام إدارة الورش الشامل...

REM Install frappe-bench
pip install frappe-bench
if %errorLevel% neq 0 (
    echo ❌ Failed to install frappe-bench
    echo فشل في تثبيت frappe-bench
    pause
    exit /b 1
)

REM Initialize bench
if not exist "frappe-bench" (
    bench init --frappe-branch version-15 frappe-bench
    if %errorLevel% neq 0 (
        echo ❌ Failed to initialize bench
        echo فشل في تهيئة bench
        pause
        exit /b 1
    )
)

cd frappe-bench

REM Get ERPNext
if not exist "apps\erpnext" (
    bench get-app --branch version-15 erpnext
    if %errorLevel% neq 0 (
        echo ❌ Failed to get ERPNext
        echo فشل في تحميل ERPNext
        pause
        exit /b 1
    )
)

REM Get Universal Workshop
if not exist "apps\universal_workshop" (
    bench get-app https://github.com/saidaladawi/universal-workshop-erp.git
    if %errorLevel% neq 0 (
        echo ❌ Failed to get Universal Workshop
        echo فشل في تحميل نظام الورش الشامل
        pause
        exit /b 1
    )
)

echo.
echo 🗄️ Database Setup Required
echo إعداد قاعدة البيانات مطلوب
echo.
echo Please install MariaDB 10.6+ manually:
echo يرجى تثبيت MariaDB 10.6+ يدوياً:
echo https://mariadb.org/download/
echo.
echo After MariaDB installation, create a site:
echo بعد تثبيت MariaDB، أنشئ موقعاً:
echo bench new-site %SITE_NAME% --admin-password %ADMIN_PASSWORD%
echo bench --site %SITE_NAME% install-app erpnext
echo bench --site %SITE_NAME% install-app universal_workshop
echo.
echo To start development server:
echo لبدء خادم التطوير:
echo bench start
echo.

echo ✅ Installation completed!
echo تم إكمال التثبيت!
echo.
echo Access your site at: http://%SITE_NAME%:8000
echo يمكنك الوصول إلى موقعك على: http://%SITE_NAME%:8000
echo Default credentials: Administrator / %ADMIN_PASSWORD%
echo بيانات الدخول الافتراضية: Administrator / %ADMIN_PASSWORD%

pause 