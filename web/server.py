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

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="Ai_Alabbasi Web")

WEB_DIR = Path(__file__).resolve().parent
DB_PATH = WEB_DIR / "conversations.db"
BRAIN_CFG = ROOT / "brain" / "brain_config.yaml"


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


# ════════════════════════ بث المحادثة (SSE) ════════════════════════
@app.post("/api/chat/stream")
def chat_stream(req: ChatReq):
    save_message(req.conv_id, "user", req.message)

    q: queue.Queue = queue.Queue()
    steps_collected = []

    def on_event(kind, data):
        q.put({"kind": kind, "data": data})

    def worker():
        try:
            agent = Agent(verbose=False, topic=req.topic, on_event=on_event)
            final = agent.run(req.message)
            # حفظ رد المساعد + الخطوات
            save_message(req.conv_id, "assistant", final, steps_collected)
        except Exception as e:
            q.put({"kind": "error", "data": str(e)})
        finally:
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

    return StreamingResponse(sse(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    })


# ════════════════════════ الواجهة ════════════════════════
# خدمة الأصول (الشعار/الأيقونات)
app.mount("/assets", StaticFiles(directory=str(WEB_DIR / "assets")), name="assets")


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
