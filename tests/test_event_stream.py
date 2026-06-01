"""اختبارات مجرى الأحداث."""
from event_stream import EventStream, EventType, Event


def test_add_and_len():
    es = EventStream()
    assert len(es) == 0
    es.message("user", "مرحبا")
    es.action("write_file", {"path": "a.txt"})
    assert len(es) == 2


def test_bool_truthy_even_when_empty():
    # مهم: المجرى الفارغ يجب أن يبقى صادقاً (تفادي القصر الدائري)
    es = EventStream()
    assert bool(es) is True


def test_by_type():
    es = EventStream()
    es.action("t1", {})
    es.action("t2", {})
    es.observation("t1", "ok")
    assert len(es.by_type(EventType.ACTION)) == 2
    assert len(es.by_type(EventType.OBSERVATION)) == 1


def test_shortcuts_set_correct_type():
    es = EventStream()
    es.message("m", 1); es.plan("p", 2); es.knowledge("k", 3); es.other("o", 4)
    types = [e.type for e in es.all()]
    assert types == [EventType.MESSAGE, EventType.PLAN, EventType.KNOWLEDGE, EventType.OTHER]


def test_max_events_cap():
    es = EventStream(max_events=5)
    for i in range(10):
        es.other("x", i)
    assert len(es) == 5
    # نُبقي الأحدث
    assert es.last(1)[0].data == 9


def test_to_json_sorted_keys():
    es = EventStream()
    es.message("user", "hi")
    j = es.to_json()
    # sort_keys=True يضع data قبل name قبل type أبجدياً
    assert j.index('"data"') < j.index('"type"')


def test_render_context_contains_payload():
    es = EventStream()
    es.action("write_file", {"path": "index.html"})
    ctx = es.render_context()
    assert "write_file" in ctx and "index.html" in ctx


def test_event_to_dict():
    ev = Event(type=EventType.ACTION, name="x", data={"a": 1}, step=3)
    d = ev.to_dict()
    assert d["type"] == "action" and d["step"] == 3
