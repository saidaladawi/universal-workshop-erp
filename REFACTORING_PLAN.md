# Universal Workshop - خطة إعادة التنظيم

## المشاكل الحالية:
1. ❌ تكرار في ملفات Setup: `install.py`, `setup/workshop_setup.py`, `boot.py`
2. ❌ تناثر ملفات الـ Onboarding في أماكن متعددة
3. ❌ عدم وضوح المسؤوليات بين الملفات
4. ❌ تعقيد في إدارة العلامة التجارية والثيمات

## الهيكل الجديد المقترح:

```
universal_workshop/
├── core/                      # 🎯 النواة الأساسية
│   ├── boot.py               # Boot logic فقط
│   ├── permissions.py        # إدارة الصلاحيات
│   └── hooks_handler.py      # معالج الـ hooks

├── setup/                     # 🎯 نظام الإعداد الموحد
│   ├── installation.py       # منطق التثبيت الأساسي (يحل محل install.py)
│   ├── onboarding/           # نظام الـ onboarding
│   │   ├── wizard.py         # منطق الـ wizard (من workshop_setup.py)
│   │   ├── progress.py       # تتبع التقدم
│   │   └── validation.py     # التحقق من البيانات
│   ├── license/              # إدارة التراخيص
│   │   ├── reader.py         # قراءة ملف الترخيص
│   │   └── validator.py      # التحقق من صحة الترخيص
│   └── branding/             # نظام العلامة التجارية
│       ├── theme_manager.py  # إدارة الثيمات
│       └── logo_manager.py   # إدارة الشعارات

├── workshop_management/       # 🎯 إدارة الورشة (كما هو)
└── public/                   # 🎯 الملفات العامة منظمة
    ├── js/
    │   ├── core/             # JS للنواة
    │   ├── setup/            # JS للإعداد والـ onboarding
    │   └── branding/         # JS للعلامة التجارية
    └── css/
        ├── core/
        ├── themes/
        └── setup/
```

## خطوات التنفيذ:

### ✅ المرحلة 1: إنشاء الهيكل الجديد
- [x] إنشاء مجلدات core/, setup/, setup/onboarding/, setup/license/, setup/branding/

### 🔄 المرحلة 2: نقل وتوحيد الكود
- [ ] نقل boot logic إلى core/boot.py
- [ ] توحيد setup logic في setup/installation.py
- [ ] نقل onboarding logic إلى setup/onboarding/
- [ ] تنظيم branding system في setup/branding/

### 🔄 المرحلة 3: تنظيف الملفات القديمة
- [ ] حذف الملفات المكررة والمتناثرة
- [ ] تحديث imports في الملفات المتبقية
- [ ] تحديث hooks.py

### 🔄 المرحلة 4: اختبار وتحسين
- [ ] اختبار النظام بالكامل
- [ ] إضافة تعليقات وثائق واضحة
- [ ] التأكد من عمل الـ onboarding

## الفوائد المتوقعة:
✅ هيكل واضح ومنظم
✅ سهولة الصيانة والتطوير
✅ عدم تكرار الكود
✅ سهولة فهم النظام للمطورين الجدد
✅ إدارة أفضل للعلامة التجارية والثيمات
