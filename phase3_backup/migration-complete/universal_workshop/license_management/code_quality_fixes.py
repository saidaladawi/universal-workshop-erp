#!/usr/bin/env python3
"""
Code Quality Fixes for License Management Module
Addresses typing deprecations, code style issues, and best practices
"""

import re
import os
from pathlib import Path


def fix_typing_imports(content):
    """Fix deprecated typing imports"""
    replacements = [
        (r"from typing import ([^,\n]*?)Dict([^,\n]*)", r"from typing import \1dict\2"),
        (r"from typing import ([^,\n]*?)List([^,\n]*)", r"from typing import \1list\2"),
        (r"from typing import ([^,\n]*?)Tuple([^,\n]*)", r"from typing import \1tuple\2"),
        (r"from typing import ([^,\n]*?)Set([^,\n]*)", r"from typing import \1set\2"),
        # Handle type annotations
        (r": Dict\[", r": dict["),
        (r": List\[", r": list["),
        (r": Tuple\[", r": tuple["),
        (r": Set\[", r": set["),
        (r"-> Dict\[", r"-> dict["),
        (r"-> List\[", r"-> list["),
        (r"-> Tuple\[", r"-> tuple["),
        (r"-> Set\[", r"-> set["),
    ]

    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)

    return content


def fix_nested_if_statements(content):
    """Fix nested if statements that can be combined"""
    # This is a complex fix that would need manual review
    # For now, just flag them
    return content


def fix_exception_handling(content):
    """Improve exception handling patterns"""
    # Replace bare try-except-pass with contextlib.suppress
    content = re.sub(
        r"(\s+)try:\n(.*?)\n\s+except Exception:\n\s+pass",
        r"\1import contextlib\n\1with contextlib.suppress(Exception):\n\2",
        content,
        flags=re.DOTALL,
    )

    return content


def fix_file(file_path):
    """Apply all fixes to a single file"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # Apply fixes
        content = fix_typing_imports(content)
        content = fix_nested_if_statements(content)
        content = fix_exception_handling(content)

        # Only write if changes were made
        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Fixed: {file_path}")
            return True

    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False

    return False


def main():
    """Main execution function"""
    license_mgmt_dir = Path("universal_workshop/license_management")

    if not license_mgmt_dir.exists():
        print(f"Directory {license_mgmt_dir} not found")
        return

    python_files = list(license_mgmt_dir.rglob("*.py"))
    fixed_count = 0

    for file_path in python_files:
        if fix_file(file_path):
            fixed_count += 1

    print(f"\nSummary: Fixed {fixed_count} out of {len(python_files)} files")


if __name__ == "__main__":
    main()
