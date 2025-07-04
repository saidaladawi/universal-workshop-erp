# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import json
import csv
import os
import time
import psutil
from abc import ABC, abstractmethod
from io import StringIO
from typing import Dict, List, Optional, Any, Generator

import frappe
from frappe import _
from frappe.utils import get_files_path, now_datetime, flt, cint

try:
    import pandas as pd
    import openpyxl

    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False


class DataSourceAdapter(ABC):
    """Abstract base class for data source adapters"""

    def __init__(self, migration_job):
        self.migration_job = migration_job
        self.field_mapping = self._parse_field_mapping()

    def _parse_field_mapping(self) -> Dict:
        """Parse field mapping from migration job"""
        if self.migration_job.field_mapping:
            if isinstance(self.migration_job.field_mapping, str):
                return json.loads(self.migration_job.field_mapping)
            return self.migration_job.field_mapping
        return {}

    @abstractmethod
    def get_total_records(self) -> int:
        """Get total number of records to be processed"""
        pass

    @abstractmethod
    def read_data(self, batch_size: int = 1000) -> Generator[List[Dict], None, None]:
        """Read data in batches"""
        pass

    @abstractmethod
    def validate_source(self) -> bool:
        """Validate the data source"""
        pass


class CSVAdapter(DataSourceAdapter):
    """CSV file adapter"""

    def __init__(self, migration_job):
        super().__init__(migration_job)
        self.file_path = self._get_file_path()
        self.encoding = "utf-8"

    def _get_file_path(self) -> str:
        """Get the full file path"""
        if not self.migration_job.source_file:
            raise ValueError(_("Source file is required for CSV migration"))

        file_doc = frappe.get_doc("File", {"file_url": self.migration_job.source_file})
        return frappe.get_site_path(file_doc.file_url.lstrip("/"))

    def validate_source(self) -> bool:
        """Validate CSV file exists and is readable"""
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(_("CSV file not found: {0}").format(self.file_path))

        # Test reading first few lines
        try:
            with open(self.file_path, "r", encoding=self.encoding) as file:
                csv.reader(file).__next__()  # Read header
                return True
        except Exception as e:
            raise ValueError(_("Invalid CSV file: {0}").format(str(e)))

    def get_total_records(self) -> int:
        """Count total records in CSV file"""
        with open(self.file_path, "r", encoding=self.encoding) as file:
            return sum(1 for line in csv.reader(file)) - 1  # Exclude header

    def read_data(self, batch_size: int = 1000) -> Generator[List[Dict], None, None]:
        """Read CSV data in batches"""
        with open(self.file_path, "r", encoding=self.encoding) as file:
            reader = csv.DictReader(file)
            batch = []

            for row in reader:
                # Apply field mapping
                mapped_row = self._apply_field_mapping(row)
                batch.append(mapped_row)

                if len(batch) >= batch_size:
                    yield batch
                    batch = []

            if batch:  # Yield remaining records
                yield batch

    def _apply_field_mapping(self, row: Dict) -> Dict:
        """Apply field mapping to a single row"""
        if not self.field_mapping:
            return row

        mapped_row = {}
        for source_field, target_field in self.field_mapping.items():
            if source_field in row:
                mapped_row[target_field] = row[source_field]

        # Include unmapped fields
        for field, value in row.items():
            if field not in self.field_mapping and field not in mapped_row:
                mapped_row[field] = value

        return mapped_row


class ExcelAdapter(DataSourceAdapter):
    """Excel file adapter"""

    def __init__(self, migration_job):
        if not EXCEL_AVAILABLE:
            raise ImportError(_("pandas and openpyxl are required for Excel migrations"))

        super().__init__(migration_job)
        self.file_path = self._get_file_path()
        self.sheet_name = 0  # Default to first sheet
        self.df = None

    def _get_file_path(self) -> str:
        """Get the full file path"""
        if not self.migration_job.source_file:
            raise ValueError(_("Source file is required for Excel migration"))

        file_doc = frappe.get_doc("File", {"file_url": self.migration_job.source_file})
        return frappe.get_site_path(file_doc.file_url.lstrip("/"))

    def validate_source(self) -> bool:
        """Validate Excel file exists and is readable"""
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(_("Excel file not found: {0}").format(self.file_path))

        try:
            # Test reading file
            self.df = pd.read_excel(self.file_path, sheet_name=self.sheet_name)
            return True
        except Exception as e:
            raise ValueError(_("Invalid Excel file: {0}").format(str(e)))

    def get_total_records(self) -> int:
        """Get total number of records in Excel file"""
        if self.df is None:
            self.df = pd.read_excel(self.file_path, sheet_name=self.sheet_name)
        return len(self.df)

    def read_data(self, batch_size: int = 1000) -> Generator[List[Dict], None, None]:
        """Read Excel data in batches"""
        if self.df is None:
            self.df = pd.read_excel(self.file_path, sheet_name=self.sheet_name)

        total_rows = len(self.df)
        for start_idx in range(0, total_rows, batch_size):
            end_idx = min(start_idx + batch_size, total_rows)
            batch_df = self.df.iloc[start_idx:end_idx]

            # Convert to list of dictionaries and apply field mapping
            batch = []
            for _, row in batch_df.iterrows():
                row_dict = row.to_dict()
                # Handle NaN values
                row_dict = {k: (v if pd.notna(v) else "") for k, v in row_dict.items()}
                mapped_row = self._apply_field_mapping(row_dict)
                batch.append(mapped_row)

            yield batch

    def _apply_field_mapping(self, row: Dict) -> Dict:
        """Apply field mapping to a single row"""
        if not self.field_mapping:
            return row

        mapped_row = {}
        for source_field, target_field in self.field_mapping.items():
            if source_field in row:
                mapped_row[target_field] = row[source_field]

        # Include unmapped fields
        for field, value in row.items():
            if field not in self.field_mapping and field not in mapped_row:
                mapped_row[field] = value

        return mapped_row


class DatabaseAdapter(DataSourceAdapter):
    """Database adapter for direct database connections"""

    def __init__(self, migration_job):
        super().__init__(migration_job)
        self.connection_config = self._parse_connection_config()
        self.query = self._get_source_query()

    def _parse_connection_config(self) -> Dict:
        """Parse database connection configuration"""
        # This would be stored in transformation_settings or a separate field
        if self.migration_job.transformation_settings:
            config = (
                json.loads(self.migration_job.transformation_settings)
                if isinstance(self.migration_job.transformation_settings, str)
                else self.migration_job.transformation_settings
            )
            return config.get("database_config", {})
        return {}

    def _get_source_query(self) -> str:
        """Get the SQL query for data extraction"""
        # This would be configured in the migration job
        return self.connection_config.get("query", "SELECT * FROM source_table")

    def validate_source(self) -> bool:
        """Validate database connection and query"""
        # Implementation would depend on database type
        # For now, just return True as this is a placeholder
        return True

    def get_total_records(self) -> int:
        """Get total number of records from database"""
        # Implementation would execute COUNT query
        return 0

    def read_data(self, batch_size: int = 1000) -> Generator[List[Dict], None, None]:
        """Read database data in batches"""
        # Implementation would execute paginated queries
        yield []


class JSONAdapter(DataSourceAdapter):
    """JSON file adapter"""

    def __init__(self, migration_job):
        super().__init__(migration_job)
        self.file_path = self._get_file_path()
        self.data = None

    def _get_file_path(self) -> str:
        """Get the full file path"""
        if not self.migration_job.source_file:
            raise ValueError(_("Source file is required for JSON migration"))

        file_doc = frappe.get_doc("File", {"file_url": self.migration_job.source_file})
        return frappe.get_site_path(file_doc.file_url.lstrip("/"))

    def validate_source(self) -> bool:
        """Validate JSON file exists and is readable"""
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(_("JSON file not found: {0}").format(self.file_path))

        try:
            with open(self.file_path, "r", encoding="utf-8") as file:
                self.data = json.load(file)
                return True
        except Exception as e:
            raise ValueError(_("Invalid JSON file: {0}").format(str(e)))

    def get_total_records(self) -> int:
        """Get total number of records in JSON file"""
        if self.data is None:
            with open(self.file_path, "r", encoding="utf-8") as file:
                self.data = json.load(file)

        if isinstance(self.data, list):
            return len(self.data)
        elif isinstance(self.data, dict) and "records" in self.data:
            return len(self.data["records"])
        else:
            return 1  # Single record

    def read_data(self, batch_size: int = 1000) -> Generator[List[Dict], None, None]:
        """Read JSON data in batches"""
        if self.data is None:
            with open(self.file_path, "r", encoding="utf-8") as file:
                self.data = json.load(file)

        # Determine data structure
        if isinstance(self.data, list):
            records = self.data
        elif isinstance(self.data, dict) and "records" in self.data:
            records = self.data["records"]
        else:
            records = [self.data]  # Single record

        # Process in batches
        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]
            mapped_batch = [self._apply_field_mapping(record) for record in batch]
            yield mapped_batch

    def _apply_field_mapping(self, row: Dict) -> Dict:
        """Apply field mapping to a single row"""
        if not self.field_mapping:
            return row

        mapped_row = {}
        for source_field, target_field in self.field_mapping.items():
            if source_field in row:
                mapped_row[target_field] = row[source_field]

        # Include unmapped fields
        for field, value in row.items():
            if field not in self.field_mapping and field not in mapped_row:
                mapped_row[field] = value

        return mapped_row


class MigrationFramework:
    """Main migration framework class"""

    def __init__(self, migration_job):
        self.migration_job = migration_job
        self.adapter = self._create_adapter()
        self.validation_rules = self._parse_validation_rules()
        self.rollback_data = {"created_records": {}, "modified_records": {}}

    def _create_adapter(self) -> DataSourceAdapter:
        """Create appropriate data source adapter"""
        source_type = self.migration_job.source_type

        adapters = {
            "CSV": CSVAdapter,
            "Excel": ExcelAdapter,
            "Database": DatabaseAdapter,
            "JSON": JSONAdapter,
        }

        if source_type not in adapters:
            raise ValueError(_("Unsupported source type: {0}").format(source_type))

        return adapters[source_type](self.migration_job)

    def _parse_validation_rules(self) -> Dict:
        """Parse validation rules from migration job"""
        if self.migration_job.validation_rules:
            if isinstance(self.migration_job.validation_rules, str):
                return json.loads(self.migration_job.validation_rules)
            return self.migration_job.validation_rules
        return {}

    def execute(self):
        """Execute the migration process"""
        try:
            # Validate source
            self.adapter.validate_source()

            # Get total records
            total_records = self.adapter.get_total_records()
            self.migration_job.total_records = total_records
            self.migration_job.processed_records = 0
            self.migration_job.successful_records = 0
            self.migration_job.failed_records = 0
            self.migration_job.save()

            # Process data in batches
            for batch in self.adapter.read_data(self.migration_job.batch_size):
                self._process_batch(batch)

                # Update progress
                self.migration_job.processed_records += len(batch)
                self._update_performance_metrics()
                self.migration_job.save()

            # Save rollback data
            self.migration_job.rollback_data = json.dumps(self.rollback_data)
            self.migration_job.save()

        except Exception as e:
            self.migration_job.log_error(f"Migration execution failed: {str(e)}")
            raise

    def _process_batch(self, batch: List[Dict]):
        """Process a batch of records"""
        for record in batch:
            try:
                self._process_record(record)
                self.migration_job.successful_records += 1
            except Exception as e:
                self.migration_job.log_error(
                    f"Failed to process record: {str(e)}", record_data=record
                )

    def _process_record(self, record: Dict):
        """Process a single record"""
        # Use validation engine if available
        validation_result = self._validate_record_with_engine(record)

        if not validation_result["is_valid"]:
            raise ValueError(f"Validation failed: {'; '.join(validation_result['errors'])}")

        # Use cleaned record from validation
        record = validation_result["cleaned_record"]

        # Transform data if needed
        transformed_record = self._transform_record(record)

        # Create or update document
        if self.migration_job.migration_type == "Import":
            self._create_document(transformed_record)
        elif self.migration_job.migration_type == "Update":
            self._update_document(transformed_record)

    def _validate_record_with_engine(self, record: Dict) -> Dict:
        """Validate record using validation engine"""
        try:
            from universal_workshop.data_migration.validation_engine import ValidationEngine

            # Create validation engine with rules from migration job
            validation_config = self.validation_rules
            if validation_config:
                engine = ValidationEngine(validation_config)
                return engine.validate_record(record)
            else:
                # Fallback to basic validation
                return self._validate_record_basic(record)

        except ImportError:
            # Fallback if validation engine not available
            return self._validate_record_basic(record)

    def _validate_record_basic(self, record: Dict) -> Dict:
        """Basic validation fallback"""
        result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "cleaned_record": record.copy(),
            "suggestions": {},
        }

        rules = self.validation_rules

        # Required fields validation
        if "required_fields" in rules:
            for field in rules["required_fields"]:
                if field not in record or not record[field]:
                    result["is_valid"] = False
                    result["errors"].append(_("Required field {0} is missing").format(field))

        # Email validation
        if rules.get("email_validation") and "email" in record:
            email = record["email"]
            if email and "@" not in email:
                result["is_valid"] = False
                result["errors"].append(_("Invalid email format: {0}").format(email))

        # Phone format validation
        if "phone_format" in rules and "phone" in record:
            phone = record["phone"]
            expected_format = rules["phone_format"]
            if phone and not phone.startswith(expected_format):
                result["is_valid"] = False
                result["errors"].append(
                    _("Phone number must start with {0}").format(expected_format)
                )

        return result

    def _transform_record(self, record: Dict) -> Dict:
        """Transform record data if needed"""
        # Basic transformations
        transformed = record.copy()

        # Date transformations, unit conversions, etc. can be added here

        return transformed

    def _create_document(self, record: Dict):
        """Create a new document"""
        doctype = self.migration_job.target_doctype

        # Create document
        doc = frappe.new_doc(doctype)
        doc.update(record)
        doc.insert()

        # Log transaction for rollback
        self.migration_job.log_transaction("create", doctype, doc.name, record)

        # Store in rollback data
        if doctype not in self.rollback_data["created_records"]:
            self.rollback_data["created_records"][doctype] = []
        self.rollback_data["created_records"][doctype].append(doc.name)

    def _update_document(self, record: Dict):
        """Update existing document"""
        doctype = self.migration_job.target_doctype

        # Find document to update (requires identifier field)
        identifier_field = "name"  # This should be configurable
        if identifier_field not in record:
            raise ValueError(_("Identifier field {0} not found in record").format(identifier_field))

        doc_name = record[identifier_field]
        if not frappe.db.exists(doctype, doc_name):
            raise ValueError(_("Document {0} {1} not found").format(doctype, doc_name))

        # Get original data for rollback
        original_doc = frappe.get_doc(doctype, doc_name)
        original_data = original_doc.as_dict()

        # Update document
        original_doc.update(record)
        original_doc.save()

        # Log transaction for rollback
        self.migration_job.log_transaction("update", doctype, doc_name, record)

        # Store in rollback data
        if doctype not in self.rollback_data["modified_records"]:
            self.rollback_data["modified_records"][doctype] = {}
        self.rollback_data["modified_records"][doctype][doc_name] = original_data

    def _update_performance_metrics(self):
        """Update performance metrics"""
        try:
            # Memory usage
            process = psutil.Process()
            memory_info = process.memory_info()
            self.migration_job.memory_usage_mb = flt(memory_info.rss / 1024 / 1024, 2)

            # CPU usage
            self.migration_job.cpu_usage_percent = flt(process.cpu_percent(), 2)

        except Exception:
            # If psutil is not available or fails, continue without metrics
            pass
