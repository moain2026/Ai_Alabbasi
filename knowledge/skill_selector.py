"""
🎯 SKILL SELECTOR — اختيار المهارات الذكي حسب السياق
═══════════════════════════════════════════════════════════════
بالنظر لمهمة المستخدم، يختار أنسب المهارات من الفهرس (الطبقة 1)
ليُفعّلها الوكيل (الطبقة 2) — تطبيقاً لمبدأ الكشف التدريجي.

طريقة المطابقة (هجينة خفيفة):
  • تطابق الكلمات المفتاحية مع الوسوم/الوصف (سريع، دقيق).
  • + تشابه دلالي عبر Embedder إن توفّر (يلتقط المرادفات).
  • يُدمج بنتيجة مرجّحة، ويُعيد الأعلى.

بلا اعتماديات خارجية إلزامية (Embedder نفسه يسقط لـ hashing).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

KDIR = Path(__file__).resolve().parent
sys.path.insert(0, str(KDIR))


def _tokens(text: str) -> set[str]:
    return {w.lower() for w in re.findall(r"[\w\u0600-\u06FF]+", text or "") if len(w) > 1}


class SkillSelector:
    """
    يختار المهارات الملائمة لمهمة.

    الاستخدام:
        from skill_indexer import SkillIndex
        idx = SkillIndex(); idx.build()
        sel = SkillSelector(idx)
        names = sel.select("ابنِ موقع Next.js عربي", top=2)
        ctx = sel.context_for("ابنِ موقع Next.js عربي")  # نص جاهز للحقن
    """

    def __init__(self, index, embedder=None, min_score: float = 0.05):
        self.index = index
        self.min_score = min_score
        self._embedder = embedder
        self._emb_tried = embedder is not None
        # متجهات مهارات مُهيّأة كسولاً
        self._skill_vecs: dict[str, list[float]] = {}

    def _emb(self):
        if self._embedder is None and not self._emb_tried:
            self._emb_tried = True
            try:
                from embedder import Embedder
                self._embedder = Embedder()
            except Exception:
                self._embedder = None
        return self._embedder

    @staticmethod
    def _fuzzy_overlap(a: set[str], b: set[str]) -> int:
        """
        تداخل متسامح مع الصرف العربي: تطابق تام أو جذع مشترك (أول 4 أحرف).
        يعالج لواحق مثل 'مقالاً' ↔ 'مقال'، 'تسويقياً' ↔ 'تسويق'.
        """
        count = 0
        for x in a:
            for y in b:
                if x == y or (len(x) >= 4 and len(y) >= 4 and (x[:4] == y[:4])):
                    count += 1
                    break
        return count

    def _keyword_score(self, task_tokens: set[str], skill: dict) -> float:
        """تداخل كلمات المهمة مع اسم/وسوم/وصف المهارة (متسامح صرفياً)."""
        skill_text = f"{skill.get('name','')} {skill.get('description','')} {skill.get('tags','')}"
        # نضيف نسخة بفواصل من الاسم (nextjs-rtl-pro → nextjs rtl pro)
        skill_text = skill_text.replace("-", " ").replace("_", " ")
        sk_tokens = _tokens(skill_text)
        if not sk_tokens or not task_tokens:
            return 0.0
        overlap = self._fuzzy_overlap(task_tokens, sk_tokens)
        return overlap / (len(task_tokens) + 1)

    def _semantic_score(self, task: str, skill: dict) -> float:
        emb = self._emb()
        if emb is None:
            return 0.0
        name = skill["name"]
        if name not in self._skill_vecs:
            text = f"{skill.get('description','')} {skill.get('tags','')}"
            self._skill_vecs[name] = emb.encode(text)
        return emb.cosine(emb.encode(task), self._skill_vecs[name])

    def rank(self, task: str) -> list[tuple[str, float]]:
        """يُعيد [(اسم_المهارة, النتيجة)] مرتّبة تنازلياً."""
        task_tokens = _tokens(task)
        scored = []
        for skill in self.index.tier1():
            kw = self._keyword_score(task_tokens, skill)
            sem = self._semantic_score(task, skill)
            # ترجيح: الكلمات المفتاحية أوثق، الدلالي يكمّل
            score = 0.6 * kw + 0.4 * sem
            scored.append((skill["name"], score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    def select(self, task: str, top: int = 2) -> list[str]:
        """يختار أسماء أفضل المهارات (فوق العتبة)."""
        ranked = self.rank(task)
        return [name for name, sc in ranked[:top] if sc >= self.min_score]

    def context_for(self, task: str, top: int = 2, max_chars: int = 4000) -> str:
        """
        يبني نص سياق المهارات المختارة (الطبقة 2) للحقن في عقل الوكيل.
        """
        names = self.select(task, top=top)
        if not names:
            return ""
        parts = ["### مهارات ذات صلة (استرشد بها):"]
        for name in names:
            content = self.index.activate(name)
            if content:
                parts.append(f"\n--- مهارة: {name} ---\n{content[:max_chars // max(1, len(names))]}")
        return "\n".join(parts)


if __name__ == "__main__":
    from skill_indexer import SkillIndex
    idx = SkillIndex(); idx.build()
    sel = SkillSelector(idx)

    names = sel.select("ابنِ موقع Next.js عربي بدعم RTL", top=2)
    print("للمهمة (Next.js):", names)
    assert "nextjs-rtl-pro" in names, names

    names2 = sel.select("احسب فاتورة الكهرباء لهذا الشهر", top=2)
    print("للمهمة (فاتورة):", names2)
    assert "electricity-bill-analyzer" in names2, names2

    ctx = sel.context_for("اكتب مقالاً تسويقياً بالعربية", top=1)
    assert "arabic-content-writer" in ctx or "محتوى" in ctx
    print("\n✅ skill_selector OK")
