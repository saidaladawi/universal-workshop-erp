# Contributing to Universal Workshop ERP
# المساهمة في نظام إدارة الورش الشامل

Thank you for your interest in contributing to Universal Workshop ERP! This document provides guidelines for contributing to our project.

شكراً لاهتمامك بالمساهمة في نظام إدارة الورش الشامل! هذا المستند يوفر إرشادات للمساهمة في مشروعنا.

## 🌐 Language Support | دعم اللغات

This project supports both Arabic and English. Please provide documentation and comments in both languages when possible.

يدعم هذا المشروع اللغتين العربية والإنجليزية. يرجى توفير الوثائق والتعليقات بكلا اللغتين عند الإمكان.

## 🚀 Getting Started | البدء

### Prerequisites | المتطلبات الأساسية

- Python 3.10+
- Node.js 18+
- MariaDB 10.3+
- Git knowledge | معرفة بـ Git
- ERPNext/Frappe framework experience | خبرة في إطار عمل ERPNext/Frappe

### Development Setup | إعداد بيئة التطوير

1. **Fork the repository | انسخ المستودع**
   ```bash
   # Fork on GitHub, then clone
   git clone https://github.com/YOUR-USERNAME/universal-workshop-erp.git
   cd universal-workshop-erp
   ```

2. **Install dependencies | ثبت التبعيات**
   ```bash
   ./scripts/install.sh
   ```

3. **Create a feature branch | أنشئ فرع للميزة**
   ```bash
   git checkout -b feature/your-feature-name
   git checkout -b feature/اسم-الميزة-الخاصة-بك
   ```

## 📝 Contribution Guidelines | إرشادات المساهمة

### Code Style | أسلوب البرمجة

- Follow ERPNext coding standards | اتبع معايير البرمجة لـ ERPNext
- Use meaningful variable names in English | استخدم أسماء متغيرات واضحة بالإنجليزية
- Add Arabic comments for complex business logic | أضف تعليقات بالعربية للمنطق التجاري المعقد
- Ensure RTL compatibility for UI components | تأكد من توافق مكونات الواجهة مع اتجاه RTL

### Documentation | التوثيق

- Update both Arabic and English documentation | حدث الوثائق بالعربية والإنجليزية
- Include screenshots for UI changes | أدرج لقطات شاشة لتغييرات الواجهة
- Document Oman-specific business requirements | وثق المتطلبات التجارية الخاصة بعُمان

### Testing | الاختبار

- Write unit tests for new features | اكتب اختبارات وحدة للميزات الجديدة
- Test Arabic text input/output | اختبر إدخال/إخراج النص العربي
- Verify VAT calculations for Oman (5%) | تحقق من حسابات ضريبة القيمة المضافة لعُمان (5%)

### Commit Messages | رسائل الالتزام

Use conventional commit format:
```
feat: add vehicle inspection module
feat: إضافة وحدة فحص المركبات

fix: resolve Arabic text encoding issue
fix: حل مشكلة ترميز النص العربي
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## 🐛 Reporting Issues | الإبلاغ عن المشاكل

### Bug Reports | تقارير الأخطاء

When reporting bugs, please include:
عند الإبلاغ عن الأخطاء، يرجى تضمين:

- **Environment | البيئة**: OS, Python version, browser
- **Steps to reproduce | خطوات إعادة الإنتاج**: Detailed steps
- **Expected vs actual behavior | السلوك المتوقع مقابل الفعلي**
- **Screenshots | لقطات الشاشة**: If applicable
- **Arabic text issues | مشاكل النص العربي**: If relevant

### Feature Requests | طلبات الميزات

- Describe the business case | وصف الحالة التجارية
- Explain Oman market relevance | اشرح الصلة بالسوق العُماني
- Consider cultural and linguistic aspects | اعتبر الجوانب الثقافية واللغوية

## 🔄 Pull Request Process | عملية طلب السحب

1. **Create feature branch | إنشاء فرع الميزة**
   ```bash
   git checkout -b feature/workshop-management
   ```

2. **Make changes | إجراء التغييرات**
   - Follow coding standards | اتبع معايير البرمجة
   - Add tests | أضف اختبارات
   - Update documentation | حدث الوثائق

3. **Test thoroughly | اختبر بدقة**
   ```bash
   # Run tests
   python -m pytest tests/
   
   # Test Arabic interface
   # اختبر الواجهة العربية
   ```

4. **Submit PR | قدم طلب السحب**
   - Use descriptive title in both languages | استخدم عنوان وصفي بكلا اللغتين
   - Fill out PR template completely | املأ قالب طلب السحب بالكامل
   - Link related issues | اربط المشاكل ذات الصلة

## 🏢 Business Logic Guidelines | إرشادات المنطق التجاري

### Oman-Specific Requirements | المتطلبات الخاصة بعُمان

- **VAT**: 5% rate implementation | تطبيق معدل 5%
- **Currency**: OMR with 3 decimal places | ر.ع. بـ 3 منازل عشرية
- **Working Days**: Sunday to Thursday | الأحد إلى الخميس
- **Language**: Arabic as primary, English as secondary | العربية أساسية، الإنجليزية ثانوية

### Workshop Management Features | ميزات إدارة الورش

- Vehicle registration with VIN support | تسجيل المركبات مع دعم VIN
- Service scheduling and tracking | جدولة وتتبع الخدمات
- Parts inventory management | إدارة مخزون قطع الغيار
- Customer communication in Arabic | التواصل مع العملاء بالعربية

## 🎯 Areas for Contribution | مجالات المساهمة

### High Priority | أولوية عالية
- Arabic localization improvements | تحسينات التعريب
- Mobile interface enhancements | تحسينات واجهة الهاتف المحمول
- Performance optimizations | تحسينات الأداء
- Oman compliance features | ميزات الامتثال العُماني

### Medium Priority | أولوية متوسطة
- Additional report templates | قوالب تقارير إضافية
- Integration with local services | التكامل مع الخدمات المحلية
- Advanced analytics | التحليلات المتقدمة

### Documentation | التوثيق
- User manual translations | ترجمات دليل المستخدم
- Video tutorials in Arabic | دروس فيديو بالعربية
- API documentation | توثيق واجهة برمجة التطبيقات

## 📞 Support | الدعم

- **GitHub Issues**: For bugs and feature requests | للأخطاء وطلبات الميزات
- **Discussions**: For questions and ideas | للأسئلة والأفكار
- **Email**: support@universal-workshop.om

## 📜 Code of Conduct | مدونة السلوك

This project adheres to a Code of Conduct. By participating, you are expected to uphold this code.

يلتزم هذا المشروع بمدونة السلوك. من خلال المشاركة، من المتوقع أن تلتزم بهذه المدونة.

### Our Pledge | تعهدنا

- Respectful and inclusive environment | بيئة محترمة وشاملة
- Professional communication | التواصل المهني
- Cultural sensitivity | الحساسية الثقافية
- Arabic language support | دعم اللغة العربية

---

Thank you for contributing to Universal Workshop ERP!
شكراً لمساهمتك في نظام إدارة الورش الشامل!
