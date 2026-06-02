"""
📚 KNOWLEDGE — قاعدة المعرفة (RAG) + حلقة التعلّم
═══════════════════════════════════════════════════════════════
نظام معرفة خفيف يعتمد SQLite FTS5 (بحث نصي كامل، بدون تبعيات ثقيلة).

وظيفتان:
  1. RAG: تخزين وثائق التقنيات (React Native, Next.js...) واسترجاع
     المقاطع الأكثر صلة عند بناء مشروع → "التمرّس".
  2. التعلّم: حفظ كل تجربة ناجحة كـ "skill" يُسترجع لاحقاً.
"""
import sqlite3
import re
import sys
from pathlib import Path
from datetime import datetime

KDIR = Path(__file__).resolve().parent
DB_PATH = KDIR / "index" / "knowledge.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# ── بحث هجين اختياري (Phase 2) — سقوط آمن إن غاب ──
sys.path.insert(0, str(KDIR))
try:
    from embedder import Embedder            # noqa
    from hybrid_search import HybridSearch    # noqa
    _HYBRID_OK = True
except Exception:
    _HYBRID_OK = False

# ── فهرسة/اختيار المهارات (Phase 3) — سقوط آمن إن غاب ──
try:
    from skill_indexer import SkillIndex      # noqa
    from skill_selector import SkillSelector  # noqa
    _SKILLS_OK = True
except Exception:
    _SKILLS_OK = False


def _fts_query(text: str) -> str:
    """يحوّل نص المستخدم لاستعلام FTS5 آمن (OR بين الكلمات)."""
    words = re.findall(r"[\w\u0600-\u06FF]+", text)
    words = [w for w in words if len(w) > 1][:12]
    if not words:
        return '""'
    return " OR ".join(f'"{w}"' for w in words)


class Knowledge:
    def __init__(self, db_path: Path = DB_PATH, hybrid: bool = True):
        self.db = sqlite3.connect(str(db_path))
        self._init_schema()
        # مُضمِّن مشترك للبحث الهجين (يُهيّأ كسولاً)
        self.use_hybrid = hybrid and _HYBRID_OK
        self._embedder = None
        # فهرس/مُختار المهارات (يُهيّأ كسولاً)
        self._skill_sel = None

    def _emb(self):
        """يُهيّئ المُضمِّن عند أول حاجة (كسول)."""
        if self._embedder is None and self.use_hybrid:
            try:
                self._embedder = Embedder()
            except Exception:
                self.use_hybrid = False
        return self._embedder

    def _init_schema(self):
        c = self.db.cursor()
        # وثائق التقنيات (RAG)
        c.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5(
                topic, title, content, source,
                tokenize='unicode61'
            )
        """)
        # المهارات المتعلّمة (التعلّم الذاتي)
        c.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS skills USING fts5(
                name, task, approach, code, tags, created,
                tokenize='unicode61'
            )
        """)
        self.db.commit()

    # ── RAG: الوثائق ──────────────────────────────────────────
    def add_doc(self, topic: str, title: str, content: str, source: str = ""):
        self.db.execute(
            "INSERT INTO docs (topic,title,content,source) VALUES (?,?,?,?)",
            (topic, title, content, source),
        )
        self.db.commit()

    def search_docs(self, query: str, topic: str = None, limit: int = 4):
        q = _fts_query(query)
        sql = "SELECT topic,title,content,source FROM docs WHERE docs MATCH ?"
        params = [q]
        if topic:
            sql += " AND topic = ?"
            params.append(topic)
        sql += " ORDER BY rank LIMIT ?"
        params.append(limit)
        try:
            rows = self.db.execute(sql, params).fetchall()
        except sqlite3.OperationalError:
            return []
        return [{"topic": r[0], "title": r[1], "content": r[2], "source": r[3]} for r in rows]

    def search_docs_hybrid(self, query: str, topic: str = None, limit: int = 4):
        """
        بحث هجين: يجلب مرشّحين أوسع من FTS5 ثم يُعيد ترتيبهم دلالياً عبر RRF.
        يسقط تلقائياً إلى search_docs العادي إن لم يتوفّر المُضمِّن.
        """
        if not self.use_hybrid:
            return self.search_docs(query, topic=topic, limit=limit)
        emb = self._emb()
        if emb is None:
            return self.search_docs(query, topic=topic, limit=limit)

        # مرشّحون من FTS (للكلمات المفتاحية الدقيقة)
        fts_cands = self.search_docs(query, topic=topic, limit=limit * 4)

        # + كنس دلالي أوسع: نجلب وثائق إضافية (نفس الموضوع) ليفهمها المُضمِّن
        # حتى لو لم تطابق كلمات الاستعلام نصّياً (سدّ فجوة المرادفات).
        sql = "SELECT topic,title,content,source FROM docs"
        params = []
        if topic:
            sql += " WHERE topic = ?"
            params.append(topic)
        sql += " LIMIT ?"
        params.append(200)   # حدّ معقول لإبقاء الترميز سريعاً
        try:
            extra = self.db.execute(sql, params).fetchall()
        except sqlite3.OperationalError:
            extra = []
        sem_cands = [{"topic": r[0], "title": r[1], "content": r[2], "source": r[3]} for r in extra]

        # دمج المرشّحين مع إزالة التكرار (حسب العنوان+المحتوى)
        seen = set()
        candidates = []
        for c in fts_cands + sem_cands:
            key = (c["title"], c["content"][:80])
            if key not in seen:
                seen.add(key)
                candidates.append(c)

        if len(candidates) <= limit:
            return candidates[:limit]

        # أعطِ كل مرشّح معرّفاً ثابتاً وفهرسه دلالياً
        for i, c in enumerate(candidates):
            c["_id"] = str(i)
        try:
            hs = HybridSearch(emb)
            hs.index(candidates, id_key="_id", text_key="content")
            # ترتيب FTS الأصلي (المرشّحون الأوائل فقط لهم رتبة FTS)
            fts_ids = [c["_id"] for c in candidates[: len(fts_cands)]]
            ranked = hs.search(query, fts_ids=fts_ids, limit=limit)
        except Exception:
            ranked = candidates[:limit]
        for c in ranked:
            c.pop("_id", None)
        return ranked

    # ── التعلّم: المهارات ─────────────────────────────────────
    def add_skill(self, name, task, approach, code="", tags=""):
        self.db.execute(
            "INSERT INTO skills (name,task,approach,code,tags,created) VALUES (?,?,?,?,?,?)",
            (name, task, approach, code, tags, datetime.now().isoformat(timespec="seconds")),
        )
        self.db.commit()

    def search_skills(self, query: str, limit: int = 3):
        q = _fts_query(query)
        try:
            rows = self.db.execute(
                "SELECT name,task,approach,code,tags,created FROM skills WHERE skills MATCH ? ORDER BY rank LIMIT ?",
                (q, limit),
            ).fetchall()
        except sqlite3.OperationalError:
            return []
        return [{"name": r[0], "task": r[1], "approach": r[2], "code": r[3],
                 "tags": r[4], "created": r[5]} for r in rows]

    def stats(self):
        d = self.db.execute("SELECT count(*) FROM docs").fetchone()[0]
        s = self.db.execute("SELECT count(*) FROM skills").fetchone()[0]
        topics = [r[0] for r in self.db.execute("SELECT DISTINCT topic FROM docs").fetchall()]
        backend = "fts5-only"
        if self.use_hybrid:
            emb = self._emb()
            backend = f"hybrid ({emb.backend})" if emb else "fts5-only"
        return {"docs": d, "skills": s, "topics": topics, "search": backend}

    def _skill_selector(self):
        """يُهيّئ مُختار المهارات عند أول حاجة (كسول)."""
        if self._skill_sel is None and _SKILLS_OK:
            try:
                idx = SkillIndex(); idx.build()
                self._skill_sel = SkillSelector(idx, embedder=self._emb())
            except Exception:
                self._skill_sel = False   # علامة فشل لتجنّب إعادة المحاولة
        return self._skill_sel or None

    def context_for(self, task: str, topic: str = None) -> str:
        """يبني نص سياق (مهارات + RAG + خبرات) لحقنه في عقل الوكيل قبل مهمة."""
        parts = []
        # 🎯 مهارات منتقاة (Progressive Disclosure — الطبقة 2)
        sel = self._skill_selector()
        if sel:
            skill_ctx = sel.context_for(task, top=2)
            if skill_ctx:
                parts.append(skill_ctx)
        skills = self.search_skills(task)
        if skills:
            parts.append("### خبرات سابقة ذات صلة (من تجاربك):")
            for s in skills:
                parts.append(f"- [{s['name']}] {s['approach']}")
        docs = self.search_docs_hybrid(task, topic=topic)
        if docs:
            parts.append("\n### مراجع تقنية ذات صلة:")
            for d in docs:
                snippet = d["content"][:600]
                parts.append(f"**{d['title']}** ({d['topic']}):\n{snippet}")
        return "\n".join(parts) if parts else ""


if __name__ == "__main__":
    k = Knowledge()
    print("📚 إحصائيات المعرفة:", k.stats())
