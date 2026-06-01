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
from pathlib import Path
from datetime import datetime

KDIR = Path(__file__).resolve().parent
DB_PATH = KDIR / "index" / "knowledge.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _fts_query(text: str) -> str:
    """يحوّل نص المستخدم لاستعلام FTS5 آمن (OR بين الكلمات)."""
    words = re.findall(r"[\w\u0600-\u06FF]+", text)
    words = [w for w in words if len(w) > 1][:12]
    if not words:
        return '""'
    return " OR ".join(f'"{w}"' for w in words)


class Knowledge:
    def __init__(self, db_path: Path = DB_PATH):
        self.db = sqlite3.connect(str(db_path))
        self._init_schema()

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
        return {"docs": d, "skills": s, "topics": topics}

    def context_for(self, task: str, topic: str = None) -> str:
        """يبني نص سياق (RAG + skills) لحقنه في عقل الوكيل قبل مهمة."""
        parts = []
        skills = self.search_skills(task)
        if skills:
            parts.append("### خبرات سابقة ذات صلة (من تجاربك):")
            for s in skills:
                parts.append(f"- [{s['name']}] {s['approach']}")
        docs = self.search_docs(task, topic=topic)
        if docs:
            parts.append("\n### مراجع تقنية ذات صلة:")
            for d in docs:
                snippet = d["content"][:600]
                parts.append(f"**{d['title']}** ({d['topic']}):\n{snippet}")
        return "\n".join(parts) if parts else ""


if __name__ == "__main__":
    k = Knowledge()
    print("📚 إحصائيات المعرفة:", k.stats())
