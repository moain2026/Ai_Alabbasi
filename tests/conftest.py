"""إعداد مسارات الاستيراد للاختبارات."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for sub in ("agent", "tools", "brain", "knowledge"):
    sys.path.insert(0, str(ROOT / sub))
