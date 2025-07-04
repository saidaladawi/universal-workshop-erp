"""
Universal Workshop ERP - Basic Data Setup
Creates essential master data for testing
"""

import frappe
from frappe import _


def setup_basic_data():
    """Create basic master data required for testing"""
    print("🔧 Setting up basic data for Universal Workshop ERP...")
    
    try:
        # Create Customer Group if not exists
        if not frappe.db.exists("Customer Group", "Individual"):
            customer_group = frappe.new_doc("Customer Group")
            customer_group.customer_group_name = "Individual"
            customer_group.is_group = 0
            customer_group.insert()
            print("✅ Created Customer Group: Individual")
        else:
            print("✅ Customer Group 'Individual' already exists")
        
        # Create Territory if not exists
        if not frappe.db.exists("Territory", "Oman"):
            territory = frappe.new_doc("Territory")
            territory.territory_name = "Oman"
            territory.is_group = 0
            territory.insert()
            print("✅ Created Territory: Oman")
        else:
            print("✅ Territory 'Oman' already exists")
        
        # Create additional Customer Groups
        customer_groups = ["Corporate", "Government", "Fleet"]
        for group_name in customer_groups:
            if not frappe.db.exists("Customer Group", group_name):
                customer_group = frappe.new_doc("Customer Group")
                customer_group.customer_group_name = group_name
                customer_group.is_group = 0
                customer_group.insert()
                print(f"✅ Created Customer Group: {group_name}")
        
        # Create additional Territories
        territories = ["Muscat", "Salalah", "Nizwa", "Sohar"]
        for territory_name in territories:
            if not frappe.db.exists("Territory", territory_name):
                territory = frappe.new_doc("Territory")
                territory.territory_name = territory_name
                territory.is_group = 0
                territory.parent_territory = "Oman"
                territory.insert()
                print(f"✅ Created Territory: {territory_name}")
        
        # Create sample items for parts
        sample_parts = [
            {"item_code": "OIL-FILTER-001", "item_name": "Oil Filter", "item_name_ar": "فلتر الزيت"},
            {"item_code": "BRAKE-PAD-001", "item_name": "Brake Pad Set", "item_name_ar": "طقم وسائد الفرامل"},
            {"item_code": "SPARK-PLUG-001", "item_name": "Spark Plug", "item_name_ar": "شمعة الإشعال"},
            {"item_code": "ENGINE-OIL-001", "item_name": "Engine Oil 5W-30", "item_name_ar": "زيت المحرك"},
        ]
        
        for part in sample_parts:
            if not frappe.db.exists("Item", part["item_code"]):
                item = frappe.new_doc("Item")
                item.item_code = part["item_code"]
                item.item_name = part["item_name"]
                item.item_group = "Parts"
                item.stock_uom = "Nos"
                item.is_stock_item = 1
                item.include_item_in_manufacturing = 0
                item.insert()
                print(f"✅ Created Item: {part['item_name']}")
        
        frappe.db.commit()
        print("\n🎉 Basic data setup completed successfully!")
        print("✅ Customer Groups: Individual, Corporate, Government, Fleet")
        print("✅ Territories: Oman, Muscat, Salalah, Nizwa, Sohar")
        print("✅ Sample Parts: 4 items created")
        
        return True
        
    except Exception as e:
        frappe.db.rollback()
        print(f"❌ Error setting up basic data: {e}")
        return False


if __name__ == "__main__":
    setup_basic_data() 