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

### 7. Dynamic Knowledge Loader ✨ NEW

On-demand knowledge loading system that minimizes memory while enabling cross-disciplinary access.

**Location**: `agents/dynamic_knowledge_loader.py`

**Features**:
- **Role-Based Loading**: Maps agent roles to primary knowledge domains
- **Task-Based Dynamic Loading**: Detects topics and loads relevant modules
- **Memory Optimization**: Tracks and optimizes loaded modules
- **Cross-Disciplinary Access**: Any agent can request any knowledge

**Knowledge Categories** (30+ files, ~16,000 lines):
- Core: `coding_foundations`, `general_programming`
- Languages: `python_mastery`, `javascript_typescript_mastery`, `kotlin_mastery`
- Domains: `frontend_mastery`, `backend_mastery`, `api_design_mastery`
- Infrastructure: `devops_mastery`, `docker_mastery`, `sre_mastery`
- Data: `database_mastery`, `postgresql_mastery`, `data_engineering_mastery`
- Security: `security_mastery`, `hacking_penetration_testing_mastery`
- Quality: `testing_mastery`, `qa_mastery`, `debugging_mastery`
- ML/AI: `ml_engineering_mastery`

### 8. Knowledge Version Control ✨ NEW

Version control and auto-update system for knowledge bases.

**Location**: `agents/knowledge_version_control.py`

**Features**:
- SHA256 hash-based version tracking
- Timestamped backups before updates
- Rollback to previous versions
- Auto-detection of outdated content
- Pending updates queue for review

**CLI Commands**:
```bash
python knowledge_version_control.py status        # Check all files
python knowledge_version_control.py backup        # Create backup
python knowledge_version_control.py rollback <name>  # Restore previous
python knowledge_version_control.py check-updates # Find outdated content
```

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

### 8. PersonaPlex Speech Interface (Phase 3)

Complete speech-to-speech interaction system for real-time voice conversations.

**Location**: `speech_interface/`

**Components**:
- **STTEngine**: Speech-to-text using faster-whisper (Whisper models)
- **TTSEngine**: Text-to-speech using piper-tts for natural voice synthesis
- **VADDetector**: Voice activity detection using silero-vad
- **WakeWordDetector**: Wake word detection with pvporcupine ("Hey Abby")
- **ConversationManager**: Orchestrates the complete conversation flow

**Features**:
- Real-time speech transcription
- Natural voice synthesis
- Automatic speech detection
- Wake word activation
- Conversation state management
- Seamless integration with task execution
- 100% offline operation

**Flow**:
1. User says wake word ("Hey Abby")
2. System activates and responds
3. VAD detects user speech
4. STT transcribes audio to text
5. Text sent to task executor
6. Response generated
7. TTS synthesizes response
8. Audio played back to user
### 8. Coordination System (Phase 3)

**NEW**: Multi-agent coordination system for orchestrating complex workflows.

**Location**: `coordination/`

**Components**:

#### Orchestrator
Master coordinator that integrates all components for multi-agent task execution.

**Features**:
- Integrates with task engine for decomposition and planning
- Creates and manages multiple agents
- Coordinates execution across agents
- Tracks progress and aggregates results
- Handles task dependencies and parallel execution

#### Message Bus
Pub/sub messaging system for inter-agent communication.

**Features**:
- Asynchronous message delivery
- Message type filtering
- Subscriber management
- Message history
- Broadcast and direct messaging

#### Task Tracker
Tracks status and progress of all tasks in a workflow.

**Features**:
- Task lifecycle management (pending → assigned → in_progress → completed/failed)
- Dependency checking
- Progress tracking (0.0 to 1.0)
- Status filtering
- Overall progress calculation

#### Result Aggregator
Collects and combines results from multiple agents.

**Features**:
- Result collection from multiple agents
- Task result aggregation
- Workflow result compilation
- Multiple output formats (summary, detailed, JSON)
- Agent contribution tracking

## Data Flow

```
User Task
    ↓
Task Analysis (TaskAnalyzer)
    ↓
    ├─→ Simple Task? → Single Subtask (No decomposition)
    └─→ Complex Task? → Task Decomposition (Multiple subtasks)
            ↓
Task Decomposition (TaskDecomposer)
    ↓
Dependency Mapping (DependencyMapper)
    ↓
Execution Planning (ExecutionPlanner)
    ↓
Orchestrator (Phase 3) ← NEW!
    ↓
    ├─→ Message Bus: Publish task assignments
    ├─→ Task Tracker: Track task status
    └─→ Agent Creation & Execution
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
Result Aggregator ← NEW!
    ↓
    ├─→ Collect results from all agents
    ├─→ Aggregate workflow results
    └─→ Format final output
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
├── clarification_protocol.py
├── dynamic_knowledge_loader.py  # ✨ NEW! On-demand knowledge
├── knowledge_version_control.py # ✨ NEW! Versioning/updates
└── knowledge/              # 30+ mastery files (~16,000 lines)

task_engine/                # Task decomposition system
├── __init__.py
├── task_analyzer.py        # Task analysis and classification
├── decomposer.py           # Recursive task breakdown
├── dependency_mapper.py    # Dependency graph (DAG)
└── execution_planner.py    # Execution planning

coordination/               # Agent coordination (Phase 3) ← NEW!
├── __init__.py
├── orchestrator.py         # Master coordinator
├── message_bus.py          # Inter-agent communication
├── task_tracker.py         # Progress tracking
└── result_aggregator.py    # Result aggregation

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
├── test_speech_interface.py
├── test_persona_library.py
├── test_task_engine.py
├── test_coordination.py
└── test_agent_stress.py   # ✨ NEW! Stress/capacity testing

examples/                   # Example scripts
├── create_web_scraper.py
├── persona_library_demo.py
├── agent_factory_demo.py
├── task_engine_demo.py
└── coordination_demo.py   # ← NEW!
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

## Stress Testing & Optimization ✨ NEW

**Location**: `tests/test_agent_stress.py`

The stress testing system determines optimal concurrent agent count within memory limits.

### Memory Thresholds

| Threshold | Value | Purpose |
|-----------|-------|---------|
| MAX_MEMORY_PERCENT | 70% | Stop spawning agents |
| OPTIMAL_MEMORY_PERCENT | 50% | Ideal operating range |
| MIN_FREE_GB | 2 | Safety buffer |

### Test Categories

1. **Capacity Testing**: `test_find_max_concurrent_agents`
   - Gradually spawns agents until memory threshold
   - Records max safe concurrent count

2. **Knowledge Access**: `TestKnowledgeAccess`
   - Verifies agents load correct knowledge for their role
   - Tests cross-disciplinary knowledge access

3. **Memory Limits**: `test_memory_stays_within_limits`
   - Ensures system never exceeds safety thresholds
   - Tests graceful degradation

4. **Task Capabilities**: `TestAgentTaskCapabilities`
   - Challenges agents with domain-specific tasks
   - Validates knowledge application

### Typical Results (16GB RAM)

```
Max safe agents:     8-12
Optimal agents:      5-8
Per-agent (full):    ~300-500MB
Per-agent (dynamic): ~50-100MB
```

### Running Stress Tests

```bash
# Full stress test suite
pytest tests/test_agent_stress.py -v

# Find max agents
pytest tests/test_agent_stress.py::TestOptimalAgentCalculation -v

# Memory validation
pytest tests/test_agent_stress.py::test_memory_stays_within_limits -v
```

## Agents vs Persona Library ✨ CLARIFICATION

A common point of confusion - here's the distinction:

| Aspect | Agents (`agents/`) | Persona Library (`persona_library/`) |
|--------|-------------------|-------------------------------------|
| **Purpose** | Runtime execution | Persistent storage |
| **Contains** | Live Agent objects | AgentDNA YAML files |
| **Lifecycle** | Created/destroyed per task | Persists across sessions |
| **Memory** | Active RAM usage | Disk storage |
| **Function** | Doing work | Remembering templates |

**The Flow**:
```
Task Request
    ↓
AgentFactory
    ↓
Check PersonaLibrary → Match Found? → Load existing AgentDNA
                       No Match?    → Generate new AgentDNA → Save to Library
    ↓
Create Agent (runtime object)
    ↓
Load Knowledge (dynamic_knowledge_loader)
    ↓
Execute Task
    ↓
Agent destroyed (memory freed)
PersonaLibrary retains DNA for future use
```

Think of it like:
- **PersonaLibrary** = Resume filing cabinet (persistent templates)
- **Agents** = Actual workers (created from resumes, do the work)

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

**Version**: 0.4.0 (Phase 4 - Knowledge Management & Testing)
