"""
🧠 BRAIN — طبقة العقل الموحّدة لوكيل Ai_Alabbasi
═══════════════════════════════════════════════════════════════
هذا هو المكان الوحيد الذي يتصل بالنموذج (LLM).
أي شيء في النظام يطلب تفكيراً → يمرّ من هنا.
تبديل النموذج = تعديل active_brain في brain_config.yaml فقط.

يدعم: OpenRouter (API) + أي نموذج محلي متوافق مع OpenAI (Ollama, LM Studio...).
"""
import os
import json
import time
import urllib.request
import urllib.error
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

CONFIG_PATH = Path(__file__).parent / "brain_config.yaml"


class Brain:
    def __init__(self, config_path: str = None):
        self.config_path = Path(config_path) if config_path else CONFIG_PATH
        self.cfg = self._load_config()
        self.active_key = self.cfg["active_brain"]
        self.brain = self.cfg["brains"][self.active_key]
        self.defaults = self.cfg.get("defaults", {})

    def _load_config(self):
        text = self.config_path.read_text(encoding="utf-8")
        if yaml:
            return yaml.safe_load(text)
        raise RuntimeError("PyYAML غير مثبّت. شغّل: pip install pyyaml")

    def info(self):
        return {
            "active": self.active_key,
            "provider": self.brain["provider"],
            "model": self.brain["model"],
            "base_url": self.brain["base_url"],
            "notes": self.brain.get("notes", ""),
        }

    def _api_key(self):
        env_name = self.brain.get("api_key_env", "")
        key = os.environ.get(env_name, "")
        if not key and self.brain["provider"] != "openai_compatible":
            raise RuntimeError(f"المفتاح غير موجود في متغير البيئة: {env_name}")
        return key or "ollama"  # المحلي لا يحتاج مفتاح

    def think(self, messages, temperature=None, max_tokens=None):
        """يرسل رسائل ويرجّع رد النموذج. messages = [{'role','content'}, ...]"""
        url = self.brain["base_url"].rstrip("/") + "/chat/completions"
        payload = {
            "model": self.brain["model"],
            "messages": messages,
            "temperature": temperature if temperature is not None else self.defaults.get("temperature", 0.3),
            "max_tokens": max_tokens or self.defaults.get("max_tokens", 4096),
        }
        headers = {
            "Authorization": f"Bearer {self._api_key()}",
            "Content-Type": "application/json",
            "User-Agent": "Ai-Alabbasi/1.0",
        }
        # ترويسات خاصة بـ OpenRouter فقط (تسبب حظر Cloudflare على مزودين آخرين)
        if self.brain["provider"] == "openrouter":
            headers["HTTP-Referer"] = "https://ai-alabbasi.local"
            headers["X-Title"] = "Ai_Alabbasi-Agent"
        data = json.dumps(payload).encode("utf-8")
        attempts = self.defaults.get("retry_attempts", 3)
        backoff = self.defaults.get("retry_backoff_seconds", 5)
        timeout = self.defaults.get("timeout_seconds", 120)

        last_err = None
        for i in range(attempts):
            try:
                req = urllib.request.Request(url, data=data, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    body = json.loads(r.read().decode("utf-8"))
                    return body["choices"][0]["message"]["content"]
            except urllib.error.HTTPError as e:
                last_err = e
                err_body = e.read().decode("utf-8", "ignore")
                if e.code == 429:  # مزحوم → أعد المحاولة
                    wait = backoff * (i + 1)
                    print(f"[brain] 429 rate-limited, retry in {wait}s ({i+1}/{attempts})")
                    time.sleep(wait)
                    continue
                raise RuntimeError(f"HTTP {e.code}: {err_body[:300]}")
            except Exception as e:
                last_err = e
                time.sleep(backoff)
        raise RuntimeError(f"فشل بعد {attempts} محاولات: {last_err}")


if __name__ == "__main__":
    b = Brain()
    print("🧠 العقل الفعّال:", json.dumps(b.info(), ensure_ascii=False, indent=2))
    print("\n--- اختبار تفكير ---")
    reply = b.think([{"role": "user", "content": "رد بجملة عربية قصيرة تثبت أنك تعمل كعقل للوكيل."}])
    print("الرد:", reply)
