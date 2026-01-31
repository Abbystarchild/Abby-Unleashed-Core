# Abby Unleashed Core - Architecture

## System Overview

Abby Unleashed is a modular, offline-capable AI orchestration system built around the concept of **digital cloning** and **intelligent agent coordination**.

## Core Components

### 1. Agent DNA Framework

The 5-Element DNA system ensures every agent has:

```
1. ROLE + SENIORITY (Who they are)
2. DOMAIN/INDUSTRY CONTEXT (What they know)
3. METHODOLOGIES (How they work)
4. CONSTRAINTS (What limits them)
5. OUTPUT FORMAT (What they deliver)
```

**Location**: `agents/agent_dna.py`

**Key Features**:
- Immutable agent identity
- Portable and serializable
- Self-validating
- Trackable (usage, success rate)

### 2. Persona Library

A persistent storage system for reusable agent personas.

**Location**: `persona_library/`

**Features**:
- YAML-based storage
- Automatic matching
- Version tracking
- Usage statistics
- CRUD operations

**Benefits**:
- Create once, use forever
- Improves over time
- Reduces redundancy
- Faster agent spawning

### 3. Clarification Protocol

Ensures agents **never guess** - they ask questions when information is insufficient.

**Location**: `agents/clarification_protocol.py`

**Checks**:
- Clear objective?
- Constraints defined?
- Output requirements clear?
- Domain specifics provided?

### 4. Personality System (Brain Clone)

Loads and applies personality configuration to all agents.

**Location**: `personality/brain_clone.py`

**Configuration**: `config/brain_clone.yaml`

**Components**:
- Identity (name, role)
- Communication style
- Decision making patterns
- Work style preferences
- Core values
- Conversation patterns

### 5. Ollama Integration

Local LLM integration for 100% offline operation.

**Location**: `ollama_integration/`

**Features**:
- Client wrapper
- Model selection (code, reasoning, general, creative)
- Streaming support
- Context management

### 6. Agent Factory

Creates agents dynamically based on task requirements.

**Location**: `agents/agent_factory.py`

**Process**:
1. Analyze task requirements
2. Check persona library for match
3. If match: reuse existing persona
4. If no match: generate new DNA
5. Create agent with DNA + personality
6. Save new persona to library

### 7. Task Engine (Phase 2)

A complete system for breaking down complex tasks into manageable subtasks with dependency management.

**Location**: `task_engine/`

**Components**:
- **TaskAnalyzer**: Analyzes task complexity, identifies domains, determines if decomposition is needed
- **TaskDecomposer**: Breaks complex tasks into subtasks using domain-specific strategies
- **DependencyMapper**: Creates directed acyclic graph (DAG) of task dependencies
- **ExecutionPlanner**: Generates optimized execution plans with parallel execution support

**Features**:
- Automatic complexity detection (simple, medium, complex)
- Domain identification (development, devops, data, research, etc.)
- Recursive task breakdown
- Cycle detection in dependencies
- Parallel execution identification
- Critical path calculation
- Progress tracking

## Data Flow

```
User Task
    ↓
Task Analysis (TaskAnalyzer)
    ↓
    ├─→ Simple Task? → Direct Execution
    └─→ Complex Task? → Task Decomposition
            ↓
Task Decomposition (TaskDecomposer)
    ↓
Dependency Mapping (DependencyMapper)
    ↓
Execution Planning (ExecutionPlanner)
    ↓
Persona Library Check
    ↓
    ├─→ Match Found? → Reuse Persona
    └─→ No Match? → Generate New DNA → Save to Library
    ↓
Agent Creation (DNA + Personality)
    ↓
Clarification Protocol
    ↓
    ├─→ Insufficient Info? → Ask Questions
    └─→ Complete Info? → Execute Task
    ↓
Task Execution (via LLM)
    ↓
Result
```

## Directory Structure

```
agents/                      # Core agent system
├── __init__.py
├── agent_dna.py            # 5-element DNA
├── base_agent.py           # Base agent class
├── agent_factory.py        # Agent creation
└── clarification_protocol.py

task_engine/                # Task decomposition system
├── __init__.py
├── task_analyzer.py        # Task analysis and classification
├── decomposer.py           # Recursive task breakdown
├── dependency_mapper.py    # Dependency graph (DAG)
└── execution_planner.py    # Execution planning

personality/                 # Personality system
├── __init__.py
└── brain_clone.py          # Personality loader

persona_library/            # Reusable personas
├── __init__.py
├── library_manager.py      # CRUD operations
└── personas/
    ├── personas.yaml       # Storage (created on first use)
    └── examples/           # Pre-built personas
        ├── senior_devops_engineer.yaml
        └── growth_product_manager.yaml

ollama_integration/         # LLM integration
├── __init__.py
├── client.py              # Ollama API client
└── model_selector.py      # Model selection

config/                     # Configuration
├── brain_clone.yaml       # Personality config
├── ollama_models.yaml     # Model preferences
└── system_config.yaml     # System settings

tests/                      # Test suite
├── test_agent_dna.py
├── test_agents.py
├── test_persona_library.py
└── test_task_engine.py

examples/                   # Example scripts
├── create_web_scraper.py
├── persona_library_demo.py
├── agent_factory_demo.py
└── task_engine_demo.py
```

## Design Principles

### 1. Offline-First
- No cloud dependencies
- All models run locally
- Complete data privacy

### 2. Reusability
- Personas stored in library
- Automatic matching before creation
- Success tracking

### 3. Professional Behavior
- Always ask questions when uncertain
- Never guess or assume
- Validate all DNA elements

### 4. Modularity
- Clear separation of concerns
- Easy to extend
- Independent components

### 5. Observability
- Comprehensive logging
- Usage tracking
- Performance metrics

## Extension Points

### Adding New Agent Types
1. Extend `base_agent.py`
2. Define specific DNA requirements
3. Add to agent factory logic

### Adding New Personas
1. Create YAML file in `persona_library/personas/examples/`
2. Include all 5 DNA elements
3. Library auto-loads on startup

### Adding New Capabilities
1. Create new module in appropriate directory
2. Import in main orchestrator
3. Update configuration as needed

## Future Architecture

### Phase 3: Coordination
```
coordination/
├── orchestrator.py         # Master coordinator
├── message_bus.py          # Inter-agent communication
├── task_tracker.py         # Progress tracking
└── result_aggregator.py
```

### Phase 4: Memory & Learning
```
memory/
├── short_term.py           # Conversation context
├── working_memory.py       # Active tasks
├── long_term.py           # SQLite + embeddings
└── semantic_search.py     # RAG

learning/
├── outcome_evaluator.py
├── delegation_optimizer.py
└── skill_library.py
```

### Phase 5: Speech Interface
```
speech_interface/
├── stt_engine.py          # Whisper
├── tts_engine.py          # Piper
├── vad_detector.py        # Voice activity
├── wake_word.py           # "Hey Abby"
└── conversation_manager.py
```

## Configuration Management

All configuration is YAML-based for easy editing:

- `config/brain_clone.yaml` - Personality
- `config/ollama_models.yaml` - Model preferences
- `config/system_config.yaml` - System settings
- `.env` - Environment variables

## Testing Strategy

- Unit tests for core components
- Integration tests for workflows
- Example scripts for validation
- Continuous testing in CI/CD (planned)

## Performance Considerations

- Lazy loading of models
- Connection pooling for Ollama
- Caching of persona lookups
- Streaming responses for UX
- Async agent execution (planned)

---

**Version**: 0.1.0 (Phase 1 Complete)
