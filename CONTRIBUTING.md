# Contributing to Abby Unleashed

Thanks for your interest in contributing! 🎉

## Quick Links

- [Bug Reports](#bug-reports)
- [Feature Requests](#feature-requests)
- [Pull Requests](#pull-requests)
- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Testing](#testing)

---

## Bug Reports

Found a bug? Open an issue with:

1. **What happened** (actual behavior)
2. **What you expected** (expected behavior)
3. **Steps to reproduce**
4. **Environment** (OS, Python version, Ollama version)
5. **Error messages** (if any)

```markdown
**Bug:** [Brief description]

**Expected:** [What should happen]

**Actual:** [What happened]

**Steps to reproduce:**
1. ...
2. ...

**Environment:**
- OS: Windows 11
- Python: 3.11.0
- Ollama: 0.1.0
- Model: qwen2.5:latest
```

---

## Feature Requests

Have an idea? Open an issue with:

1. **Problem** you're trying to solve
2. **Proposed solution**
3. **Alternatives** you've considered
4. **Why it matters** (use case)

---

## Pull Requests

### Before You Start

1. Check existing issues/PRs to avoid duplicates
2. For major changes, open an issue first to discuss
3. Fork the repo and create a branch from `main`

### PR Process

1. **Fork** and clone the repo
2. **Create a branch:** `git checkout -b feature/your-feature`
3. **Make changes** with tests
4. **Test:** `pytest tests/`
5. **Commit:** Use clear commit messages
6. **Push:** `git push origin feature/your-feature`
7. **Open PR** against `main`

### Commit Messages

```
type: short description

Longer description if needed.

Fixes #123
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `style`, `chore`

Examples:
- `feat: add rate limiting to API endpoints`
- `fix: handle empty responses in orchestrator`
- `docs: update quick start guide`
- `test: add tests for task decomposer`

---

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR-USERNAME/Abby-Unleashed-Core.git
cd Abby-Unleashed-Core

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt
pip install -e .  # Install in editable mode

# Install dev dependencies
pip install pytest pytest-cov black flake8

# Start Ollama
ollama serve
ollama pull qwen2.5:latest
```

---

## Code Style

We use:
- **Black** for formatting
- **Flake8** for linting
- **Type hints** where helpful

```bash
# Format code
black .

# Check linting
flake8 --max-line-length=100

# Before committing
black . && flake8 --max-line-length=100 && pytest
```

### Guidelines

1. **Keep it simple** - Clear code > clever code
2. **Document public APIs** - Docstrings for classes and functions
3. **Type hints** - For function signatures
4. **Small functions** - One function, one job
5. **Tests** - For new features and bug fixes

---

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test file
pytest tests/test_agents.py -v

# Run specific test
pytest tests/test_agents.py::test_agent_creation -v
```

### Writing Tests

Put tests in `tests/` directory. Use pytest fixtures for shared setup.

```python
# tests/test_my_feature.py
import pytest
from my_module import MyClass

@pytest.fixture
def my_object():
    return MyClass(param="value")

def test_my_feature(my_object):
    result = my_object.do_something()
    assert result == expected_value

def test_edge_case():
    with pytest.raises(ValueError):
        MyClass(param="invalid")
```

---

## Project Structure

```
Abby-Unleashed-Core/
├── agents/           # Agent system (DNA, base classes, factory)
├── coordination/     # Multi-agent coordination
├── task_engine/      # Task decomposition and planning
├── speech_interface/ # Voice (STT, TTS, wake word)
├── memory/           # Memory systems
├── learning/         # Learning and optimization
├── persona_library/  # Reusable personas
├── config/           # Configuration files
├── tests/            # Test suite
├── docs/             # Documentation
└── examples/         # Example scripts
```

---

## Getting Help

- 💬 Open a [Discussion](https://github.com/Abbystarchild/Abby-Unleashed-Core/discussions)
- 🐛 File an [Issue](https://github.com/Abbystarchild/Abby-Unleashed-Core/issues)
- 📖 Read the [Documentation](docs/)

---

## Recognition

Contributors are listed in the README. Thank you! 🙏
