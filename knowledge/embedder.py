"""
🔢 EMBEDDER — محرّك تمثيلات متجهية (Embeddings) محلي
═══════════════════════════════════════════════════════════════
يحوّل النص إلى متجه أرقام لقياس التشابه الدلالي (semantic).

القاعدة الذهبية (أقل اعتماديات):
  • إن توفّر sentence-transformers → نستخدم all-MiniLM-L6-v2 (جودة عالية).
  • وإلا → نسقط لمُضمِّن خفيف نقي بايثون (hashing bag-of-words)
    يعمل بلا أي اعتماديات — جودة أقل لكن وظيفي وسريع.

كلا المسارين يُرجعان متجهاً مُطبّعاً (norm=1) لاستخدام التشابه الجيبي.
"""
from __future__ import annotations

import hashlib
import math
import re


def _tokenize(text: str) -> list[str]:
    """تقطيع بسيط يدعم العربية والإنجليزية."""
    return [w.lower() for w in re.findall(r"[\w\u0600-\u06FF]+", text or "") if len(w) > 1]


class Embedder:
    """
    مُضمِّن نصوص مع سقوط آمن.

    الاستخدام:
        emb = Embedder()
        v = emb.encode("بناء تطبيق React Native")
        sim = Embedder.cosine(v1, v2)
    """

    def __init__(self, dim: int = 256, model_name: str = "all-MiniLM-L6-v2"):
        self.dim = dim
        self.model_name = model_name
        self._model = None
        self.backend = "hashing"   # الافتراضي
        self._try_load_transformer()

    def _try_load_transformer(self) -> None:
        """يحاول تحميل sentence-transformers إن توفّر (اختياري)."""
        try:
            from sentence_transformers import SentenceTransformer  # noqa
            self._model = SentenceTransformer(self.model_name)
            self.dim = self._model.get_sentence_embedding_dimension()
            self.backend = "sentence-transformers"
        except Exception:
            self._model = None
            self.backend = "hashing"

    # ── الترميز ───────────────────────────────────────────────
    def encode(self, text: str) -> list[float]:
        """يُرجع متجهاً مُطبّعاً للنص."""
        if self._model is not None:
            vec = self._model.encode(text, normalize_embeddings=True)
            return [float(x) for x in vec]
        return self._hash_encode(text)

    def _hash_encode(self, text: str) -> list[float]:
        """
        مُضمِّن خفيف: كل كلمة تُسقَط على بُعد عبر التجزئة (hashing trick)،
        مع وزن تكرار، ثم نُطبّع المتجه.
        """
        vec = [0.0] * self.dim
        toks = _tokenize(text)
        if not toks:
            return vec
        for tok in toks:
            h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dim
            sign = 1.0 if (h >> 8) % 2 == 0 else -1.0
            vec[idx] += sign
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

    # ── التشابه ───────────────────────────────────────────────
    @staticmethod
    def cosine(a: list[float], b: list[float]) -> float:
        """التشابه الجيبي بين متجهين (يفترض أنهما مُطبّعان لكن آمن عموماً)."""
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)


if __name__ == "__main__":
    emb = Embedder()
    print(f"🔢 backend: {emb.backend} (dim={emb.dim})")
    v1 = emb.encode("بناء تطبيق React Native للجوال")
    v2 = emb.encode("تطوير تطبيق موبايل بـ React Native")
    v3 = emb.encode("وصفة طبخ الكبسة اليمنية")
    s12 = Embedder.cosine(v1, v2)
    s13 = Embedder.cosine(v1, v3)
    print(f"تشابه (متقارب): {s12:.3f}")
    print(f"تشابه (بعيد):   {s13:.3f}")
    assert s12 > s13, "النصان المتقاربان يجب أن يكونا أكثر تشابهاً"
    print("✅ embedder OK")
