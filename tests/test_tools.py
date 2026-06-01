"""اختبارات الأدوات الجديدة (file_str_replace, run_python) والحماية."""
import pytest
import tools as T


def test_registry_has_new_tools():
    assert "file_str_replace" in T.TOOLS
    assert "run_python" in T.TOOLS


def test_safe_path_blocks_escape():
    with pytest.raises(ValueError):
        T._safe_path("../../etc/passwd")


def test_file_str_replace_flow(tmp_path):
    # نكتب ملفاً داخل projects ثم نستبدل
    T.write_file("_pytest_sr/a.txt", "أهلاً يا عالم")
    r = T.file_str_replace("_pytest_sr/a.txt", "عالم", "عبّاس")
    assert "استُبدل" in r
    assert "عبّاس" in T.read_file("_pytest_sr/a.txt")
    # تنظيف
    T.run_shell("rm -rf _pytest_sr")


def test_file_str_replace_missing():
    assert "غير موجود" in T.file_str_replace("_nope/x.txt", "a", "b")


def test_file_str_replace_not_found():
    T.write_file("_pytest_sr2/b.txt", "نص ثابت")
    assert "لم يُعثر" in T.file_str_replace("_pytest_sr2/b.txt", "غائب", "x")
    T.run_shell("rm -rf _pytest_sr2")


def test_run_python_tool():
    out = T.call_tool("run_python", {"code": "print(2**10)"})
    assert "1024" in out


def test_unknown_tool():
    assert "غير معروفة" in T.call_tool("ghost", {})
