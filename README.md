# Lantern 🏮

**Chat with local AI models from your phone.**

Lantern is a mobile-first web interface that connects to [Ollama](https://ollama.com) running on your machine. It generates a QR code — scan it with your phone and start chatting with your local LLMs instantly. No app download, no cloud dependency.

---

## How It Works

```
Your Mac/PC                    Your Phone
┌──────────────┐               📱
│  Ollama      │──QR code──►  Scan & chat
│  Lantern 🏮  │◄──HTTP────   over WiFi
└──────────────┘
```

## Features

- 📱 Mobile-optimized chat interface
- 🔄 Stream token-by-token responses
- 📋 Switch between installed Ollama models
- 📲 QR code auto-generated for instant phone access
- ✨ Zero setup on your phone — just scan

## Quick Start

```bash
# Install Ollama and pull a model
ollama pull llama3.2

# Run Lantern
uv run uvicorn lantern.main:app --host 0.0.0.0 --port 8344

# Open on your phone: scan the QR code, or visit http://<your-ip>:8344
```

## Stack

- **FastAPI** — backend
- **Jinja2** — server-rendered templates
- **Ollama** — local LLM runtime
- **Tailwind CSS** — mobile-first UI

---

**MiniGioLabs** — [github.com/MiniGioLabs](https://github.com/MiniGioLabs)
