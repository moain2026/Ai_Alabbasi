#!/usr/bin/env python3
"""
🌐 WEB SERVER — واجهة محادثة Ai_Alabbasi (شبه Manus)
═══════════════════════════════════════════════════════════════
يكشف الوكيل عبر HTTP + بث مباشر (SSE) لخطوات التفكير والأدوات.

التشغيل:
    cd /home/work/Ai_Alabbasi
    . .venv/bin/activate
    python web/server.py
ثم افتح: http://localhost:8000
"""
import os
import sys
import json
import queue
import threading
import sqlite3
import time
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "agent"))
sys.path.insert(0, str(ROOT / "brain"))
sys.path.insert(0, str(ROOT / "knowledge"))

# ── تحميل المفاتيح من config/.env (الوكيل يقرأها من البيئة) ──
def load_env():
    env_file = ROOT / "config" / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and v and not os.environ.get(k):
                os.environ[k] = v
load_env()

from agent import Agent  # noqa
from brain import Brain  # noqa

try:
    import yaml
except ImportError:
    yaml = None

from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="Ai_Alabbasi Web")

WEB_DIR = Path(__file__).resolve().parent
DB_PATH = WEB_DIR / "conversations.db"
BRAIN_CFG = ROOT / "brain" / "brain_config.yaml"

# 📂 مجلد المرفقات (داخل projects/ ليبقى ضمن نطاق الوكيل الآمن)
UPLOADS_DIR = ROOT / "projects" / "_uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# الامتدادات المسموح بها للرفع (أمان)
ALLOWED_EXT = {
    ".txt", ".md", ".json", ".csv", ".yaml", ".yml", ".py", ".js", ".ts",
    ".html", ".css", ".sql", ".sh", ".xml", ".log", ".pdf",
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp",
}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp"}
MAX_UPLOAD_MB = 20

# 🛑 سجلّ المهام الجارية لدعم الإيقاف (cancellation)
#    conv_id → {"cancel": bool}
RUNNING_TASKS: dict[int, dict] = {}


# ════════════════════════ قاعدة بيانات المحادثات ════════════════════════
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conv_id INTEGER NOT NULL,
        role TEXT NOT NULL,          -- user | assistant
        content TEXT NOT NULL,
        steps TEXT,                  -- JSON للخطوات (للمساعد)
        created_at TEXT NOT NULL,
        FOREIGN KEY(conv_id) REFERENCES conversations(id)
    );
    """)
    conn.commit()
    conn.close()


init_db()


# ════════════════════════ نماذج الطلبات ════════════════════════
class NewConv(BaseModel):
    title: str = "محادثة جديدة"


class ChatReq(BaseModel):
    conv_id: int
    message: str
    topic: str | None = None
    attachments: list[str] | None = None   # أسماء ملفات مرفوعة في projects/_uploads
    skill: str | None = None               # اسم مهارة مختارة (اختياري)


# ════════════════════════ مسارات الـ API ════════════════════════
@app.get("/api/brains")
def get_brains():
    if not yaml:
        return {"active": "?", "brains": {}}
    cfg = yaml.safe_load(BRAIN_CFG.read_text(encoding="utf-8"))
    return {
        "active": cfg["active_brain"],
        "brains": {k: {"model": v["model"], "notes": v.get("notes", "")}
                   for k, v in cfg["brains"].items()},
    }


@app.post("/api/brain/{key}")
def set_brain(key: str):
    cfg = yaml.safe_load(BRAIN_CFG.read_text(encoding="utf-8"))
    if key not in cfg["brains"]:
        return JSONResponse({"ok": False, "error": "غير موجود"}, status_code=404)
    cfg["active_brain"] = key
    BRAIN_CFG.write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return {"ok": True, "active": key}


@app.get("/api/conversations")
def list_convs():
    conn = db()
    rows = conn.execute("SELECT * FROM conversations ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/api/conversations")
def create_conv(c: NewConv):
    conn = db()
    cur = conn.execute(
        "INSERT INTO conversations(title, created_at) VALUES(?,?)",
        (c.title, datetime.now().isoformat()),
    )
    conn.commit()
    cid = cur.lastrowid
    conn.close()
    return {"id": cid, "title": c.title}


@app.delete("/api/conversations/{cid}")
def delete_conv(cid: int):
    conn = db()
    conn.execute("DELETE FROM messages WHERE conv_id=?", (cid,))
    conn.execute("DELETE FROM conversations WHERE id=?", (cid,))
    conn.commit()
    conn.close()
    return {"ok": True}


@app.get("/api/conversations/{cid}/messages")
def get_messages(cid: int):
    conn = db()
    rows = conn.execute(
        "SELECT * FROM messages WHERE conv_id=? ORDER BY id ASC", (cid,)
    ).fetchall()
    conn.close()
    out = []
    for r in rows:
        d = dict(r)
        if d.get("steps"):
            try:
                d["steps"] = json.loads(d["steps"])
            except Exception:
                d["steps"] = []
        out.append(d)
    return out


def save_message(conv_id, role, content, steps=None):
    conn = db()
    conn.execute(
        "INSERT INTO messages(conv_id, role, content, steps, created_at) VALUES(?,?,?,?,?)",
        (conv_id, role, content, json.dumps(steps, ensure_ascii=False) if steps else None,
         datetime.now().isoformat()),
    )
    # أول رسالة مستخدم → اجعلها عنوان المحادثة
    if role == "user":
        cnt = conn.execute("SELECT COUNT(*) c FROM messages WHERE conv_id=? AND role='user'", (conv_id,)).fetchone()["c"]
        if cnt == 1:
            conn.execute("UPDATE conversations SET title=? WHERE id=?", (content[:40], conv_id))
    conn.commit()
    conn.close()


# ════════════════════════ رفع الملفات والصور 📎 ════════════════════════
def _safe_upload_name(name: str) -> str:
    """تنظيف اسم الملف لمنع اختراق المسارات (path traversal)."""
    name = os.path.basename(name or "file")
    name = name.replace("..", "_").replace("/", "_").replace("\\", "_")
    return name[:120] or "file"


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """يرفع ملفاً/صورة إلى projects/_uploads ويُرجع بياناته."""
    raw_name = _safe_upload_name(file.filename or "file")
    ext = Path(raw_name).suffix.lower()
    if ext not in ALLOWED_EXT:
        return JSONResponse(
            {"ok": False, "error": f"امتداد غير مسموح: {ext or 'بدون امتداد'}"},
            status_code=400,
        )

    data = await file.read()
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        return JSONResponse(
            {"ok": False, "error": f"الحجم يتجاوز {MAX_UPLOAD_MB}MB"},
            status_code=400,
        )

    # تفادي الكتابة فوق ملف موجود
    stem, suf = Path(raw_name).stem, Path(raw_name).suffix
    final_name, i = raw_name, 1
    while (UPLOADS_DIR / final_name).exists():
        final_name = f"{stem}_{i}{suf}"
        i += 1

    (UPLOADS_DIR / final_name).write_bytes(data)
    return {
        "ok": True,
        "name": final_name,
        "size": len(data),
        "is_image": ext in IMAGE_EXT,
        "url": f"/uploads/{final_name}",
        "rel_path": f"_uploads/{final_name}",   # المسار النسبي داخل projects/
    }


@app.get("/api/files")
def list_uploads():
    """يسرد الملفات المرفوعة."""
    out = []
    for p in sorted(UPLOADS_DIR.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True):
        if p.is_file():
            out.append({
                "name": p.name,
                "size": p.stat().st_size,
                "is_image": p.suffix.lower() in IMAGE_EXT,
                "url": f"/uploads/{p.name}",
            })
    return out


@app.delete("/api/files/{name}")
def delete_upload(name: str):
    """يحذف ملفاً مرفوعاً."""
    p = UPLOADS_DIR / _safe_upload_name(name)
    if p.exists() and p.is_file():
        p.unlink()
        return {"ok": True}
    return JSONResponse({"ok": False, "error": "غير موجود"}, status_code=404)


# ════════════════════════ المهارات 🧩 ════════════════════════
@app.get("/api/skills")
def list_skills():
    """يسرد المهارات المتاحة (من knowledge + external_skills إن وُجدت)."""
    skills = []
    # 1) المهارات المتعلّمة ذاتياً (skills.db)
    try:
        from knowledge import Knowledge  # noqa
        kb = Knowledge()
        if hasattr(kb, "list_skills"):
            for s in kb.list_skills():
                skills.append({"name": s.get("name", ""),
                               "desc": s.get("task", "")[:80],
                               "source": "self-learned"})
    except Exception:
        pass

    # 2) مهارات البذرة + الخارجية عبر الفهرس (Progressive Disclosure — الطبقة 1)
    try:
        sys.path.insert(0, str(ROOT / "knowledge"))
        from skill_indexer import SkillIndex  # noqa
        idx = SkillIndex(); idx.build()
        for s in idx.tier1():
            skills.append({"name": s["name"], "desc": s["description"][:80],
                           "source": s["source"]})
    except Exception:
        # سقوط: قراءة مباشرة من المجلّدات
        for sub in ("skills_seed", "external_skills"):
            d = ROOT / "knowledge" / sub
            if d.exists():
                for sk in sorted(d.rglob("SKILL.md"))[:300]:
                    try:
                        head = sk.read_text(encoding="utf-8", errors="ignore")[:600]
                        desc = ""
                        for line in head.splitlines():
                            if line.lower().startswith("description:"):
                                desc = line.split(":", 1)[1].strip().strip('"')[:80]
                                break
                        skills.append({"name": sk.parent.name, "desc": desc, "source": sub})
                    except Exception:
                        continue

    # 3) مهارات افتراضية إن لم يوجد شيء (placeholders للعرض)
    if not skills:
        skills = [
            {"name": "arabic-content-writer", "desc": "كتابة محتوى عربي فصيح", "source": "builtin"},
            {"name": "nextjs-rtl-pro", "desc": "بناء Next.js عربي RTL", "source": "builtin"},
            {"name": "electricity-bill-analyzer", "desc": "تحليل فواتير الكهرباء", "source": "builtin"},
        ]
    return skills


# ════════════════════════ الإيقاف 🛑 ════════════════════════
@app.post("/api/stop/{conv_id}")
def stop_task(conv_id: int):
    """يطلب إيقاف المهمة الجارية لمحادثة معيّنة."""
    t = RUNNING_TASKS.get(conv_id)
    if t:
        t["cancel"] = True
        return {"ok": True, "stopped": conv_id}
    return {"ok": False, "error": "لا توجد مهمة جارية"}


# ════════════════════════ بث المحادثة (SSE) ════════════════════════
@app.post("/api/chat/stream")
def chat_stream(req: ChatReq):
    # دمج المرفقات والمهارة في نص المهمة المُرسل للوكيل
    full_msg = req.message
    if req.attachments:
        files_note = "\n\n📎 الملفات المرفقة (متاحة في projects/_uploads/):\n" + \
            "\n".join(f"- _uploads/{a}" for a in req.attachments)
        full_msg += files_note
    if req.skill:
        full_msg = f"[المهارة المختارة: {req.skill}]\n{full_msg}"

    save_message(req.conv_id, "user", req.message)

    q: queue.Queue = queue.Queue()
    steps_collected = []

    # تسجيل المهمة لدعم الإيقاف
    ctrl = {"cancel": False}
    RUNNING_TASKS[req.conv_id] = ctrl

    def on_event(kind, data):
        if ctrl["cancel"]:
            raise KeyboardInterrupt("أوقف المستخدم المهمة")
        q.put({"kind": kind, "data": data})

    def worker():
        try:
            agent = Agent(verbose=False, topic=req.topic, on_event=on_event)
            final = agent.run(full_msg)
            # حفظ رد المساعد + الخطوات
            save_message(req.conv_id, "assistant", final, steps_collected)
        except KeyboardInterrupt:
            q.put({"kind": "stopped", "data": "🛑 أُوقفت المهمة بطلبك."})
            save_message(req.conv_id, "assistant", "🛑 أُوقفت المهمة بطلبك.", steps_collected)
        except Exception as e:
            q.put({"kind": "error", "data": str(e)})
        finally:
            RUNNING_TASKS.pop(req.conv_id, None)
            q.put({"kind": "__end__", "data": None})

    threading.Thread(target=worker, daemon=True).start()

    def sse():
        while True:
            ev = q.get()
            if ev["kind"] == "__end__":
                yield f"data: {json.dumps({'kind':'end'}, ensure_ascii=False)}\n\n"
                break
            # اجمع الخطوات لحفظها لاحقاً (ما عدا done)
            if ev["kind"] in ("thought", "tool", "tool_result", "step"):
                steps_collected.append(ev)
            yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"
            if ev["kind"] == "stopped":
                # بعد الإيقاف، أرسل end وأنهِ
                yield f"data: {json.dumps({'kind':'end'}, ensure_ascii=False)}\n\n"
                break

    return StreamingResponse(sse(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    })


# ════════════════════════ الواجهة ════════════════════════
# خدمة الأصول (الشعار/الأيقونات)
app.mount("/assets", StaticFiles(directory=str(WEB_DIR / "assets")), name="assets")
# خدمة الملفات المرفوعة (لمعاينة الصور)
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")


@app.get("/favicon.ico")
def favicon():
    from fastapi.responses import FileResponse
    return FileResponse(str(WEB_DIR / "assets" / "favicon.ico"))


@app.get("/", response_class=HTMLResponse)
def index():
    return (WEB_DIR / "index.html").read_text(encoding="utf-8")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    print(f"🌐 Ai_Alabbasi Web → http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
