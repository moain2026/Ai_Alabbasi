"""
🔄 STATE MACHINE — آلة حالات الوكيل (نمط Manus)
═══════════════════════════════════════════════════════════════
تُنظّم دورة حياة الوكيل وتضبط الانتقالات المسموحة بينها،
مما يجعل المقاطعة (Interrupt) والاستئناف (Resume) آمنين ومتوقّعين.

الحالات:
  IDLE        — خامل (لم يبدأ)
  RUNNING     — يعمل (حلقة ReAct)
  INTERRUPTED — قُوطع (بطلب المستخدم)
  RESUMING    — يستأنف بعد مقاطعة (قد يُعيد التخطيط)
  DONE        — أنهى المهمة بنجاح
  FAILED      — فشل (خطأ غير قابل للاسترداد)

بلا اعتماديات خارجية.
"""
from __future__ import annotations

from enum import Enum


class State(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    INTERRUPTED = "interrupted"
    RESUMING = "resuming"
    DONE = "done"
    FAILED = "failed"


# الانتقالات المسموحة: من → إلى
_ALLOWED: dict[State, set[State]] = {
    State.IDLE:        {State.RUNNING},
    State.RUNNING:     {State.INTERRUPTED, State.DONE, State.FAILED},
    State.INTERRUPTED: {State.RESUMING, State.FAILED, State.IDLE},
    State.RESUMING:    {State.RUNNING, State.FAILED},
    State.DONE:        set(),     # نهائية
    State.FAILED:      {State.IDLE},  # يمكن إعادة التشغيل
}


class InvalidTransition(Exception):
    """انتقال حالة غير مسموح."""


class StateMachine:
    """
    آلة حالات بسيطة وآمنة.

    الاستخدام:
        sm = StateMachine()
        sm.to(State.RUNNING)
        if sm.can(State.INTERRUPTED):
            sm.to(State.INTERRUPTED)
    """

    def __init__(self, initial: State = State.IDLE):
        self._state = initial
        self._history: list[State] = [initial]

    @property
    def state(self) -> State:
        return self._state

    @property
    def history(self) -> list[State]:
        return list(self._history)

    def can(self, target: State) -> bool:
        """هل الانتقال للحالة المطلوبة مسموح؟"""
        return target in _ALLOWED.get(self._state, set())

    def to(self, target: State) -> State:
        """ينتقل للحالة المطلوبة أو يرفع InvalidTransition."""
        if not self.can(target):
            raise InvalidTransition(
                f"انتقال غير مسموح: {self._state.value} → {target.value}"
            )
        self._state = target
        self._history.append(target)
        return self._state

    # ── اختصارات منطقية ───────────────────────────────────────
    def is_active(self) -> bool:
        return self._state in (State.RUNNING, State.RESUMING)

    def is_terminal(self) -> bool:
        return self._state in (State.DONE,) or not _ALLOWED.get(self._state)

    def reset(self) -> None:
        self._state = State.IDLE
        self._history = [State.IDLE]


if __name__ == "__main__":
    sm = StateMachine()
    assert sm.state == State.IDLE
    sm.to(State.RUNNING)
    assert sm.is_active()
    assert sm.can(State.INTERRUPTED)
    sm.to(State.INTERRUPTED)
    sm.to(State.RESUMING)
    sm.to(State.RUNNING)
    sm.to(State.DONE)
    assert sm.is_terminal()
    # انتقال غير مسموح
    try:
        sm.to(State.RUNNING)
        raise AssertionError("كان يجب أن يفشل")
    except InvalidTransition:
        pass
    print("المسار:", " → ".join(s.value for s in sm.history))
    print("✅ state_machine OK")
