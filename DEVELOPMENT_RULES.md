# 📝 قواعد التطوير الذهبية - يجب اتباعها دائماً

## 🔍 قاعدة 1: تحقق قبل الإنشاء
```bash
# قبل إنشاء أي ملف، تحقق من وجوده
find apps/universal_workshop -name "*filename*" -type f
grep -r "function_name" apps/universal_workshop/
```

## 🔍 قاعدة 2: اقرأ الملفات الموجودة أولاً
```bash
# اقرأ محتوى الملف قبل نقله أو تعديله
cat apps/universal_workshop/path/to/file.py
```

## 🔍 قاعدة 3: تحقق من التبعيات
```bash
# ابحث عن أي مراجع للملف/الدالة
grep -r "import.*filename" apps/universal_workshop/
grep -r "from.*filename" apps/universal_workshop/
```

## 🔍 قاعدة 4: تحقق من hooks.py
```bash
# تحقق من أي مراجع في hooks.py
grep -n "filename\|function_name" apps/universal_workshop/universal_workshop/hooks.py
```

## 🔍 قاعدة 5: لا تكرر الوظائف الموجودة
- تحقق من user_management/ قبل إنشاء permissions
- تحقق من boot.py قبل إنشاء session managers  
- تحقق من hooks.py قبل إنشاء handlers

## ❌ أخطاء تم ارتكابها:
1. إنشاء core/permissions.py رغم وجود user_management.permission_hooks
2. إنشاء core/session_manager.py رغم وجود user_management/session_manager.py
3. عدم التحقق من النظام الموجود قبل الإضافة

## ✅ الطريقة الصحيحة:
1. تحقق من الوجود
2. اقرأ المحتوى  
3. تحقق من التبعيات
4. نفذ التغيير
5. اختبر النتيجة
