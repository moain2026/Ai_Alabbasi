# 🚀 PLAN.md — خطة ترقية Ai_Alabbasi v2.0

> **الخطة الرئيسية.** هذا "العقل الخارجي" للمشروع — يُحدَّث بعد كل مهمة.
> عند بدء التنفيذ، تُنسخ نسخة من هذا الملف إلى جذر المستودع كما تطلب المهمة.

---

## 📊 الحالة العامة

| الحقل | القيمة |
|------|--------|
| 📅 تاريخ البدء | 2026-06-01 |
| 🔄 آخر تحديث | 2026-06-01 |
| 🟡 الحالة | **التخطيط مكتمل — بانتظار إذن بدء التنفيذ** |
| 📈 النسبة المنجزة | 0% (تنفيذ) / 100% (تخطيط) |
| 🌿 Branch (للتنفيذ) | `upgrade/v2-manus-patterns` (لم يُنشأ بعد) |
| 🌿 Branch (الحالي) | `genspark_ai_developer` (مجلد التخطيط) |

---

## 🎯 الأهداف الكبرى (7 أهداف)

1. ☐ **تطبيق أنماط Manus** (Planner + Event Stream + todo + CodeAct + Interrupt + State Machine)
2. ☐ **ترقية RAG لـ Hybrid Search** (sentence-transformers + FTS5 + RRF، 85 → 500+ مقطع)
3. ☐ **دمج 717 مهارة** (تنظيف 12 مكرّر + إعادة هيكلة + فهرسة ذكية)
4. ☐ **تشغيل سحابي** (Daytona/E2B + Hibernation + Zero-Trust)
5. ☐ **ربط Web UI بالوكيل** (WebSocket + بث events + مقاطعة)
6. ☐ **5 مهارات شخصية عربية**
7. ☐ **جودة الكود ومعايير عالمية** (30+ اختبار + CI/CD + type hints + docstrings)

---

## 📋 المهام الفرعية (pseudocode مرقّم)

### 🟢 المرحلة 1: Manus Patterns (الأهم — 80% من القيمة)
```
1.1 ☐ agent/event_stream.py        # مجرى الأحداث (6 أنواع: Message/Action/Observation/Plan/Knowledge/Other)
1.2 ☐ agent/planner.py             # وحدة المخطّط (pseudocode مرقّم + reflection)
1.3 ☐ agent/todo_manager.py        # مدير todo.md (Recitation + str_replace)
1.4 ☐ agent/state_machine.py       # آلة الحالات (RUNNING/INTERRUPTED/RESUMING/DONE)
1.5 ☐ agent/interrupt_handler.py   # المقاطعة + إعادة التخطيط
1.6 ☐ agent/code_act_executor.py   # CodeAct (تنفيذ Python داخل sandbox)
1.7 ☐ tools/tools.py               # إضافة file_str_replace (للـ Recitation)
1.8 ☐ agent/agent.py               # دمج الوحدات + sort_keys=True (KV-cache)
1.9 ☐ tests/test_planner.py + test_event_stream.py + test_todo_manager.py + …
1.10 ☐ commit + push (atomic لكل وحدة)
```

### 🟢 المرحلة 2: Hybrid Search
```
2.1 ☐ requirements.txt             # إضافة sentence-transformers (tier optional)
2.2 ☐ knowledge/embedder.py        # محرّك embeddings محلي (all-MiniLM-L6-v2)
2.3 ☐ knowledge/hybrid_search.py   # دمج FTS5 + vectors عبر RRF
2.4 ☐ knowledge/knowledge.py       # تعديل context_for() لاستخدام Hybrid
2.5 ☐ knowledge/ingest.py          # توسيع SOURCES (50+ تقنية)
2.6 ☐ تشغيل ingest كامل            # 85 → 500+ مقطع
2.7 ☐ tests/test_hybrid_search.py + test_embedder.py
2.8 ☐ commit + push
```

### 🟢 المرحلة 3: دمج المهارات (717)
```
3.1 ☐ knowledge/external_skills/   # فك ZIP (staging)
3.2 ☐ scripts/clean_skills.py      # حذف 12 مكرّر + مجلد "مهارات مانوس"
3.3 ☐ إعادة الهيكلة                # 4 مجلدات: essential/codex/specialized/media
3.4 ☐ knowledge/skill_indexer.py   # فهرسة الطبقة 1 (Progressive Disclosure)
3.5 ☐ knowledge/skill_selector.py  # اختيار ذكي حسب السياق
3.6 ☐ تكامل مع context_for()       # في knowledge.py
3.7 ☐ tests/test_skill_indexer.py + test_skill_selector.py
3.8 ☐ commit + push
```

### 🟢 المرحلة 4: Daytona Cloud Sandbox
```
4.1 ☐ tools/cloud_sandbox.py       # تكامل Daytona/E2B SDK
4.2 ☐ tools/tools.py               # backend اختياري (local/daytona/e2b)
4.3 ☐ config                       # sandbox.backend في الإعدادات
4.4 ☐ tests/test_cloud_sandbox.py  # (mock SDK)
4.5 ☐ commit + push
```

### 🟢 المرحلة 5: Web UI Live
```
5.1 ☐ web/server.py                # WebSocket endpoint
5.2 ☐ ربط agent events             # عبر on_event callback (موجود!)
5.3 ☐ web/index.html               # استقبال events live
5.4 ☐ web/index.html               # زر مقاطعة (interrupt)
5.5 ☐ tests/test_websocket.py
5.6 ☐ commit + push
```

### 🟢 المرحلة 6: مهارات Ai_Alabbasi الشخصية (5)
```
6.1 ☐ knowledge/skills_seed/arabic-content-writer/SKILL.md
6.2 ☐ knowledge/skills_seed/electricity-bill-analyzer/SKILL.md   # مرتبط بـ electricity-billing-pwa
6.3 ☐ knowledge/skills_seed/yemeni-context-aware/SKILL.md
6.4 ☐ knowledge/skills_seed/nextjs-rtl-pro/SKILL.md              # مرتبط بـ osoul-aldiafa
6.5 ☐ knowledge/skills_seed/moain-personal-style/SKILL.md
6.6 ☐ تكامل مع نظام skills + الفهرسة
6.7 ☐ commit + push
```

### 🟢 المرحلة 7: جودة الكود
```
7.1 ☐ tests/                       # 30+ اختبار شامل، coverage ≥ 70%
7.2 ☐ .github/workflows/ci.yml     # CI/CD (pytest + ruff)
7.3 ☐ .pre-commit-config.yaml      # ruff + black
7.4 ☐ type hints                   # لكل دالة
7.5 ☐ docstrings                   # عربية + إنجليزية
7.6 ☐ README.md                    # تحديث بالميزات الجديدة
7.7 ☐ CHANGELOG.md                 # توثيق v1 → v2
7.8 ☐ commit + push نهائي + فتح PR
```

---

## 🔢 ملخص العدّ

| المرحلة | عدد المهام الفرعية |
|---------|---------------------|
| 1. Manus Patterns | 10 |
| 2. Hybrid Search | 8 |
| 3. دمج المهارات | 8 |
| 4. سحابي | 5 |
| 5. Web UI | 6 |
| 6. مهارات شخصية | 7 |
| 7. جودة الكود | 8 |
| **المجموع** | **52 مهمة فرعية** |

---

## 📈 سجل التقدّم (السجل اليومي)

### 2026-06-01 — المرحلة 0 + التخطيط
```
🔄 العمل الحالي: إنهاء المرحلة 0 (الفهم) + بناء مجلد "خطة العمل"
✅ أكملت:
   • قراءة التقرير 1 (تحليل Ai_Alabbasi) كاملاً — 18 فجوة + خطة 6 مراحل
   • قراءة التقرير 2 (Manus) كاملاً — 7 أنماط + 6 دروس + 29 أداة
   • تحميل وتحليل ZIP المهارات: 717 ملف / 705 فريد / 12 مكرّر
   • بحث تكميلي: Hybrid Search + Progressive Disclosure + CodeAct + Daytona + KV-cache
   • بناء مجلد "خطة العمل" بـ 9 ملفات تحليل وتخطيط
📝 ملاحظات: الأرقام الفعلية للمهارات (717) تختلف عن المذكور (675) — اعتمدنا الفعلي
🐛 مشاكل: ترميز UTF-8 في تقرير Manus (حُلّ بـ errors='ignore')
💡 تحسينات اكتشفتها: sort_keys=True تحسين KV-cache رخيص وفوري
🔬 ما تعلمته: RRF يحقّق 92.3% Recall@5 بدون معايرة أوزان
```

### 2026-06-01 (2) — بدء التنفيذ: تطوير الواجهة (المرحلة 5 — مُقدَّمة)
```
✅ أنشأت فرع upgrade/v2-manus-patterns
✅ حلّلت الواجهة الحالية + واجهتَي Manus و Genspark
✅ طوّرت web/server.py — 5 endpoints جديدة:
   • POST /api/upload          — رفع ملفات/صور (مع فحص امتداد + حجم 20MB)
   • GET  /api/files           — سرد المرفقات
   • DELETE /api/files/{name}  — حذف مرفق
   • GET  /api/skills          — قائمة المهارات (self-learned + external + builtin)
   • POST /api/stop/{conv_id}  — إيقاف المهمة الجارية (cancellation)
✅ طوّرت web/index.html — شريط أدوات composer كامل:
   • 📎 إرفاق ملفات  • 🖼️ إرفاق صور  • 🧩 اختيار مهارة (قائمة منبثقة)
   • 🎤 إملاء صوتي (Web Speech API)  • ■ زر إيقاف يتحوّل أثناء التنفيذ
   • معاينة المرفقات (thumbnails) + لصق صورة + سحب وإفلات
✅ اختبرت كل الـ endpoints بنجاح (رفع/سرد/حذف/إيقاف/مهارات + رفض .exe)
✅ الواجهة تُحمّل بلا أخطاء console
📝 ملاحظة: المرفقات تُخزَّن في projects/_uploads/ (ضمن نطاق _safe_path)
🔬 أمان: تنظيف أسماء الملفات (path-traversal) + قائمة امتدادات بيضاء
```

### [التالي] — استكمال المرحلة 1 (أنماط Manus الأساسية)
```
🔜 الخطوات القادمة:
   1. agent/event_stream.py (1.1)
   2. agent/planner.py (1.2)
   3. agent/todo_manager.py (1.3)
   4. ربط الواجهة الجديدة ببث الأحداث الحيّ (WebSocket — المرحلة 5)
```

---

## 🔬 البحوث التكميلية (مرجع)

التفاصيل الكاملة في `04_البحوث_التكميلية.md`. ملخص:
- ✅ Hybrid Search: sentence-transformers محلي + RRF (k=60) → 92.3% Recall@5.
- ✅ Progressive Disclosure: 3 طبقات (80/2000/on-demand token).
- ✅ CodeAct: أداة إضافية داخل sandbox (لا تستبدل الأدوات الـ7).
- ✅ Daytona: backend اختياري مع Hibernation.
- ✅ KV-cache: sort_keys=True فوري.

---

## ⚙️ القرارات المعمارية (ADRs)

التفاصيل الكاملة في `06_قرارات_معمارية.md`. القرارات:
- **ADR-001:** sentence-transformers (محلي) بدل Milvus/Pinecone (سحابي ثقيل).
- **ADR-002:** CodeAct كأداة إضافية لا بديلة.
- **ADR-003:** sort_keys=True في json.dumps (KV-cache).
- **ADR-004:** backend sandbox قابل للتبديل (local افتراضي).
- **ADR-005:** فهرسة الطبقة 1 فقط للمهارات (Progressive Disclosure).

---

## ⚠️ المخاطر ومعايير القبول

التفاصيل الكاملة في `07_المخاطر_والقبول.md`. أبرز المخاطر:
- كسر التوافق العكسي → اختبارات شاملة + إضافة قبل حذف.
- ثقل sentence-transformers → tier optional + lazy import.
- خرق `_safe_path` في CodeAct → تنفيذ محصور صارم.

---

## ✅ نصائح ذهبية مطبّقة في الخطة

- **Quick Win:** المرحلة 1 أولاً (80% قيمة بـ 20% جهد).
- **Atomic Commits:** كل وحدة = commit مستقل.
- **بحث قبل كل مهمة:** يُحدَّث `04_البحوث_التكميلية.md`.
- **لا حذف قبل اختبار:** القاعدة الذهبية 7.

---

> **آخر تحديث:** 2026-06-01 — ⚡ Genspark High-Performance Agent
> **القاعدة:** بعد كل مهمة منجزة → ☐ تصير ☑ + سطر في سجل التقدّم + تحديث النسبة.
