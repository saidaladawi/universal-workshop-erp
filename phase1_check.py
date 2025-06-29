#!/usr/bin/env python3
"""
Phase 1 Verification Script for Universal Workshop ERP Refactoring
Checks if Phase 1 requirements have been completed successfully.
"""

import os
import sys
from pathlib import Path
from datetime import datetime


def check_backup_created():
    """Check if backup was created (1.1)"""
    print("🔍 Checking Phase 1.1: Backup Creation")

    # Check for backup directory
    backup_dirs = [d for d in os.listdir("apps/") if d.startswith("universal_workshop.backup.")]
    if backup_dirs:
        print(f"✅ File backup found: {backup_dirs[0]}")
    else:
        print("❌ No file backup found")
        return False

    # Check for database backup
    backup_path = Path("sites/universal.local/private/backups/")
    if backup_path.exists():
        recent_backups = [f for f in backup_path.iterdir() if f.name.startswith("20250629")]
        if recent_backups:
            print(f"✅ Database backup found: {len(recent_backups)} files")
        else:
            print("❌ No recent database backup found")
            return False
    else:
        print("❌ Backup directory not found")
        return False

    # Check for git tag
    try:
        result = os.popen("cd apps/universal_workshop && git tag | grep pre-refactoring").read()
        if "pre-refactoring" in result:
            print("✅ Git backup tag found")
        else:
            print("❌ Git backup tag not found")
            return False
    except:
        print("❌ Error checking git tags")
        return False

    return True


def check_dependency_analysis():
    """Check if dependency analysis was completed (1.2)"""
    print("\n🔍 Checking Phase 1.2: Dependency Analysis")

    files_to_check = ["dependency_map.txt", "import_analysis.txt", "external_dependencies.txt"]
    all_exist = True

    for file in files_to_check:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"✅ {file}: {size} bytes")
        else:
            print(f"❌ {file}: Not found")
            all_exist = False

    return all_exist


def check_directory_structure():
    """Check if new directory structure was created (1.3)"""
    print("\n🔍 Checking Phase 1.3: Directory Structure Creation")

    required_dirs = [
        "apps/universal_workshop/universal_workshop/core/boot",
        "apps/universal_workshop/universal_workshop/core/permissions",
        "apps/universal_workshop/universal_workshop/core/session",
        "apps/universal_workshop/universal_workshop/core/monitoring",
        "apps/universal_workshop/universal_workshop/setup/installation",
        "apps/universal_workshop/universal_workshop/setup/onboarding",
        "apps/universal_workshop/universal_workshop/setup/licensing",
        "apps/universal_workshop/universal_workshop/setup/branding",
        "apps/universal_workshop/universal_workshop/workshop_operations",
        "apps/universal_workshop/universal_workshop/system_administration",
        "apps/universal_workshop/universal_workshop/mobile_operations",
        "apps/universal_workshop/universal_workshop/assets/js/core",
        "apps/universal_workshop/universal_workshop/assets/js/modules",
        "apps/universal_workshop/universal_workshop/assets/js/shared",
        "apps/universal_workshop/universal_workshop/assets/css/core",
        "apps/universal_workshop/universal_workshop/assets/css/themes",
    ]

    all_exist = True
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✅ {dir_path}")
        else:
            print(f"❌ {dir_path}: Missing")
            all_exist = False

    return all_exist


def check_safety_framework():
    """Check if safety testing framework was created (1.4)"""
    print("\n🔍 Checking Phase 1.4: Safety Testing Framework")

    if os.path.exists("test_refactoring_safety.py"):
        size = os.path.getsize("test_refactoring_safety.py")
        print(f"✅ Safety testing framework: {size} bytes")
        return True
    else:
        print("❌ Safety testing framework: Not found")
        return False


def main():
    """Main verification function"""
    print("🔍 Universal Workshop ERP - Phase 1 Verification")
    print("=" * 60)
    print(f"Verification Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Change to correct directory
    os.chdir("/home/said/frappe-dev/frappe-bench")

    # Run all checks
    checks = [
        ("1.1 Backup Creation", check_backup_created),
        ("1.2 Dependency Analysis", check_dependency_analysis),
        ("1.3 Directory Structure", check_directory_structure),
        ("1.4 Safety Framework", check_safety_framework),
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Error in {name}: {e}")
            results.append((name, False))

    # Print summary
    print("\n" + "=" * 60)
    print("📊 PHASE 1 VERIFICATION SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\nResults: {passed}/{total} checks passed")

    if passed == total:
        print("\n🎉 Phase 1 COMPLETED SUCCESSFULLY!")
        print("✅ System is ready for Phase 2: Core System Consolidation")
        return 0
    else:
        print(f"\n⚠️  Phase 1 INCOMPLETE: {total - passed} issues found")
        print("❌ Please address the failed checks before proceeding to Phase 2")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
