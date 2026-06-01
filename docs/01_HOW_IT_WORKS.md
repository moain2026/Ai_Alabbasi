# ⚙️ كيف يعمل الوكيل — شرح تقني

## 🔁 حلقة الوكيل (ReAct Loop)

الوكيل يعمل بنمط **ReAct** (Reason + Act): يفكّر ثم ينفّذ، بشكل تكراري.

```
المهمة
  ↓
┌─────────────────────────────────┐
│  1. العقل يفكّر (Brain.think)     │ ← يرسل السياق للنموذج
│  2. يُخرج JSON: {tool, args}      │
│  3. الوكيل ينفّذ الأداة           │ ← call_tool
│  4. يأخذ النتيجة ويعيدها للعقل    │
│  5. يكرّر حتى {done: true}        │
└─────────────────────────────────┘
  ↓
النتيجة النهائية
```

### مثال حقيقي (من أول تشغيل):
```
الخطوة 1: 💭 أبدأ بإنشاء calc.py → write_file ✅
الخطوة 2: 💭 أنشئ الاختبارات → write_file ✅
الخطوة 3: 💭 أشغّل → run_shell "python ..." → ❌ python not found
الخطوة 4: 💭 أجرّب python3 → run_shell ✅ نجح
الخطوة 5: 💭 نجحت كل الاختبارات → done ✅
```
👈 لاحظ: الوكيل **واجه خطأ وأصلحه بنفسه** — هذا جوهر الذكاء.

---

## 🧠 طبقة العقل (brain/)

### `brain_config.yaml`
ملف الإعداد المركزي. كل نموذج له "مفتاح" (مثل `genspark_claude_opus`) يحدّد:
- `provider`: نوع المزوّد (genspark / openrouter / openai_compatible)
- `model`: اسم النموذج الدقيق
- `base_url`: عنوان الـ API
- `api_key_env`: اسم متغير البيئة الذي يحمل المفتاح

**التبديل:** غيّر `active_brain` لأي مفتاح آخر. هذا كل شيء.

### `brain.py`
كلاس `Brain`:
- يقرأ الإعداد
- `think(messages)`: يرسل المحادثة للنموذج ويرجّع الرد
- يتعامل مع إعادة المحاولة عند الزحام (429)
- يضيف ترويسات OpenRouter فقط لمزوّد OpenRouter (يتجنّب حظر Cloudflare على غيره)

---

## 🛠️ طبقة الأدوات (tools/)

| الأداة | الوظيفة |
|--------|---------|
| `run_shell(command)` | تنفيذ أوامر terminal داخل `projects/` |
| `write_file(path, content)` | كتابة/إنشاء ملف |
| `read_file(path)` | قراءة ملف |
| `list_dir(path)` | عرض محتويات مجلد |
| `web_search(query)` | بحث ويب (DuckDuckGo) |

🔒 **الحماية:** كل الأدوات محصورة داخل `projects/` عبر `_safe_path` — الوكيل لا يستطيع الخروج والعبث بالنظام.

---

## 🔑 الأمان (config/)
- المفاتيح في `.env` بصلاحية `600`
- لا مفاتيح في الكود
- المسارات محصورة في `projects/`

---

## ▶️ كيف تشغّله

```bash
cd /home/work/Ai_Alabbasi
set -a; source config/.env; set +a       # حمّل المفاتيح

# مهمة مخصصة:
python3 agent/agent.py "ابنِ لي موقع Next.js بسيط فيه صفحة ترحيب"

# اختبار العقل فقط:
python3 brain/brain.py

# اختبار الأدوات:
python3 tools/tools.py
```

## 🔄 تبديل العقل
```bash
# عدّل brain/brain_config.yaml:
active_brain: genspark_gpt5_codex   # مثلاً للبرمجة بـ GPT-5
# أو للنموذج المحلي بعد تثبيت Ollama:
active_brain: local_ollama
```
