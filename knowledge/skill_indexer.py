"""
🗂️ SKILL INDEXER — فهرسة المهارات (Progressive Disclosure — الطبقة 1)
═══════════════════════════════════════════════════════════════
نمط Manus للكشف التدريجي عن المهارات على 3 طبقات:
  • الطبقة 1 (Discovery ~80 رمز): الاسم + الوصف فقط — تُحمَّل دائماً.
  • الطبقة 2 (Activation ~2000 رمز): محتوى SKILL.md كاملاً — عند الاختيار.
  • الطبقة 3 (Execution): ملفات/سكربتات إضافية — عند الحاجة فعلاً.

هذا الفهرس يقرأ frontmatter كل SKILL.md ويبني فهرس الطبقة 1 الخفيف،
ويوفّر تحميل الطبقة 2 عند الطلب.

يبحث في مجلّدين:
  knowledge/skills_seed/**/SKILL.md       (مهارات البذرة المرافقة)
  knowledge/external_skills/**/SKILL.md   (مهارات خارجية إن وُجدت)

بلا اعتماديات خارجية.
"""
from __future__ import annotations

from pathlib import Path

KDIR = Path(__file__).resolve().parent
SEED_DIR = KDIR / "skills_seed"
EXTERNAL_DIR = KDIR / "external_skills"


def parse_frontmatter(text: str) -> dict:
    """
    يستخرج حقول frontmatter البسيطة (key: value) بين سطرَي ---.
    لا يعتمد PyYAML — تحليل خفيف يكفي لحقول المهارات.
    """
    meta: dict[str, str] = {}
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return meta
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip().lower()] = v.strip().strip('"').strip("'")
    return meta


class SkillIndex:
    """
    فهرس مهارات خفيف (الطبقة 1).

    الاستخدام:
        idx = SkillIndex()
        idx.build()
        for s in idx.tier1():
            print(s["name"], s["description"])
        full = idx.activate("nextjs-rtl-pro")   # الطبقة 2
    """

    def __init__(self, dirs: list[Path] | None = None):
        self.dirs = dirs or [SEED_DIR, EXTERNAL_DIR]
        self._skills: dict[str, dict] = {}

    def build(self, max_skills: int = 1000) -> int:
        """يفهرس كل ملفات SKILL.md المتاحة (الطبقة 1). يُعيد العدد."""
        self._skills.clear()
        count = 0
        for base in self.dirs:
            if not base.exists():
                continue
            for sk in sorted(base.rglob("SKILL.md")):
                if count >= max_skills:
                    break
                try:
                    text = sk.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                meta = parse_frontmatter(text)
                name = meta.get("name") or sk.parent.name
                entry = {
                    "name": name,
                    "description": meta.get("description", "")[:200],
                    "tags": meta.get("tags", ""),
                    "tier": meta.get("tier", "1"),
                    "path": str(sk),
                    "source": "seed" if base == SEED_DIR else "external",
                }
                self._skills[name] = entry
                count += 1
        return count

    def tier1(self) -> list[dict]:
        """يُعيد بطاقات الطبقة 1 (اسم + وصف + وسوم) — خفيفة."""
        return [
            {"name": s["name"], "description": s["description"],
             "tags": s["tags"], "source": s["source"]}
            for s in self._skills.values()
        ]

    def get(self, name: str) -> dict | None:
        return self._skills.get(name)

    def activate(self, name: str) -> str:
        """الطبقة 2: يُعيد محتوى SKILL.md كاملاً للمهارة المختارة."""
        s = self._skills.get(name)
        if not s:
            return ""
        try:
            return Path(s["path"]).read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""

    def __len__(self) -> int:
        return len(self._skills)


if __name__ == "__main__":
    idx = SkillIndex()
    n = idx.build()
    print(f"🗂️ فُهرست {n} مهارة (الطبقة 1):")
    for s in idx.tier1():
        print(f"  • {s['name']}: {s['description'][:50]}")
    assert n >= 5, f"يُتوقّع 5 مهارات بذرة على الأقل، وُجد {n}"
    # تفعيل الطبقة 2
    full = idx.activate("moain-personal-style")
    assert "أسلوب معين" in full
    print("\n✅ skill_indexer OK")
