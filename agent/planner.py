"""
📐 PLANNER — وحدة التخطيط (نمط Manus)
═══════════════════════════════════════════════════════════════
قبل التنفيذ، يطلب الوكيل من العقل خطة مرقّمة (pseudocode) للمهمة.
ثم — بعد كل عدد من الخطوات — يتأمّل (reflection) هل الخطة ما زالت صالحة.

التصميم:
  • يعتمد على "العقل" (Brain) لتوليد الخطة — لكنه يقبل أي كائن فيه think().
  • يُرجع قائمة خطوات نصية بسيطة (تتغذّى منها TodoManager).
  • بلا اعتماديات خارجية.

العقد (contract): brain.think(messages, max_tokens) -> str
"""
from __future__ import annotations

import json
import re

PLAN_SYSTEM = (
    "أنت مخطّط مهام خبير. حلّل المهمة وأخرج خطة تنفيذ مرقّمة وعملية.\n"
    "القواعد:\n"
    "1. أخرج JSON فقط: {\"steps\": [\"خطوة 1\", \"خطوة 2\", ...]}\n"
    "2. كل خطوة فعل واحد واضح وقابل للتنفيذ بأداة.\n"
    "3. من 2 إلى 8 خطوات. لا شرح خارج JSON.\n"
    "4. رتّب الخطوات منطقياً (التبعيات أولاً)."
)

REFLECT_SYSTEM = (
    "أنت مراجع خطط. بالنظر للخطة الأصلية وما نُفّذ، قرّر إن كانت الخطة "
    "ما زالت صالحة أم تحتاج تعديلاً.\n"
    "أخرج JSON فقط: {\"valid\": true/false, \"revised_steps\": [...]} "
    "(اترك revised_steps فارغة إن كانت صالحة)."
)


def _extract_json(text: str) -> dict | None:
    """يستخرج أول كائن JSON من نص (متسامح)."""
    if not text:
        return None
    # حاول الكتلة الكاملة أولاً
    try:
        return json.loads(text)
    except Exception:
        pass
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            return None
    return None


class Planner:
    """
    مخطّط يعتمد على العقل لتوليد ومراجعة الخطط.

    الاستخدام:
        planner = Planner(brain)
        steps = planner.make_plan("ابنِ صفحة هبوط عربية")
        # ... بعد تنفيذ بعض الخطوات ...
        ok, new_steps = planner.reflect(task, steps, done_summary)
    """

    def __init__(self, brain, max_steps: int = 8):
        self.brain = brain
        self.max_steps = max_steps

    def make_plan(self, task: str) -> list[str]:
        """يولّد خطة مرقّمة للمهمة. يُرجع قائمة خطوات (قد تكون فارغة عند الفشل)."""
        try:
            reply = self.brain.think(
                [
                    {"role": "system", "content": PLAN_SYSTEM},
                    {"role": "user", "content": f"المهمة: {task}"},
                ],
                max_tokens=600,
            )
        except Exception:
            return []
        data = _extract_json(reply) or {}
        steps = data.get("steps") or []
        steps = [str(s).strip() for s in steps if str(s).strip()]
        return steps[: self.max_steps]

    def reflect(
        self, task: str, plan: list[str], done_summary: str
    ) -> tuple[bool, list[str]]:
        """
        يتأمّل صلاحية الخطة بعد تنفيذ جزء منها.
        يُرجع (صالحة؟، خطوات_منقّحة). عند الفشل يعتبر الخطة صالحة (آمن).
        """
        try:
            reply = self.brain.think(
                [
                    {"role": "system", "content": REFLECT_SYSTEM},
                    {
                        "role": "user",
                        "content": (
                            f"المهمة: {task}\n"
                            f"الخطة الأصلية: {json.dumps(plan, ensure_ascii=False)}\n"
                            f"ما نُفّذ: {done_summary[:1000]}"
                        ),
                    },
                ],
                max_tokens=600,
            )
        except Exception:
            return True, plan
        data = _extract_json(reply) or {}
        valid = bool(data.get("valid", True))
        revised = [str(s).strip() for s in (data.get("revised_steps") or []) if str(s).strip()]
        if valid or not revised:
            return True, plan
        return False, revised[: self.max_steps]


if __name__ == "__main__":
    # عقل وهمي للاختبار بلا مفتاح
    class FakeBrain:
        def think(self, messages, max_tokens=600):
            if "مراجع" in messages[0]["content"]:
                return '{"valid": true, "revised_steps": []}'
            return '{"steps": ["أنشئ index.html", "أضف CSS بـ RTL", "اختبر"]}'

    p = Planner(FakeBrain())
    steps = p.make_plan("ابنِ صفحة هبوط")
    assert steps == ["أنشئ index.html", "أضف CSS بـ RTL", "اختبر"], steps
    ok, rev = p.reflect("ابنِ صفحة هبوط", steps, "أنشأت index.html")
    assert ok is True
    print("الخطة:", steps)
    print("✅ planner OK")
