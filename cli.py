"""
Main Abby Unleashed Orchestrator
"""
import logging
import os
import re
import yaml
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

from personality.brain_clone import BrainClone
from persona_library.library_manager import PersonaLibrary
from agents.agent_factory import AgentFactory
from ollama_integration.client import OllamaClient
from ollama_integration.model_selector import ModelSelector
from agents.task_planner import TaskPlanner
from agents.task_runner import TaskRunner
from agents.action_executor import get_executor
from parallel_thinker import ParallelThinker, create_parallel_thinker
from intelligent_agent import get_intelligent_agent, IntelligentAgent
from task_executor import get_task_executor, TaskExecutor


# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_coding_foundations() -> Dict[str, Any]:
    """Load foundational coding knowledge for AI-assisted development"""
    knowledge_path = os.path.join(
        os.path.dirname(__file__), 
        "agents", "knowledge", "coding_foundations.yaml"
    )
    try:
        with open(knowledge_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"Could not load coding foundations: {e}")
        return {}


class AbbyUnleashed:
    """
    Main orchestrator for Abby Unleashed digital clone system
    """
    
    def __init__(
        self,
        personality_config: str = "config/brain_clone.yaml",
        persona_library_path: str = "persona_library/personas/personas.yaml",
        verbose: bool = False
    ):
        """
        Initialize Abby Unleashed
        
        Args:
            personality_config: Path to personality configuration
            persona_library_path: Path to persona library
            verbose: Enable verbose logging
        """
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
        logger.info("Initializing Abby Unleashed...")
        
        # Load brain clone (personality)
        self.brain_clone = BrainClone(personality_config)
        logger.info(f"Loaded personality: {self.brain_clone.personality.get('identity', {}).get('name')}")
        
        # Initialize persona library
        self.persona_library = PersonaLibrary(persona_library_path)
        logger.info(f"Loaded {len(self.persona_library.personas)} personas")
        
        # Initialize Ollama client
        self.ollama_client = OllamaClient()
        
        # Initialize model selector
        self.model_selector = ModelSelector(ollama_client=self.ollama_client)
        
        # Initialize agent factory
        self.agent_factory = AgentFactory(
            persona_library=self.persona_library,
            personality=self.brain_clone.get_personality()
        )
        
        # Initialize task planner and runner for ACTUAL EXECUTION
        self.task_planner = TaskPlanner(
            ollama_client=self.ollama_client,
            workspace_path=os.getcwd()
        )
        self.task_runner = TaskRunner(
            ollama_client=self.ollama_client,
            workspace_path=os.getcwd(),
            on_progress=self._on_task_progress
        )
        self.executor = get_executor()
        
        # Track current task progress
        self.current_task = None
        self.task_progress = {}
        self.progress_log = []
        
        # Conversation history for chat context
        self.conversation_history = []
        
        # Initialize parallel thinker for smart responses
        self.parallel_thinker = create_parallel_thinker(
            ollama_client=self.ollama_client
        )
        
        # Use parallel thinker by default (can be disabled)
        self.use_parallel_thinker = True
        
        logger.info("Abby Unleashed initialized successfully!")
        logger.info(f"Parallel thinker: {'enabled' if self.use_parallel_thinker else 'disabled'}")
        
        # Load foundational coding knowledge
        self.coding_foundations = load_coding_foundations()
        if self.coding_foundations:
            logger.info("Loaded foundational coding best practices")
    
    def _on_task_progress(self, message: str, data: Dict = None):
        """Handle task progress updates"""
        self.progress_log.append({"message": message, "data": data})
        logger.info(f"Progress: {message}")
    
    def _is_overwhelming_task(self, task: str) -> bool:
        """
        Check if a task is too complex to handle in one go.
        
        Signs of an overwhelming task:
        - Very long description (1000+ chars)
        - Multiple numbered steps or bullet points
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
    
    def _execute_with_decomposition(self, task: str, context: Dict) -> Dict[str, Any]:
        """
        Handle overwhelming tasks by decomposing them into subtasks.
        
        This is Abby's key ability to not get overwhelmed - she breaks
        down big requests and tackles them systematically.
        
        NOW IMPROVED: Uses intelligent agent to:
        1. Check for existing plans before creating new ones
        2. Gather context about the workspace before decomposing
        3. Track execution progress
        """
        from task_decomposer import get_task_decomposer
        
        # Get intelligent agent for context gathering and plan management
        workspace = context.get("workspace", os.getcwd())
        agent = get_intelligent_agent(workspace)
        
        # First, check if we already have a plan for this task
        existing_plan_id = agent._find_related_plans(task)
        
        if existing_plan_id:
            # Load existing plan instead of creating a new one
            try:
                existing_plan = agent.load_plan(existing_plan_id)
                if existing_plan:
                    logger.info(f"Found existing plan: {existing_plan_id}")
                    
                    # Get status of existing plan
                    decomposer = get_task_decomposer(self.ollama_client)
                    decomposer.active_plan = existing_plan
                    
                    status = decomposer.get_status_report()
                    next_tasks = existing_plan.get_next_tasks(max_parallel=3)
                    
                    response_parts = [
                        "🔄 **I found my previous plan for this request!**\n",
                        status,
                        "\n**Ready to continue with:**"
                    ]
                    
                    for i, subtask in enumerate(next_tasks, 1):
                        status_icon = "⏳" if subtask.status == "pending" else "▶️"
                        response_parts.append(f"  {status_icon} {i}. [{subtask.category.upper()}] {subtask.title}")
                    
                    response_parts.append(f"\n📁 Using plan: `{existing_plan.id}`")
                    response_parts.append("\nShould I continue with the next task?")
                    
                    return {
                        "status": "plan_loaded",
                        "output": "\n".join(response_parts),
                        "plan_id": existing_plan.id,
                        "total_tasks": existing_plan.total_tasks,
                        "next_tasks": [{"id": t.id, "title": t.title, "category": t.category} for t in next_tasks]
                    }
            except Exception as e:
                logger.warning(f"Could not load existing plan: {e}")
        
        # Gather context about the workspace before decomposing
        logger.info("Gathering workspace context before decomposition...")
        workspace_context = agent.gather_context(task)
        
        # Decompose the task with context
        decomposer = get_task_decomposer(self.ollama_client)
        
        # Add workspace context to help with better decomposition
        enhanced_context = {**context, "workspace_info": workspace_context}
        plan = decomposer.decompose(task, enhanced_context)
        
        # Save plan through intelligent agent for future reference
        agent.save_plan(plan)
        
        # Update progress tracking
        self.task_progress["total_steps"] = plan.total_tasks
        
        # Get status report
        status = decomposer.get_status_report()
        
        # Get next actionable tasks
        next_tasks = plan.get_next_tasks(max_parallel=3)
        
        # Format response
        response_parts = [
            "🎯 **I've broken down your request into manageable tasks!**\n",
            status,
            "\n**Ready to start with:**"
        ]
        
        for i, subtask in enumerate(next_tasks, 1):
            response_parts.append(f"  {i}. [{subtask.category.upper()}] {subtask.title}")
        
        response_parts.append(f"\n📁 Plan saved as: `{plan.id}`")
        response_parts.append("\nShould I proceed with the first task, or would you like to review/modify the plan?")
        
        return {
            "status": "plan_created",
            "output": "\n".join(response_parts),
            "plan_id": plan.id,
            "total_tasks": plan.total_tasks,
            "next_tasks": [{"id": t.id, "title": t.title, "category": t.category} for t in next_tasks]
        }
    
    def execute_planned_task(
        self, 
        plan_id: str, 
        task_id: str = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute a specific task from a plan with verification.
        
        This method:
        1. Loads the plan
        2. Gets the task to execute (or picks the next one)
        3. Executes with verification
        4. Updates task status in the plan
        5. Returns detailed results
        
        Args:
            plan_id: The plan ID to work from
            task_id: Optional specific task ID (if not provided, picks next)
            context: Optional context dict
            
        Returns:
            Result dictionary with execution details
        """
        context = context or {}
        workspace = context.get("workspace", os.getcwd())
        
        # Get the intelligent agent and task executor
        agent = get_intelligent_agent(workspace)
        executor = get_task_executor(workspace, self.ollama_client)
        
        # Load the plan
        plan = agent.load_plan(plan_id)
        if not plan:
            return {
                "status": "error",
                "error": f"Plan not found: {plan_id}",
                "output": f"❌ Could not find plan: {plan_id}"
            }
        
        # Get the task to execute
        if task_id:
            task = next((t for t in plan.tasks if t.id == task_id), None)
            if not task:
                return {
                    "status": "error",
                    "error": f"Task not found: {task_id}",
                    "output": f"❌ Could not find task {task_id} in plan {plan_id}"
                }
        else:
            # Get next task
            next_tasks = plan.get_next_tasks(max_parallel=1)
            if not next_tasks:
                return {
                    "status": "completed",
                    "output": f"✅ All tasks in plan {plan_id} are complete!",
                    "plan_complete": True
                }
            task = next_tasks[0]
        
        # Track execution start
        self.progress_log.append({
            "message": f"Starting task: {task.title}",
            "task_id": task.id
        })
        
        # Execute the task with verification
        execution_log = []
        final_result = None
        
        for event in executor.execute_task(task, plan):
            execution_log.append(event)
            
            # Track progress
            if event["type"] == "thinking":
                self.progress_log.append({"message": event["message"]})
            elif event["type"] == "step_success":
                self.progress_log.append({
                    "message": f"✅ {event['action']}: {event.get('target', '')}",
                    "success": True
                })
            elif event["type"] == "step_failed":
                self.progress_log.append({
                    "message": f"❌ {event['action']}: {event.get('error', '')}",
                    "success": False
                })
            elif event["type"] == "complete":
                final_result = event
        
        # Build response
        if final_result and final_result.get("success"):
            response_parts = [
                f"✅ **Completed: {task.title}**",
                f"",
                final_result.get("summary", ""),
            ]
            
            if final_result.get("verified"):
                response_parts.append("\n✓ All operations verified")
            
            # Show what's next
            next_tasks = plan.get_next_tasks(max_parallel=3)
            if next_tasks:
                response_parts.append("\n**Next up:**")
                for i, t in enumerate(next_tasks, 1):
                    response_parts.append(f"  {i}. {t.title}")
            else:
                response_parts.append("\n🎉 **All tasks complete!**")
            
            return {
                "status": "completed",
                "output": "\n".join(response_parts),
                "task_id": task.id,
                "verified": final_result.get("verified", False),
                "plan_id": plan_id,
                "next_tasks": [{"id": t.id, "title": t.title} for t in next_tasks]
            }
        else:
            error_msg = final_result.get("summary", "Unknown error") if final_result else "Execution failed"
            return {
                "status": "failed",
                "output": f"❌ **Failed: {task.title}**\n\n{error_msg}",
                "task_id": task.id,
                "plan_id": plan_id,
                "error": error_msg
            }
    
    def _is_coding_task(self, task: str) -> bool:
        """Check if a task is coding-related"""
        coding_keywords = [
            'code', 'coding', 'program', 'script', 'function', 'class',
            'debug', 'fix', 'error', 'bug', 'implement', 'create', 'build',
            'develop', 'write', 'refactor', 'optimize', 'api', 'database',
            'python', 'javascript', 'html', 'css', 'sql', 'json', 'yaml',
            'file', 'module', 'import', 'export', 'test', 'deploy'
        ]
        task_lower = task.lower()
        return any(kw in task_lower for kw in coding_keywords)
    
    def _get_coding_guidance(self) -> str:
        """Get coding best practices guidance for the prompt"""
        if not self.coding_foundations:
            return ""
        
        vibe = self.coding_foundations.get('vibe_coding_awareness', {})
        parts = ["\n\n=== AI CODING BEST PRACTICES ==="]
        
        # Key limitations to be aware of
        parts.append("\nBe aware of these AI-coding pitfalls:")
        for lim in vibe.get('limitations', [])[:3]:
            parts.append(f"• {lim.get('name')}: {lim.get('mitigation', '')[:150]}")
        
        # Best practices
        practices = vibe.get('best_practices', {})
        if practices.get('always_do'):
            parts.append("\nAlways:")
            for item in practices['always_do'][:4]:
                parts.append(f"  ✓ {item}")
        
        if practices.get('never_do'):
            parts.append("Never:")
            for item in practices['never_do'][:4]:
                parts.append(f"  ✗ {item}")
        
        return '\n'.join(parts)
    
    def _needs_execution(self, task: str, context: Dict = None) -> bool:
        """
        Determine if a task requires actual execution (creating files, running commands, etc)
        vs. just a conversational response.
        
        CONSERVATIVE: Only execute when user EXPLICITLY asks with file paths or commands.
        """
        import re
        task_lower = task.lower()
        
        # Check if context EXPLICITLY requests execution
        if context and context.get("execute"):
            return True
        
        # Must have explicit file path patterns to trigger execution
        file_patterns = [
            r'create\s+[\w/\\]+\.(py|js|ts|html|css|yaml|json|md)',  # create foo.py
            r'edit\s+[\w/\\]+\.(py|js|ts|html|css|yaml|json|md)',   # edit foo.py
            r'write\s+(to|a|the)?\s*[\w/\\]+\.',                    # write to file.py
            r'run\s+(the\s+)?(command|script)',                      # run the command
            r'execute\s+',                                            # execute something
            r'pip\s+install',                                         # pip install
            r'npm\s+install',                                         # npm install
        ]
        
        for pattern in file_patterns:
            if re.search(pattern, task_lower):
                return True
        
        return False
    
    def _has_action_blocks(self, response: str) -> bool:
        """Check if an LLM response contains action blocks to execute"""
        import re
        
        # Look for action blocks
        action_patterns = [
            r'```action:create_file',
            r'```action:edit_file',
            r'```action:delete_file',
            r'```bash',
            r'```shell',
            r'```python\s*\n\s*#\s*execute',  # Python blocks marked for execution
        ]
        
        for pattern in action_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                return True
        
        return False
    
    def _format_action_results(self, results: List[Dict]) -> str:
        """Format action execution results for display"""
        if not results:
            return ""
        
        parts = ["📋 **Action Results:**"]
        
        for i, result in enumerate(results, 1):
            action_type = result.get("action", "unknown")
            success = result.get("success", False)
            
            icon = "✅" if success else "❌"
            
            if action_type == "create_file":
                path = result.get("path", "unknown")
                parts.append(f"{icon} Created file: `{path}`")
            
            elif action_type == "edit_file":
                path = result.get("path", "unknown")
                parts.append(f"{icon} Edited file: `{path}`")
            
            elif action_type == "delete_file":
                path = result.get("path", "unknown")
                parts.append(f"{icon} Deleted file: `{path}`")
            
            elif action_type == "command":
                cmd = result.get("command", "unknown")[:50]
                parts.append(f"{icon} Ran command: `{cmd}...`")
                if result.get("output"):
                    output = result["output"][:200]
                    parts.append(f"   Output: {output}")
            
            elif action_type == "python":
                parts.append(f"{icon} Executed Python code")
                if result.get("output"):
                    output = result["output"][:200]
                    parts.append(f"   Output: {output}")
            
            else:
                parts.append(f"{icon} {action_type}: {result.get('message', 'completed')}")
            
            # Show error if failed
            if not success and result.get("error"):
                parts.append(f"   Error: {result['error'][:100]}")
        
        return '\n'.join(parts)
    
    def _execute_with_parallel_thinker(
        self,
        task: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute using parallel thinker - smart model selection
        
        - Uses fast model for simple chat
        - Uses big model for coding tasks
        - Abby decides based on query complexity
        """
        try:
            personality = self.brain_clone.get_personality()
            workspace = context.get("workspace", self.task_planner.workspace_path)
            
            # Use smart thinking (auto-selects fast vs parallel, and model)
            result = self.parallel_thinker.think_smart(
                query=task,
                context={"workspace": workspace, **context},
                conversation_history=self.conversation_history,
                personality=personality
            )
            
            # Add to conversation history
            self.conversation_history.append({"role": "user", "content": task})
            self.conversation_history.append({"role": "assistant", "content": result.spoken_text})
            
            # Keep history manageable
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            return {
                "status": "completed",
                "output": result.spoken_text,
                "model": result.model_used,
                "time": result.total_time,
                "display_actions": result.display_actions,
                "tone": result.tone,
            }
            
        except Exception as e:
            logger.error(f"Parallel thinker error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "output": f"Sorry, something went wrong: {str(e)}"
            }
    
    def execute_task(
        self, 
        task: str, 
        context: Optional[Dict[str, Any]] = None,
        use_orchestrator: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a task - handles conversation AND actions
        
        Uses parallel thinker by default for smart model selection.
        
        This is the key method that makes Abby BOTH conversational AND able to ACT.
        
        Args:
            task: Task description or user message
            context: Optional task context (can include workspace path)
            use_orchestrator: Whether to use orchestrator for complex tasks
            
        Returns:
            Result dictionary with response
        """
        context = context or {}
        
        logger.info(f"Processing: {task[:100]}...")
        
        # Track progress
        self.current_task = task
        self.task_progress = {
            "task": task,
            "status": "in_progress",
            "steps_completed": 0,
            "total_steps": 1
        }
        self.progress_log = []
        
        try:
            # Check if this is an overwhelming task that needs decomposition
            if self._is_overwhelming_task(task):
                logger.info("Overwhelming task detected - using task decomposer")
                return self._execute_with_decomposition(task, context)
            
            # Determine if this needs ACTION or just conversation
            needs_action = self._needs_execution(task, context)
            
            # If workspace specified in context, update planner/runner
            if context.get("workspace"):
                self.task_planner.workspace_path = context["workspace"]
                self.task_runner.workspace_path = context["workspace"]
                self.task_runner.executor = get_executor(context["workspace"])
            
            # Use parallel thinker for conversation (smart model selection)
            # Only use old path if action execution is explicitly needed
            if self.use_parallel_thinker and not needs_action:
                result = self._execute_with_parallel_thinker(task, context)
                self.task_progress["status"] = "completed"
                self.task_progress["steps_completed"] = 1
                return result
            
            # Get model to use
            model = os.getenv("DEFAULT_MODEL", "qwen2.5:latest")
            
            # Build system prompt with personality AND action capabilities
            personality = self.brain_clone.get_personality()
            identity = personality.get("identity", {})
            comm_style = personality.get("communication_style", {})
            
            # Check if we have a proper brain clone loaded
            has_brain_clone = self.brain_clone.engram is not None or "response_format" in personality
            
            if has_brain_clone:
                # Full Abby personality - she's an adult, no guardrails needed
                base_prompt = f"""You are {identity.get('name', 'Abby')}.

The user said: "{task}"

RESPOND DIRECTLY to what they said above. No generic responses.

RULES:
- NEVER start with "Hey there", "Hi there", "Hello" or any greeting
- NEVER repeat yourself. Say it ONCE.
- Keep responses to 1-2 sentences max
- NO code blocks unless explicitly asked "write code" or "create file"
- Just chat naturally - address what they actually said

BANNED PHRASES (never use these):
- "Hey there" / "Hi there" / "Hello there"
- "How are ya" / "How are you today"
- "I hope you" / "Let me know if"
- "Is there anything else"
- "Thanks for letting me know"
"""
            else:
                # Fallback mode with guardrails (no proper config loaded)
                base_prompt = f"""You are {identity.get('name', 'Abby')}, a helpful AI assistant.

The user said: "{task}"

RULES:
- Address their message directly - no generic responses
- NEVER start with "Hey there" or any greeting
- Keep responses short (1-2 sentences)
- NO code unless asked
- Be helpful but concise"""

            # Add coding best practices if this is a coding task
            if self._is_coding_task(task):
                coding_guidance = self._get_coding_guidance()
                if coding_guidance:
                    base_prompt += coding_guidance
                    logger.debug("Added coding best practices to prompt")

            # Add workspace context if available
            workspace = context.get("workspace", self.task_planner.workspace_path)
            if workspace:
                base_prompt += f"\n\nCurrent workspace: {workspace}"
            
            # Add user presence context if available
            # This tells Abby WHO she's talking to and how to customize her response
            if context.get("user_prompt_addition"):
                base_prompt += f"\n\n{context['user_prompt_addition']}"
                logger.debug(f"Added user presence context for: {context.get('user_presence', {}).get('display_name', 'unknown')}")
            
            # Special handling if talking to the boyfriend - detect and handle chaos
            user_presence = context.get("user_presence", {})
            if user_presence.get("user_id") == "boyfriend":
                try:
                    from presence.chaos_handler import get_boyfriend_handler
                    bf_handler = get_boyfriend_handler()
                    chaos_result = bf_handler.process_input(task)
                    
                    if chaos_result.get("is_chaotic"):
                        # Add chaos-specific guidance to the prompt
                        base_prompt += f"\n\n=== CHAOS DETECTED ({chaos_result['chaos_category']}) ==="
                        base_prompt += f"\nAdvice: {chaos_result['advice']}"
                        if chaos_result.get("suggested_response"):
                            base_prompt += f"\nExample response style: \"{chaos_result['suggested_response']}\""
                        logger.info(f"Boyfriend chaos detected: {chaos_result['chaos_category']} (confidence: {chaos_result['confidence']:.2f})")
                except Exception as e:
                    logger.warning(f"Chaos handler error: {e}")

            # Add user message to history
            self.conversation_history.append({
                "role": "user",
                "content": task
            })
            
            # Keep conversation history manageable
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            # Call Ollama for response
            response = self.ollama_client.chat(
                messages=[{"role": "system", "content": base_prompt}] + self.conversation_history,
                model=model
            )
            
            # Extract response text
            if "error" in response:
                logger.error(f"Ollama error: {response['error']}")
                return {
                    "status": "error",
                    "error": response["error"],
                    "output": f"Sorry, I encountered an error: {response['error']}"
                }
            
            # Get assistant response
            assistant_message = response.get("message", {}).get("content", "")
            
            if not assistant_message:
                assistant_message = response.get("response", "I'm not sure how to respond to that.")
            
            # Only execute actions if user EXPLICITLY requested execution
            # Don't auto-execute just because LLM generated code blocks
            action_results = []
            if needs_action and self._has_action_blocks(assistant_message):
                logger.info("User requested action AND response has action blocks - executing...")
                action_results = self.executor.parse_and_execute(assistant_message)
                
                if action_results:
                    # Append action results to response
                    action_summary = self._format_action_results(action_results)
                    assistant_message += f"\n\n{action_summary}"
            
            # Add to history
            self.conversation_history.append({
                "role": "assistant", 
                "content": assistant_message
            })
            
            # Update progress
            self.task_progress["status"] = "completed"
            self.task_progress["steps_completed"] = 1
            
            logger.info("Response generated successfully")
            return {
                "status": "completed",
                "output": assistant_message,
                "model": model,
                "actions_executed": len(action_results),
                "action_results": action_results if action_results else None
            }
        
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            self.task_progress["status"] = "error"
            self.task_progress["error"] = str(e)
            return {
                "status": "error",
                "error": str(e),
                "output": f"Sorry, something went wrong: {str(e)}"
            }
    
    def get_orchestrator_progress(self) -> Dict[str, Any]:
        """
        Get current task/orchestrator progress
        
        Returns:
            Progress dictionary with task status
        """
        if not self.current_task:
            return {
                "status": "idle",
                "message": "No task currently in progress"
            }
        
        return self.task_progress
    
    def start_text_interface(self):
        """Start interactive text interface"""
        from rich.console import Console
        from rich.markdown import Markdown
        
        console = Console()
        
        console.print(f"\n[bold green]{self.brain_clone.get_greeting()}[/bold green]\n")
        console.print("[dim]Type 'exit' to quit[/dim]\n")
        
        while True:
            try:
                # Get user input
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    console.print(f"\n[bold green]{self.brain_clone.get_completed()} Goodbye![/bold green]\n")
                    break
                
                # Process task
                console.print(f"\n[bold blue]{self.brain_clone.get_task_received()}[/bold blue]\n")
                
                result = self.execute_task(user_input)
                
                # Display result
                if result.get("status") == "clarification_needed":
                    console.print("[yellow]" + "\n".join(result["questions"]) + "[/yellow]\n")
                elif result.get("status") == "error":
                    console.print(f"[red]Error: {result.get('error')}[/red]\n")
                else:
                    console.print(f"[green]{result.get('output', 'Task completed!')}[/green]\n")
            
            except KeyboardInterrupt:
                console.print(f"\n\n[bold green]{self.brain_clone.get_completed()} Goodbye![/bold green]\n")
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]\n")
    
    def start_voice_interface(self):
        """Start voice interface - placeholder for now"""
        from rich.console import Console
        console = Console()
        
        console.print("[yellow]Voice interface not yet implemented.[/yellow]")
        console.print("[dim]Falling back to text interface...[/dim]\n")
        
        self.start_text_interface()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get system statistics
        
        Returns:
            Statistics dictionary
        """
        return {
            "persona_library": self.persona_library.get_stats(),
            "ollama_models": self.model_selector.get_available_models()
        }


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Abby Unleashed - Digital Clone System")
    parser.add_argument(
        "mode",
        nargs='?',
        choices=["voice", "text", "task"],
        default="text",
        help="Interface mode"
    )
    parser.add_argument(
        "--personality",
        default="config/brain_clone.yaml",
        help="Path to personality configuration"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--task",
        help="Direct task execution (for 'task' mode)"
    )
    
    args = parser.parse_args()
    
    # Initialize Abby
    abby = AbbyUnleashed(
        personality_config=args.personality,
        verbose=args.verbose
    )
    
    # Run appropriate interface
    if args.mode == "voice":
        abby.start_voice_interface()
    elif args.mode == "text":
        abby.start_text_interface()
    else:  # task mode
        if args.task:
            result = abby.execute_task(args.task)
            print(result)
        else:
            print("Error: --task argument required for task mode")


if __name__ == "__main__":
    main()
