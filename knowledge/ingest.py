"""
📥 INGEST — تغذية قاعدة المعرفة بتوثيق التقنيات
═══════════════════════════════════════════════════════════════
يجلب صفحات توثيق رسمية للتقنيات التي يريد عبّاس التمرّس عليها،
ينظّفها، ويفهرسها في قاعدة المعرفة (RAG).
"""
import sys
import re
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from knowledge import Knowledge  # noqa

# مصادر التوثيق الرسمية (نصّية/خفيفة) لكل تقنية
SOURCES = {
    "react-native": [
        ("https://raw.githubusercontent.com/facebook/react-native-website/main/docs/getting-started.md", "البدء مع React Native"),
        ("https://raw.githubusercontent.com/facebook/react-native-website/main/docs/components-and-apis.md", "المكوّنات والـ APIs"),
        ("https://raw.githubusercontent.com/facebook/react-native-website/main/docs/intro-react.md", "أساسيات React"),
        ("https://raw.githubusercontent.com/facebook/react-native-website/main/docs/navigation.md", "التنقّل Navigation"),
    ],
    "nextjs": [
        ("https://raw.githubusercontent.com/vercel/next.js/canary/docs/01-app/01-getting-started/01-installation.mdx", "تثبيت Next.js"),
        ("https://raw.githubusercontent.com/vercel/next.js/canary/docs/01-app/01-getting-started/03-layouts-and-pages.mdx", "الصفحات والتخطيطات"),
        ("https://raw.githubusercontent.com/vercel/next.js/canary/docs/01-app/01-getting-started/05-server-and-client-components.mdx", "مكوّنات الخادم والعميل"),
        ("https://raw.githubusercontent.com/vercel/next.js/canary/docs/01-app/01-getting-started/06-fetching-data.mdx", "جلب البيانات"),
    ],
    "angular": [
        ("https://raw.githubusercontent.com/angular/angular/main/adev/src/content/introduction/what-is-angular.md", "ما هو Angular"),
        ("https://raw.githubusercontent.com/angular/angular/main/adev/src/content/guide/components/anatomy-of-components.md", "تشريح المكوّنات"),
    ],
}


def fetch(url: str) -> str:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Ai-Alabbasi/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read().decode("utf-8", "ignore")
    except Exception as e:
        return f"__ERR__ {e}"


def clean(md: str) -> str:
    """تنظيف خفيف لـ markdown."""
    md = re.sub(r"<!--.*?-->", "", md, flags=re.S)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip()


def chunk(text: str, size: int = 1500):
    """تقسيم لمقاطع بحجم مناسب للاسترجاع."""
    paras = text.split("\n\n")
    out, buf = [], ""
    for p in paras:
        if len(buf) + len(p) > size:
            if buf:
                out.append(buf.strip())
            buf = p
        else:
            buf += "\n\n" + p
    if buf.strip():
        out.append(buf.strip())
    return out


def main():
    k = Knowledge()
    total = 0
    for topic, items in SOURCES.items():
        print(f"\n📦 {topic}")
        for url, title in items:
            raw = fetch(url)
            if raw.startswith("__ERR__"):
                print(f"  ❌ {title}: {raw[:60]}")
                continue
            text = clean(raw)
            chunks = chunk(text)
            for i, ch in enumerate(chunks):
                k.add_doc(topic, f"{title} [{i+1}/{len(chunks)}]", ch, url)
            total += len(chunks)
            print(f"  ✅ {title} → {len(chunks)} مقطع")
    print(f"\n📚 الإجمالي: {total} مقطع مفهرس")
    print("الإحصائيات:", k.stats())


if __name__ == "__main__":
    main()
