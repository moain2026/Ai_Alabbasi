---
name: nextjs-rtl-pro
description: "بناء تطبيقات Next.js عربية احترافية بدعم RTL كامل و Tailwind (مرتبط بـ osoul-aldiafa)"
tags: nextjs, rtl, عربي, tailwind, react, واجهات, ويب
tier: 1
---

# ⚛️ خبير Next.js العربي (RTL)

مهارة لبناء تطبيقات Next.js عربية بدعم RTL كامل وتصميم احترافي.
مرتبطة بمشروع `osoul-aldiafa`.

## متى تُستخدم
- إنشاء/تطوير تطبيق Next.js موجّه لجمهور عربي.
- ضبط RTL وخطوط عربية وتنسيق Tailwind.

## الأساسيات
1. **اتجاه الصفحة**: في `app/layout.tsx`:
   ```tsx
   <html lang="ar" dir="rtl">
   ```
2. **الخط العربي** (Next/font):
   ```tsx
   import { Cairo } from "next/font/google";
   const cairo = Cairo({ subsets: ["arabic"], display: "swap" });
   // ...
   <body className={cairo.className}>
   ```
3. **Tailwind RTL**: استخدم الخصائص المنطقية بدل اليمين/اليسار:
   - `ms-4` / `me-4` بدل `ml-4` / `mr-4`
   - `ps-4` / `pe-4` بدل `pl-4` / `pr-4`
   - `text-start` / `text-end` بدل `text-left` / `text-right`
4. **الأيقونات الاتجاهية**: اعكسها في RTL (`rtl:rotate-180`).

## بنية مقترحة (App Router)
```
app/
  layout.tsx        # html dir=rtl + الخط
  page.tsx          # الصفحة الرئيسية
  globals.css       # Tailwind + تخصيصات RTL
components/
  ui/               # مكوّنات قابلة لإعادة الاستخدام
```

## خطوات التنفيذ
1. أنشئ المشروع: `npx create-next-app@latest --ts --tailwind`.
2. اضبط `dir="rtl"` و `lang="ar"` في layout.
3. أضف خطاً عربياً (Cairo/Tajawal) عبر next/font.
4. استبدل كل الفئات الاتجاهية بالمنطقية (ms/me/ps/pe).
5. اختبر المحاذاة والأيقونات في RTL.
6. تحقّق من الأداء (lighthouse) وإمكانية الوصول.

## أخطاء شائعة
- نسيان `dir="rtl"` → نصوص عربية بمحاذاة خاطئة.
- استخدام `ml/mr` الثابتة → تنكسر في RTL.
- خطوط لاتينية لا تدعم العربية → حروف مشوّهة.
