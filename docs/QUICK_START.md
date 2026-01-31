# Quick Start Guide

Get Abby Unleashed running in 5 minutes!

## Prerequisites

- **Python 3.9+** installed
- **Ollama** (optional for Phase 1, required for full functionality)

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/Abbystarchild/Abby-Unleashed-Core.git
cd Abby-Unleashed-Core
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Or use the setup script:

```bash
bash setup.sh
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` if needed (defaults work for most cases).

## Basic Usage

### Text Interface (Interactive)

The simplest way to start:

```bash
python cli.py text
```

You'll see:

```
Hey! What can I help you with?

You: 
```

Type your task and press Enter!

### Direct Task Execution

Execute a single task:

```bash
python cli.py task --task "Create a REST API for user management"
```

### Voice Interface (Coming Soon)

```bash
python cli.py voice
```

Currently falls back to text mode.

## Example Tasks

Try these tasks to see Abby in action:

### 1. Code Development
```
You: Create a Python web scraper for product prices
```

### 2. Data Analysis
```
You: Analyze sales data and create a dashboard
```

### 3. DevOps Task
```
You: Deploy a containerized application to AWS
```

### 4. Research Task
```
You: Research best practices for microservices architecture
```

## Running Examples

Check out the example scripts:

```bash
# Agent factory demo
python examples/agent_factory_demo.py

# Persona library demo
python examples/persona_library_demo.py

# Web scraper example
python examples/create_web_scraper.py

# Task engine demo (NEW!)
python examples/task_engine_demo.py
```

## Running Tests

Validate your installation:

```bash
pytest tests/
```

You should see all tests passing:

```
===== 19 passed in 0.05s =====
```

## Configuration

### Customize Personality

Edit `config/brain_clone.yaml`:

```yaml
identity:
  name: "Your Name"
  role: "Your Role"

communication_style:
  tone: "friendly"
  verbosity: "detailed"
```

### Model Preferences

Edit `config/ollama_models.yaml`:

```yaml
models:
  code:
    - "qwen2.5-coder:latest"
```

## Common Issues

### "Module not found" errors

Make sure you're in the project directory:

```bash
cd Abby-Unleashed-Core
python cli.py text
```

### "Connection refused" to Ollama

Ollama isn't required for Phase 1 (core functionality). The system will work in demo mode.

To use real LLM capabilities:

1. Install Ollama: https://ollama.ai/
2. Start Ollama: `ollama serve`
3. Pull a model: `ollama pull qwen2.5:latest`

### Import errors in examples

Run examples from the project root:

```bash
python examples/agent_factory_demo.py
```

## Next Steps

1. **Explore the Code**: Check out `agents/`, `personality/`, `persona_library/`

2. **Customize Personality**: Edit `config/brain_clone.yaml`

3. **Create Custom Personas**: See `persona_library/personas/examples/`

4. **Read Documentation**: Check `docs/ARCHITECTURE.md`

5. **Run Tests**: `pytest tests/ -v`

## Getting Help

- **Issues**: Open an issue on GitHub
- **Docs**: Check `docs/` directory
- **Examples**: See `examples/` directory

## What's Working (Phase 1)

✅ Agent DNA framework (5-element system)
✅ Base agent classes and factory
✅ Clarification protocol
✅ Persona library with CRUD
✅ Ollama integration
✅ Model selector
✅ Personality system
✅ CLI interface (text mode)
✅ Configuration system
✅ Example personas
✅ Comprehensive tests

## What's Working (Phase 2)

✅ Task decomposition engine
✅ Task analyzer (complexity, domain detection)
✅ Task decomposer (recursive breakdown)
✅ Dependency mapper (DAG, cycle detection)
✅ Execution planner (parallel execution, critical path)

## What's Coming

🚧 Speech interface (STT, TTS, VAD)
🚧 Agent coordination system
🚧 Memory systems
🚧 Learning systems
🚧 Web dashboard

---

**Enjoy using Abby Unleashed!** 🚀
