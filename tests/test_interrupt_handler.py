"""اختبارات معالج المقاطعة."""
from interrupt_handler import InterruptHandler


def test_no_request_initially():
    ih = InterruptHandler()
    assert ih.requested() is False


def test_stop_request():
    ih = InterruptHandler()
    ih.interrupt()
    assert ih.requested() is True
    assert ih.consume() is None
    assert ih.requested() is False


def test_guidance_request():
    ih = InterruptHandler()
    ih.interrupt("ركّز على الأمان")
    assert ih.requested() is True
    assert ih.consume() == "ركّز على الأمان"
    assert ih.requested() is False


def test_clear():
    ih = InterruptHandler()
    ih.interrupt("x")
    ih.clear()
    assert ih.requested() is False


def test_empty_guidance_treated_as_stop():
    ih = InterruptHandler()
    ih.interrupt("   ")
    assert ih.consume() is None
