"""اختبارات المُضمِّن (Embedder)."""
from embedder import Embedder, _tokenize


def test_encode_returns_normalized_vector():
    emb = Embedder(dim=128)
    v = emb.encode("بناء تطبيق")
    assert len(v) == emb.dim
    # متجه مُطبّع: طوله ≈ 1 (إلا الفارغ)
    norm = sum(x * x for x in v) ** 0.5
    assert abs(norm - 1.0) < 1e-6


def test_empty_text_zero_vector():
    emb = Embedder(dim=64)
    v = emb.encode("")
    assert all(x == 0.0 for x in v)


def test_semantic_similarity_close_vs_far():
    emb = Embedder()
    v1 = emb.encode("تطبيق React Native للجوال")
    v2 = emb.encode("React Native تطبيق الموبايل")
    v3 = emb.encode("وصفة طبخ يمنية")
    assert Embedder.cosine(v1, v2) > Embedder.cosine(v1, v3)


def test_cosine_edge_cases():
    assert Embedder.cosine([], []) == 0.0
    assert Embedder.cosine([1, 0], [1, 0, 0]) == 0.0  # أطوال مختلفة
    assert abs(Embedder.cosine([1, 0], [1, 0]) - 1.0) < 1e-9


def test_tokenize_handles_arabic_and_english():
    toks = _tokenize("Build تطبيق Mobile الجوال")
    assert "build" in toks and "تطبيق" in toks and "الجوال" in toks


def test_backend_is_set():
    emb = Embedder()
    assert emb.backend in ("hashing", "sentence-transformers")
