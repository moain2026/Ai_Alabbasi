"""
📋 TODO MANAGER — مدير قائمة المهام (نمط Manus Recitation)
═══════════════════════════════════════════════════════════════
Manus يكتب خطته في ملف todo.md ثم "يتلوها" (Recitation) في كل خطوة
ليُبقي الهدف في آخر السياق (مقاومة "الضياع في المنتصف").

هذا المدير:
  • ينشئ/يقرأ todo.md لكل مشروع داخل projects/_state/
  • يحدّث حالة كل مهمة (☐ → ☑) عبر استبدال نصّي
  • يولّد "تلاوة" موجزة لحقنها في السياق

بلا اعتماديات خارجية.
"""
from __future__ import annotations

import re
from pathlib import Path

# نخزّن حالة المهام في projects/_state (داخل حدود الوكيل)
STATE_DIR = Path(__file__).resolve().parent.parent / "projects" / "_state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

PENDING = "☐"
DONE = "☑"


class TodoManager:
    """
    يدير ملف todo.md لمهمة واحدة.

    الاستخدام:
        tm = TodoManager("بناء موقع")
        tm.set_items(["إنشاء index.html", "إضافة CSS", "اختبار"])
        tm.complete("إنشاء index.html")
        print(tm.recite())
    """

    def __init__(self, title: str = "المهمة", slug: str | None = None):
        self.title = title
        self.slug = slug or self._slugify(title)
        self.path = STATE_DIR / f"todo_{self.slug}.md"
        self._items: list[tuple[str, bool]] = []  # (نص, مكتمل؟)
        if self.path.exists():
            self._load()

    @staticmethod
    def _slugify(text: str) -> str:
        s = re.sub(r"[^\w\u0600-\u06FF]+", "_", text.strip())
        return (s[:40] or "task").strip("_")

    # ── إدارة العناصر ─────────────────────────────────────────
    def set_items(self, items: list[str]) -> None:
        """يضع قائمة مهام جديدة (كلها معلّقة) ويحفظ."""
        self._items = [(it.strip(), False) for it in items if it.strip()]
        self._save()

    def add_item(self, item: str) -> None:
        self._items.append((item.strip(), False))
        self._save()

    def complete(self, item_substr: str) -> bool:
        """يعلّم أول مهمة معلّقة تطابق النص كمكتملة. يُعيد True عند النجاح."""
        for i, (txt, done) in enumerate(self._items):
            if not done and item_substr.strip() in txt:
                self._items[i] = (txt, True)
                self._save()
                return True
        return False

    def all_done(self) -> bool:
        return bool(self._items) and all(d for _, d in self._items)

    def progress(self) -> tuple[int, int]:
        done = sum(1 for _, d in self._items if d)
        return done, len(self._items)

    # ── تخزين ─────────────────────────────────────────────────
    def _render(self) -> str:
        lines = [f"# 📋 {self.title}", ""]
        for txt, done in self._items:
            lines.append(f"- {DONE if done else PENDING} {txt}")
        done, total = self.progress()
        lines.append("")
        lines.append(f"<!-- التقدّم: {done}/{total} -->")
        return "\n".join(lines) + "\n"

    def _save(self) -> None:
        self.path.write_text(self._render(), encoding="utf-8")

    def _load(self) -> None:
        self._items = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith(f"- {DONE}"):
                self._items.append((line[len(f"- {DONE}"):].strip(), True))
            elif line.startswith(f"- {PENDING}"):
                self._items.append((line[len(f"- {PENDING}"):].strip(), False))

    # ── التلاوة (Recitation) ──────────────────────────────────
    def recite(self) -> str:
        """
        يولّد نصاً موجزاً للحقن في آخر السياق — يُبقي الهدف حاضراً.
        يُبرز المهمة التالية المعلّقة.
        """
        done, total = self.progress()
        lines = [f"📋 قائمة المهام ({done}/{total}) — {self.title}:"]
        next_marked = False
        for txt, d in self._items:
            if d:
                lines.append(f"  {DONE} {txt}")
            elif not next_marked:
                lines.append(f"  ▶ {txt}   ← التالي")
                next_marked = True
            else:
                lines.append(f"  {PENDING} {txt}")
        return "\n".join(lines)


if __name__ == "__main__":
    tm = TodoManager("بناء صفحة هبوط", slug="_test_demo")
    tm.set_items(["إنشاء index.html", "إضافة CSS بـ RTL", "اختبار المتصفح"])
    assert tm.progress() == (0, 3)
    assert tm.complete("index.html") is True
    assert tm.progress() == (1, 3)
    print(tm.recite())
    # إعادة التحميل من الملف للتأكد من الثبات
    tm2 = TodoManager("بناء صفحة هبوط", slug="_test_demo")
    assert tm2.progress() == (1, 3), tm2.progress()
    tm.path.unlink(missing_ok=True)
    print("\n✅ todo_manager OK")
