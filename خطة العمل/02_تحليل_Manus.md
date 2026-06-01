# 🧬 تحليل Manus AI الشامل
## الأنماط السبعة + دروس هندسة السياق الستة + الأدوات الـ29 + الملفات المسرّبة

> المصدر: التقرير التقني الشامل عن Manus AI (مرفوع) + مدوّنة Peak Ji الرسمية + الملفات المسرّبة على
> `x1xhlol/system-prompts-and-models-of-ai-tools`.
> **ملاحظة:** التقرير الأصلي يذكر "hermes-agent-smart" — نتجاهل ذلك؛ الأنماط نفسها تنطبق على Ai_Alabbasi.

---

## 🎯 من هو Manus؟

وكيل ذكاء اصطناعي مستقل من شركة **Monica** الصينية، يعتمد على:
- **Claude 3.5/3.7 Sonnet** + **Qwen** المضبوط بدقة (fine-tuned).

ما يميّزه (7 أمور):

| # | الميزة | لماذا فريدة |
|---|--------|-------------|
| 1 | **CodeAct بدل Tool Calling** | يكتب Python قابل للتنفيذ بدل استدعاءات دوال محدودة |
| 2 | **بنية ثلاثية الطبقات** | Planner → Executor → Verifier منفصلة |
| 3 | **Event Stream كذاكرة عمل** | سجل زمني لكل ما يحدث في الجلسة |
| 4 | **todo.md المتجدّد (Recitation)** | يُعيد كتابة الخطة كل دورة لإبقاء التركيز |
| 5 | **Wide Research** | يُطلق 100+ وكيل فرعي بالتوازي |
| 6 | **Browser Operator** | يتحكّم بمتصفح المستخدم عبر MCP |
| 7 | **مقاطعة سلسة + إعادة تخطيط ديناميكي** | المستخدم يقاطع → الوكيل يُعيد بناء todo.md |

---

## 🔁 1. حلقة العمل (Agent Loop) — القاعدة الذهبية

```
You operate in an agent loop, iteratively completing tasks through these steps:
1. Analyze Events:   فهم احتياج المستخدم والحالة الحالية عبر event stream
2. Select Tools:     اختيار الأداة التالية بناءً على الحالة + التخطيط + المعرفة
3. Wait for Execution: تنفيذ الأداة في الـ sandbox، تُضاف الملاحظة
4. Iterate:          أداة واحدة فقط لكل دورة، كرّر حتى الإنجاز
5. Submit Results:   إرسال النتائج عبر أدوات الرسائل مع المرفقات
6. Enter Standby:    دخول وضع الخمول عند اكتمال المهام
```

> 🔴 **القاعدة الذهبية:** *"One tool call per iteration"* — أهم قرار معماري في Manus.
> **حالتنا:** Ai_Alabbasi يطبّق هذا بالفعل (خطوة واحدة لكل دورة) ✅.

---

## 📡 2. Event Stream — أنواع الأحداث الستة

```
Event types in the chronological stream:
1. Message:     رسائل المستخدم الفعلية
2. Action:      استخدام أداة (function calling)
3. Observation: نتائج تنفيذ الأداة
4. Plan:        تخطيط الخطوات من Planner module
5. Knowledge:   أفضل الممارسات من Knowledge module
6. Datasource:  توثيق Data API
7. Other:       أحداث متفرقة
```

**كيف نطبّقه في Ai_Alabbasi:** `agent/event_stream.py` يسجّل كل هذه الأنواع كقائمة زمنية،
ويُعاد بناء السياق منها كل دورة بدلاً من تمرير `messages` الخام.

---

## 🧭 3. Planner Module — قلب المقاطعة وإعادة التخطيط

```
- النظام مزوّد بـ planner module للتخطيط الكلّي
- الخطط تُمثَّل بـ pseudocode مرقّم
- كل تحديث يشمل: رقم الخطوة الحالية + الحالة + التأمّل (reflection)
- الـ pseudocode يُحدَّث عند تغيّر هدف المهمة الكلّي
- يجب إكمال كل الخطوات والوصول لرقم الخطوة النهائي عند الإنجاز
```

> 🔥 **السرّ:** عندما يرسل المستخدم رسالة جديدة → يلتقطها Event Stream → يقرأها Planner →
> يُعيد بناء قائمة الـ pseudocode → يُعيد كتابة `todo.md` من الصفر.

---

## 📝 4. todo.md Rules — آلية الـ Recitation

```
- أنشئ todo.md كقائمة تحقّق بناءً على خطة Planner
- التخطيط له الأولوية، لكن todo.md يحوي تفاصيل أكثر
- حدّث علامات todo.md عبر أداة الاستبدال النصّي فور إكمال كل بند
- أعِد بناء todo.md عند تغيّر التخطيط جوهرياً
- استخدم todo.md لتسجيل وتحديث التقدّم في مهام جمع المعلومات
- عند اكتمال كل الخطوات، تحقّق من todo.md وأزِل البنود المتخطّاة
```

> 📖 **شرح Recitation (من فريق Manus):** *"بإعادة كتابة قائمة todo باستمرار، يقوم Manus بـ«تلاوة»
> أهدافه في نهاية السياق. هذا يدفع الخطة إلى نطاق الانتباه الحديث (recent attention span)،
> ويتجنّب الضياع في المنتصف (lost-in-the-middle)، ويقلّل انحراف الأهداف."*

---

## 💬 5. Message Rules — رسالتان فقط

- **notify** (غير حاجبة، لا تنتظر رداً) — للتحديثات الدورية. استخدمها بكثرة.
- **ask** (حاجبة، تنتظر رداً) — للضرورات فقط (قلّل الإزعاج).
- الردّ الأول مختصر (تأكيد استلام فقط).
- قدّم كل الملفات ذات الصلة كمرفقات.

---

## 🖥️ 6. بيئة الـ Sandbox

```
- Ubuntu 22.04 (linux/amd64) + إنترنت
- User: ubuntu (صلاحيات sudo)
- Python 3.10.12 · Node.js 20.18.0 · bc
- البيئة تنام عند الخمول وتستيقظ تلقائياً (Hibernation)
```

> **حالتنا:** Ai_Alabbasi محلي فقط → الهدف 4 يضيف Daytona/E2B لتحقيق الـ Hibernation.

---

## 🛠️ 7. الأدوات الـ29 الكاملة

| الفئة | الأدوات |
|-------|---------|
| **Communication** (2) | `message_notify_user` · `message_ask_user` |
| **Files** (6) | `file_read` · `file_write` · `file_str_replace` · `file_find_in_content` · `file_find_by_name` · (+sudo options) |
| **Shell** (5) | `shell_exec` (بمعرّف جلسة) · `shell_view` · `shell_wait` · `shell_write_to_process` · `shell_kill_process` |
| **Browser** (12) | `browser_view` · `browser_navigate` · `browser_click` · `browser_input` · `browser_move_mouse` · `browser_press_key` · `browser_select_option` · `browser_scroll_up/down` · `browser_console_exec` · `browser_console_view` · … |
| **Deploy** (2+) | `expose_port` · … |

> **حالتنا:** عندنا 7 أدوات فقط. الفجوة الأهم: `file_str_replace` (للـ Recitation)، جلسات shell، أدوات browser.

---

## 🎓 8. دروس هندسة السياق الستة (من مدوّنة Peak Ji الرسمية)

| # | الدرس | التفاصيل العملية |
|---|-------|-------------------|
| 1 | **صمّم حول KV-Cache** | نسبة إدخال/إخراج 100:1 · الـ tokens المخزّنة أرخص 10× · أبقِ البادئة (prefix) ثابتة · append-only · JSON حتمي (`sort_keys=True`). |
| 2 | **أخفِ الأدوات ولا تحذفها** | استخدم state machine + بادئات ثابتة (`browser_` / `shell_`) بدل حذف الأدوات (يكسر الـ cache). |
| 3 | **نظام الملفات = سياق لا نهائي** | اكتب للملفات بدل حشو السياق · ضغط قابل للاستعادة (restorable compression). |
| 4 | **Recitation عبر todo.md** | مكافحة الضياع في المنتصف بإعادة كتابة الأهداف في نهاية السياق. |
| 5 | **أبقِ الأخطاء في السياق** | لا تخفِ الأخطاء — النموذج يتعلّم منها ويتجنّب تكرارها. |
| 6 | **لا تنخدع بالأمثلة (few-shot)** | تنويع الصياغة يمنع الوكيل من تقليد نمط واحد بشكل أعمى. |

> 🎯 **أهم درس قابل للتطبيق فوراً على Ai_Alabbasi:** الدرس 1 — إضافة `sort_keys=True` في
> `json.dumps` داخل `agent.py` (تحسين رخيص يرفع كفاءة KV-cache فوراً). انظر ADR-003.

---

## 🌊 9. Wide Research — المعالجة المتوازية

Manus يُطلق 100+ وكيل فرعي بالتوازي لمهام جمع المعلومات الضخمة (مثل تحليل 100 شركة).
كل وكيل فرعي يعمل في sandbox منفصل، والنتائج تُجمَّع في النهاية.

> **حالتنا:** خارج النطاق المباشر لـ v2.0 (Backlog) — لكن البنية (Event Stream + Sandbox سحابي)
> تمهّد له مستقبلاً.

---

## 🔗 10. ما الذي نأخذه فعلياً إلى Ai_Alabbasi؟

| نمط Manus | الأولوية | الملف الجديد |
|-----------|---------|--------------|
| Planner Module | 🔴 عالية | `agent/planner.py` |
| Event Stream | 🔴 عالية | `agent/event_stream.py` |
| todo.md Recitation | 🔴 عالية | `agent/todo_manager.py` |
| Interrupt Handler | 🔴 عالية | `agent/interrupt_handler.py` |
| CodeAct Executor | 🔴 عالية | `agent/code_act_executor.py` |
| State Machine | 🔴 عالية | `agent/state_machine.py` |
| KV-Cache (sort_keys) | 🟢 سريعة | تعديل `agent/agent.py` |
| file_str_replace | 🟡 متوسطة | تعديل `tools/tools.py` |
| Browser tools | 🟢 لاحقاً | Backlog |
| Wide Research | 🟢 لاحقاً | Backlog |

---

> **آخر تحديث:** 2026-06-01 — ⚡ Genspark High-Performance Agent
