# ⚡ Quick Start - Try Abby in 5 Minutes

Get Abby running and solving a real problem in **under 5 minutes**.

## What This Is

**Abby Unleashed** is an AI orchestration system that breaks down complex tasks and coordinates multiple AI agents to solve them. Think of it as a project manager who:

1. **Understands** your task
2. **Breaks it down** into subtasks
3. **Assigns specialists** (coding agent, design agent, etc.)
4. **Coordinates** their work
5. **Delivers** the combined result

## Prerequisites

- Python 3.9+
- [Ollama](https://ollama.ai/) installed

## 5-Minute Setup

### Step 1: Clone and Install (2 min)

```bash
git clone https://github.com/Abbystarchild/Abby-Unleashed-Core.git
cd Abby-Unleashed-Core
pip install -r requirements.txt
```

### Step 2: Start Ollama (1 min)

```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Pull a model (first time only)
ollama pull qwen2.5:latest
```

### Step 3: Run Abby (30 sec)

```bash
# Interactive text mode
python cli.py text
```

### Step 4: Try It! (1.5 min)

Type this task:

```
Create a Python web scraper that extracts product names and prices from an e-commerce site
```

Watch Abby:
1. Analyze the task complexity
2. Identify needed skills (Python, web scraping, HTML parsing)
3. Create a specialized "Web Scraper Engineer" agent
4. Generate working code

---

## Three Ways to Use Abby

### 1. Interactive Chat (Easiest)

```bash
python cli.py text
```

Just type your request. Good for:
- Exploring capabilities
- One-off tasks
- Learning how it works

### 2. Direct Task Execution (Scripts)

```bash
python cli.py task --task "Build a REST API for managing todo items"
```

Good for:
- Automation scripts
- CI/CD pipelines
- Batch processing

### 3. Voice Mode (Natural)

```bash
python cli.py voice
```

Say "Hey Abby" and speak your request. Good for:
- Hands-free coding
- Brainstorming
- Multitasking

---

## Real Examples (Copy & Paste These)

### Example 1: Code Generation

```
Create a Python class for managing a shopping cart with add, remove, 
update quantity, and calculate total methods
```

**Result:** Complete, working Python class with docstrings.

### Example 2: Multi-Step Task

```
Build a REST API with Flask that has:
- User registration and login
- JWT authentication
- CRUD operations for blog posts
- Input validation
```

**Result:** Abby breaks this into 4+ subtasks, creates specialists for auth, database, and API design, then combines their work.

### Example 3: Research + Implementation

```
Research best practices for rate limiting APIs, then implement 
a rate limiter middleware for Flask
```

**Result:** Summary of approaches + working implementation.

---

## What Makes Abby Different?

| Feature | Abby Unleashed | ChatGPT/Claude | Traditional Scripts |
|---------|---------------|----------------|---------------------|
| Breaks down complex tasks | ✅ Auto-decomposes | ❌ You break it down | ❌ You break it down |
| Creates specialized agents | ✅ Dynamic DNA system | ❌ One generalist | ❌ N/A |
| Coordinates multiple agents | ✅ Built-in orchestrator | ❌ Manual | ❌ Manual |
| Learns from success/failure | ✅ Outcome tracking | ❌ No memory | ❌ No memory |
| Works 100% offline | ✅ Local LLMs via Ollama | ❌ Cloud required | ✅ |
| Voice interface | ✅ Wake word + STT/TTS | ❌ | ❌ |

---

## Next Steps

- 📖 [Full README](../README.md) - Complete documentation
- 🎯 [Use Cases](USE_CASES.md) - Detailed real-world examples
- ⚔️ [Comparison Guide](COMPARISON.md) - Abby vs. other frameworks
- 🏗️ [Architecture](docs/ARCHITECTURE.md) - How it works under the hood

---

## Troubleshooting

### "Ollama not running"

```bash
# Make sure Ollama is running
ollama serve
```

### "Model not found"

```bash
# Pull the default model
ollama pull qwen2.5:latest
```

### "Import errors"

```bash
# Install all dependencies
pip install -r requirements.txt
```

### Still stuck?

Open an issue on GitHub or check the [full documentation](../README.md).

---

**⏱️ Total time: ~5 minutes**

You now have a working AI orchestration system. Go build something cool! 🚀
