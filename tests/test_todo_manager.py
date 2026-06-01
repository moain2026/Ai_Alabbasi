"""اختبارات مدير المهام (Recitation)."""
import pytest
from todo_manager import TodoManager, PENDING, DONE


@pytest.fixture
def tm():
    t = TodoManager("مهمة اختبار", slug="_pytest_demo")
    yield t
    t.path.unlink(missing_ok=True)


def test_set_items_and_progress(tm):
    tm.set_items(["خطوة أ", "خطوة ب", "خطوة ج"])
    assert tm.progress() == (0, 3)


def test_complete(tm):
    tm.set_items(["خطوة أ", "خطوة ب"])
    assert tm.complete("خطوة أ") is True
    assert tm.progress() == (1, 2)
    # مهمة غير موجودة
    assert tm.complete("غير موجودة") is False


def test_all_done(tm):
    tm.set_items(["x"])
    assert tm.all_done() is False
    tm.complete("x")
    assert tm.all_done() is True


def test_persistence(tm):
    tm.set_items(["أ", "ب"])
    tm.complete("أ")
    # أعِد التحميل من الملف
    tm2 = TodoManager("مهمة اختبار", slug="_pytest_demo")
    assert tm2.progress() == (1, 2)


def test_recite_marks_next(tm):
    tm.set_items(["أولى", "ثانية"])
    tm.complete("أولى")
    r = tm.recite()
    assert DONE in r
    assert "← التالي" in r
    assert "ثانية" in r


def test_slugify_safe():
    t = TodoManager("مهمة / خطيرة ../..")
    assert "/" not in t.slug and ".." not in t.slug
    t.path.unlink(missing_ok=True)
