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
    def __init__(self, max_steps: int = 25, verbose: bool = True, topic: str = None, learn: bool = True):
        self.brain = Brain()
        self.max_steps = max_steps
        self.verbose = verbose
        self.topic = topic            # تقنية التركيز (react-native/nextjs/angular) للـ RAG
        self.learn = learn            # حفظ skill بعد النجاح
        self.kb = Knowledge() if Knowledge else None
        self.log_path = LOG_DIR / f"run_{datetime.now():%Y%m%d_%H%M%S}.log"

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

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ]

        for step in range(1, self.max_steps + 1):
            self._log(f"\n──── الخطوة {step}/{self.max_steps} ────")
            try:
                reply = self.brain.think(messages)
            except Exception as e:
                self._log(f"❌ خطأ في العقل: {e}")
                return f"فشل: {e}"

            action = extract_json(reply)
            if not action:
                self._log(f"⚠️ رد غير منظّم:\n{reply[:500]}")
                messages.append({"role": "assistant", "content": reply})
                messages.append({"role": "user", "content": "أخرج JSON صالحاً فقط كما في التعليمات."})
                continue

            messages.append({"role": "assistant", "content": json.dumps(action, ensure_ascii=False)})

            if action.get("thought"):
                self._log(f"💭 {action['thought']}")

            if action.get("done"):
                final = action.get("final", "تم.")
                self._log(f"\n✅ انتهى:\n{final}")
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
            result = T.call_tool(tool, args)
            self._log(f"📤 النتيجة:\n{result[:1000]}")
            messages.append({"role": "user", "content": f"نتيجة {tool}:\n{result[:4000]}"})

        self._log("\n⏹️ بلغ الحد الأقصى للخطوات.")
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
