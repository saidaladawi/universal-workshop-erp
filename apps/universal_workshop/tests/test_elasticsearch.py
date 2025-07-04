#!/usr/bin/env python3

import frappe


def test_elasticsearch_integration():
	"""Test Elasticsearch integration for customer search"""
	try:
		from universal_workshop.search_integration.customer_indexer import CustomerIndexer
		from universal_workshop.search_integration.elasticsearch_client import get_elasticsearch_client

		print("Testing Elasticsearch Integration...")

		# Test 1: Check Elasticsearch client availability
		print("\n1. Testing Elasticsearch Client...")
		es_client = get_elasticsearch_client()

		if es_client.is_available():
			print("✅ Elasticsearch client connected successfully")
		else:
			print("⚠️  Elasticsearch not available - fallback mode will be used")

		# Test 2: Test Customer Indexer
		print("\n2. Testing Customer Indexer...")
		indexer = CustomerIndexer()

		# Try to setup index (will fail gracefully if ES not available)
		if indexer.setup_customer_index():
			print("✅ Customer index setup successful")
		else:
			print("⚠️  Customer index setup failed - using fallback search")

		# Test 3: Test search functionality (with fallback)
		print("\n3. Testing Search Functionality...")
		results = indexer.search_customers("test", size=5)
		print(f"✅ Search function returned {results.get('total', 0)} results")

		# Test 4: Test API endpoints
		print("\n4. Testing API Endpoints...")

		# Test customer search API
		search_result = frappe.call(
			"universal_workshop.search_integration.api.search_customers", query="Ahmad"
		)

		if search_result:
			print("✅ Customer search API working")
		else:
			print("❌ Customer search API failed")

		# Test suggestions API
		suggestions_result = frappe.call(
			"universal_workshop.search_integration.api.get_customer_suggestions",
			field="customer_name",
			text="A",
		)

		if suggestions_result:
			print("✅ Customer suggestions API working")
		else:
			print("❌ Customer suggestions API failed")

		# Test 5: Test search status
		print("\n5. Testing Search Status...")
		status_result = frappe.call("universal_workshop.search_integration.api.search_status")

		if status_result and status_result.get("success"):
			status = status_result["status"]
			print(f"✅ Search status: {status['search_type']}")
			if status.get("elasticsearch_available"):
				print(f"   Index documents: {status.get('index_stats', {}).get('document_count', 0)}")
		else:
			print("❌ Search status check failed")

		print("\n" + "=" * 50)
		print("ELASTICSEARCH INTEGRATION TEST COMPLETED")
		print("=" * 50)

		return True

	except ImportError as e:
		print(f"❌ Import error: {e}")
		print("💡 Install Elasticsearch: pip install elasticsearch")
		return False

	except Exception as e:
		print(f"❌ Test failed: {e}")
		return False


if __name__ == "__main__":
	frappe.init(site="universal.local")
	frappe.connect()
	test_elasticsearch_integration()
