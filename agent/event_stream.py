"""
📡 EVENT STREAM — مجرى الأحداث (نمط Manus)
═══════════════════════════════════════════════════════════════
يمثّل ذاكرة الوكيل الزمنية: سلسلة أحداث مرتّبة زمنياً يُبنى منها السياق.
Manus يصنّف الأحداث إلى 6 أنواع — نعتمدها هنا بصيغة خفيفة بلا اعتماديات.

الأنواع الستة:
  MESSAGE      — رسالة من/إلى المستخدم
  ACTION       — استدعاء أداة (نية تنفيذ)
  OBSERVATION  — نتيجة تنفيذ أداة
  PLAN         — خطوة من المخطّط (planner)
  KNOWLEDGE    — معرفة محقونة (RAG/مهارة)
  OTHER        — أحداث متنوّعة (تفكير، حالة، خطأ…)

التصميم: بسيط، قابل للتسلسل (JSON)، بلا اعتماديات خارجية.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any


class EventType(str, Enum):
    """الأنواع الستة لأحداث Manus."""
    MESSAGE = "message"
    ACTION = "action"
    OBSERVATION = "observation"
    PLAN = "plan"
    KNOWLEDGE = "knowledge"
    OTHER = "other"


@dataclass
class Event:
    """حدث واحد في المجرى الزمني."""
    type: EventType
    name: str                       # وصف قصير (مثل اسم الأداة أو "thought")
    data: Any = None                # الحمولة (نص/قاموس)
    ts: float = field(default_factory=time.time)
    step: int = 0                   # رقم خطوة ReAct المرتبطة

    def to_dict(self) -> dict:
        d = asdict(self)
        d["type"] = self.type.value
        return d


class EventStream:
    """
    مجرى أحداث الوكيل — ذاكرته الزمنية القابلة لإعادة البناء.

    الاستخدام:
        es = EventStream()
        es.add(EventType.MESSAGE, "user", "ابنِ موقعاً")
        es.add(EventType.ACTION, "write_file", {"path": "..."})
        context = es.render_context()
    """

    def __init__(self, max_events: int = 1000):
        self._events: list[Event] = []
        self._max = max_events

    def add(self, etype: EventType, name: str, data: Any = None, step: int = 0) -> Event:
        """يضيف حدثاً جديداً ويُعيده."""
        ev = Event(type=etype, name=name, data=data, step=step)
        self._events.append(ev)
        # حماية من النمو غير المحدود (نُبقي الأحدث)
        if len(self._events) > self._max:
            self._events = self._events[-self._max:]
        return ev

    # ── اختصارات للأنواع الشائعة ─────────────────────────────
    def message(self, name: str, data: Any, step: int = 0) -> Event:
        return self.add(EventType.MESSAGE, name, data, step)

    def action(self, name: str, data: Any, step: int = 0) -> Event:
        return self.add(EventType.ACTION, name, data, step)

    def observation(self, name: str, data: Any, step: int = 0) -> Event:
        return self.add(EventType.OBSERVATION, name, data, step)

    def plan(self, name: str, data: Any, step: int = 0) -> Event:
        return self.add(EventType.PLAN, name, data, step)

    def knowledge(self, name: str, data: Any, step: int = 0) -> Event:
        return self.add(EventType.KNOWLEDGE, name, data, step)

    def other(self, name: str, data: Any, step: int = 0) -> Event:
        return self.add(EventType.OTHER, name, data, step)

    # ── قراءة ─────────────────────────────────────────────────
    def all(self) -> list[Event]:
        return list(self._events)

    def by_type(self, etype: EventType) -> list[Event]:
        return [e for e in self._events if e.type == etype]

    def last(self, n: int = 1) -> list[Event]:
        return self._events[-n:]

    def __len__(self) -> int:
        return len(self._events)

    def __bool__(self) -> bool:
        # دائماً صادق عند وجود الكائن (حتى لو فارغاً) — لتفادي
        # القصر الدائري `self.events and ...` مع المجرى الفارغ.
        return True

    # ── تسلسل ─────────────────────────────────────────────────
    def to_json(self) -> str:
        # sort_keys=True لاستقرار KV-cache (نمط Manus)
        return json.dumps(
            [e.to_dict() for e in self._events],
            ensure_ascii=False, sort_keys=True,
        )

    def render_context(self, max_chars: int = 6000) -> str:
        """
        يبني نصاً موجزاً من المجرى لحقنه في سياق النموذج.
        يُبقي آخر الأحداث ضمن حدّ الأحرف.
        """
        lines: list[str] = []
        icons = {
            EventType.MESSAGE: "💬",
            EventType.ACTION: "🛠️",
            EventType.OBSERVATION: "📤",
            EventType.PLAN: "📋",
            EventType.KNOWLEDGE: "📚",
            EventType.OTHER: "•",
        }
        for e in self._events:
            payload = e.data
            if isinstance(payload, (dict, list)):
                payload = json.dumps(payload, ensure_ascii=False)
            payload = str(payload)[:400]
            lines.append(f"{icons.get(e.type, '•')} [{e.name}] {payload}")
        text = "\n".join(lines)
        return text[-max_chars:]


if __name__ == "__main__":
    es = EventStream()
    es.message("user", "ابنِ صفحة هبوط")
    es.plan("planner", ["1. أنشئ index.html", "2. أضف CSS"])
    es.action("write_file", {"path": "index.html"}, step=1)
    es.observation("write_file", "✅ كُتب", step=1)
    es.knowledge("rag", "استخدم RTL للعربية")
    print(es.render_context())
    print("\n--- JSON ---")
    print(es.to_json()[:200])
    print(f"\nعدد الأحداث: {len(es)}")
    assert len(es) == 5
    assert len(es.by_type(EventType.ACTION)) == 1
    print("✅ event_stream OK")
