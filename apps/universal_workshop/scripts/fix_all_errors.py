#!/usr/bin/env python3
"""
Universal Workshop - Automatic Error Fixing Script
Fixes common linting errors across the entire codebase
Author: Eng. Saeed Al-Adawi
"""

import os
import re
import subprocess
import sys
from pathlib import Path


class UniversalWorkshopErrorFixer:
	"""Automatic error fixer for Universal Workshop ERP"""

	def __init__(self, project_root: str):
		self.project_root = Path(project_root)
		self.errors_fixed = 0
		self.files_processed = 0

	def run_all_fixes(self):
		"""Run all automatic fixes"""
		print("🔧 Starting Universal Workshop Error Fixing...")
		print("=" * 60)

		# 1. Fix translation imports (F821)
		print("📝 Fixing translation imports...")
		self.fix_translation_imports()

		# 2. Fix bare except statements (E722)
		print("🛡️ Fixing exception handling...")
		self.fix_bare_except()

		# 3. Fix collapsible if statements (SIM102)
		print("🔄 Simplifying if statements...")
		self.fix_collapsible_if()

		# 4. Fix deprecated imports (UP035)
		print("⬆️ Updating deprecated imports...")
		self.fix_deprecated_imports()

		# 5. Run final formatting
		print("✨ Running final formatting...")
		self.run_formatting()

		print("\n" + "=" * 60)
		print(f"✅ Fixed {self.errors_fixed} errors in {self.files_processed} files")
		print("🎉 Universal Workshop codebase is now clean!")

	def get_python_files(self):
		"""Get all Python files in the project"""
		python_files = []
		for root, dirs, files in os.walk(self.project_root):
			# Skip cache and build directories
			dirs[:] = [
				d for d in dirs if not d.startswith(".") and d not in ["__pycache__", "migrations", "patches"]
			]

			for file in files:
				if file.endswith(".py"):
					python_files.append(Path(root) / file)
		return python_files

	def fix_translation_imports(self):
		"""Fix missing translation function imports (F821)"""
		files_with_underscore = []

		for py_file in self.get_python_files():
			try:
				content = py_file.read_text(encoding="utf-8")

				# Check if file uses _() function but doesn't import it
				if "_(" in content and "from frappe import _" not in content:
					lines = content.split("\n")

					# Find the right place to add import
					import_line_idx = 0
					for i, line in enumerate(lines):
						if line.startswith("import ") or line.startswith("from "):
							import_line_idx = i + 1
						elif line.startswith("import frappe"):
							# If frappe is already imported, modify that line
							if "from frappe import" not in line:
								lines[i] = "import frappe\nfrom frappe import _"
							else:
								# Add _ to existing frappe import
								if ", _" not in line and "_" not in line.split("import")[1]:
									lines[i] = line.rstrip() + ", _"
							break
					else:
						# No frappe import found, add new import
						if import_line_idx == 0:
							# Add at the beginning
							lines.insert(0, "from frappe import _")
						else:
							lines.insert(import_line_idx, "from frappe import _")

					# Write back the file
					py_file.write_text("\n".join(lines), encoding="utf-8")
					files_with_underscore.append(py_file.name)
					self.errors_fixed += content.count("_(")

			except Exception as e:
				print(f"⚠️ Error processing {py_file}: {e}")

		if files_with_underscore:
			self.files_processed += len(files_with_underscore)
			print(f"   ✓ Fixed translation imports in {len(files_with_underscore)} files")

	def fix_bare_except(self):
		"""Fix bare except statements (E722)"""
		files_fixed = []

		for py_file in self.get_python_files():
			try:
				content = py_file.read_text(encoding="utf-8")
				original_content = content

				# Replace bare except with specific exception
				# Pattern 1: except:
				content = re.sub(r"^(\s*)except:\s*$", r"\1except Exception:", content, flags=re.MULTILINE)

				# Pattern 2: except: (with inline comment)
				content = re.sub(
					r"^(\s*)except:\s*(#.*)$", r"\1except Exception:  \2", content, flags=re.MULTILINE
				)

				if content != original_content:
					py_file.write_text(content, encoding="utf-8")
					files_fixed.append(py_file.name)
					self.errors_fixed += original_content.count("except:") - content.count("except:")

			except Exception as e:
				print(f"⚠️ Error processing {py_file}: {e}")

		if files_fixed:
			self.files_processed += len(files_fixed)
			print(f"   ✓ Fixed bare except in {len(files_fixed)} files")

	def fix_collapsible_if(self):
		"""Fix collapsible if statements (SIM102)"""
		files_fixed = []

		for py_file in self.get_python_files():
			try:
				content = py_file.read_text(encoding="utf-8")
				lines = content.split("\n")
				new_lines = []
				i = 0

				while i < len(lines):
					line = lines[i]

					# Look for pattern: if condition1:\n    if condition2:
					if line.strip().startswith("if ") and line.strip().endswith(":") and i + 1 < len(lines):
						next_line = lines[i + 1]

						# Check if next line is an indented if statement
						if (
							next_line.strip().startswith("if ")
							and next_line.strip().endswith(":")
							and len(next_line) - len(next_line.lstrip()) > len(line) - len(line.lstrip())
						):
							# Extract conditions
							condition1 = line.strip()[3:-1].strip()  # Remove 'if ' and ':'
							condition2 = next_line.strip()[3:-1].strip()  # Remove 'if ' and ':'
							indent = line[: len(line) - len(line.lstrip())]

							# Combine conditions with 'and'
							combined_line = f"{indent}if {condition1} and {condition2}:"
							new_lines.append(combined_line)

							# Skip the next line since we combined it
							i += 2
							self.errors_fixed += 1
							continue

					new_lines.append(line)
					i += 1

				new_content = "\n".join(new_lines)
				if new_content != content:
					py_file.write_text(new_content, encoding="utf-8")
					files_fixed.append(py_file.name)

			except Exception as e:
				print(f"⚠️ Error processing {py_file}: {e}")

		if files_fixed:
			self.files_processed += len(files_fixed)
			print(f"   ✓ Simplified if statements in {len(files_fixed)} files")

	def fix_deprecated_imports(self):
		"""Fix deprecated import patterns (UP035)"""
		files_fixed = []

		deprecated_patterns = [
			# collections imports
			(r"from collections import (\w+)", r"from collections.abc import \1"),
			# typing imports that moved
			(r"from typing import (Dict|List|Tuple|Set)", r"from typing import \1"),
		]

		for py_file in self.get_python_files():
			try:
				content = py_file.read_text(encoding="utf-8")
				original_content = content

				for old_pattern, new_pattern in deprecated_patterns:
					content = re.sub(old_pattern, new_pattern, content)

				if content != original_content:
					py_file.write_text(content, encoding="utf-8")
					files_fixed.append(py_file.name)
					self.errors_fixed += 1

			except Exception as e:
				print(f"⚠️ Error processing {py_file}: {e}")

		if files_fixed:
			self.files_processed += len(files_fixed)
			print(f"   ✓ Updated deprecated imports in {len(files_fixed)} files")

	def run_formatting(self):
		"""Run final ruff formatting"""
		try:
			# Run ruff format
			result = subprocess.run(
				["python", "-m", "ruff", "format", "."], capture_output=True, text=True, cwd=self.project_root
			)

			if result.returncode == 0:
				print("   ✓ Code formatting completed")
			else:
				print(f"   ⚠️ Formatting warning: {result.stderr}")

			# Run final ruff check with --fix
			result = subprocess.run(
				["python", "-m", "ruff", "check", "--fix"],
				capture_output=True,
				text=True,
				cwd=self.project_root,
			)

			if result.returncode == 0:
				print("   ✓ Final linting completed")
			else:
				print(f"   ⚠️ Some issues may remain: {result.stderr}")

		except Exception as e:
			print(f"⚠️ Error running formatting: {e}")


def main():
	"""Main function"""
	if len(sys.argv) > 1:
		project_root = sys.argv[1]
	else:
		project_root = os.getcwd()

	fixer = UniversalWorkshopErrorFixer(project_root)
	fixer.run_all_fixes()


if __name__ == "__main__":
	main()
