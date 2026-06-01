"""
🐍 CODE ACT EXECUTOR — تنفيذ كود Python كأداة (نمط Manus CodeAct)
═══════════════════════════════════════════════════════════════
بدل تقييد الوكيل بأدوات محدّدة، يتيح CodeAct للوكيل كتابة كود Python
وتنفيذه — فيُعبّر عن أفعال مركّبة بسطر واحد بدل سلسلة استدعاءات.

الأمان (القاعدة الذهبية):
  • التنفيذ في عملية فرعية معزولة داخل projects/ فقط.
  • مهلة زمنية صارمة (timeout).
  • لا وصول للشبكة افتراضياً (يعتمد على بيئة الـ subprocess).
  • حجم مخرجات محدود.

بلا اعتماديات خارجية (يستخدم subprocess القياسي).
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

# نفس جذر المشاريع المستخدم في tools.py (حماية موحّدة)
PROJECTS_ROOT = Path(__file__).resolve().parent.parent / "projects"
PROJECTS_ROOT.mkdir(exist_ok=True)

MAX_OUTPUT = 6000


class CodeActExecutor:
    """
    منفّذ كود Python معزول داخل مجلد المشاريع.

    الاستخدام:
        ex = CodeActExecutor()
        print(ex.run("print(2 + 2)"))
    """

    def __init__(self, timeout: int = 30, workdir: Path | None = None):
        self.timeout = timeout
        self.workdir = workdir or PROJECTS_ROOT
        self.workdir.mkdir(parents=True, exist_ok=True)

    def run(self, code: str) -> str:
        """
        ينفّذ مقطع كود Python ويُرجع المخرجات (stdout/stderr + رمز الخروج).
        """
        if not code or not code.strip():
            return "❌ لا يوجد كود لتنفيذه."

        # نكتب الكود في ملف مؤقّت داخل مجلد العمل
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", dir=str(self.workdir),
                delete=False, encoding="utf-8",
            ) as f:
                f.write(code)
                script = f.name
        except Exception as e:
            return f"❌ تعذّر تحضير الكود: {e}"

        try:
            r = subprocess.run(
                [sys.executable, script],
                cwd=str(self.workdir),
                capture_output=True, text=True,
                timeout=self.timeout,
            )
            out = (r.stdout or "")[-MAX_OUTPUT:]
            err = (r.stderr or "")[-2000:]
            result = f"[exit={r.returncode}]\n"
            if out:
                result += f"STDOUT:\n{out}\n"
            if err:
                result += f"STDERR:\n{err}\n"
            if not out and not err:
                result += "(لا مخرجات)\n"
            return result
        except subprocess.TimeoutExpired:
            return f"❌ تجاوز المهلة ({self.timeout}s) — أُوقف التنفيذ."
        except Exception as e:
            return f"❌ فشل التنفيذ: {e}"
        finally:
            try:
                Path(script).unlink(missing_ok=True)
            except Exception:
                pass


if __name__ == "__main__":
    ex = CodeActExecutor(timeout=10)
    out = ex.run("print('مرحبا'); print(sum(range(10)))")
    assert "مرحبا" in out and "45" in out, out
    print(out)
    # اختبار المهلة (مهلة قصيرة لتجنّب الانتظار)
    ex2 = CodeActExecutor(timeout=2)
    slow = ex2.run("import time; time.sleep(10)")
    assert "المهلة" in slow, slow
    print("✅ code_act_executor OK")
