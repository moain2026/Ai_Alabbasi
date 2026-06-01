"""
🛠️ TOOLS — أدوات الوكيل (يده التي ينفّذ بها)
═══════════════════════════════════════════════════════════════
كل أداة دالة بسيطة ترجع نصاً (النتيجة أو الخطأ).
الوكيل يستدعيها عبر اسمها + معاملاتها.
"""
import os
import subprocess
import json
import urllib.request
from pathlib import Path

# جذر المشاريع — الوكيل يعمل داخله فقط (حماية)
PROJECTS_ROOT = Path(__file__).resolve().parent.parent / "projects"
PROJECTS_ROOT.mkdir(exist_ok=True)


def _safe_path(path: str) -> Path:
    """يمنع الخروج خارج مجلد المشاريع."""
    p = (PROJECTS_ROOT / path).resolve()
    if not str(p).startswith(str(PROJECTS_ROOT)):
        raise ValueError(f"مسار غير مسموح (خارج projects/): {path}")
    return p


def run_shell(command: str, timeout: int = 120) -> str:
    """ينفّذ أمر shell داخل مجلد المشاريع ويرجّع المخرجات."""
    try:
        r = subprocess.run(
            command, shell=True, cwd=str(PROJECTS_ROOT),
            capture_output=True, text=True, timeout=timeout,
        )
        out = (r.stdout or "")[-4000:]
        err = (r.stderr or "")[-2000:]
        code = r.returncode
        result = f"[exit={code}]\n"
        if out:
            result += f"STDOUT:\n{out}\n"
        if err:
            result += f"STDERR:\n{err}\n"
        return result.strip() or f"[exit={code}] (لا مخرجات)"
    except subprocess.TimeoutExpired:
        return f"⏱️ انتهى الوقت ({timeout}s) — الأمر طويل جداً."
    except Exception as e:
        return f"❌ خطأ في التنفيذ: {e}"


def write_file(path: str, content: str) -> str:
    """يكتب ملفاً (ينشئ المجلدات تلقائياً)."""
    try:
        p = _safe_path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"✅ كُتب: {path} ({len(content)} حرف)"
    except Exception as e:
        return f"❌ فشل الكتابة: {e}"


def read_file(path: str) -> str:
    """يقرأ ملفاً."""
    try:
        p = _safe_path(path)
        if not p.exists():
            return f"❌ غير موجود: {path}"
        return p.read_text(encoding="utf-8")[:8000]
    except Exception as e:
        return f"❌ فشل القراءة: {e}"


def list_dir(path: str = ".") -> str:
    """يعرض محتويات مجلد."""
    try:
        p = _safe_path(path)
        if not p.exists():
            return f"❌ غير موجود: {path}"
        items = []
        for x in sorted(p.iterdir()):
            items.append(f"{'📁' if x.is_dir() else '📄'} {x.name}")
        return "\n".join(items) or "(فارغ)"
    except Exception as e:
        return f"❌ فشل: {e}"


def web_search(query: str) -> str:
    """بحث ويب بسيط عبر DuckDuckGo (بدون مفتاح)."""
    try:
        url = "https://api.duckduckgo.com/?q=" + urllib.parse.quote(query) + "&format=json&no_html=1"
        req = urllib.request.Request(url, headers={"User-Agent": "Ai-Alabbasi/1.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            d = json.loads(r.read().decode("utf-8"))
        out = d.get("AbstractText", "") or d.get("Answer", "")
        topics = d.get("RelatedTopics", [])[:5]
        lines = [out] if out else []
        for t in topics:
            if isinstance(t, dict) and t.get("Text"):
                lines.append("• " + t["Text"])
        return "\n".join(lines) or "(لا نتائج واضحة — جرّب صياغة أخرى)"
    except Exception as e:
        return f"❌ فشل البحث: {e}"


def make_dir(path: str) -> str:
    """ينشئ مجلداً."""
    try:
        p = _safe_path(path)
        p.mkdir(parents=True, exist_ok=True)
        return f"✅ أُنشئ المجلد: {path}"
    except Exception as e:
        return f"❌ فشل: {e}"


def append_file(path: str, content: str) -> str:
    """يضيف لنهاية ملف (دون حذف المحتوى)."""
    try:
        p = _safe_path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(content)
        return f"✅ أُضيف إلى: {path} ({len(content)} حرف)"
    except Exception as e:
        return f"❌ فشل: {e}"


# سجل الأدوات — الوكيل يقرأ منه
TOOLS = {
    "run_shell":  {"fn": run_shell,  "args": ["command"], "desc": "نفّذ أمر terminal داخل projects/ (yarn/npm/git/python3 متاحة)"},
    "write_file": {"fn": write_file, "args": ["path", "content"], "desc": "اكتب/أنشئ ملفاً (يستبدل المحتوى)"},
    "append_file":{"fn": append_file,"args": ["path", "content"], "desc": "أضف لنهاية ملف"},
    "read_file":  {"fn": read_file,  "args": ["path"], "desc": "اقرأ ملفاً"},
    "list_dir":   {"fn": list_dir,   "args": ["path"], "desc": "اعرض محتويات مجلد"},
    "make_dir":   {"fn": make_dir,   "args": ["path"], "desc": "أنشئ مجلداً"},
    "web_search": {"fn": web_search, "args": ["query"], "desc": "ابحث في الويب"},
}

import urllib.parse  # noqa (مستخدم في web_search)


def tools_spec() -> str:
    """وصف الأدوات للنموذج."""
    lines = []
    for name, t in TOOLS.items():
        lines.append(f"- {name}({', '.join(t['args'])}): {t['desc']}")
    return "\n".join(lines)


def call_tool(name: str, args: dict) -> str:
    if name not in TOOLS:
        return f"❌ أداة غير معروفة: {name}"
    try:
        return TOOLS[name]["fn"](**args)
    except TypeError as e:
        return f"❌ معاملات خاطئة لـ {name}: {e}"


if __name__ == "__main__":
    print("🛠️ الأدوات المتاحة:\n" + tools_spec())
    print("\n--- اختبار ---")
    print(write_file("test/hello.txt", "مرحبا من الوكيل"))
    print(read_file("test/hello.txt"))
    print(list_dir("test"))
    print(run_shell("echo 'الأدوات تعمل' && pwd"))
