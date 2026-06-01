"""
🔁 AGENT — حلقة الوكيل (ReAct: Reason + Act)
═══════════════════════════════════════════════════════════════
يربط العقل (Brain) بالأدوات (Tools) في حلقة:
  يفكّر → يختار أداة → ينفّذ → يراقب النتيجة → يكرّر حتى ينجز.
"""
import sys
import json
import re
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "brain"))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "knowledge"))

from brain import Brain          # noqa
import tools as T                # noqa
try:
    from knowledge import Knowledge  # noqa
except Exception:
    Knowledge = None

# ── وحدات أنماط Manus (Phase 1) — اختيارية، لا تكسر السلوك القديم ──
sys.path.insert(0, str(ROOT / "agent"))
try:
    from event_stream import EventStream, EventType   # noqa
    from planner import Planner                        # noqa
    from todo_manager import TodoManager               # noqa
    from state_machine import StateMachine, State      # noqa
    from interrupt_handler import InterruptHandler     # noqa
    _MANUS_OK = True
except Exception:
    _MANUS_OK = False

LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)


SYSTEM_PROMPT = """أنت Ai_Alabbasi، وكيل برمجي ذكي خاص بعبّاس. تنفّذ مهام كاملة بنفسك بدقة.

لديك أدوات. للاستخدام، أخرج JSON فقط بهذا الشكل تماماً عندما تريد تنفيذ أداة:
{{"thought": "تفكيرك المختصر", "tool": "اسم_الأداة", "args": {{...}}}}

عندما تنتهي من المهمة كلياً، أخرج:
{{"thought": "ملخص ما أنجزت", "done": true, "final": "رسالتك النهائية لعبّاس"}}

الأدوات المتاحة:
{tools}

قواعد صارمة:
- أخرج JSON واحد فقط في كل رد. لا نص خارج JSON.
- نفّذ خطوة واحدة في كل مرة وانتظر النتيجة.
- كل الملفات/الأوامر تعمل داخل مجلد projects/.
- اكتب كوداً نظيفاً واختبره بالتشغيل قبل أن تعلن الانتهاء.
- إذا فشل أمر، اقرأ الخطأ وأصلحه، لا تكرر نفس الفعل."""


def extract_json(text: str):
    """يستخرج أول كائن JSON صالح من رد النموذج."""
    text = text.strip()
    # إزالة code fences
    text = re.sub(r"^```(json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    # محاولة مباشرة
    try:
        return json.loads(text)
    except Exception:
        pass
    # ابحث عن أول { ... } متوازن
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except Exception:
                    return None
    return None


class Agent:
    def __init__(self, max_steps: int = 25, verbose: bool = True, topic: str = None,
                 learn: bool = True, on_event=None, plan: bool = True,
                 interrupt_handler=None):
        self.brain = Brain()
        self.max_steps = max_steps
        self.verbose = verbose
        self.topic = topic            # تقنية التركيز (react-native/nextjs/angular) للـ RAG
        self.learn = learn            # حفظ skill بعد النجاح
        self.kb = Knowledge() if Knowledge else None
        self.on_event = on_event      # callback(kind, data) للبث المباشر (الواجهة)
        self.log_path = LOG_DIR / f"run_{datetime.now():%Y%m%d_%H%M%S}.log"

        # ── أنماط Manus (Phase 1) ──
        self.use_plan = plan and _MANUS_OK
        self.events = EventStream() if _MANUS_OK else None
        self.sm = StateMachine() if _MANUS_OK else None
        self.interrupt = interrupt_handler   # InterruptHandler اختياري من الخادم
        self._planner = Planner(self.brain) if _MANUS_OK else None
        self._todo = None             # يُنشأ عند بدء المهمة

    def _emit(self, kind: str, data):
        """يبث حدثاً للمستمع (الواجهة) إن وُجد."""
        if self.on_event:
            try:
                self.on_event(kind, data)
            except Exception:
                pass

    def _log(self, msg: str):
        if self.verbose:
            print(msg)
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(msg + "\n")

    def run(self, task: str) -> str:
        info = self.brain.info()
        self._log(f"🧠 العقل: {info['model']} ({info['active']})")
        self._log(f"🎯 المهمة: {task}\n" + "=" * 60)

        system = SYSTEM_PROMPT.format(tools=T.tools_spec())

        # 📚 حقن المعرفة (RAG + خبرات سابقة) — هنا “التمرّس”
        kb_context = ""
        if self.kb:
            kb_context = self.kb.context_for(task, topic=self.topic)
            if kb_context:
                self._log(f"📚 حُقنت معرفة ذات صلة ({len(kb_context)} حرف)")

        user_msg = f"المهمة: {task}"
        if kb_context:
            user_msg += f"\n\n--- معرفة مساعدة (استفد منها) ---\n{kb_context}"

        # 📋 التخطيط المسبق + قائمة المهام (نمط Manus Planner + Recitation)
        plan_steps = []
        if self.use_plan:
            try:
                self.sm.to(State.RUNNING)
            except Exception:
                pass
            self.events and self.events.message("user", task)
            plan_steps = self._planner.make_plan(task)
            if plan_steps:
                self._todo = TodoManager(title=task[:60], slug=None)
                self._todo.set_items(plan_steps)
                self.events and self.events.plan("planner", plan_steps)
                self._emit("plan", plan_steps)
                self._log("📋 الخطة:\n" + "\n".join(f"  {i+1}. {s}" for i, s in enumerate(plan_steps)))
                user_msg += "\n\n--- خطة مقترحة (نفّذها بالترتيب) ---\n" + \
                    "\n".join(f"{i+1}. {s}" for i, s in enumerate(plan_steps))

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ]

        self._emit("start", {"task": task, "model": info["model"]})
        for step in range(1, self.max_steps + 1):
            self._log(f"\n──── الخطوة {step}/{self.max_steps} ────")
            self._emit("step", {"n": step, "total": self.max_steps})

            # ⏸️ فحص المقاطعة (نمط Manus Interrupt)
            if self.interrupt and self.interrupt.requested():
                guidance = self.interrupt.consume()
                if guidance:
                    self._log(f"⏸️ مقاطعة بتوجيه جديد: {guidance}")
                    self._emit("thought", f"(مقاطعة — إعادة توجيه: {guidance})")
                    self.events and self.events.message("user", guidance, step)
                    messages.append({"role": "user", "content": f"توجيه جديد من المستخدم (أعد التخطيط وفقه): {guidance}"})
                    if self.sm and self.sm.can(State.INTERRUPTED):
                        self.sm.to(State.INTERRUPTED); self.sm.to(State.RESUMING); self.sm.to(State.RUNNING)
                else:
                    self._log("⏸️ أُوقف بطلب المستخدم.")
                    self._emit("stopped", "🛑 أُوقفت المهمة بطلبك.")
                    if self.sm and self.sm.can(State.INTERRUPTED):
                        self.sm.to(State.INTERRUPTED)
                    return "🛑 أُوقفت المهمة بطلبك."

            # 🔁 التلاوة (Recitation): أعِد قائمة المهام لآخر السياق كل بضع خطوات
            if self._todo and step > 1:
                messages.append({"role": "user", "content": self._todo.recite()})

            try:
                reply = self.brain.think(messages)
            except Exception as e:
                self._log(f"❌ خطأ في العقل: {e}")
                # 🔔 أصدر حدث خطأ واضحاً للواجهة بدل التوقف الصامت
                msg = str(e)
                if "المفتاح غير موجود" in msg or "api_key" in msg.lower() or "api key" in msg.lower():
                    hint = (
                        "⚠️ لا يوجد مفتاح API للنموذج.\n"
                        f"التفاصيل: {msg}\n"
                        "الحل: أنشئ ملف config/.env وأضف المفتاح المطلوب "
                        "(انظر config/.env.example)، ثم أعد تشغيل الخادم."
                    )
                else:
                    hint = f"❌ فشل العقل: {msg}"
                self._emit("error", hint)
                return hint

            # كشف أخطاء المزوّد (رصيد/مفتاح) — أوقف فوراً بدل التكرار
            low = reply.lower()
            if any(s in low for s in ["credits have been exhausted", "insufficient", "quota", "unauthorized", "invalid api key", "rate limit exceeded"]):
                self._log(f"\n⛔ خطأ من المزوّد: {reply[:300]}")
                self._emit("error", reply.strip()[:400])
                return f"⛔ توقّف الوكيل — مشكلة في مزوّد النموذج:\n{reply.strip()[:300]}"

            action = extract_json(reply)
            if not action:
                self._log(f"⚠️ رد غير منظّم:\n{reply[:500]}")
                self._emit("thought", "(رد غير منظّم — أعيد المحاولة)")
                messages.append({"role": "assistant", "content": reply})
                messages.append({"role": "user", "content": "أخرج JSON صالحاً فقط كما في التعليمات."})
                bad = getattr(self, "_bad", 0) + 1
                self._bad = bad
                if bad >= 3:
                    self._emit("error", "النموذج يرجّع ردوداً غير صالحة متكررة.")
                    return "⛔ توقّف الوكيل — النموذج لا يرجّع أوامر صالحة (جرّب عقلاً آخر من الإعدادات)."
                continue
            self._bad = 0

            messages.append({"role": "assistant", "content": json.dumps(action, ensure_ascii=False)})

            if action.get("thought"):
                self._log(f"💭 {action['thought']}")
                self._emit("thought", action["thought"])
                self.events and self.events.other("thought", action["thought"], step)

            if action.get("done"):
                final = action.get("final", "تم.")
                self._log(f"\n✅ انتهى:\n{final}")
                self._emit("done", final)
                # علّم كل المهام المتبقية كمكتملة + حدّث الحالة
                if self._todo:
                    for txt, d in list(self._todo._items):
                        if not d:
                            self._todo.complete(txt)
                if self.sm and self.sm.can(State.DONE):
                    self.sm.to(State.DONE)
                # 🔁 حلقة التعلّم: احفظ التجربة الناجحة كـ skill
                if self.learn and self.kb:
                    self._save_skill(task, action.get("thought", ""), final)
                return final

            tool = action.get("tool")
            args = action.get("args", {})
            if not tool:
                messages.append({"role": "user", "content": "لم تحدد أداة. حدد tool أو done."})
                continue

            self._log(f"🛠️ {tool}({json.dumps(args, ensure_ascii=False)[:200]})")
            self._emit("tool", {"name": tool, "args": args})
            self.events and self.events.action(tool, args, step)
            result = T.call_tool(tool, args)
            self._log(f"📤 النتيجة:\n{result[:1000]}")
            self._emit("tool_result", {"name": tool, "result": result[:2000]})
            self.events and self.events.observation(tool, result[:500], step)
            messages.append({"role": "user", "content": f"نتيجة {tool}:\n{result[:4000]}"})

        self._log("\n⏹️ بلغ الحد الأقصى للخطوات.")
        if self.sm and self.sm.can(State.FAILED):
            self.sm.to(State.FAILED)
        return "بلغ الوكيل الحد الأقصى للخطوات دون إنهاء المهمة."

    def _save_skill(self, task: str, thought: str, final: str):
        """يستخلص خبرة من المهمة الناجحة ويحفظها."""
        try:
            prompt = [
                {"role": "system", "content": "استخلص خبرة معاد الاستخدام من مهمة ناجحة. أخرج JSON فقط: {\"name\":\"اسم قصير\",\"approach\":\"الطريقة المختصرة القابلة لإعادة الاستخدام\",\"tags\":\"كلمات مفتاحية\"}"},
                {"role": "user", "content": f"المهمة: {task}\nالنتيجة: {final[:800]}"},
            ]
            raw = self.brain.think(prompt, max_tokens=400)
            data = extract_json(raw)
            if data and data.get("name"):
                self.kb.add_skill(
                    name=data["name"], task=task[:300],
                    approach=data.get("approach", thought),
                    tags=data.get("tags", self.topic or ""),
                )
                self._log(f"🧠 تعلّم خبرة جديدة: {data['name']}")
        except Exception as e:
            self._log(f"(تعذّر حفظ الخبرة: {e})")


if __name__ == "__main__":
    # دعم --topic لتحديد تقنية التركيز (RAG)
    args = sys.argv[1:]
    topic = None
    if "--topic" in args:
        i = args.index("--topic")
        topic = args[i + 1] if i + 1 < len(args) else None
        args = args[:i] + args[i + 2:]
    task = " ".join(args) or "أنشئ ملف hello.py يطبع 'Ai_Alabbasi يعمل' ثم شغّله."
    agent = Agent(topic=topic)
    agent.run(task)
