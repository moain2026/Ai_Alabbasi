# 📋 سجل التغييرات — Ai_Alabbasi

جميع التغييرات المهمة في هذا المشروع موثّقة هنا.
الصيغة مبنية على [Keep a Changelog](https://keepachangelog.com/)،
والمشروع يتبع [الإصدار الدلالي (SemVer)](https://semver.org/lang/ar/).

---

## [2.0.0] — 2026-06-03

ترقية كبرى لجعل الوكيل **أذكى من Manus AI** عبر خطة من 7 مراحل.

### ✨ أُضيف (Added)

#### المرحلة 1 — أنماط Manus السبعة
- **EventStream** (`agent/event_stream.py`): تيار أحداث موحّد بستة أنواع
  (MESSAGE / ACTION / OBSERVATION / PLAN / KNOWLEDGE / OTHER) مع تصيير سياق للعقل.
- **Planner** (`agent/planner.py`): توليد خطة مرقّمة قبل التنفيذ + انعكاس (reflection) بعدها.
- **TodoManager** (`agent/todo_manager.py`): قائمة مهام مع "التلاوة" (Recitation) لإبقاء الهدف حاضراً.
- **StateMachine** (`agent/state_machine.py`): آلة حالات بست حالات وانتقالات محروسة.
- **InterruptHandler** (`agent/interrupt_handler.py`): مقاطعة آمنة الخيوط أثناء التنفيذ.
- **CodeActExecutor** (`agent/code_act_executor.py`): تنفيذ Python في عملية معزولة داخل `projects/`.
- أداتان جديدتان: `file_str_replace` (استبدال جراحي دقيق) و `run_python`.

#### المرحلة 2 — البحث الهجين (Hybrid Search)
- **Embedder** (`knowledge/embedder.py`): متجهات دلالية مع تبعية اختيارية
  (`sentence-transformers`) وبديل آمن قائم على التجزئة (hashing) عند غيابها.
- **HybridSearch** (`knowledge/hybrid_search.py`): دمج نتائج FTS5 + الدلالة عبر
  **Reciprocal Rank Fusion (RRF, k=60)**.
- تكامل `search_docs_hybrid` في قاعدة المعرفة مع مسح دلالي واسع لإيجاد المرادفات.

#### المرحلة 3 — فهرسة واختيار ذكي للمهارات (Progressive Disclosure)
- **SkillIndex** (`knowledge/skill_indexer.py`): تحميل تدريجي على 3 طبقات
  (اكتشاف ~80 رمز → تفعيل كامل → تنفيذ)، بدون الحاجة لـ PyYAML.
- **SkillSelector** (`knowledge/skill_selector.py`): اختيار ذكي بمطابقة ضبابية
  تراعي صرف العربية (مطابقة أول 4 أحرف) + درجة دلالية.

#### المرحلة 4 — صندوق رمل سحابي قابل للتبديل
- **CloudSandbox** (`tools/cloud_sandbox.py`): واجهة موحّدة بثلاث خلفيات
  (`local` افتراضي / `daytona` / `e2b`) مع سقوط آمن إلى المحلي عند غياب الـ SDK.

#### المرحلة 5 — الواجهة الحية
- عرض حدث **الخطة (plan)** في الواجهة الحية كقائمة مرقّمة.

#### المرحلة 6 — 5 مهارات عربية شخصية
- `arabic-content-writer`, `electricity-bill-analyzer`, `yemeni-context-aware`,
  `nextjs-rtl-pro`, `moain-personal-style`.

#### المرحلة 7 — جودة وتوثيق
- إضافة `CHANGELOG.md` و قالب سير عمل CI (`ci-templates/ci.yml.template`).
  > لتفعيله: انسخه إلى `.github/workflows/ci.yml` (يتطلب صلاحية `workflows`).
- تحديث `README.md` بميزات الإصدار 2.0.

### 🔧 أُصلح (Fixed)
- **أخطاء العقل الصامتة:** الآن تُبثّ كحدث `error` واضح (مثل غياب مفتاح API).
- **EventStream falsy:** أُضيف `__bool__` ليعيد True ومنع كسر التقييم القصير.
- **مطابقة المهارات بصفر:** أُصلحت بمطابقة بادئة عربية ضبابية + تضمين اسم المهارة.

### 🔒 الأمان
- المفاتيح في `config/.env` (صلاحية `600`، مستثناة من Git).
- جميع التبعيات الثقيلة **اختيارية** مع بديل آمن.

---

## [1.0.0] — الإصدار الأساسي
- عقل قابل للتبديل من ملف YAML واحد.
- حلقة وكيل ReAct + أدوات محصورة بـ `_safe_path`.
- قاعدة معرفة RAG عبر SQLite FTS5 + تعلّم تراكمي.
- واجهة تفاعلية + واجهة ويب.
