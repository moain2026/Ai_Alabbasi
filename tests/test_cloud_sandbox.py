"""اختبارات الـ Cloud Sandbox القابل للتبديل."""
from cloud_sandbox import CloudSandbox


def test_default_backend_is_local():
    sb = CloudSandbox()
    assert sb.backend == "local"


def test_local_execution():
    sb = CloudSandbox()
    out = sb.run("echo مرحبا && python3 -c 'print(6*7)'")
    assert "42" in out
    assert "exit=0" in out


def test_fallback_when_cloud_sdk_missing():
    # طلب daytona بلا SDK → يجب السقوط لـ local
    sb = CloudSandbox(backend="daytona")
    assert sb.backend == "local"
    sb2 = CloudSandbox(backend="e2b")
    assert sb2.backend == "local"


def test_has_module_detection():
    assert CloudSandbox._has_module("os") is True
    assert CloudSandbox._has_module("module_xyz_inexistent") is False


def test_timeout_handling():
    sb = CloudSandbox(timeout=1)
    out = sb.run("sleep 5")
    assert "المهلة" in out
