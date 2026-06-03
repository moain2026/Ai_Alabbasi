# 🤖 Ai_Alabbasi — وكيل ذكي قابل للتثبيت في أي مكان

> وكيل برمجي ذكي مستقل، **عقله قابل للتبديل من ملف واحد** (API قوي أو نموذج محلي)،
> **يتمرّس** على تقنيات محدّدة (React Native / Next.js / Angular...) عبر معرفة متراكمة،
> ويبني أنظمة ومواقع بدقة وينفّذ مهامّ كاملة بنفسه.

<p align="center">
  <b>صُنع لعبّاس العباسي</b> · مرخّص MIT
</p>

---

## 🎯 الهدف

بناء "وكيل خاص بك" — مثل مانوس لكن **تملكه بالكامل**:
- 🧠 **عقل واحد مركزي** تبدّله بسطر واحد (Claude / GPT-5 / DeepSeek / نموذج محلي).
- 📚 **يتمرّس ويصبح خبيراً** عبر قاعدة معرفة (RAG) + حلقة تعلّم تحفظ كل تجربة ناجحة.
- 🛠️ **ينفّذ فعلياً**: يكتب كوداً، يشغّله، يختبره، ويصلّح أخطاءه بنفسه.
- 🌍 **يعمل في أي مكان**: VPS، سيرفر، أو جهازك.

> 📖 لفهم أعمق للمعمارية والتفاصيل، راجع مجلد **[`docs/`](docs/)**.

---

## 🚀 جديد في الإصدار 2.0 — أذكى من Manus AI

ترقية كبرى عبر 7 مراحل (راجع [`CHANGELOG.md`](CHANGELOG.md)):

| الميزة | الوصف | الملف |
|-------|-------|------|
| 🗂️ **تيار الأحداث** | EventStream بستة أنواع موحّدة | `agent/event_stream.py` |
| 📝 **مخطّط + قائمة مهام** | خطة مرقّمة + "تلاوة" الهدف (Recitation) | `agent/planner.py` · `agent/todo_manager.py` |
| ⚙️ **آلة حالات + مقاطعة** | تحكّم آمن في دورة حياة المهمة | `agent/state_machine.py` · `agent/interrupt_handler.py` |
| 🐍 **CodeAct** | تنفيذ Python معزول داخل `projects/` | `agent/code_act_executor.py` |
| 🔎 **بحث هجين** | FTS5 + متجهات دلالية مدموجة بـ RRF | `knowledge/hybrid_search.py` |
| 🧩 **اختيار ذكي للمهارات** | كشف تدريجي 3 طبقات + مطابقة عربية ضبابية | `knowledge/skill_indexer.py` |
| ☁️ **صندوق رمل سحابي** | local / Daytona / E2B بسقوط آمن | `tools/cloud_sandbox.py` |
| 🎨 **5 مهارات عربية** | كتابة محتوى، تحليل فواتير، سياق يمني… | `knowledge/skills_seed/` |

> ✅ **74 اختبار ناجح** · جميع التبعيات الثقيلة **اختيارية** مع بديل آمن.

---

## ⚡ التثبيت السريع (أي مكان)

```bash
# 1. استنساخ المستودع
git clone https://github.com/Moain2026/Ai_Alabbasi.git
cd Ai_Alabbasi

# 2. تثبيت التبعيات (خفيفة جداً — PyYAML فقط)
pip install -r requirements.txt

# 3. إعداد المفاتيح
cp config/.env.example config/.env
chmod 600 config/.env
# عدّل config/.env وضع مفتاحك (Genspark أو OpenRouter)

# 4. تغذية قاعدة المعرفة (اختياري — للتمرّس)
python3 knowledge/ingest.py

# 5. التشغيل!
set -a; source config/.env; set +a
python3 run.py
```

✅ **متطلبات النظام:** Python 3.10+ ، و(اختياري) Node.js/npm/git لبناء مشاريع الويب.

---

## 🧠 تبديل العقل (نموذج واحد، مكان واحد)

عدّل سطراً واحداً في [`brain/brain_config.yaml`](brain/brain_config.yaml):

```yaml
active_brain: genspark_claude_opus   # 🥇 الأقوى للبناء الدقيق
# active_brain: genspark_gpt5_codex  # GPT-5 مخصص للبرمجة
# active_brain: genspark_deepseek    # DeepSeek V4 قوي ورخيص
# active_brain: openrouter_free_qwen # مجاني عبر OpenRouter
# active_brain: local_ollama         # محلي مجاني (بعد تثبيت Ollama)
```

**8 عقول جاهزة** + دعم أي نموذج متوافق مع OpenAI (محلي عبر Ollama/LM Studio).

---

## 🗣️ الاستخدام

### واجهة تفاعلية (موصى بها)
```bash
python3 run.py
```
أوامر داخل الجلسة:
| الأمر | الوظيفة |
|------|---------|
| `/topic nextjs` | حدّد تقنية التركيز (لتفعيل التمرّس RAG) |
| `/brain <key>` | بدّل العقل فوراً |
| `/kb` | إحصائيات قاعدة المعرفة |
| `/skills <بحث>` | ابحث في الخبرات المتعلّمة |
| `/help` · `/exit` | مساعدة · خروج |

### أمر واحد مباشر
```bash
python3 agent/agent.py --topic react-native "ابنِ لي شاشة تسجيل دخول"
```

---

## 🏗️ البنية

```
Ai_Alabbasi/
├── run.py              ▶️ الواجهة التفاعلية
├── brain/              🧠 العقل (إعداد + محرّك موحّد لكل النماذج)
├── agent/              🔁 حلقة الوكيل (ReAct + حقن معرفة + تعلّم)
├── tools/              🛠️ الأدوات (ملفات/terminal/بحث، محصورة بأمان)
├── knowledge/          📚 المعرفة (RAG عبر SQLite FTS5) + skills متراكمة
├── config/             🔑 المفاتيح (.env معزول — غير مرفوع)
├── projects/           📦 ما يبنيه الوكيل
├── logs/               📝 سجلّات التشغيل
├── docs/               📖 التوثيق الكامل ← اقرأه للتفاصيل
└── external/           📥 أنظمة مرجعية (تُحمّل منفصلة)
```

---

## 📖 التوثيق الكامل

للتعمّق، راجع مجلد [`docs/`](docs/):

| الملف | المحتوى |
|------|---------|
| [`00_MASTER_PLAN.md`](docs/00_MASTER_PLAN.md) | الرؤية + المعمارية + خطة المراحل |
| [`01_HOW_IT_WORKS.md`](docs/01_HOW_IT_WORKS.md) | شرح تقني تفصيلي لحلقة الوكيل |
| [`02_STATUS.md`](docs/02_STATUS.md) | الحالة الحالية والخطوات القادمة |
| [`03_KNOWLEDGE_RAG.md`](docs/03_KNOWLEDGE_RAG.md) | نظام التمرّس (RAG + التعلّم) |

---

## 🔒 الأمان
- المفاتيح في `config/.env` (صلاحية `600`، مستثناة من Git).
- الوكيل محصور في مجلد `projects/` — لا يستطيع العبث بباقي النظام.
- لا تَرفع `.env` لأي مستودع عام.

---

## 🧩 كيف يعمل التمرّس؟

```
مهمة → يبحث في قاعدة المعرفة (توثيق + خبرات سابقة)
     → يحقنها في العقل قبل التنفيذ
     → يبني مستنداً لمعرفة حقيقية
     → ينجح → يحفظ خبرة جديدة (skill)
     → المرة القادمة أدقّ وأسرع
```

النموذج لا "يصبح أذكى" — بل **يتراكم خبرةً ومعرفةً** فيصير خبيراً في تقنياتك.

---

<p align="center">
  <sub>Ai_Alabbasi · وكيل ذكي مفتوح · بُني بدقة 🤝</sub>
</p>
