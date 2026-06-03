"""
☁️ CLOUD SANDBOX — تنفيذ معزول قابل للتبديل (محلي / Daytona / E2B)
═══════════════════════════════════════════════════════════════
يوحّد واجهة تنفيذ الأوامر عبر backends مختلفة:
  • local   — العملية الفرعية المحلية (الافتراضي، بلا اعتماديات).
  • daytona — Daytona SDK (اختياري، سحابي).
  • e2b     — E2B SDK (اختياري، سحابي).

الفلسفة (القاعدة الذهبية):
  • backend واحد يُختار من الإعداد؛ الافتراضي local.
  • SDKات السحابة اختيارية تماماً — إن غابت يسقط لـ local بأمان.
  • نفس الواجهة: run(command) -> str.

الإعداد عبر متغيّر البيئة:
  SANDBOX_BACKEND = local | daytona | e2b   (الافتراضي local)
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

PROJECTS_ROOT = Path(__file__).resolve().parent.parent / "projects"
PROJECTS_ROOT.mkdir(exist_ok=True)

MAX_OUTPUT = 4000


class CloudSandbox:
    """
    منفّذ أوامر موحّد قابل للتبديل بين backends.

    الاستخدام:
        sb = CloudSandbox()                 # يقرأ SANDBOX_BACKEND
        print(sb.backend)                   # local افتراضياً
        print(sb.run("echo مرحبا"))
    """

    def __init__(self, backend: str | None = None, timeout: int = 120):
        self.timeout = timeout
        requested = (backend or os.environ.get("SANDBOX_BACKEND", "local")).lower()
        self.backend = self._resolve_backend(requested)
        self._remote = None

    def _resolve_backend(self, requested: str) -> str:
        """يتحقّق من توفّر backend المطلوب، وإلا يسقط لـ local."""
        if requested == "daytona" and self._has_module("daytona_sdk"):
            return "daytona"
        if requested == "e2b" and self._has_module("e2b"):
            return "e2b"
        return "local"

    @staticmethod
    def _has_module(name: str) -> bool:
        try:
            __import__(name)
            return True
        except Exception:
            return False

    # ── التنفيذ ───────────────────────────────────────────────
    def run(self, command: str) -> str:
        """ينفّذ أمراً عبر backend المختار ويُعيد المخرجات نصاً."""
        if self.backend == "daytona":
            return self._run_daytona(command)
        if self.backend == "e2b":
            return self._run_e2b(command)
        return self._run_local(command)

    def _run_local(self, command: str) -> str:
        """تنفيذ محلي داخل projects/ (آمن، الافتراضي)."""
        try:
            r = subprocess.run(
                command, shell=True, cwd=str(PROJECTS_ROOT),
                capture_output=True, text=True, timeout=self.timeout,
            )
            out = (r.stdout or "")[-MAX_OUTPUT:]
            err = (r.stderr or "")[-1500:]
            res = f"[backend=local exit={r.returncode}]\n"
            if out:
                res += f"STDOUT:\n{out}\n"
            if err:
                res += f"STDERR:\n{err}\n"
            return res
        except subprocess.TimeoutExpired:
            return f"❌ تجاوز المهلة ({self.timeout}s)."
        except Exception as e:
            return f"❌ فشل التنفيذ المحلي: {e}"

    def _run_daytona(self, command: str) -> str:
        """تنفيذ عبر Daytona SDK (اختياري). يسقط لـ local عند الفشل."""
        try:
            from daytona_sdk import Daytona  # noqa
            if self._remote is None:
                self._remote = Daytona()
            # واجهة افتراضية — تُعدّل وفق نسخة SDK الفعلية
            result = self._remote.process.exec(command)  # type: ignore
            return f"[backend=daytona]\n{str(result)[:MAX_OUTPUT]}"
        except Exception as e:
            return f"⚠️ تعذّر Daytona ({e}) — السقوط للمحلي:\n" + self._run_local(command)

    def _run_e2b(self, command: str) -> str:
        """تنفيذ عبر E2B SDK (اختياري). يسقط لـ local عند الفشل."""
        try:
            from e2b import Sandbox  # noqa
            if self._remote is None:
                self._remote = Sandbox()
            result = self._remote.commands.run(command)  # type: ignore
            return f"[backend=e2b]\n{str(result)[:MAX_OUTPUT]}"
        except Exception as e:
            return f"⚠️ تعذّر E2B ({e}) — السقوط للمحلي:\n" + self._run_local(command)


if __name__ == "__main__":
    sb = CloudSandbox()
    print(f"☁️ backend: {sb.backend}")
    out = sb.run("echo 'sandbox يعمل' && python3 -c 'print(6*7)'")
    print(out)
    assert "42" in out and "exit=0" in out
    # طلب backend سحابي غير متوفّر → يجب السقوط لـ local
    sb2 = CloudSandbox(backend="daytona")
    assert sb2.backend == "local", "يجب السقوط لـ local عند غياب SDK"
    print("✅ cloud_sandbox OK")
