/**
 * نظام الهوية البصرية المتقدم - Universal Workshop ERP
 * يدعم التخصيص الكامل لكل ورشة
 */

class WorkshopBrandingSystem {
	constructor(workshopId) {
		this.workshopId = workshopId;
		this.brandingConfig = null;
		this.defaultTheme = {
			colors: {
				primary: '#1976d2',
				secondary: '#dc004e',
				accent: '#ff5722',
				background: '#fafafa',
				surface: '#ffffff',
				text: '#212121'
			},
			typography: {
				fontFamily: 'Cairo, Roboto, sans-serif',
				fontSize: {
					small: '12px',
					medium: '14px',
					large: '16px',
					xlarge: '18px'
				}
			},
			layout: {
				direction: 'rtl', // للعربية
				borderRadius: '4px',
				spacing: {
					small: '8px',
					medium: '16px',
					large: '24px',
					xlarge: '32px'
				}
			}
		};
		this.init();
	}

	async init() {
		await this.loadBrandingConfig();
		this.applyBranding();
		this.setupDynamicUpdates();
	}

	async loadBrandingConfig() {
		try {
			const response = await frappe.call({
				method: 'universal_workshop.branding.get_workshop_branding',
				args: { workshop_id: this.workshopId }
			});

			this.brandingConfig = response.message || {};
			console.log('تم تحميل الهوية البصرية:', this.brandingConfig);
		} catch (error) {
			console.error('خطأ في تحميل الهوية البصرية:', error);
			this.brandingConfig = {};
		}
	}

	applyBranding() {
		// تطبيق الألوان المخصصة
		this.applyColors();

		// تطبيق الشعار
		this.applyLogo();

		// تطبيق الخطوط
		this.applyFonts();

		// تطبيق التخطيط المخصص
		this.applyLayout();

		// تطبيق CSS مخصص
		this.applyCustomCSS();
	}

	applyColors() {
		const colors = { ...this.defaultTheme.colors, ...this.brandingConfig.colors };

		// إنشاء CSS Variables للألوان
		const root = document.documentElement;

		Object.entries(colors).forEach(([key, value]) => {
			root.style.setProperty(`--color-${key}`, value);
		});

		// تطبيق الألوان على العناصر الأساسية
		const dynamicCSS = `
            :root {
                --primary-color: ${colors.primary};
                --secondary-color: ${colors.secondary};
                --accent-color: ${colors.accent};
                --background-color: ${colors.background};
                --surface-color: ${colors.surface};
                --text-color: ${colors.text};
            }
            
            .navbar-brand, .btn-primary {
                background-color: var(--primary-color) !important;
                border-color: var(--primary-color) !important;
            }
            
            .btn-secondary {
                background-color: var(--secondary-color) !important;
                border-color: var(--secondary-color) !important;
            }
            
            .page-head {
                background-color: var(--surface-color) !important;
                border-bottom: 2px solid var(--primary-color) !important;
            }
            
            .sidebar-menu .menu-item.active {
                background-color: var(--primary-color) !important;
                color: white !important;
            }
        `;

		this.injectCSS('workshop-colors', dynamicCSS);
	}

	applyLogo() {
		const logos = this.brandingConfig.logos || {};

		// تطبيق الشعار الرئيسي
		if (logos.primary) {
			const logoElements = document.querySelectorAll('.navbar-brand img, .app-logo');
			logoElements.forEach(img => {
				img.src = logos.primary;
				img.alt = this.brandingConfig.workshop_name || 'Workshop Logo';
			});
		}

		// تطبيق favicon
		if (logos.favicon) {
			let favicon = document.querySelector('link[rel="icon"]');
			if (!favicon) {
				favicon = document.createElement('link');
				favicon.rel = 'icon';
				document.head.appendChild(favicon);
			}
			favicon.href = logos.favicon;
		}

		// تطبيق شعار التقارير
		if (logos.reports) {
			const reportLogos = document.querySelectorAll('.report-logo');
			reportLogos.forEach(img => {
				img.src = logos.reports;
			});
		}
	}

	applyFonts() {
		const typography = { ...this.defaultTheme.typography, ...this.brandingConfig.typography };

		// تحميل الخطوط المخصصة
		if (typography.customFontUrl) {
			const fontLink = document.createElement('link');
			fontLink.rel = 'stylesheet';
			fontLink.href = typography.customFontUrl;
			document.head.appendChild(fontLink);
		}

		// تطبيق الخطوط
		const fontCSS = `
            body, .frappe-app {
                font-family: ${typography.fontFamily} !important;
            }
            
            .small-text { font-size: ${typography.fontSize.small} !important; }
            .medium-text { font-size: ${typography.fontSize.medium} !important; }
            .large-text { font-size: ${typography.fontSize.large} !important; }
            .xlarge-text { font-size: ${typography.fontSize.xlarge} !important; }
        `;

		this.injectCSS('workshop-typography', fontCSS);
	}

	applyLayout() {
		const layout = { ...this.defaultTheme.layout, ...this.brandingConfig.layout };

		// تطبيق اتجاه التخطيط (RTL/LTR)
		document.documentElement.dir = layout.direction;
		document.documentElement.lang = layout.direction === 'rtl' ? 'ar' : 'en';

		// تطبيق التباعد والحدود
		const layoutCSS = `
            .frappe-app {
                direction: ${layout.direction};
            }
            
            .btn, .form-control, .card {
                border-radius: ${layout.borderRadius} !important;
            }
            
            .small-spacing { margin: ${layout.spacing.small} !important; }
            .medium-spacing { margin: ${layout.spacing.medium} !important; }
            .large-spacing { margin: ${layout.spacing.large} !important; }
            .xlarge-spacing { margin: ${layout.spacing.xlarge} !important; }
        `;

		this.injectCSS('workshop-layout', layoutCSS);
	}

	applyCustomCSS() {
		if (this.brandingConfig.customCSS) {
			this.injectCSS('workshop-custom', this.brandingConfig.customCSS);
		}
	}

	injectCSS(id, css) {
		// إزالة CSS القديم إذا وُجد
		const existingStyle = document.getElementById(id);
		if (existingStyle) {
			existingStyle.remove();
		}

		// إضافة CSS الجديد
		const style = document.createElement('style');
		style.id = id;
		style.textContent = css;
		document.head.appendChild(style);
	}

	// تخصيص قوالب التقارير والفواتير
	customizeReportTemplates() {
		const workshopInfo = this.brandingConfig.workshop_info || {};

		// قالب الفاتورة المخصص
		const invoiceTemplate = `
            <div class="invoice-header" style="
                background: linear-gradient(135deg, ${this.brandingConfig.colors.primary}, ${this.brandingConfig.colors.secondary});
                color: white;
                padding: 20px;
                border-radius: 10px 10px 0 0;
            ">
                <div class="row">
                    <div class="col-md-6">
                        <img src="${this.brandingConfig.logos.primary}" alt="Logo" style="max-height: 80px;">
                    </div>
                    <div class="col-md-6 text-right">
                        <h2>${workshopInfo.name_ar}</h2>
                        <h4>${workshopInfo.name_en}</h4>
                        <p>${workshopInfo.address}</p>
                        <p>Tel: ${workshopInfo.phone} | Email: ${workshopInfo.email}</p>
                    </div>
                </div>
            </div>
        `;

		// حفظ القالب للاستخدام
		frappe.templates.custom_invoice_header = invoiceTemplate;
	}

	// تحديث الهوية البصرية ديناميكياً
	setupDynamicUpdates() {
		// الاستماع لتحديثات الهوية البصرية
		frappe.realtime.on('branding_updated', (data) => {
			if (data.workshop_id === this.workshopId) {
				console.log('تحديث الهوية البصرية...');
				this.brandingConfig = { ...this.brandingConfig, ...data.updates };
				this.applyBranding();
			}
		});
	}

	// حفظ تخصيص الهوية البصرية
	async saveBrandingConfig(updates) {
		try {
			const response = await frappe.call({
				method: 'universal_workshop.branding.save_workshop_branding',
				args: {
					workshop_id: this.workshopId,
					branding_config: updates
				}
			});

			if (response.message.success) {
				// تحديث التكوين المحلي
				this.brandingConfig = { ...this.brandingConfig, ...updates };
				this.applyBranding();

				// إشعار المستخدمين الآخرين
				frappe.realtime.publish('branding_updated', {
					workshop_id: this.workshopId,
					updates: updates
				});

				frappe.show_alert({
					message: 'تم حفظ الهوية البصرية بنجاح',
					indicator: 'green'
				});
			}
		} catch (error) {
			console.error('خطأ في حفظ الهوية البصرية:', error);
			frappe.show_alert({
				message: 'فشل في حفظ الهوية البصرية',
				indicator: 'red'
			});
		}
	}

	// واجهة تخصيص الهوية البصرية
	openBrandingCustomizer() {
		const dialog = new frappe.ui.Dialog({
			title: 'تخصيص الهوية البصرية',
			fields: [
				{
					fieldtype: 'Section Break',
					label: 'الألوان'
				},
				{
					fieldtype: 'Color',
					fieldname: 'primary_color',
					label: 'اللون الأساسي',
					default: this.brandingConfig.colors?.primary || '#1976d2'
				},
				{
					fieldtype: 'Color',
					fieldname: 'secondary_color',
					label: 'اللون الثانوي',
					default: this.brandingConfig.colors?.secondary || '#dc004e'
				},
				{
					fieldtype: 'Section Break',
					label: 'الشعارات'
				},
				{
					fieldtype: 'Attach Image',
					fieldname: 'primary_logo',
					label: 'الشعار الرئيسي',
					default: this.brandingConfig.logos?.primary
				},
				{
					fieldtype: 'Attach Image',
					fieldname: 'favicon',
					label: 'أيقونة الموقع',
					default: this.brandingConfig.logos?.favicon
				},
				{
					fieldtype: 'Section Break',
					label: 'معلومات الورشة'
				},
				{
					fieldtype: 'Data',
					fieldname: 'workshop_name_ar',
					label: 'اسم الورشة (عربي)',
					default: this.brandingConfig.workshop_info?.name_ar
				},
				{
					fieldtype: 'Data',
					fieldname: 'workshop_name_en',
					label: 'اسم الورشة (إنجليزي)',
					default: this.brandingConfig.workshop_info?.name_en
				},
				{
					fieldtype: 'Small Text',
					fieldname: 'address',
					label: 'العنوان',
					default: this.brandingConfig.workshop_info?.address
				},
				{
					fieldtype: 'Section Break',
					label: 'CSS مخصص'
				},
				{
					fieldtype: 'Code',
					fieldname: 'custom_css',
					label: 'CSS إضافي',
					options: 'CSS',
					default: this.brandingConfig.customCSS || ''
				}
			],
			primary_action_label: 'حفظ التخصيص',
			primary_action: (values) => {
				const updates = {
					colors: {
						primary: values.primary_color,
						secondary: values.secondary_color
					},
					logos: {
						primary: values.primary_logo,
						favicon: values.favicon
					},
					workshop_info: {
						name_ar: values.workshop_name_ar,
						name_en: values.workshop_name_en,
						address: values.address
					},
					customCSS: values.custom_css
				};

				this.saveBrandingConfig(updates);
				dialog.hide();
			}
		});

		dialog.show();
	}
}

// تهيئة نظام الهوية البصرية عند تحميل الصفحة
frappe.ready(() => {
	// الحصول على معرف الورشة من الجلسة الحالية
	const workshopId = frappe.boot.workshop_id || 'default';

	// تهيئة نظام الهوية البصرية
	window.brandingSystem = new WorkshopBrandingSystem(workshopId);

	// إضافة زر التخصيص للمشرفين
	if (frappe.user.has_role('System Manager')) {
		$('.navbar-right').prepend(`
            <li>
                <a href="#" onclick="window.brandingSystem.openBrandingCustomizer()" title="تخصيص الهوية البصرية">
                    <i class="fa fa-paint-brush"></i>
                </a>
            </li>
        `);
	}
});

// تصدير الكلاس للاستخدام في ملفات أخرى
if (typeof module !== 'undefined' && module.exports) {
	module.exports = WorkshopBrandingSystem;
}
