# 🚀 Quick Start Guide - Abby Unleashed Core

Get Abby Unleashed running in under 5 minutes!

## Prerequisites

- Python 3.9+ ([Download](https://www.python.org/downloads/))
- Ollama ([Install](https://ollama.ai/))
- Git ([Install](https://git-scm.com/downloads))

## Quick Install

```bash
git clone https://github.com/Abbystarchild/Abby-Unleashed-Core.git
cd Abby-Unleashed-Core
./start.sh text
```

The script validates your environment and starts the application automatically.

## Usage Modes

**Text Mode** (Interactive):
```bash
python cli.py text
```

**Voice Mode** (Speech-to-Speech):
```bash
python cli.py voice
```

**Direct Task**:
```bash
python cli.py task --task "your task here"
```

## Docker Setup

```bash
docker-compose up --build
```

## Configuration

Edit `.env` for settings:
```bash
OLLAMA_HOST=http://localhost:11434
LOG_LEVEL=INFO
```

## Troubleshooting

**Can't connect to Ollama?**
```bash
ollama serve
ollama pull qwen2.5:latest
```

See full guide at [docs/INSTALLATION.md](INSTALLATION.md)
