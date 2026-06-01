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


def file_str_replace(path: str, old_str: str, new_str: str) -> str:
    """
    استبدال نصّي جراحي داخل ملف (نمط Manus str_replace).
    يستبدل أول ظهور فقط لـ old_str بـ new_str — يفشل إن لم يوجد أو تكرّر.
    مفيد لتعديل todo.md (Recitation) وللتعديلات الدقيقة دون إعادة كتابة الملف.
    """
    try:
        p = _safe_path(path)
        if not p.exists():
            return f"❌ غير موجود: {path}"
        text = p.read_text(encoding="utf-8")
        count = text.count(old_str)
        if count == 0:
            return f"❌ لم يُعثر على النص المطلوب في: {path}"
        if count > 1:
            return f"❌ النص متكرر {count} مرات في {path} — وسّع old_str ليكون فريداً."
        new_text = text.replace(old_str, new_str, 1)
        p.write_text(new_text, encoding="utf-8")
        return f"✅ استُبدل في: {path} ({len(old_str)}→{len(new_str)} حرف)"
    except Exception as e:
        return f"❌ فشل الاستبدال: {e}"


# سجل الأدوات — الوكيل يقرأ منه
TOOLS = {
    "run_shell":  {"fn": run_shell,  "args": ["command"], "desc": "نفّذ أمر terminal داخل projects/ (yarn/npm/git/python3 متاحة)"},
    "write_file": {"fn": write_file, "args": ["path", "content"], "desc": "اكتب/أنشئ ملفاً (يستبدل المحتوى)"},
    "append_file":{"fn": append_file,"args": ["path", "content"], "desc": "أضف لنهاية ملف"},
    "file_str_replace":{"fn": file_str_replace,"args": ["path", "old_str", "new_str"], "desc": "استبدال نصّي جراحي داخل ملف (لتعديل todo.md والتعديلات الدقيقة)"},
    "read_file":  {"fn": read_file,  "args": ["path"], "desc": "اقرأ ملفاً"},
    "list_dir":   {"fn": list_dir,   "args": ["path"], "desc": "اعرض محتويات مجلد"},
    "make_dir":   {"fn": make_dir,   "args": ["path"], "desc": "أنشئ مجلداً"},
    "web_search": {"fn": web_search, "args": ["query"], "desc": "ابحث في الويب"},
    "run_python": {"fn": None, "args": ["code"], "desc": "نفّذ كود Python داخل sandbox معزول (CodeAct) وأرجِع المخرجات"},
}


def _run_python(code: str) -> str:
    """جسر CodeAct — يُستورد بكسل لتجنّب التبعية الدائرية."""
    try:
        import sys as _sys
        from pathlib import Path as _P
        _sys.path.insert(0, str(_P(__file__).resolve().parent.parent / "agent"))
        from code_act_executor import CodeActExecutor
        return CodeActExecutor().run(code)
    except Exception as e:
        return f"❌ تعذّر تشغيل CodeAct: {e}"


TOOLS["run_python"]["fn"] = _run_python

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
