# Abby Conversation Quality Improvement Plan

## Current Problem
Abby "sounds dumb" despite having sophisticated capabilities. The issue is:
1. **Poor prompt engineering** - System prompts are task-focused, not conversational
2. **Model limitations** - Small local models can't match cloud AI without optimization
3. **No conversation benchmarks** - We can't improve what we don't measure

## Goal
Make Abby conversationally indistinguishable from Copilot for general chat.

---

## Phase 1: Model Optimization (Day 1)

### 1.1 Check Available Models
```bash
ollama list
```
Recommended models for conversation (in order of quality):
- `llama3.1:70b` - Best quality, needs 48GB+ VRAM
- `llama3.1:8b` - Great balance, needs 8GB VRAM
- `mistral-nemo:12b` - Excellent conversation, 12GB VRAM
- `qwen2.5:14b` - Very capable, 16GB VRAM
- `mistral:7b` - Current, decent but needs help

### 1.2 Optimal Model Parameters
```yaml
# Conversation-optimized settings
temperature: 0.7          # Balanced creativity
top_p: 0.9                # Nucleus sampling
top_k: 40                 # Limit vocabulary
repeat_penalty: 1.1       # Slight penalty (not 1.8!)
num_predict: 256          # Reasonable length
num_ctx: 4096             # Good context window
```

**Key insight:** `repeat_penalty: 1.8` is WAY too high. This makes responses stilted.

---

## Phase 2: System Prompt Rewrite (Day 1-2)

### 2.1 Current Problem
The current prompt is:
- Too long and complex
- Task-execution focused
- Has contradictory instructions
- Stuffed with capabilities

### 2.2 New Conversational Prompt
```
You are Abby, a friendly AI assistant. 

CORE RULES:
1. Be natural and conversational
2. Keep responses 1-3 sentences unless asked for more
3. Never repeat yourself or the user's question
4. Be direct - don't hedge with "I think" or "maybe"
5. Match the user's energy and tone

You remember previous conversations and know your user personally.
```

That's it. Simple, clear, effective.

### 2.3 Context Injection (done separately)
- User identity (who they are)
- Recent conversation (last 5-10 turns)
- Current visual context (if watching)

---

## Phase 3: Response Quality Pipeline (Day 2-3)

### 3.1 Pre-Processing
Before sending to LLM:
- Strip excessive whitespace
- Detect question vs command vs statement
- Add minimal context

### 3.2 Post-Processing
After receiving from LLM:
- Remove self-references ("As an AI...")
- Trim excessive length (hard cap at 500 chars for chat)
- Detect and remove repetition
- Clean markdown artifacts

### 3.3 Response Quality Checks
```python
def is_quality_response(response: str) -> bool:
    # Not too short
    if len(response) < 10:
        return False
    # Not too long
    if len(response) > 500:
        return False  # Trigger retry with "be more concise"
    # No AI disclaimers
    if "as an ai" in response.lower():
        return False
    # No repetition of question
    # No excessive hedging
    return True
```

---

## Phase 4: Conversation Memory (Day 3-4)

### 4.1 Smart History Management
```python
# Keep last N turns, but summarize older ones
MAX_FULL_TURNS = 6
MAX_SUMMARY_TURNS = 20

def get_conversation_context(history):
    recent = history[-MAX_FULL_TURNS:]
    older = history[:-MAX_FULL_TURNS]
    
    if older:
        summary = summarize_conversation(older)
        return [{"role": "system", "content": f"Earlier: {summary}"}] + recent
    return recent
```

### 4.2 User Memory
- Remember facts about the user
- Reference previous conversations naturally
- "Last time you mentioned..."

---

## Phase 5: Conversation Quality Benchmarks (Day 4-5)

### 5.1 Test Categories
1. **Greeting & Small Talk** - Natural, warm responses
2. **Simple Questions** - Direct, accurate answers
3. **Follow-up Questions** - Context awareness
4. **Complex Questions** - Thoughtful, structured responses
5. **Humor & Banter** - Appropriate tone matching
6. **Corrections** - Graceful handling of mistakes

### 5.2 Example Benchmarks
```python
CONVERSATION_BENCHMARKS = [
    {
        "input": "Hey",
        "good_patterns": ["Hey!", "Hi!", "Hello!"],
        "bad_patterns": ["Hello! How can I assist you today?", "Greetings!"],
        "max_length": 50
    },
    {
        "input": "What's 2+2?",
        "good_patterns": ["4", "Four"],
        "bad_patterns": ["Let me calculate", "The answer is"],
        "max_length": 20
    },
    {
        "input": "Tell me a joke",
        "requirements": ["actually_funny", "not_a_pun", "complete_joke"],
        "max_length": 200
    }
]
```

---

## Phase 6: Implementation Files

### Files to Create/Modify:
1. `config/conversation_settings.yaml` - Model params & prompts
2. `conversation/quality_filter.py` - Response post-processing
3. `conversation/context_manager.py` - Smart history management
4. `tests/test_conversation_quality.py` - Benchmark tests

### Files to Modify:
1. `cli.py` - Use new prompt system
2. `realtime_conversation.py` - Integrate quality filters
3. `api_server.py` - Update conversation endpoints

---

## Phase 7: Quick Wins (Immediate Impact)

### 7.1 Fix Right Now
1. ❌ `repeat_penalty: 1.8` → ✅ `repeat_penalty: 1.1`
2. ❌ Complex 20-line prompt → ✅ Simple 5-line prompt
3. ❌ `num_predict: 150` → ✅ `num_predict: 256`

### 7.2 Test Immediately
After each change, test with:
- "Hey Abby"
- "What's the weather like?" (tests admitting uncertainty)
- "Tell me something interesting"
- "Remember when we..." (tests memory)

---

## Success Criteria

Abby passes conversation quality if:
- [ ] Responds in <2 seconds
- [ ] Responses feel natural (not robotic)
- [ ] Never says "As an AI..."
- [ ] Remembers conversation context
- [ ] Matches user's tone
- [ ] Keeps responses appropriately brief
- [ ] Can handle humor
- [ ] Admits when she doesn't know something
- [ ] Doesn't repeat herself

---

## Timeline

| Day | Phase | Deliverable |
|-----|-------|-------------|
| 1 | Model + Params | Optimal settings configured |
| 1-2 | Prompt Rewrite | New system prompt deployed |
| 2-3 | Quality Pipeline | Response filtering working |
| 3-4 | Memory | Smart context management |
| 4-5 | Benchmarks | Quality tests passing |
| 5+ | Iteration | Continuous improvement |

---

## Let's Start Now

Ready to implement Phase 1 & 2 (the quick wins that will have immediate impact)?
