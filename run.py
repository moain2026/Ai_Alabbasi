#!/usr/bin/env python3
"""
▶️ RUN — واجهة تشغيل Ai_Alabbasi التفاعلية
═══════════════════════════════════════════════════════════════
محادثة مستمرة مع الوكيل. أوامر خاصة:
  /brain            عرض العقل الحالي
  /brain <key>      تبديل العقل (مؤقت لهذه الجلسة)
  /topic <name>     تحديد تقنية التركيز (nextjs/react-native/angular)
  /kb               إحصائيات المعرفة
  /skills <q>       بحث في الخبرات المتعلّمة
  /help             المساعدة
  /exit             خروج
بدون أمر خاص → يُنفَّذ كمهمة للوكيل.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "brain"))
sys.path.insert(0, str(ROOT / "agent"))
sys.path.insert(0, str(ROOT / "knowledge"))

from agent import Agent          # noqa
from knowledge import Knowledge  # noqa
import yaml                      # noqa

CFG = ROOT / "brain" / "brain_config.yaml"


def list_brains():
    cfg = yaml.safe_load(CFG.read_text(encoding="utf-8"))
    return cfg["brains"], cfg["active_brain"]


def set_brain(key):
    cfg = yaml.safe_load(CFG.read_text(encoding="utf-8"))
    if key not in cfg["brains"]:
        return False
    cfg["active_brain"] = key
    CFG.write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return True


def main():
    topic = None
    print("═" * 55)
    print("  🤖 Ai_Alabbasi — وكيل عبّاس الذكي")
    print("  اكتب /help للأوامر، /exit للخروج")
    print("═" * 55)
    brains, active = list_brains()
    print(f"🧠 العقل: {active} ({brains[active]['model']})")

    while True:
        try:
            line = input("\n👤 عبّاس> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 مع السلامة")
            break
        if not line:
            continue

        if line == "/exit":
            print("👋 مع السلامة")
            break
        elif line == "/help":
            print(__doc__)
        elif line == "/brain":
            brains, active = list_brains()
            print(f"🧠 الحالي: {active} ({brains[active]['model']})")
            print("المتاح:")
            for k, v in brains.items():
                print(f"  - {k}: {v['model']}")
        elif line.startswith("/brain "):
            key = line.split(maxsplit=1)[1].strip()
            if set_brain(key):
                print(f"✅ تم التبديل إلى: {key}")
            else:
                print(f"❌ غير موجود: {key}")
        elif line.startswith("/topic "):
            topic = line.split(maxsplit=1)[1].strip()
            print(f"🎯 تقنية التركيز: {topic}")
        elif line == "/kb":
            print("📚", Knowledge().stats())
        elif line.startswith("/skills "):
            q = line.split(maxsplit=1)[1]
            for s in Knowledge().search_skills(q):
                print(f"  🧠 {s['name']}: {s['approach'][:80]}")
        else:
            agent = Agent(topic=topic)
            agent.run(line)


if __name__ == "__main__":
    main()
