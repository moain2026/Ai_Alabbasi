"""اختبارات المخطّط (بعقل وهمي بلا مفتاح)."""
from planner import Planner, _extract_json


class FakeBrain:
    def __init__(self, plan_reply=None, reflect_reply=None):
        self.plan_reply = plan_reply or '{"steps": ["خطوة1", "خطوة2"]}'
        self.reflect_reply = reflect_reply or '{"valid": true, "revised_steps": []}'

    def think(self, messages, max_tokens=600):
        if "مراجع" in messages[0]["content"]:
            return self.reflect_reply
        return self.plan_reply


def test_make_plan():
    p = Planner(FakeBrain())
    assert p.make_plan("مهمة") == ["خطوة1", "خطوة2"]


def test_make_plan_caps_steps():
    big = '{"steps": [' + ",".join(f'"s{i}"' for i in range(20)) + "]}"
    p = Planner(FakeBrain(plan_reply=big), max_steps=5)
    assert len(p.make_plan("مهمة")) == 5


def test_make_plan_handles_bad_json():
    p = Planner(FakeBrain(plan_reply="ليس JSON إطلاقاً"))
    assert p.make_plan("مهمة") == []


def test_reflect_valid():
    p = Planner(FakeBrain())
    ok, steps = p.reflect("مهمة", ["خطوة1"], "نُفّذت خطوة1")
    assert ok is True


def test_reflect_revises():
    fb = FakeBrain(reflect_reply='{"valid": false, "revised_steps": ["جديدة1", "جديدة2"]}')
    p = Planner(fb)
    ok, steps = p.reflect("مهمة", ["قديمة"], "ملخص")
    assert ok is False
    assert steps == ["جديدة1", "جديدة2"]


def test_extract_json_embedded():
    assert _extract_json('بعض النص {"a": 1} نص آخر') == {"a": 1}
    assert _extract_json("لا JSON") is None
