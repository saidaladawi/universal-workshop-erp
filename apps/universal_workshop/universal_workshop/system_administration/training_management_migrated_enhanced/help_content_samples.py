# Copyright (c) 2024, Universal Workshop and contributors
# Sample Help Content for Contextual Help System

import frappe
from frappe import _


def create_sample_help_content():
	"""Create sample help content for demonstration"""
	
	sample_content = [
		{
			"title": "Creating a New Training Module",
			"title_ar": "إنشاء وحدة تدريبية جديدة",
			"content_key": "create-training-module",
			"help_type": "Guided Tour",
			"priority": "High",
			"target_doctype": "Training Module",
			"content": """
				<div class="help-content">
					<h5>Creating a Training Module</h5>
					<p>Follow these steps to create a comprehensive training module:</p>
					<ol>
						<li>Enter a clear, descriptive title for your module</li>
						<li>Add both English and Arabic descriptions for multilingual support</li>
						<li>Set the appropriate difficulty level based on your audience</li>
						<li>Define estimated duration in hours</li>
						<li>Upload relevant content files and videos</li>
						<li>Create assessment questions to test understanding</li>
					</ol>
					<p><strong>Tip:</strong> Use clear, concise language and include practical examples.</p>
				</div>
			""",
			"content_ar": """
				<div class="help-content" dir="rtl">
					<h5>إنشاء وحدة تدريبية</h5>
					<p>اتبع هذه الخطوات لإنشاء وحدة تدريبية شاملة:</p>
					<ol>
						<li>أدخل عنواناً واضحاً ووصفياً للوحدة</li>
						<li>أضف أوصافاً باللغتين الإنجليزية والعربية للدعم متعدد اللغات</li>
						<li>حدد مستوى الصعوبة المناسب حسب جمهورك</li>
						<li>حدد المدة المقدرة بالساعات</li>
						<li>ارفع ملفات المحتوى ومقاطع الفيديو ذات الصلة</li>
						<li>أنشئ أسئلة تقييم لاختبار الفهم</li>
					</ol>
					<p><strong>نصيحة:</strong> استخدم لغة واضحة ومقتضبة وتضمين أمثلة عملية.</p>
				</div>
			""",
			"application_routes": [
				{"route": "/app/training-module/new"},
				{"route": "/app/Form/Training Module"}
			],
			"user_roles": [
				{"role": "Training Manager"},
				{"role": "System Manager"}
			]
		},
		{
			"title": "Understanding Training Progress",
			"title_ar": "فهم تقدم التدريب",
			"content_key": "training-progress-help",
			"help_type": "Tooltip",
			"priority": "Medium",
			"target_doctype": "Training Progress",
			"target_field": "progress_percentage",
			"tooltip_text": "Progress percentage shows how much of the training module has been completed. It's calculated based on time spent, quiz scores, and module completion status.",
			"tooltip_text_ar": "نسبة التقدم تُظهر كم من الوحدة التدريبية تم إكمالها. يتم حسابها بناءً على الوقت المستغرق ودرجات الاختبار وحالة إكمال الوحدة.",
			"application_routes": [
				{"route": "/app/training-progress"},
				{"route": "/app/Form/Training Progress"}
			]
		},
		{
			"title": "Role-Based Training Path Assignment",
			"title_ar": "تعيين مسار التدريب القائم على الأدوار",
			"content_key": "role-based-training",
			"help_type": "Modal",
			"priority": "High",
			"target_doctype": "Training Path",
			"content": """
				<div class="help-content">
					<h5>Role-Based Training Paths</h5>
					<p>Training paths are automatically assigned based on user roles:</p>
					<ul>
						<li><strong>Workshop Manager:</strong> Advanced management and leadership training</li>
						<li><strong>Technician:</strong> Technical skills and safety procedures</li>
						<li><strong>Administrative Staff:</strong> Administrative processes and customer service</li>
					</ul>
					<p>Users are automatically enrolled when they meet the prerequisites and have the required role.</p>
					<p><strong>Auto-enrollment criteria:</strong></p>
					<ul>
						<li>User has the target role</li>
						<li>All prerequisite paths are completed</li>
						<li>Minimum competency levels are met</li>
						<li>Department filters match (if specified)</li>
					</ul>
				</div>
			""",
			"application_routes": [
				{"route": "/app/training-path"},
				{"route": "/app/Form/Training Path"},
				{"route": "/training-path-admin"}
			],
			"user_roles": [
				{"role": "Training Manager"},
				{"role": "System Manager"},
				{"role": "Workshop Manager"}
			]
		},
		{
			"title": "Training Dashboard Overview",
			"title_ar": "نظرة عامة على لوحة التدريب",
			"content_key": "training-dashboard-overview",
			"help_type": "Contextual Banner",
			"priority": "Medium",
			"target_page": "/training-dashboard",
			"content": """
				<p>This dashboard provides a comprehensive view of your training progress, upcoming modules, and achievements. 
				Use the charts to track your learning journey and identify areas for improvement.</p>
			""",
			"content_ar": """
				<p>توفر هذه اللوحة عرضاً شاملاً لتقدم التدريب والوحدات القادمة والإنجازات. 
				استخدم الرسوم البيانية لتتبع رحلة التعلم وتحديد المجالات التي تحتاج للتحسين.</p>
			""",
			"application_routes": [
				{"route": "/training-dashboard"}
			]
		},
		{
			"title": "Knowledge Base Search Tips",
			"title_ar": "نصائح البحث في قاعدة المعرفة",
			"content_key": "knowledge-base-search",
			"help_type": "Popover",
			"priority": "Low",
			"target_page": "/knowledge-base",
			"content": """
				<div class="help-content">
					<h6>Search Tips</h6>
					<ul>
						<li>Use specific keywords for better results</li>
						<li>Try both English and Arabic terms</li>
						<li>Use quotation marks for exact phrases</li>
						<li>Filter by category to narrow down results</li>
					</ul>
				</div>
			""",
			"application_routes": [
				{"route": "/knowledge-base"}
			]
		}
	]
	
	for content_data in sample_content:
		# Check if already exists
		if not frappe.db.exists("Help Content", {"content_key": content_data["content_key"]}):
			# Create new help content
			help_doc = frappe.new_doc("Help Content")
			
			# Set basic fields
			for field in ["title", "title_ar", "content_key", "help_type", "priority", 
						 "target_doctype", "target_page", "target_field", "content", 
						 "content_ar", "tooltip_text", "tooltip_text_ar"]:
				if field in content_data:
					setattr(help_doc, field, content_data[field])
			
			# Add routes
			if "application_routes" in content_data:
				for route_data in content_data["application_routes"]:
					route_row = help_doc.append("application_routes", {})
					route_row.route = route_data["route"]
			
			# Add roles
			if "user_roles" in content_data:
				for role_data in content_data["user_roles"]:
					role_row = help_doc.append("user_roles", {})
					role_row.role = role_data["role"]
			
			# Set default values
			help_doc.is_active = 1
			help_doc.view_count = 0
			
			try:
				help_doc.insert(ignore_permissions=True)
				print(f"Created help content: {content_data['title']}")
			except Exception as e:
				print(f"Error creating help content {content_data['title']}: {str(e)}")


if __name__ == "__main__":
	create_sample_help_content()
