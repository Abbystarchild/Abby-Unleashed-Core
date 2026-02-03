"""
Streaming Conversation Manager for Abby Unleashed

Enables:
- Real-time streaming of responses (like ChatGPT/Claude)
- Visible thinking process [THINKING] vs [SPEAKING]
- Multi-step task planning and execution
- User interrupts mid-task
- PersonaPlex integration for natural conversation flow
- Response quality validation
"""
import asyncio
import json
import logging
import time
import re
import queue
import threading
from typing import Optional, Dict, Any, List, Callable, Generator
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


def is_overwhelming_task(task: str) -> bool:
    """
    Check if a task is too complex to handle in one go.
    
    Signs of an overwhelming task:
    - Very long description (1500+ chars)
    - Multiple numbered steps or bullet points (5+)
    - Multiple different features/pages mentioned
    - Words like "complete app", "full project", "production ready"
    """
    task_lower = task.lower()
    
    # Length check
    if len(task) > 1500:
        return True
    
    # Count numbered items
    numbered = len(re.findall(r'(?:^|\n)\s*\d+[\.\):]', task))
    if numbered >= 5:
        return True
    
    # Count bullet points
    bullets = len(re.findall(r'(?:^|\n)\s*[-•*]\s+', task))
    if bullets >= 5:
        return True
    
    # Check for "build entire app" patterns
    overwhelming_patterns = [
        r'complete\s+(?:app|application|project)',
        r'production\s+ready',
        r'fully?\s+(?:fleshed|completed|functional)',
        r'from\s+scratch',
        r'entire\s+(?:app|system|project)',
        r'work\s+on\s+both\s+(?:ios|apple)\s+and\s+android',
    ]
    if any(re.search(pattern, task_lower) for pattern in overwhelming_patterns):
        return True
    
    # Count distinct pages/screens mentioned
    pages = set(re.findall(r'(\w+)\s+(?:page|screen|view)', task_lower))
    if len(pages) >= 4:
        return True
    
    return False


# Banned phrases that indicate a broken/generic response
BANNED_RESPONSE_PATTERNS = [
    r"^hey there[!,.]?\s*",
    r"^hi there[!,.]?\s*", 
    r"^hello there[!,.]?\s*",
    r"^how are ya",
    r"^i hope you",
    r"^let me know if",
    r"^is there anything else",
    r"^i'm happy to help",
    r"^hey buddy[!,.]?\s*",
    r"^thanks for letting me know",
]


def is_response_broken(response: str, conversation_history: List[Dict] = None) -> tuple:
    """
    Check if a response appears broken/repetitive.
    
    Returns:
        (is_broken: bool, reason: str or None)
    """
    if not response:
        return True, "Empty response"
    
    response_lower = response.lower().strip()
    
    # Check for banned patterns
    for pattern in BANNED_RESPONSE_PATTERNS:
        if re.match(pattern, response_lower, re.IGNORECASE):
            return True, f"Response starts with banned pattern: {pattern}"
    
    # Check for repetition with recent history
    if conversation_history:
        recent_assistant_msgs = [
            msg.get('content', '').lower()[:50] 
            for msg in conversation_history[-4:] 
            if msg.get('role') == 'assistant'
        ]
        
        response_start = response_lower[:50]
        for prev in recent_assistant_msgs:
            if prev and response_start == prev:
                return True, "Response is identical to a recent response"
    
    return False, None


class ThinkingState(Enum):
    """What Abby is currently doing"""
    IDLE = "idle"
    LISTENING = "listening"    # Actively listening for speech
    THINKING = "thinking"      # Processing/reasoning internally
    SPEAKING = "speaking"      # Generating response for user
    DOING = "doing"           # Executing an action (file ops, commands)
    WAITING = "waiting"       # Waiting for user input
    INTERRUPTED = "interrupted"  # User interrupted


@dataclass
class TaskStep:
    """A single step in a multi-step task"""
    id: int
    description: str
    status: str = "pending"  # pending, in-progress, completed, skipped
    result: Optional[str] = None


@dataclass 
class StreamEvent:
    """An event in the response stream"""
    type: str  # 'thinking', 'text', 'action', 'step', 'done', 'error', 'interrupt', 'listening'
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> dict:
        return {
            'type': self.type,
            'content': self.content,
            'metadata': self.metadata,
            'timestamp': self.timestamp
        }
    
    def to_sse(self) -> str:
        """Format as Server-Sent Event"""
        return f"data: {json.dumps(self.to_dict())}\n\n"


class StreamingConversation:
    """
    Manages streaming, continuous conversation with Abby.
    Integrates PersonaPlex features for natural conversation.
    
    Features:
    - Streams tokens as they're generated
    - Shows thinking process before final response
    - Plans multi-step tasks and shows progress
    - Accepts interrupts from user (even mid-speech)
    - Natural turn-taking with PersonaPlex VAD
    """
    
    def __init__(self, abby_instance=None):
        self.abby = abby_instance
        self.state = ThinkingState.IDLE
        self.current_task: Optional[str] = None
        self.task_steps: List[TaskStep] = []
        self.current_step_index = 0
        
        # Interrupt handling - supports mid-speech interrupts
        self.interrupt_requested = False
        self.interrupt_message: Optional[str] = None
        self.can_be_interrupted = True  # Allow interrupts during speech
        
        # Event queue for streaming
        self.event_queue: queue.Queue = queue.Queue()
        
        # Callbacks
        self.on_state_change: Optional[Callable] = None
        self.on_event: Optional[Callable] = None
        self.on_user_speaking: Optional[Callable] = None  # Called when user starts speaking (for interrupt)
        
        # Conversation context
        self.conversation_history: List[Dict] = []
        
        # PersonaPlex conversation manager (optional, for full local speech)
        self._personaplex_manager = None
        
        # Speaking state for interrupt detection
        self._is_speaking = False
        self._speech_start_time = None
        
        logger.info("StreamingConversation initialized with interrupt support")
    
    def enable_personaplex(self):
        """
        Enable full PersonaPlex features (local STT, VAD, wake word).
        This provides more natural conversation with proper turn-taking.
        """
        try:
            from speech_interface import ConversationManager
            self._personaplex_manager = ConversationManager(
                tts_backend="elevenlabs"  # Use ElevenLabs for voice
            )
            
            # Connect Abby as the task executor
            if self.abby:
                self._personaplex_manager.set_task_executor(
                    lambda text: self.abby.execute_task(text).get('output', '')
                )
            
            self._personaplex_manager.initialize()
            logger.info("PersonaPlex full conversation mode enabled")
            return True
        except Exception as e:
            logger.warning(f"PersonaPlex not available: {e}")
            return False
    
    def _set_state(self, new_state: ThinkingState):
        """Update state and notify listeners"""
        old_state = self.state
        self.state = new_state
        
        # Track speaking state for interrupts
        if new_state == ThinkingState.SPEAKING:
            self._is_speaking = True
            self._speech_start_time = time.time()
        elif old_state == ThinkingState.SPEAKING:
            self._is_speaking = False
        
        logger.info(f"State: {old_state.value} -> {new_state.value}")
        
        if self.on_state_change:
            self.on_state_change(old_state, new_state)
        
        self._emit_event('state', new_state.value, {'previous': old_state.value})
    
    def _emit_event(self, event_type: str, content: str, metadata: Dict = None):
        """Emit an event to the stream"""
        event = StreamEvent(
            type=event_type,
            content=content,
            metadata=metadata or {}
        )
        self.event_queue.put(event)
        
        if self.on_event:
            self.on_event(event)
    
    def on_user_started_speaking(self):
        """
        Called when user starts speaking (detected by VAD or browser).
        This enables natural interruption like in real conversation.
        """
        if self._is_speaking and self.can_be_interrupted:
            # User started talking while Abby was speaking - natural interrupt!
            speech_duration = time.time() - (self._speech_start_time or time.time())
            
            # Only interrupt if Abby has been speaking for at least 1 second
            # (avoid interrupting greetings/short responses)
            if speech_duration > 1.0:
                logger.info(f"Natural interrupt: user spoke while Abby was talking (after {speech_duration:.1f}s)")
                self.interrupt("User started speaking")
                return True
        
        return False
    
    def interrupt(self, message: str = None):
        """
        Request an interrupt of the current task.
        
        Args:
            message: Optional new instruction to redirect to
        """
        if self.state in [ThinkingState.IDLE, ThinkingState.WAITING, ThinkingState.LISTENING]:
            return False  # Nothing to interrupt
        
        self.interrupt_requested = True
        self.interrupt_message = message
        self._is_speaking = False  # Stop speaking immediately
        self._emit_event('interrupt', 'Interrupt requested', {'redirect': message})
        logger.info(f"Interrupt requested: {message}")
        return True
    
    def _check_interrupt(self) -> bool:
        """Check if we should stop current work"""
        if self.interrupt_requested:
            self._set_state(ThinkingState.INTERRUPTED)
            self._emit_event('interrupted', 'Task interrupted by user')
            return True
        return False
    
    def _plan_task(self, user_input: str) -> List[TaskStep]:
        """
        Analyze user input and plan steps if it's a complex task.
        Returns list of steps, or empty list for simple conversation.
        """
        # Keywords that suggest multi-step work
        complex_indicators = [
            'create', 'build', 'implement', 'set up', 'configure',
            'then', 'after that', 'next', 'also', 'and then',
            'step by step', 'walk me through', 'help me with'
        ]
        
        input_lower = user_input.lower()
        is_complex = any(ind in input_lower for ind in complex_indicators)
        
        if not is_complex or len(user_input) < 50:
            return []  # Simple conversation, no planning needed
        
        # For complex tasks, generate a plan
        self._emit_event('thinking', 'Planning approach...')
        
        # Use Abby to generate a plan
        plan_prompt = f"""Break this request into 2-4 simple steps. Just list them briefly:
"{user_input}"

Format:
1. [First step]
2. [Second step]
etc."""
        
        try:
            if self.abby:
                result = self.abby.ollama_client.generate(
                    prompt=plan_prompt,
                    model="mistral:latest",
                    options={"num_predict": 150, "temperature": 0.3}
                )
                plan_text = result.get('response', '')
                
                # Parse steps from response
                steps = []
                for line in plan_text.strip().split('\n'):
                    line = line.strip()
                    if line and (line[0].isdigit() or line.startswith('-')):
                        # Remove numbering/bullets
                        step_text = re.sub(r'^[\d\.\-\*]+\s*', '', line).strip()
                        if step_text:
                            steps.append(TaskStep(
                                id=len(steps) + 1,
                                description=step_text
                            ))
                
                if steps:
                    self._emit_event('plan', f"I'll handle this in {len(steps)} steps", 
                                   {'steps': [s.description for s in steps]})
                    return steps
        except Exception as e:
            logger.warning(f"Planning failed: {e}")
        
        return []
    
    def stream_response(self, user_input: str, context: Dict = None) -> Generator[StreamEvent, None, None]:
        """
        Process user input and yield streaming events.
        
        This is a generator that yields events as they happen:
        - thinking: Abby's internal reasoning
        - text: Actual response text
        - action: Actions being taken
        - step: Progress on multi-step tasks
        - done: Response complete
        - error: Something went wrong
        - interrupt: User interrupted
        
        Usage:
            for event in conversation.stream_response("Hello"):
                print(event.type, event.content)
        """
        self.interrupt_requested = False
        self.interrupt_message = None
        context = context or {}
        
        try:
            self._set_state(ThinkingState.THINKING)
            self._emit_event('thinking', 'Processing...')
            
            # Add to conversation history
            self.conversation_history.append({
                "role": "user",
                "content": user_input
            })
            
            # Check for plan continuation commands
            if self._is_continue_command(user_input):
                logger.info("Continue command detected - resuming plan")
                yield from self._handle_continue_command(user_input, context)
                return
            
            # Check for overwhelming task first - needs special handling
            if is_overwhelming_task(user_input):
                logger.info("Overwhelming task detected in streaming - using decomposition")
                yield from self._handle_overwhelming_task(user_input, context)
                return
            
            # Check for complex task that needs planning
            self.task_steps = self._plan_task(user_input)
            
            if self._check_interrupt():
                yield from self._drain_events()
                return
            
            if self.task_steps:
                # Multi-step execution
                yield from self._execute_planned_task(user_input, context)
            else:
                # Simple conversation - stream response
                yield from self._stream_simple_response(user_input, context)
            
            # Check for follow-up actions
            if not self.interrupt_requested:
                self._set_state(ThinkingState.WAITING)
            
            self._emit_event('done', 'Response complete')
            
        except Exception as e:
            logger.error(f"Stream error: {e}")
            self._emit_event('error', str(e))
            self._set_state(ThinkingState.IDLE)
        
        yield from self._drain_events()
    
    def _drain_events(self) -> Generator[StreamEvent, None, None]:
        """Yield all events from the queue"""
        while not self.event_queue.empty():
            try:
                yield self.event_queue.get_nowait()
            except queue.Empty:
                break
    
    def _handle_overwhelming_task(self, user_input: str, context: Dict) -> Generator[StreamEvent, None, None]:
        """Handle overwhelming tasks by decomposing them into manageable subtasks"""
        try:
            from task_decomposer import TaskDecomposer
            from intelligent_agent import get_intelligent_agent
            
            # Get intelligent agent for plan management
            agent = get_intelligent_agent()
            
            # First, check if we already have a plan for this
            existing_plans = agent._find_related_plans(user_input)
            highly_similar = [p for p in existing_plans if p["similarity"] > 0.6]
            
            if highly_similar:
                # We have an existing plan - resume it instead of creating new
                plan_info = highly_similar[0]
                self._emit_event('thinking', f'Found existing plan with {plan_info["similarity"]:.0%} match...')
                yield from self._drain_events()
                
                plan = agent.load_plan(plan_info["id"])
                if plan:
                    progress = plan.get_progress()
                    self._emit_event('text', f"I already have a plan for this! **{plan.id}**\n\n")
                    self._emit_event('text', f"📊 Progress: {progress['completed']}/{progress['total']} tasks ({progress['percent']:.0f}% done)\n\n")
                    
                    # Show what's completed and what's next
                    completed = [t for t in plan.tasks if t.status.value == "completed"]
                    if completed:
                        self._emit_event('text', "**Completed:**\n")
                        for t in completed[:5]:
                            self._emit_event('text', f"  ✅ {t.title}\n")
                        yield from self._drain_events()
                    
                    next_tasks = plan.get_next_tasks(max_parallel=3)
                    if next_tasks:
                        self._emit_event('text', "\n**Ready to continue with:**\n")
                        for i, task in enumerate(next_tasks, 1):
                            self._emit_event('text', f"{i}. {task.title}\n")
                        self._emit_event('text', "\nSay 'continue' or tell me which task to work on!\n")
                    else:
                        self._emit_event('text', "\n🎉 All tasks complete! Want me to verify the work?\n")
                    
                    yield from self._drain_events()
                    self.current_plan = plan
                    agent.active_plan_id = plan.id
                    
                    self._set_state(ThinkingState.WAITING)
                    self._emit_event('done', 'Resumed existing plan')
                    yield from self._drain_events()
                    return
            
            # No existing plan - create new one
            self._emit_event('thinking', 'This is a big project! Let me break it down into manageable steps...')
            yield from self._drain_events()
            
            # Create decomposer
            if self.abby and hasattr(self.abby, 'ollama_client'):
                decomposer = TaskDecomposer(self.abby.ollama_client)
            else:
                self._emit_event('error', "Can't decompose without Ollama client")
                yield from self._drain_events()
                return
            
            # Gather context first (like a good agent!)
            self._emit_event('thinking', 'Gathering context about the workspace...')
            yield from self._drain_events()
            
            workspace = context.get('workspace')
            gathered_context = agent.gather_context(user_input, workspace)
            
            # Report what we found
            if gathered_context.get('workspace_exists'):
                files_count = len(gathered_context.get('existing_files', []))
                project_type = gathered_context.get('project_info', {}).get('type', 'unknown')
                if files_count > 0:
                    self._emit_event('thinking', f'Found existing {project_type} project with {files_count} files...')
                    yield from self._drain_events()
            
            # Decompose the task
            self._emit_event('thinking', 'Analyzing requirements and dependencies...')
            yield from self._drain_events()
            
            plan = decomposer.decompose(user_input, gathered_context)
            
            if not plan or not plan.tasks:
                self._emit_event('error', 'Failed to break down the task. Try being more specific?')
                yield from self._drain_events()
                return
            
            # Track this as active plan
            agent.active_plan_id = plan.id
            
            if not plan or not plan.tasks:
                self._emit_event('error', 'Failed to break down the task. Try being more specific?')
                yield from self._drain_events()
                return
            
            # Report the plan
            self._emit_event('text', f"Okay! I've broken this down into {len(plan.tasks)} subtasks:\n\n")
            yield from self._drain_events()
            
            # List all tasks by category
            categories = {}
            for task in plan.tasks:
                cat = task.category
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(task)
            
            for cat, tasks in categories.items():
                self._emit_event('text', f"**{cat.upper()}:**\n")
                for task in tasks:
                    deps = f" (needs: {', '.join(task.dependencies)})" if task.dependencies else ""
                    self._emit_event('text', f"  • {task.title}{deps}\n")
                yield from self._drain_events()
            
            self._emit_event('text', f"\n📋 **Plan saved as:** {plan.id}\n\n")
            
            # Ask what to start with
            next_tasks = plan.get_next_tasks(max_parallel=3)
            if next_tasks:
                self._emit_event('text', "**Ready to start with:**\n")
                for i, task in enumerate(next_tasks, 1):
                    self._emit_event('text', f"{i}. {task.title}\n")
                self._emit_event('text', "\nTell me which one to start, or say 'start all' to begin!\n")
            
            yield from self._drain_events()
            
            # Store plan for follow-up
            if not hasattr(self, 'current_plan'):
                self.current_plan = None
            self.current_plan = plan
            
            self._set_state(ThinkingState.WAITING)
            self._emit_event('done', 'Task decomposition complete')
            yield from self._drain_events()
            
        except ImportError as e:
            logger.error(f"TaskDecomposer not available: {e}")
            self._emit_event('error', f"Task decomposition not available: {e}")
            yield from self._drain_events()
        except Exception as e:
            logger.error(f"Error in overwhelming task handling: {e}")
            self._emit_event('error', f"Failed to decompose task: {e}")
            yield from self._drain_events()
    
    def _stream_simple_response(self, user_input: str, context: Dict) -> Generator[StreamEvent, None, None]:
        """Stream a simple conversational response"""
        self._set_state(ThinkingState.SPEAKING)
        
        if not self.abby:
            self._emit_event('text', "I'm not fully initialized yet.")
            return
        
        # Build prompt
        personality = self.abby.brain_clone.get_personality()
        identity = personality.get("identity", {})
        comm_style = personality.get("communication_style", {})
        
        # Build a list of recent response starters to avoid
        recent_starters = []
        for msg in self.conversation_history[-6:]:
            if msg.get('role') == 'assistant':
                content = msg.get('content', '')
                if content:
                    # Get first 20 chars to detect repeated starts
                    starter = content[:20].lower()
                    recent_starters.append(starter)
        
        # Create dynamic anti-repetition rule
        anti_repeat_rule = ""
        if recent_starters:
            anti_repeat_rule = "\n\nYou recently started responses with these patterns - DO NOT use them again:\n"
            for starter in recent_starters[-3:]:
                anti_repeat_rule += f'- "{starter}..."\n'
        
        system_prompt = f"""You are {identity.get('name', 'Abby')}.

CRITICAL: Read what the user said and respond SPECIFICALLY to their message.

USER SAID: "{user_input}"

RULES:
1. Address what the user ACTUALLY said above
2. Keep responses to 1-2 sentences MAX
3. NO greetings like "Hey there", "Hello", "Hi there" - just answer directly
4. NO code unless explicitly asked for code
5. If input is unclear: "Didn't catch that, say again?"

BANNED PHRASES (never use these):
- "Hey there"
- "Hi there" 
- "Hello there"
- "How are ya"
- "I hope you"
- "Let me know if"
- "Is there anything else"
- "I'm happy to help"

NEVER:
- Start with a greeting
- Be vague or generic
- Talk about these rules{anti_repeat_rule}"""
        
        # Add user context
        if context.get('user_prompt_addition'):
            system_prompt += f"\n\n{context['user_prompt_addition']}"
        
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.conversation_history[-10:])  # Last 10 turns
        
        # Stream from Ollama
        try:
            response_stream = self.abby.ollama_client.chat(
                messages=messages,
                model="mistral:latest",
                stream=True
            )
            
            full_response = ""
            for chunk in response_stream:
                if self._check_interrupt():
                    yield from self._drain_events()
                    return
                
                if 'message' in chunk:
                    token = chunk['message'].get('content', '')
                    if token:
                        full_response += token
                        self._emit_event('text', token, {'partial': True})
                        yield from self._drain_events()
                
                if chunk.get('done'):
                    break
            
            # Check response quality
            is_broken, reason = is_response_broken(full_response, self.conversation_history)
            if is_broken:
                logger.warning(f"Broken response detected: {reason}")
                logger.warning(f"Response was: {full_response[:100]}...")
                # Don't add broken responses to history to avoid reinforcing the pattern
                # But we already streamed it, so log for debugging
            
            # Add to history (even if broken, to maintain context)
            self.conversation_history.append({
                "role": "assistant",
                "content": full_response
            })
            
            # Keep history manageable
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            self._emit_event('text', '', {'partial': False, 'complete': True})
            
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            self._emit_event('error', f"Response error: {e}")
    
    def _execute_planned_task(self, user_input: str, context: Dict) -> Generator[StreamEvent, None, None]:
        """Execute a multi-step planned task"""
        for i, step in enumerate(self.task_steps):
            if self._check_interrupt():
                yield from self._drain_events()
                return
            
            step.status = "in-progress"
            self.current_step_index = i
            
            self._emit_event('step', f"Step {i+1}: {step.description}", {
                'step_index': i,
                'total_steps': len(self.task_steps),
                'status': 'in-progress'
            })
            
            self._set_state(ThinkingState.DOING)
            
            # Execute this step
            step_prompt = f"""You're working on: "{user_input}"

Current step ({i+1}/{len(self.task_steps)}): {step.description}

Respond briefly about this step only. If it requires action, do it. Keep response under 2 sentences."""
            
            try:
                result = self.abby.execute_task(step_prompt, context)
                step.result = result.get('output', '')
                step.status = "completed"
                
                self._emit_event('text', step.result)
                self._emit_event('step', f"Completed step {i+1}", {
                    'step_index': i,
                    'status': 'completed'
                })
                
            except Exception as e:
                step.status = "error"
                step.result = str(e)
                self._emit_event('error', f"Step {i+1} failed: {e}")
            
            yield from self._drain_events()
            
            # Small pause between steps
            if i < len(self.task_steps) - 1:
                time.sleep(0.5)
        
        self._emit_event('text', f"\n\n✅ All {len(self.task_steps)} steps complete!")
    
    def _is_continue_command(self, user_input: str) -> bool:
        """Check if user is asking to continue with a plan"""
        user_lower = user_input.lower().strip()
        
        # Direct continue commands
        continue_patterns = [
            'continue',
            'start',
            'proceed',
            'go ahead',
            'next task',
            'next step',
            'keep going',
            'do it',
            'lets go',
            "let's go",
            'work on task',
            'start task',
            'begin task',
        ]
        
        # Check for any continue pattern
        for pattern in continue_patterns:
            if pattern in user_lower:
                return True
                
        # Check for task number references like "task 1" or "#1"
        if re.search(r'task\s*\d+|#\s*\d+|number\s*\d+', user_lower):
            return True
            
        return False
    
    def _handle_continue_command(self, user_input: str, context: Dict) -> Generator[StreamEvent, None, None]:
        """Handle request to continue with plan execution"""
        try:
            from task_decomposer import TaskDecomposer
            from intelligent_agent import get_intelligent_agent
            from task_executor import get_task_executor
            
            agent = get_intelligent_agent()
            
            # Check if we have a current plan
            plan = getattr(self, 'current_plan', None)
            
            if not plan and agent.active_plan_id:
                # Try to load the active plan
                plan = agent.load_plan(agent.active_plan_id)
            
            if not plan:
                # Check for any recent plans
                existing = agent._find_related_plans("SafeConnect dating app")
                if existing and existing[0]['similarity'] > 0.5:
                    plan = agent.load_plan(existing[0]['id'])
            
            if not plan:
                self._emit_event('text', "I don't have an active plan. Tell me what you'd like to build!")
                yield from self._drain_events()
                return
            
            # Parse which task user wants
            user_lower = user_input.lower()
            task_num_match = re.search(r'(?:task\s*|#\s*|number\s*)(\d+)', user_lower)
            
            target_task = None
            if task_num_match:
                task_num = int(task_num_match.group(1))
                if 1 <= task_num <= len(plan.tasks):
                    target_task = plan.tasks[task_num - 1]
            
            if not target_task:
                # Get next available task
                next_tasks = plan.get_next_tasks(max_parallel=1)
                if next_tasks:
                    target_task = next_tasks[0]
                else:
                    self._emit_event('text', "🎉 All tasks in the plan are complete! Want to start something new?")
                    yield from self._drain_events()
                    return
            
            # Now execute the task with verification
            self._emit_event('thinking', f'Starting work on: {target_task.title}')
            yield from self._drain_events()
            
            # Get the task executor
            workspace = context.get('workspace')
            executor = get_task_executor(workspace, self.abby.ollama_client if self.abby else None)
            
            # Execute with streaming progress
            execution_events = []
            for event in executor.execute_task(target_task, plan):
                execution_events.append(event)
                
                if event['type'] == 'thinking':
                    self._emit_event('thinking', event['message'])
                elif event['type'] == 'step_success':
                    self._emit_event('text', f"✅ {event['action']}: {event.get('target', '')[:50]}\n")
                elif event['type'] == 'step_failed':
                    self._emit_event('text', f"❌ {event['action']}: {event.get('error', '')[:100]}\n")
                elif event['type'] == 'complete':
                    if event.get('success'):
                        self._emit_event('text', f"\n{event.get('summary', 'Task completed!')}\n")
                    else:
                        self._emit_event('text', f"\n⚠️ Task had issues: {event.get('summary', '')}\n")
                
                yield from self._drain_events()
            
            # Show what's next
            next_tasks = plan.get_next_tasks(max_parallel=3)
            if next_tasks:
                self._emit_event('text', "\n**Next tasks:**\n")
                for i, t in enumerate(next_tasks, 1):
                    self._emit_event('text', f"  {i}. {t.title}\n")
                self._emit_event('text', "\nSay 'continue' for the next task!\n")
            else:
                self._emit_event('text', "\n🎉 **All tasks complete!** Great work!\n")
            
            yield from self._drain_events()
            
            self._set_state(ThinkingState.WAITING)
            self._emit_event('done', 'Task execution complete')
            
        except Exception as e:
            logger.error(f"Error handling continue command: {e}")
            self._emit_event('error', f"Error: {e}")
        
        yield from self._drain_events()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current conversation status"""
        return {
            'state': self.state.value,
            'current_task': self.current_task,
            'steps': [{'id': s.id, 'description': s.description, 'status': s.status} 
                     for s in self.task_steps],
            'current_step': self.current_step_index,
            'can_interrupt': self.state not in [ThinkingState.IDLE, ThinkingState.WAITING],
            'history_length': len(self.conversation_history)
        }
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history.clear()
        self.task_steps.clear()
        self.current_step_index = 0


# Singleton instance
_streaming_conversation: Optional[StreamingConversation] = None

def get_streaming_conversation() -> StreamingConversation:
    """Get or create the streaming conversation instance"""
    global _streaming_conversation
    if _streaming_conversation is None:
        _streaming_conversation = StreamingConversation()
    return _streaming_conversation
