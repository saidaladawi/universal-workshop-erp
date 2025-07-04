#!/usr/bin/env python3
"""
Code Quality Checker for Universal Workshop
Runs comprehensive code quality checks and fixes
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
	"""Run a command and capture output"""
	print(f"\n🔍 {description}")
	print(f"Running: {' '.join(cmd)}")

	try:
		result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent)

		if result.stdout:
			print("✅ Output:")
			print(result.stdout)

		if result.stderr and result.returncode != 0:
			print("❌ Errors:")
			print(result.stderr)

		return result.returncode == 0
	except Exception as e:
		print(f"❌ Failed to run command: {e}")
		return False


def main():
	"""Main quality check runner"""
	print("🚀 Universal Workshop Code Quality Check")
	print("=" * 50)

	# Ensure we're in the right directory
	os.chdir(Path(__file__).parent.parent)

	checks = [
		{"cmd": ["ruff", "check", ".", "--statistics"], "description": "Ruff Linting Check"},
		{"cmd": ["ruff", "format", "--check", "."], "description": "Ruff Format Check"},
		{
			"cmd": ["mypy", "universal_workshop", "--ignore-missing-imports"],
			"description": "MyPy Type Checking",
		},
		{"cmd": ["pytest", "--tb=short", "-v"], "description": "Unit Tests"},
	]

	fixes = [
		{"cmd": ["ruff", "check", ".", "--fix"], "description": "Auto-fix Ruff Issues"},
		{"cmd": ["ruff", "format", "."], "description": "Auto-format Code"},
	]

	# Run checks first
	print("\n📊 RUNNING QUALITY CHECKS")
	print("-" * 30)

	check_results = []
	for check in checks:
		success = run_command(check["cmd"], check["description"])
		check_results.append((check["description"], success))

	# Offer to run fixes
	failed_checks = [desc for desc, success in check_results if not success]

	if failed_checks:
		print(f"\n⚠️  {len(failed_checks)} checks failed:")
		for desc in failed_checks:
			print(f"   - {desc}")

		answer = input("\n🔧 Would you like to run auto-fixes? (y/N): ").lower().strip()

		if answer in ["y", "yes"]:
			print("\n🛠️  RUNNING AUTO-FIXES")
			print("-" * 25)

			for fix in fixes:
				run_command(fix["cmd"], fix["description"])

			print("\n🔄 Re-running checks after fixes...")
			for check in checks[:2]:  # Only re-run ruff checks
				run_command(check["cmd"], f"Re-check: {check['description']}")

	else:
		print("\n✅ All quality checks passed!")

	print("\n📈 SUMMARY")
	print("-" * 10)
	for desc, success in check_results:
		status = "✅ PASS" if success else "❌ FAIL"
		print(f"{status} {desc}")


if __name__ == "__main__":
	main()
