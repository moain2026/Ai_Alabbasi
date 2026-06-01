"""اختبارات البحث الهجين + RRF."""
from embedder import Embedder
from hybrid_search import HybridSearch, reciprocal_rank_fusion


def test_rrf_basic():
    # عنصر يتصدّر القائمتين يجب أن يفوز
    f = reciprocal_rank_fusion([["a", "b", "c"], ["a", "c", "b"]])
    assert f["a"] > f["b"]
    assert f["a"] > f["c"]


def test_rrf_symmetric():
    f = reciprocal_rank_fusion([["a", "b"], ["b", "a"]])
    assert abs(f["a"] - f["b"]) < 1e-9


def test_hybrid_relevance():
    docs = [
        {"id": "1", "content": "بناء تطبيق جوال بـ React Native"},
        {"id": "2", "content": "تصميم واجهات ويب Next.js"},
        {"id": "3", "content": "وصفات الطبخ اليمني"},
    ]
    hs = HybridSearch(Embedder())
    hs.index(docs)
    res = hs.search("تطبيق موبايل React Native", limit=2)
    ids = [r["id"] for r in res]
    assert "1" in ids
    assert "3" not in ids


def test_hybrid_combines_fts():
    docs = [{"id": str(i), "content": f"محتوى رقم {i}"} for i in range(5)]
    hs = HybridSearch(Embedder())
    hs.index(docs)
    # FTS يفضّل المستند 4؛ يجب أن يظهر في النتائج
    res = hs.search("محتوى", fts_ids=["4", "0"], limit=3)
    assert "4" in [r["id"] for r in res]


def test_empty_index_returns_empty():
    hs = HybridSearch(Embedder())
    assert hs.search("أي شيء") == []
