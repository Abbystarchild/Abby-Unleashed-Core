# 🚀 Abby Unleashed Core

**Complete Digital Clone System** with AI orchestration, personality cloning, and 100% offline operation.

## Overview

Abby Unleashed is a fully-functional, offline-capable AI orchestration system that serves as a digital clone. It combines:

- **Real-time speech-to-speech interface** (PersonaPlex integrated ✅)
- **Dynamic multi-agent orchestration** with recursive task decomposition
- **Personality cloning system** (your "brain clone")
- **Reusable persona library** with 5-element agent DNA
- **Learning and memory systems** for continuous improvement
- **100% offline operation** using Ollama + local speech models

## Features

✅ **PersonaPlex Voice Interface**
- Real-time speech-to-speech interaction
- Wake word detection ("Hey Abby")
- Voice Activity Detection (VAD)
- Natural text-to-speech synthesis
- Offline speech recognition with Whisper

✅ **5-Element Agent DNA Framework**
- Role + Seniority
- Industry/Domain Context
- Methodologies
- Constraints
- Output Format

✅ **Clarification Protocol**
- Agents ALWAYS ask questions when uncertain
- No assumptions or guessing
- Professional expert behavior

✅ **Persona Library**
- Create once, use forever
- Automatic persona matching
- Success tracking and improvement

✅ **Brain Clone System**
- Complete personality configuration
- Decision-making patterns
- Communication style
- Values and priorities

## Quick Start

### Prerequisites

- Python 3.9+
- [Ollama](https://ollama.ai/) installed and running
- Optional: Audio devices for speech interface

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Abbystarchild/Abby-Unleashed-Core.git
cd Abby-Unleashed-Core
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy environment file:
```bash
cp .env.example .env
```

4. Start Ollama (in another terminal):
```bash
ollama serve
```

5. Pull a model:
```bash
ollama pull qwen2.5:latest
```

### Usage

#### Text Mode (Default)
```bash
python cli.py text
```

#### Voice Mode (PersonaPlex)
```bash
python cli.py voice
```

**Voice Mode Features:**
- Say "Hey Abby" to activate listening
- Natural conversation flow with voice responses
- Automatic speech detection
- Real-time transcription and processing

#### Direct Task Execution
```bash
python cli.py task --task "Create a web scraper for product prices"
```

## Project Structure

```
Abby-Unleashed-Core/
├── agents/                    # Agent system with DNA framework
│   ├── agent_dna.py          # 5-element DNA definition
│   ├── base_agent.py         # Base agent class
│   ├── agent_factory.py      # Agent creation
│   └── clarification_protocol.py
├── speech_interface/          # PersonaPlex integration
│   ├── stt_engine.py         # Speech-to-text (Whisper)
│   ├── tts_engine.py         # Text-to-speech (Piper)
│   ├── vad_detector.py       # Voice activity detection
│   ├── wake_word.py          # Wake word detection
│   └── conversation_manager.py # Conversation orchestration
├── task_engine/              # Task decomposition and planning
│   ├── task_analyzer.py      # Task analysis and classification
│   ├── decomposer.py         # Recursive task breakdown
│   ├── dependency_mapper.py  # Dependency graph (DAG)
│   └── execution_planner.py  # Execution planning
├── coordination/             # Agent coordination system (Phase 3)
│   ├── orchestrator.py       # Master coordinator
│   ├── message_bus.py        # Inter-agent communication
│   ├── task_tracker.py       # Progress tracking
│   └── result_aggregator.py  # Result aggregation
├── personality/               # Personality system
│   └── brain_clone.py        # Personality loader
├── persona_library/           # Reusable persona storage
│   ├── library_manager.py
│   └── personas/
│       └── examples/         # Pre-built personas
├── ollama_integration/        # Ollama API integration
│   ├── client.py
│   └── model_selector.py
├── config/                    # Configuration files
│   ├── brain_clone.yaml      # Personality config
│   ├── ollama_models.yaml    # Model preferences
│   └── system_config.yaml    # System settings
├── cli.py                     # Main CLI interface
├── requirements.txt
└── setup.py
```

## Configuration

### Personality Configuration

Edit `config/brain_clone.yaml` to customize Abby's personality:

```yaml
identity:
  name: "Abbystarchild"
  role: "Digital Clone and AI Orchestrator"

communication_style:
  tone: "warm but professional"
  verbosity: "concise with depth when needed"
  clarification_behavior: "always ask when uncertain"

values:
  top_priorities:
    - "Privacy and offline-first"
    - "Quality and reliability"
```

### Model Configuration

Edit `config/ollama_models.yaml` to set model preferences:

```yaml
models:
  code:
    - "qwen2.5-coder:latest"
  reasoning:
    - "deepseek-r1:latest"
```

## Examples

### Creating a Custom Agent

```python
from agents import AgentDNA, Agent

# Define agent DNA
dna = AgentDNA(
    role="DevOps Engineer",
    seniority="Senior",
    domain="Cloud Infrastructure",
    industry_knowledge=["AWS", "Kubernetes", "Terraform"],
    methodologies=["GitOps", "IaC", "Blue-green deployment"],
    constraints={"budget": "$500/month", "security": "SOC 2"},
    output_format={"code": "Terraform", "docs": "Markdown"}
)

# Create agent
agent = Agent(dna=dna)

# Execute task
result = agent.execute_task("Deploy web app to AWS", {})
```

### Using the Orchestrator

```python
from cli import AbbyUnleashed

# Initialize
abby = AbbyUnleashed()

# Execute task
result = abby.execute_task("Build a REST API for user management")

# Check persona library stats
stats = abby.get_stats()
print(f"Total personas: {stats['persona_library']['total_personas']}")
```

### Using the Orchestrator

```python
from cli import AbbyUnleashed

# Initialize
abby = AbbyUnleashed()

# Execute task with orchestrator (Phase 3)
result = abby.execute_task("Build a REST API for user management")

# Get progress
progress = abby.get_orchestrator_progress()
print(f"Overall progress: {progress['overall_progress']:.1%}")

# Check stats
stats = abby.get_stats()
print(f"Total tasks: {stats['orchestrator']['task_stats']['total_tasks']}")
```

### Using the Task Engine

```python
from task_engine import TaskAnalyzer, TaskDecomposer, DependencyMapper, ExecutionPlanner

# Initialize components
analyzer = TaskAnalyzer()
decomposer = TaskDecomposer()
mapper = DependencyMapper()
planner = ExecutionPlanner()

# Analyze a complex task
task = "Build a REST API with authentication and deploy to AWS"
analysis = analyzer.analyze(task)
print(f"Complexity: {analysis['complexity'].value}")
print(f"Domains: {analysis['domains']}")

# Decompose into subtasks
decomposition = decomposer.decompose(analysis)
print(f"Subtasks: {len(decomposition['subtasks'])}")

# Build dependency graph
dep_map = mapper.build_graph(decomposition['subtasks'])
print(f"Execution order: {dep_map['execution_order']}")

# Create execution plan
plan = planner.create_plan(dep_map, decomposition['subtasks'])
print(f"Total steps: {plan['total_steps']}")
print(f"Can parallelize: {plan['can_parallelize']}")
```

## Development Status

### ✅ Completed (Phase 1)
- [x] Agent DNA framework (5-element system)
- [x] Base agent classes and factory
- [x] Clarification protocol
- [x] Persona library with CRUD operations
- [x] Ollama integration client
- [x] Model selector
- [x] Personality system (brain clone)
- [x] CLI interface (text mode)
- [x] Configuration system
- [x] Example personas

### ✅ Completed (Phase 2)
- [x] Task decomposition engine
  - [x] Task analyzer (complexity detection, domain identification)
  - [x] Task decomposer (recursive breakdown with domain strategies)
  - [x] Dependency mapper (DAG creation, cycle detection)
  - [x] Execution planner (parallel execution, critical path)

### ✅ Completed (Phase 3)
- [x] Agent coordination system
  - [x] Orchestrator (master coordinator for multi-agent tasks)
  - [x] Message bus (inter-agent communication with pub/sub)
  - [x] Task tracker (progress tracking for all tasks)
  - [x] Result aggregator (combines outputs from multiple agents)
  - [x] Integration with task engine and agent factory
  - [x] CLI integration with orchestrator

### 🚧 In Progress
- [ ] Speech interface (STT, TTS, VAD)
- [ ] Memory systems
- [ ] Learning systems
- [ ] Web dashboard

### 📋 Planned
- [ ] Advanced task planning
- [ ] Knowledge graph
- [ ] Performance optimization
- [ ] Comprehensive testing

## Documentation

- [Quick Start Guide](docs/QUICK_START.md)
- [Architecture Overview](docs/ARCHITECTURE.md)
- [PersonaPlex Integration Guide](docs/PERSONAPLEX_INTEGRATION.md) ⭐ NEW

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- Inspired by [PersonaPlex](https://github.com/NVIDIA/personaplex)
- Built with [Ollama](https://ollama.ai/)
- Speech capabilities via Whisper and Piper

---

**Built with ❤️ by Abbystarchild**
