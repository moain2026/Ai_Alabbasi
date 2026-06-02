"""اختبارات فهرس المهارات (الطبقة 1 + التفعيل)."""
from skill_indexer import SkillIndex, parse_frontmatter


def test_parse_frontmatter():
    text = '---\nname: test\ndescription: "وصف"\ntags: a, b\n---\n# عنوان'
    meta = parse_frontmatter(text)
    assert meta["name"] == "test"
    assert meta["description"] == "وصف"
    assert meta["tags"] == "a, b"


def test_parse_frontmatter_no_block():
    assert parse_frontmatter("# لا frontmatter") == {}


def test_build_finds_seed_skills():
    idx = SkillIndex()
    n = idx.build()
    assert n >= 5
    names = [s["name"] for s in idx.tier1()]
    assert "nextjs-rtl-pro" in names
    assert "electricity-bill-analyzer" in names


def test_tier1_is_lightweight():
    idx = SkillIndex(); idx.build()
    for s in idx.tier1():
        # الطبقة 1: اسم + وصف + وسوم فقط (لا محتوى كامل)
        assert set(s.keys()) == {"name", "description", "tags", "source"}


def test_activate_returns_full_content():
    idx = SkillIndex(); idx.build()
    full = idx.activate("moain-personal-style")
    assert "أسلوب معين" in full
    assert len(full) > 200


def test_activate_unknown_returns_empty():
    idx = SkillIndex(); idx.build()
    assert idx.activate("لا-توجد") == ""


def test_get():
    idx = SkillIndex(); idx.build()
    s = idx.get("arabic-content-writer")
    assert s is not None and s["name"] == "arabic-content-writer"
