"""اختبارات منفّذ CodeAct."""
from code_act_executor import CodeActExecutor


def test_simple_print():
    ex = CodeActExecutor(timeout=10)
    out = ex.run("print('مرحبا')")
    assert "مرحبا" in out
    assert "exit=0" in out


def test_computation():
    ex = CodeActExecutor(timeout=10)
    out = ex.run("print(sum(range(101)))")
    assert "5050" in out


def test_empty_code():
    ex = CodeActExecutor()
    assert "لا يوجد كود" in ex.run("")


def test_timeout():
    ex = CodeActExecutor(timeout=1)
    out = ex.run("import time; time.sleep(5)")
    assert "المهلة" in out


def test_error_captured():
    ex = CodeActExecutor(timeout=10)
    out = ex.run("raise ValueError('خطأ متعمّد')")
    assert "exit=1" in out
    assert "ValueError" in out
