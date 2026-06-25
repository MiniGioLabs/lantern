"""Lantern — Your AI lantern. Chat with local LLMs from your phone."""

from __future__ import annotations

import json, logging, time, qrcode, io, base64, asyncio
from pathlib import Path

import httpx
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
OLLAMA = "http://localhost:11434"
app = FastAPI(title="Lantern")


# ── Pages ───────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    models = await get_models()
    return templates.TemplateResponse(request, "chat.html", {
        "request": request,
        "models": models or [{"name": "No models"}],
        "lan_ip": await lan_ip(),
        "qr_code": qr_base64(await lan_ip()),
    })


# ── Chat API ────────────────────────────────────────────────────────

@app.post("/api/generate", response_class=HTMLResponse)
async def start_chat(request: Request, model: str = Form(...), prompt: str = Form(...)):
    """Return user message bubble + SSE-connected AI bubble that will stream."""
    prompt_esc = prompt.replace('"', '\\"').replace('\n', '\\n')
    model_esc = model.replace('"', '\\"')
    return HTMLResponse(f"""
    <div class="flex justify-end msg-in">
        <div class="bg-brand/20 text-gray-100 rounded-2xl rounded-br-md px-4 py-2.5 max-w-[85%] text-sm">{prompt}</div>
    </div>
    <div id="stream-target" class="flex justify-start msg-in"
         hx-ext="sse" sse-connect="/api/stream?model={model_esc}&prompt={prompt_esc}"
         sse-swap="message" hx-swap="innerHTML">
        <div class="bg-gray-800 text-gray-100 rounded-2xl rounded-bl-md px-4 py-2.5 max-w-[90%] text-sm">
            <span class="inline-block w-2 h-4 bg-brand animate-pulse rounded-sm"></span>
        </div>
    </div>
    <script>setTimeout(function(){{var c=document.getElementById('chat');c.scrollTop=c.scrollHeight}},100)</script>
    """)


@app.get("/api/stream")
async def stream_tokens(model: str, prompt: str):
    """SSE endpoint — streams tokens one at a time."""
    async def event_stream():
        full_text = ""
        try:
            async with httpx.AsyncClient(timeout=120) as c:
                async with c.stream("POST", f"{OLLAMA}/api/generate",
                                    json={"model": model, "prompt": prompt, "stream": True}) as r:
                    async for line in r.aiter_lines():
                        if line:
                            try:
                                chunk = json.loads(line)
                                token = chunk.get("response", "")
                                if token:
                                    full_text += token
                                    safe = token.replace("<", "&lt;").replace(">", "&gt;")
                                    yield f"event: message\ndata: <div class=\"bg-gray-800 text-gray-100 rounded-2xl rounded-bl-md px-4 py-2.5 max-w-[90%] text-sm whitespace-pre-wrap\">{full_text.replace('<','&lt;').replace('>','&gt;')}</div>\n\n"
                                if chunk.get("done"):
                                    break
                            except json.JSONDecodeError:
                                pass
        except Exception as e:
            yield f"event: message\ndata: <div class=\"bg-gray-800 text-red-400 rounded-2xl rounded-bl-md px-4 py-2.5 max-w-[90%] text-sm\">Error: {str(e)[:60]}</div>\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ── Models API ──────────────────────────────────────────────────────

@app.get("/api/models")
async def api_models():
    return await get_models()


# ── Helpers ─────────────────────────────────────────────────────────

async def get_models() -> list[dict]:
    try:
        async with httpx.AsyncClient() as c:
            r = await c.get(f"{OLLAMA}/api/tags", timeout=5)
            return r.json().get("models", [])
    except Exception:
        return []


async def lan_ip() -> str:
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"


def qr_base64(ip: str) -> str:
    url = f"http://{ip}:8000"
    qr = qrcode.make(url, box_size=4)
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


@app.get("/health")
async def health():
    models = await get_models()
    return {"status": "ok", "ollama": len(models) > 0, "models": len(models)}
