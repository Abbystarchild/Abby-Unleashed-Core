"""
Task Planner - Breaks down user requests into actionable steps

Instead of just responding with what COULD be done, Abby now:
1. Analyzes the request
2. Creates a concrete action plan
3. Executes each step
4. Reports real results
"""

import os
import logging
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Types of actions Abby can take"""
    READ_FILE = "read_file"
    CREATE_FILE = "create_file"
    EDIT_FILE = "edit_file"
    DELETE_FILE = "delete_file"
    RUN_COMMAND = "run_command"
    RUN_PYTHON = "run_python"
    RUN_TESTS = "run_tests"
    GIT_COMMIT = "git_commit"
    GIT_PUSH = "git_push"
    RESEARCH = "research"
    CREATE_AGENT = "create_agent"
    ANALYZE_CODE = "analyze_code"
    GENERATE_CODE = "generate_code"
    RESPOND = "respond"  # Just respond with text (no action)


@dataclass
class PlannedAction:
    """A single planned action"""
    action_type: ActionType
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[int] = field(default_factory=list)  # Indices of actions this depends on
    status: str = "pending"  # pending, in_progress, completed, failed
    result: Optional[Dict[str, Any]] = None


@dataclass
class TaskPlan:
    """A complete plan for executing a task"""
    task: str
    workspace: str
    actions: List[PlannedAction] = field(default_factory=list)
    status: str = "planning"
    context: Dict[str, Any] = field(default_factory=dict)


class TaskPlanner:
    """
    Plans and executes tasks by breaking them into concrete actions.
    """
    
    # Keywords that indicate different types of work
    ACTION_KEYWORDS = {
        "create": ["create", "make", "build", "generate", "add", "new", "write"],
        "edit": ["edit", "modify", "change", "update", "fix", "refactor", "improve"],
        "delete": ["delete", "remove", "clean"],
        "test": ["test", "verify", "check", "validate", "run tests"],
        "run": ["run", "execute", "start", "launch"],
        "analyze": ["analyze", "review", "examine", "look at", "check"],
        "research": ["research", "find", "search", "look up", "learn about"],
        "git": ["commit", "push", "pull", "merge", "branch"],
    }
    
    # File type patterns
    FILE_PATTERNS = {
        "python": [".py"],
        "javascript": [".js", ".jsx", ".ts", ".tsx"],
        "kotlin": [".kt", ".kts"],
        "web": [".html", ".css", ".scss"],
        "config": [".json", ".yaml", ".yml", ".toml", ".env"],
        "docs": [".md", ".txt", ".rst"],
    }
    
    def __init__(self, ollama_client, workspace_path: str = None):
        """
        Initialize the task planner.
        
        Args:
            ollama_client: Ollama client for LLM calls
            workspace_path: Default workspace path
        """
        self.ollama_client = ollama_client
        self.workspace_path = workspace_path or os.getcwd()
        self.current_plan: Optional[TaskPlan] = None
    
    def analyze_task(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze a task to understand what needs to be done.
        
        Returns:
            Analysis with detected intents, file types, and suggested actions
        """
        task_lower = task.lower()
        context = context or {}
        
        analysis = {
            "task": task,
            "intents": [],
            "file_types": [],
            "workspace": context.get("workspace", self.workspace_path),
            "requires_code": False,
            "requires_files": False,
            "requires_research": False,
            "is_question": task.strip().endswith("?") or task_lower.startswith(("what", "how", "why", "when", "where", "who", "can")),
        }
        
        # Detect intents
        for intent, keywords in self.ACTION_KEYWORDS.items():
            if any(kw in task_lower for kw in keywords):
                analysis["intents"].append(intent)
        
        # Detect file types
        for file_type, extensions in self.FILE_PATTERNS.items():
            if any(ext in task_lower or file_type in task_lower for ext in extensions):
                analysis["file_types"].append(file_type)
        
        # Determine requirements
        analysis["requires_code"] = any(i in ["create", "edit", "run"] for i in analysis["intents"])
        analysis["requires_files"] = any(i in ["create", "edit", "delete", "analyze"] for i in analysis["intents"])
        analysis["requires_research"] = "research" in analysis["intents"] or "how to" in task_lower
        
        return analysis
    
    def create_plan(self, task: str, context: Dict[str, Any] = None) -> TaskPlan:
        """
        Create an execution plan for a task.
        
        This uses the LLM to generate a concrete plan of actions.
        """
        context = context or {}
        workspace = context.get("workspace", self.workspace_path)
        
        # Analyze the task first
        analysis = self.analyze_task(task, context)
        
        # Create the plan
        plan = TaskPlan(
            task=task,
            workspace=workspace,
            context=context
        )
        
        # Use LLM to generate detailed action plan
        plan_prompt = self._build_planning_prompt(task, analysis, context)
        
        try:
            response = self.ollama_client.chat(
                messages=[
                    {"role": "system", "content": self._get_planner_system_prompt()},
                    {"role": "user", "content": plan_prompt}
                ],
                model=os.getenv("DEFAULT_MODEL", "qwen2.5:latest")
            )
            
            # Parse the response into actions
            response_text = response.get("message", {}).get("content", "")
            plan.actions = self._parse_plan_response(response_text, workspace)
            plan.status = "ready"
            
        except Exception as e:
            logger.error(f"Error creating plan: {e}")
            # Fallback to simple analysis-based plan
            plan.actions = self._create_fallback_plan(analysis, workspace)
            plan.status = "ready"
        
        self.current_plan = plan
        return plan
    
    def _get_planner_system_prompt(self) -> str:
        """Get the system prompt for the planning LLM"""
        return """You are a task planning AI. Your job is to break down user requests into CONCRETE, EXECUTABLE actions.

For each action, specify:
1. ACTION_TYPE: One of: CREATE_FILE, EDIT_FILE, READ_FILE, RUN_COMMAND, RUN_TESTS, GIT_COMMIT, GIT_PUSH, RESEARCH, ANALYZE_CODE, GENERATE_CODE
2. DESCRIPTION: What this action does
3. PARAMETERS: Specific parameters needed

Format your response as a JSON array of actions:
```json
[
  {
    "action_type": "READ_FILE",
    "description": "Read the main app file to understand structure",
    "parameters": {"path": "src/app.py"}
  },
  {
    "action_type": "CREATE_FILE",
    "description": "Create a new feature module",
    "parameters": {"path": "src/new_feature.py", "content": "# New feature code here"}
  }
]
```

IMPORTANT:
- Be SPECIFIC about file paths and content
- Include actual code in CREATE_FILE and EDIT_FILE actions
- For EDIT_FILE, include both 'old_content' and 'new_content'
- For RUN_COMMAND, include the exact command
- Always analyze existing code before making changes
- Generate complete, working code, not placeholders"""
    
    def _build_planning_prompt(self, task: str, analysis: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Build the prompt for the planner"""
        workspace = analysis.get("workspace", self.workspace_path)
        
        prompt_parts = [
            f"Task: {task}",
            f"\nWorkspace: {workspace}",
            f"\nAnalysis:",
            f"- Detected intents: {', '.join(analysis['intents']) or 'general'}",
            f"- File types: {', '.join(analysis['file_types']) or 'unknown'}",
            f"- Requires code: {analysis['requires_code']}",
            f"- Is a question: {analysis['is_question']}",
        ]
        
        # Add context info
        if context:
            prompt_parts.append("\nContext:")
            for key, value in context.items():
                prompt_parts.append(f"- {key}: {value}")
        
        # Add file listing if available
        if os.path.exists(workspace):
            try:
                files = os.listdir(workspace)[:20]  # Limit to 20 files
                prompt_parts.append(f"\nFiles in workspace: {', '.join(files)}")
            except:
                pass
        
        prompt_parts.append("\n\nCreate a detailed action plan to accomplish this task.")
        prompt_parts.append("Return ONLY the JSON array of actions.")
        
        return "\n".join(prompt_parts)
    
    def _parse_plan_response(self, response: str, workspace: str) -> List[PlannedAction]:
        """Parse LLM response into PlannedAction objects"""
        actions = []
        
        # Try to extract JSON from response
        try:
            # Find JSON array in response
            import re
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                action_list = json.loads(json_match.group())
                
                for i, action_data in enumerate(action_list):
                    action_type_str = action_data.get("action_type", "RESPOND")
                    
                    try:
                        action_type = ActionType[action_type_str]
                    except KeyError:
                        action_type = ActionType.RESPOND
                    
                    action = PlannedAction(
                        action_type=action_type,
                        description=action_data.get("description", ""),
                        parameters=action_data.get("parameters", {}),
                        depends_on=action_data.get("depends_on", [])
                    )
                    actions.append(action)
        except json.JSONDecodeError:
            logger.warning("Could not parse plan response as JSON")
        
        return actions
    
    def _create_fallback_plan(self, analysis: Dict[str, Any], workspace: str) -> List[PlannedAction]:
        """Create a simple plan based on analysis when LLM fails"""
        actions = []
        
        # If it's a question, just respond
        if analysis.get("is_question"):
            actions.append(PlannedAction(
                action_type=ActionType.RESPOND,
                description="Respond to the user's question",
                parameters={"task": analysis["task"]}
            ))
            return actions
        
        # If requires research, add research step
        if analysis.get("requires_research"):
            actions.append(PlannedAction(
                action_type=ActionType.RESEARCH,
                description="Research the topic",
                parameters={"topic": analysis["task"]}
            ))
        
        # If requires file analysis, add that
        if analysis.get("requires_files"):
            actions.append(PlannedAction(
                action_type=ActionType.ANALYZE_CODE,
                description="Analyze existing code",
                parameters={"workspace": workspace}
            ))
        
        # If requires code generation
        if analysis.get("requires_code"):
            actions.append(PlannedAction(
                action_type=ActionType.GENERATE_CODE,
                description="Generate required code",
                parameters={"task": analysis["task"]}
            ))
        
        return actions
    
    def get_plan_summary(self, plan: TaskPlan = None) -> str:
        """Get a human-readable summary of a plan"""
        plan = plan or self.current_plan
        if not plan:
            return "No plan created"
        
        lines = [
            f"📋 Task: {plan.task}",
            f"📁 Workspace: {plan.workspace}",
            f"📊 Status: {plan.status}",
            f"\n🔧 Actions ({len(plan.actions)} steps):"
        ]
        
        for i, action in enumerate(plan.actions, 1):
            status_icon = {
                "pending": "⏳",
                "in_progress": "🔄",
                "completed": "✅",
                "failed": "❌"
            }.get(action.status, "❓")
            
            lines.append(f"  {status_icon} {i}. [{action.action_type.value}] {action.description}")
        
        return "\n".join(lines)
