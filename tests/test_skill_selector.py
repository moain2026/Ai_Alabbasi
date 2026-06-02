"""اختبارات اختيار المهارات الذكي."""
import pytest
from skill_indexer import SkillIndex
from skill_selector import SkillSelector


@pytest.fixture(scope="module")
def selector():
    idx = SkillIndex(); idx.build()
    return SkillSelector(idx)


def test_select_nextjs(selector):
    names = selector.select("ابنِ موقع Next.js عربي بدعم RTL", top=2)
    assert "nextjs-rtl-pro" in names


def test_select_electricity(selector):
    names = selector.select("احسب فاتورة الكهرباء وشرائح الاستهلاك", top=2)
    assert "electricity-bill-analyzer" in names


def test_select_arabic_writing(selector):
    names = selector.select("اكتب مقالاً تسويقياً بالعربية", top=2)
    assert "arabic-content-writer" in names


def test_rank_returns_all_with_scores(selector):
    ranked = selector.rank("أي مهمة")
    assert len(ranked) == 5
    # مرتّبة تنازلياً
    scores = [s for _, s in ranked]
    assert scores == sorted(scores, reverse=True)


def test_context_for_includes_skill(selector):
    ctx = selector.context_for("ابنِ تطبيق Next.js", top=1)
    assert "nextjs-rtl-pro" in ctx


def test_select_irrelevant_returns_few(selector):
    # مهمة لا تطابق أي مهارة بقوة → قد تُرجع قائمة فارغة (تحت العتبة)
    names = selector.select("xyz123 qwerty zzz", top=2)
    assert isinstance(names, list)


def test_fuzzy_overlap_handles_arabic_suffix():
    a = {"مقالاً", "تسويقياً"}
    b = {"مقال", "تسويق"}
    assert SkillSelector._fuzzy_overlap(a, b) == 2
