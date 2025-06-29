# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import json
import re
from typing import Any, Dict, List, Optional

import frappe
from frappe import _

try:
	from elasticsearch import Elasticsearch

	ELASTICSEARCH_AVAILABLE = True
except ImportError:
	ELASTICSEARCH_AVAILABLE = False

	# Create a placeholder class for type hints
	class Elasticsearch:
		pass


class SearchConfig:
	"""Configuration for Elasticsearch search"""

	def __init__(
		self,
		host: str = "localhost",
		port: int = 9200,
		scheme: str = "http",
		username: str | None = None,
		password: str | None = None,
		verify_certs: bool = False,
		index_prefix: str = "universal_workshop",
	):
		self.host = host
		self.port = port
		self.scheme = scheme
		self.username = username
		self.password = password
		self.verify_certs = verify_certs
		self.index_prefix = index_prefix


class ElasticsearchClient:
	"""
	Elasticsearch client for Universal Workshop ERP with Arabic language support
	"""

	def __init__(self, config: SearchConfig | None = None):
		"""Initialize Elasticsearch client with configuration"""
		self.config = config or self._get_default_config()
		self.client = None
		self._connected = False

		if ELASTICSEARCH_AVAILABLE:
			self._initialize_client()
		else:
			frappe.log_error("Elasticsearch library not available. Install: pip install elasticsearch")

	def _get_default_config(self) -> SearchConfig:
		"""Get default configuration from site config or environment"""
		site_config = frappe.get_site_config()

		return SearchConfig(
			host=site_config.get("elasticsearch_host", "localhost"),
			port=site_config.get("elasticsearch_port", 9200),
			scheme=site_config.get("elasticsearch_scheme", "http"),
			username=site_config.get("elasticsearch_username"),
			password=site_config.get("elasticsearch_password"),
			verify_certs=site_config.get("elasticsearch_verify_certs", False),
			index_prefix=site_config.get("elasticsearch_index_prefix", "universal_workshop"),
		)

	def _initialize_client(self):
		"""Initialize the Elasticsearch client connection"""
		if not ELASTICSEARCH_AVAILABLE:
			return

		try:
			# Build connection configuration
			es_config = {
				"hosts": [f"{self.config.scheme}://{self.config.host}:{self.config.port}"],
				"verify_certs": self.config.verify_certs,
				"timeout": 30,
				"max_retries": 3,
			}

			# Add authentication if provided
			if self.config.username and self.config.password:
				es_config["http_auth"] = (self.config.username, self.config.password)

			from elasticsearch import Elasticsearch

			self.client = Elasticsearch(**es_config)

			# Test connection
			if self.client and self.client.ping():
				self._connected = True
				frappe.logger().info("Elasticsearch connection established")
			else:
				frappe.log_error("Failed to connect to Elasticsearch")

		except Exception as e:
			frappe.log_error(f"Elasticsearch initialization error: {e!s}")
			self.client = None

	def is_available(self) -> bool:
		"""Check if Elasticsearch is available and connected"""
		return ELASTICSEARCH_AVAILABLE and self._connected and self.client is not None

	def get_index_name(self, doctype: str) -> str:
		"""Get the full index name for a DocType"""
		return f"{self.config.index_prefix}_{doctype.lower().replace(' ', '_')}"

	def create_index_mapping(self, doctype: str, fields_config: dict[str, Any]) -> bool:
		"""Create index mapping with Arabic language analyzer support"""
		if not self.is_available() or not self.client:
			return False

		index_name = self.get_index_name(doctype)

		# Define the index mapping with Arabic analyzer
		mapping = {
			"settings": {
				"analysis": {
					"analyzer": {
						"arabic_custom": {
							"type": "custom",
							"tokenizer": "standard",
							"filter": ["lowercase", "arabic_normalization", "arabic_stop", "arabic_stemmer"],
						}
					},
					"filter": {
						"arabic_stop": {"type": "stop", "stopwords": "_arabic_"},
						"arabic_stemmer": {"type": "stemmer", "language": "arabic"},
					},
				}
			},
			"mappings": {"properties": self._build_field_mappings(fields_config)},
		}

		try:
			# Delete index if it exists
			if self.client.indices.exists(index=index_name):
				self.client.indices.delete(index=index_name)

			# Create new index with mapping
			self.client.indices.create(index=index_name, body=mapping)
			return True

		except Exception as e:
			frappe.log_error(f"Failed to create index {index_name}: {e!s}")
			return False

	def _build_field_mappings(self, fields_config: dict[str, Any]) -> dict[str, Any]:
		"""Build Elasticsearch field mappings based on configuration"""
		mappings = {}

		for field_name, field_config in fields_config.items():
			field_type = field_config.get("type", "text")

			if field_type == "text":
				analyzer = "arabic_custom" if field_name.endswith("_ar") else "standard"
				mappings[field_name] = {
					"type": "text",
					"analyzer": analyzer,
					"fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
				}
			else:
				mappings[field_name] = {"type": field_type}

		return mappings

	def index_document(self, doctype: str, doc_id: str, document: dict[str, Any]) -> bool:
		"""Index a document in Elasticsearch"""
		if not self.is_available() or not self.client:
			return False

		try:
			index_name = self.get_index_name(doctype)
			normalized_doc = self._normalize_arabic_text(document)

			response = self.client.index(index=index_name, id=doc_id, body=normalized_doc)

			return response.get("result") in ["created", "updated"]

		except Exception as e:
			frappe.log_error(f"Failed to index document {doc_id}: {e!s}")
			return False

	def search_documents(
		self, doctype: str, query: str, filters: dict | None = None, size: int = 20, from_: int = 0
	) -> dict[str, Any]:
		"""Search documents with fuzzy matching and multi-language support"""
		if not self.is_available() or not self.client:
			return {"hits": [], "total": 0, "max_score": 0}

		try:
			index_name = self.get_index_name(doctype)
			search_body = self._build_search_query(query, filters)
			search_body["size"] = size
			search_body["from"] = from_

			response = self.client.search(index=index_name, body=search_body)

			return {
				"hits": [hit["_source"] for hit in response["hits"]["hits"]],
				"total": response["hits"]["total"]["value"],
				"max_score": response["hits"]["max_score"] or 0,
			}

		except Exception as e:
			frappe.log_error(f"Search failed for query '{query}': {e!s}")
			return {"hits": [], "total": 0, "max_score": 0}

	def _build_search_query(self, query: str, filters: dict | None = None) -> dict[str, Any]:
		"""Build Elasticsearch search query with fuzzy matching"""
		query_part = {
			"bool": {
				"should": [
					{
						"multi_match": {
							"query": query,
							"type": "best_fields",
							"fields": ["*"],
							"fuzziness": "AUTO",
						}
					}
				]
			}
		}

		# Add filters if provided
		if filters:
			filter_conditions = []
			for field, value in filters.items():
				if isinstance(value, list):
					filter_conditions.append({"terms": {field: value}})
				else:
					filter_conditions.append({"term": {field: value}})

			query_part["bool"]["filter"] = filter_conditions

		return {"query": query_part}

	def _normalize_arabic_text(self, document: dict[str, Any]) -> dict[str, Any]:
		"""Normalize Arabic text in document for better search"""
		normalized_doc = document.copy()

		for key, value in document.items():
			if isinstance(value, str) and re.search(r"[\u0600-\u06FF]", value):
				# Remove diacritics
				normalized_value = re.sub(r"[\u064B-\u0652\u0670\u0640]", "", value)
				# Normalize Alef variations
				normalized_value = re.sub(r"[آأإ]", "ا", normalized_value)
				# Normalize Teh Marbuta
				normalized_value = re.sub(r"ة", "ه", normalized_value)
				normalized_doc[key] = normalized_value

		return normalized_doc

	def delete_document(self, doctype: str, doc_id: str) -> bool:
		"""Delete a document from the index"""
		if not self.is_available() or not self.client:
			return False

		try:
			index_name = self.get_index_name(doctype)
			response = self.client.delete(index=index_name, id=doc_id)
			return response.get("result") == "deleted"

		except Exception as e:
			frappe.log_error(f"Failed to delete document {doc_id}: {e!s}")
			return False


# Global client instance
_es_client = None


def get_elasticsearch_client():
	"""Get the global Elasticsearch client instance"""
	global _es_client
	if _es_client is None:
		_es_client = ElasticsearchClient()
	return _es_client
