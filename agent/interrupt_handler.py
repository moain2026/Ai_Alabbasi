"""
⏸️ INTERRUPT HANDLER — معالج المقاطعة وإعادة التخطيط (نمط Manus)
═══════════════════════════════════════════════════════════════
يتيح للمستخدم مقاطعة الوكيل أثناء العمل، ثم:
  • الإيقاف الكامل، أو
  • حقن توجيه جديد وإعادة التخطيط (Resume with new guidance).

التصميم: علم مقاطعة آمن للخيوط (thread-safe) + رسالة توجيه اختيارية.
يتكامل مع StateMachine و on_event الموجودَين. بلا اعتماديات خارجية.
"""
from __future__ import annotations

import threading


class InterruptHandler:
    """
    منسّق مقاطعة آمن بين الخيوط.

    الاستخدام (داخل حلقة الوكيل):
        ih = InterruptHandler()
        # في كل خطوة:
        if ih.requested():
            guidance = ih.consume()       # يستهلك الطلب
            if guidance:
                # أعد التخطيط بالتوجيه الجديد
            else:
                break                      # إيقاف كامل

    من الخيط الآخر (الخادم):
        ih.interrupt()                     # إيقاف
        ih.interrupt("ركّز على الأداء")    # مقاطعة + توجيه
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._requested = False
        self._guidance: str | None = None

    def interrupt(self, guidance: str | None = None) -> None:
        """يطلب مقاطعة، مع توجيه اختياري لإعادة التخطيط."""
        with self._lock:
            self._requested = True
            g = guidance.strip() if guidance else ""
            self._guidance = g or None   # توجيه فارغ = إيقاف كامل

    def requested(self) -> bool:
        """هل هناك طلب مقاطعة معلّق؟ (لا يستهلكه)."""
        with self._lock:
            return self._requested

    def consume(self) -> str | None:
        """
        يستهلك طلب المقاطعة ويُعيد التوجيه (أو None للإيقاف الكامل).
        بعده يعود requested() إلى False.
        """
        with self._lock:
            g = self._guidance
            self._requested = False
            self._guidance = None
            return g

    def clear(self) -> None:
        """يلغي أي طلب معلّق."""
        with self._lock:
            self._requested = False
            self._guidance = None


if __name__ == "__main__":
    ih = InterruptHandler()
    assert ih.requested() is False
    # إيقاف كامل
    ih.interrupt()
    assert ih.requested() is True
    assert ih.consume() is None
    assert ih.requested() is False
    # مقاطعة بتوجيه
    ih.interrupt("ركّز على الأمان")
    assert ih.requested() is True
    g = ih.consume()
    assert g == "ركّز على الأمان", g
    assert ih.requested() is False
    print("✅ interrupt_handler OK")
