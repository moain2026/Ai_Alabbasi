"""
🔎 HYBRID SEARCH — بحث هجين (FTS5 نصّي + متجهات دلالية) عبر RRF
═══════════════════════════════════════════════════════════════
يدمج نتيجتين:
  1. البحث النصّي الكامل (FTS5) — دقيق للكلمات المفتاحية.
  2. البحث الدلالي (Embeddings) — يفهم المعنى والمرادفات.

الدمج عبر RRF (Reciprocal Rank Fusion):
    score(d) = Σ  1 / (k + rank_i(d))
حيث k ثابت (افتراضي 60). يكافئ المستندات التي تتصدّر أيّ قائمة.

التصميم: مستقلّ — يأخذ نتائج FTS الجاهزة + دالة ترميز، فيُعيد ترتيباً مدموجاً.
بلا اعتماديات خارجية (يعمل مع embedder الخفيف).
"""
from __future__ import annotations

from typing import Callable


def reciprocal_rank_fusion(
    ranked_lists: list[list[str]], k: int = 60
) -> dict[str, float]:
    """
    يدمج عدة قوائم مرتّبة (بمعرّفات) عبر RRF ويُرجع {id: score}.
    ranked_lists: كل عنصر قائمة معرّفات مرتّبة تنازلياً بالأهمية.
    """
    scores: dict[str, float] = {}
    for lst in ranked_lists:
        for rank, doc_id in enumerate(lst):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    return scores


class HybridSearch:
    """
    بحث هجين فوق مجموعة وثائق.

    الاستخدام:
        hs = HybridSearch(embedder)
        hs.index(docs)            # docs: list[dict] فيها id + content
        results = hs.search("استعلام", fts_ids=[...], limit=4)

    fts_ids: ترتيب نتائج FTS5 (معرّفات) القادم من Knowledge — اختياري.
    """

    def __init__(self, embedder, k: int = 60):
        self.embedder = embedder
        self.k = k
        self._docs: dict[str, dict] = {}
        self._vectors: dict[str, list[float]] = {}

    def index(self, docs: list[dict], id_key: str = "id", text_key: str = "content") -> None:
        """يبني فهرس المتجهات للوثائق."""
        for d in docs:
            doc_id = str(d.get(id_key))
            self._docs[doc_id] = d
            self._vectors[doc_id] = self.embedder.encode(d.get(text_key, ""))

    def _semantic_rank(self, query: str, limit: int) -> list[str]:
        """يرتّب الوثائق دلالياً حسب التشابه الجيبي."""
        if not self._vectors:
            return []
        qv = self.embedder.encode(query)
        scored = [
            (doc_id, self.embedder.cosine(qv, vec))
            for doc_id, vec in self._vectors.items()
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [doc_id for doc_id, _ in scored[:limit]]

    def search(
        self, query: str, fts_ids: list[str] | None = None, limit: int = 4
    ) -> list[dict]:
        """
        يُجري بحثاً هجيناً ويُعيد أفضل الوثائق (قواميس كاملة).
        يدمج ترتيب FTS (إن مُرّر) مع الترتيب الدلالي عبر RRF.
        """
        sem_ids = self._semantic_rank(query, limit * 3)
        ranked_lists = [sem_ids]
        if fts_ids:
            ranked_lists.append([str(i) for i in fts_ids])
        fused = reciprocal_rank_fusion(ranked_lists, k=self.k)
        best = sorted(fused.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [self._docs[doc_id] for doc_id, _ in best if doc_id in self._docs]


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from embedder import Embedder

    docs = [
        {"id": "1", "content": "بناء تطبيق جوال بـ React Native و Expo"},
        {"id": "2", "content": "تصميم واجهات ويب بـ Next.js و Tailwind"},
        {"id": "3", "content": "تطوير تطبيقات الموبايل والهواتف الذكية"},
        {"id": "4", "content": "وصفات الطبخ اليمني التقليدي"},
    ]
    hs = HybridSearch(Embedder())
    hs.index(docs)
    # محاكاة ترتيب FTS يفضّل المستند 1
    res = hs.search("تطبيق موبايل React Native", fts_ids=["1", "3"], limit=2)
    ids = [r["id"] for r in res]
    print("النتائج:", ids)
    assert "1" in ids, ids
    assert "4" not in ids, "الوصفات لا علاقة لها"
    # اختبار RRF مباشرة
    f = reciprocal_rank_fusion([["a", "b"], ["b", "a"]])
    assert abs(f["a"] - f["b"]) < 1e-9, "a و b متماثلان في الترتيب المعكوس"
    print("✅ hybrid_search OK")
