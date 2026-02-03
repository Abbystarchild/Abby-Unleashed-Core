"""
Task Decomposer for Abby

Handles breaking down complex, overwhelming requests into manageable subtasks.
This is crucial for Abby to handle large development projects without getting
lost or producing incomplete work.

Key Principles:
1. NEVER try to do everything at once
2. Create clear, actionable subtasks
3. Track progress and state
4. Allow for parallel work where possible
5. Save progress so work isn't lost

Usage:
    decomposer = TaskDecomposer(ollama_client)
    plan = decomposer.decompose("Build a complete dating app with...")
    
    for task in plan.get_next_tasks():
        result = execute_task(task)
        plan.mark_complete(task.id, result)
"""

import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from concurrent.futures import ThreadPoolExecutor, Future

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskPriority(Enum):
    CRITICAL = 1  # Must do first
    HIGH = 2      # Important
    MEDIUM = 3    # Normal
    LOW = 4       # Nice to have


@dataclass
class SubTask:
    """A single actionable subtask"""
    id: str
    title: str
    description: str
    category: str  # e.g., "analysis", "frontend", "backend", "testing"
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[str] = field(default_factory=list)  # IDs of tasks that must complete first
    estimated_complexity: int = 1  # 1-5 scale
    assigned_agent: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: List[str] = field(default_factory=list)
    files_to_create: List[str] = field(default_factory=list)
    files_to_modify: List[str] = field(default_factory=list)


@dataclass
class TaskPlan:
    """Complete plan for a complex task"""
    id: str
    original_request: str
    summary: str
    tasks: List[SubTask] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    completed_tasks: int = 0
    total_tasks: int = 0
    current_phase: str = "planning"
    notes: List[str] = field(default_factory=list)
    
    def get_next_tasks(self, max_parallel: int = 3) -> List[SubTask]:
        """Get next tasks that can be worked on (dependencies satisfied)"""
        completed_ids = {t.id for t in self.tasks if t.status == TaskStatus.COMPLETED}
        in_progress_ids = {t.id for t in self.tasks if t.status == TaskStatus.IN_PROGRESS}
        
        available = []
        for task in self.tasks:
            if task.status != TaskStatus.PENDING:
                continue
            # Check if all dependencies are completed
            if all(dep in completed_ids for dep in task.dependencies):
                available.append(task)
        
        # Sort by priority and return up to max_parallel
        available.sort(key=lambda t: (t.priority.value, -t.estimated_complexity))
        
        # Don't exceed max parallel tasks
        can_start = max_parallel - len(in_progress_ids)
        return available[:max(0, can_start)]
    
    def mark_complete(self, task_id: str, result: str = ""):
        """Mark a task as complete"""
        for task in self.tasks:
            if task.id == task_id:
                task.status = TaskStatus.COMPLETED
                task.result = result
                task.completed_at = datetime.now()
                self.completed_tasks += 1
                break
    
    def mark_failed(self, task_id: str, error: str):
        """Mark a task as failed"""
        for task in self.tasks:
            if task.id == task_id:
                task.status = TaskStatus.FAILED
                task.error = error
                break
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current progress"""
        status_counts = {}
        for task in self.tasks:
            status = task.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total": self.total_tasks,
            "completed": self.completed_tasks,
            "percent": (self.completed_tasks / self.total_tasks * 100) if self.total_tasks > 0 else 0,
            "by_status": status_counts,
            "current_phase": self.current_phase
        }
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for saving"""
        return {
            "id": self.id,
            "original_request": self.original_request,
            "summary": self.summary,
            "tasks": [
                {
                    "id": t.id,
                    "title": t.title,
                    "description": t.description,
                    "category": t.category,
                    "priority": t.priority.value,
                    "status": t.status.value,
                    "dependencies": t.dependencies,
                    "estimated_complexity": t.estimated_complexity,
                    "result": t.result,
                    "error": t.error,
                    "notes": t.notes,
                    "files_to_create": t.files_to_create,
                    "files_to_modify": t.files_to_modify,
                }
                for t in self.tasks
            ],
            "created_at": self.created_at.isoformat(),
            "completed_tasks": self.completed_tasks,
            "total_tasks": self.total_tasks,
            "current_phase": self.current_phase,
            "notes": self.notes,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TaskPlan':
        """Load from dictionary"""
        plan = cls(
            id=data["id"],
            original_request=data["original_request"],
            summary=data["summary"],
            created_at=datetime.fromisoformat(data["created_at"]),
            completed_tasks=data["completed_tasks"],
            total_tasks=data["total_tasks"],
            current_phase=data["current_phase"],
            notes=data.get("notes", []),
        )
        
        for t in data["tasks"]:
            task = SubTask(
                id=t["id"],
                title=t["title"],
                description=t["description"],
                category=t["category"],
                priority=TaskPriority(t["priority"]),
                status=TaskStatus(t["status"]),
                dependencies=t.get("dependencies", []),
                estimated_complexity=t.get("estimated_complexity", 1),
                result=t.get("result"),
                error=t.get("error"),
                notes=t.get("notes", []),
                files_to_create=t.get("files_to_create", []),
                files_to_modify=t.get("files_to_modify", []),
            )
            plan.tasks.append(task)
        
        return plan


class TaskDecomposer:
    """
    Decomposes complex tasks into manageable subtasks.
    
    This is Abby's key tool for handling overwhelming requests.
    Instead of trying to do everything at once, she breaks it down
    and tackles it piece by piece.
    """
    
    # Task categories and their typical subtasks
    CATEGORY_PATTERNS = {
        "analysis": ["analyze", "review", "check", "examine", "research", "investigate", "understand"],
        "design": ["design", "plan", "architect", "structure", "layout", "wireframe"],
        "frontend": ["ui", "ux", "screen", "page", "component", "view", "display", "button", "form"],
        "backend": ["api", "server", "database", "endpoint", "service", "logic", "auth"],
        "integration": ["connect", "wire", "integrate", "link", "combine", "merge"],
        "testing": ["test", "verify", "validate", "check", "debug", "fix"],
        "assets": ["image", "icon", "graphic", "asset", "placeholder", "media", "sound", "animation"],
        "documentation": ["document", "readme", "comment", "explain", "note"],
    }
    
    def __init__(self, ollama_client=None, save_dir: str = "session_state/task_plans"):
        """
        Initialize the task decomposer.
        
        Args:
            ollama_client: Ollama client for AI-assisted decomposition
            save_dir: Directory to save task plans
        """
        self.ollama = ollama_client
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.current_plan: Optional[TaskPlan] = None
        
    def decompose(self, request: str, context: Dict[str, Any] = None) -> TaskPlan:
        """
        Decompose a complex request into a task plan.
        
        Args:
            request: The full user request
            context: Additional context (workspace, existing files, etc.)
            
        Returns:
            TaskPlan with organized subtasks
        """
        context = context or {}
        
        logger.info(f"Decomposing request: {request[:100]}...")
        
        # Generate unique plan ID
        plan_id = f"plan_{int(time.time())}"
        
        # Create initial plan
        plan = TaskPlan(
            id=plan_id,
            original_request=request,
            summary=self._generate_summary(request),
        )
        
        # Extract tasks using multiple strategies
        tasks = []
        
        # 1. Try AI-assisted decomposition first
        if self.ollama:
            ai_tasks = self._ai_decompose(request, context)
            tasks.extend(ai_tasks)
        
        # 2. Rule-based extraction as fallback/supplement
        rule_tasks = self._rule_based_decompose(request, context)
        
        # Merge tasks (avoid duplicates)
        existing_titles = {t.title.lower() for t in tasks}
        for task in rule_tasks:
            if task.title.lower() not in existing_titles:
                tasks.append(task)
                existing_titles.add(task.title.lower())
        
        # 3. Add standard phases if missing
        tasks = self._ensure_standard_phases(tasks, request)
        
        # 4. Establish dependencies
        tasks = self._establish_dependencies(tasks)
        
        # 5. Assign IDs and finalize
        for i, task in enumerate(tasks):
            task.id = f"task_{i+1:03d}"
        
        plan.tasks = tasks
        plan.total_tasks = len(tasks)
        
        # Save the plan
        self._save_plan(plan)
        self.current_plan = plan
        
        logger.info(f"Created plan with {len(tasks)} tasks")
        return plan
    
    def _generate_summary(self, request: str) -> str:
        """Generate a brief summary of the request"""
        # Extract first sentence or first 200 chars
        first_sentence = re.split(r'[.!?]', request)[0]
        if len(first_sentence) > 200:
            return first_sentence[:197] + "..."
        return first_sentence
    
    def _ai_decompose(self, request: str, context: Dict) -> List[SubTask]:
        """Use AI to decompose the task"""
        tasks = []
        
        try:
            prompt = f"""Break this development request into specific, actionable tasks.
Each task should be something that can be completed in 1-2 hours.

REQUEST:
{request[:4000]}

Output a JSON array of tasks:
[
    {{
        "title": "Short task title",
        "description": "What to do",
        "category": "analysis|design|frontend|backend|integration|testing|assets|documentation",
        "complexity": 1-5,
        "files": ["files to create or modify"]
    }}
]

Tasks (JSON only):"""

            response = self.ollama.generate(
                prompt=prompt,
                model="mistral:latest",
                options={"temperature": 0.3, "num_predict": 2000}
            )
            
            if "error" in response:
                logger.warning(f"AI decomposition failed: {response['error']}")
                return []
            
            text = response.get("response", "")
            
            # Extract JSON array
            json_match = re.search(r'\[.*\]', text, re.DOTALL)
            if json_match:
                # Fix common JSON issues
                json_str = json_match.group()
                json_str = re.sub(r'(?<!\\)\\(?!["\\/bfnrt])', r'\\\\', json_str)
                
                try:
                    task_data = json.loads(json_str)
                    
                    for item in task_data:
                        task = SubTask(
                            id="",  # Will be assigned later
                            title=item.get("title", "Unnamed Task"),
                            description=item.get("description", ""),
                            category=item.get("category", "general"),
                            estimated_complexity=item.get("complexity", 2),
                            files_to_create=item.get("files", []),
                        )
                        tasks.append(task)
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON parse error in AI decomposition: {e}")
                    
        except Exception as e:
            logger.error(f"AI decomposition error: {e}")
        
        return tasks
    
    def _rule_based_decompose(self, request: str, context: Dict) -> List[SubTask]:
        """Rule-based task extraction"""
        tasks = []
        request_lower = request.lower()
        
        # Extract explicit numbered items
        numbered = re.findall(r'(?:^|\n)\s*(\d+)[\.\):\s]+([^\n]+)', request)
        for num, text in numbered:
            category = self._categorize_text(text)
            tasks.append(SubTask(
                id="",
                title=f"Item {num}: {text[:50]}",
                description=text,
                category=category,
            ))
        
        # Extract bullet points
        bullets = re.findall(r'(?:^|\n)\s*[-•*]\s+([^\n]+)', request)
        for text in bullets:
            if len(text) > 10:
                category = self._categorize_text(text)
                tasks.append(SubTask(
                    id="",
                    title=text[:60],
                    description=text,
                    category=category,
                ))
        
        # Extract mentioned pages/screens
        pages = re.findall(r'(\w+)\s+(?:page|screen|view)', request_lower)
        for page in set(pages):
            tasks.append(SubTask(
                id="",
                title=f"Implement {page.title()} Page",
                description=f"Build the {page} page/screen with required functionality",
                category="frontend",
                priority=TaskPriority.HIGH,
            ))
        
        # Extract mentioned features
        features = re.findall(r'(?:feature|functionality|option|ability)[\s:]+([^,.!?\n]+)', request_lower)
        for feature in set(features):
            if len(feature) > 5:
                tasks.append(SubTask(
                    id="",
                    title=f"Feature: {feature.strip().title()}",
                    description=f"Implement {feature.strip()}",
                    category="backend" if any(w in feature for w in ['api', 'database', 'server']) else "frontend",
                ))
        
        return tasks
    
    def _categorize_text(self, text: str) -> str:
        """Determine category for a piece of text"""
        text_lower = text.lower()
        
        for category, keywords in self.CATEGORY_PATTERNS.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return "general"
    
    def _ensure_standard_phases(self, tasks: List[SubTask], request: str) -> List[SubTask]:
        """Ensure standard development phases are included"""
        categories = {t.category for t in tasks}
        
        # Always start with analysis
        if "analysis" not in categories:
            tasks.insert(0, SubTask(
                id="",
                title="Analyze Requirements & Existing Code",
                description="Review the request, understand requirements, check existing codebase",
                category="analysis",
                priority=TaskPriority.CRITICAL,
                estimated_complexity=2,
            ))
        
        # Add design phase if building something substantial
        if "design" not in categories and any(w in request.lower() for w in ['build', 'create', 'develop', 'implement']):
            tasks.insert(1, SubTask(
                id="",
                title="Design Architecture & Plan Approach",
                description="Design system architecture, plan component structure, identify data models",
                category="design",
                priority=TaskPriority.HIGH,
                estimated_complexity=3,
            ))
        
        # Always end with testing
        if "testing" not in categories:
            tasks.append(SubTask(
                id="",
                title="Integration Testing & Bug Fixes",
                description="Test all features, fix bugs, ensure everything works together",
                category="testing",
                priority=TaskPriority.HIGH,
                estimated_complexity=3,
            ))
        
        return tasks
    
    def _establish_dependencies(self, tasks: List[SubTask]) -> List[SubTask]:
        """Establish dependencies between tasks"""
        # Category order (earlier categories should complete before later ones)
        category_order = ["analysis", "design", "backend", "frontend", "assets", "integration", "testing", "documentation"]
        
        # Group tasks by category
        by_category: Dict[str, List[int]] = {}
        for i, task in enumerate(tasks):
            cat = task.category
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(i)
        
        # Set dependencies based on category order
        for i, cat in enumerate(category_order):
            if cat not in by_category:
                continue
                
            # Find previous category tasks
            prev_cats = category_order[:i]
            prev_task_ids = []
            for prev_cat in prev_cats:
                if prev_cat in by_category:
                    # Just depend on one task from each previous category (not all)
                    prev_task_ids.append(f"task_{by_category[prev_cat][-1]+1:03d}")
            
            # Assign dependencies
            for task_idx in by_category[cat]:
                if prev_task_ids:
                    # Only depend on the last completed category
                    tasks[task_idx].dependencies = [prev_task_ids[-1]] if prev_task_ids else []
        
        return tasks
    
    def _save_plan(self, plan: TaskPlan):
        """Save plan to disk"""
        filepath = self.save_dir / f"{plan.id}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(plan.to_dict(), f, indent=2, default=str)
        logger.info(f"Saved plan to {filepath}")
    
    def load_plan(self, plan_id: str) -> Optional[TaskPlan]:
        """Load a plan from disk"""
        filepath = self.save_dir / f"{plan_id}.json"
        if not filepath.exists():
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        plan = TaskPlan.from_dict(data)
        self.current_plan = plan
        return plan
    
    def list_plans(self) -> List[Dict[str, Any]]:
        """List all saved plans"""
        plans = []
        for filepath in self.save_dir.glob("plan_*.json"):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                plans.append({
                    "id": data["id"],
                    "summary": data["summary"],
                    "total_tasks": data["total_tasks"],
                    "completed_tasks": data["completed_tasks"],
                    "created_at": data["created_at"],
                })
            except Exception as e:
                logger.warning(f"Error loading plan {filepath}: {e}")
        
        return sorted(plans, key=lambda p: p["created_at"], reverse=True)
    
    def get_status_report(self) -> str:
        """Get a human-readable status report of current plan"""
        if not self.current_plan:
            return "No active plan."
        
        plan = self.current_plan
        progress = plan.get_progress()
        
        lines = [
            f"📋 Task Plan: {plan.summary}",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"Progress: {progress['completed']}/{progress['total']} ({progress['percent']:.1f}%)",
            f"",
        ]
        
        # Group by status
        by_status = {}
        for task in plan.tasks:
            status = task.status.value
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(task)
        
        status_icons = {
            "completed": "✅",
            "in_progress": "🔄",
            "pending": "⏳",
            "blocked": "🚫",
            "failed": "❌",
        }
        
        for status in ["in_progress", "pending", "completed", "failed", "blocked"]:
            if status not in by_status:
                continue
            tasks = by_status[status]
            icon = status_icons.get(status, "•")
            lines.append(f"{icon} {status.upper()} ({len(tasks)}):")
            for task in tasks[:5]:  # Show max 5 per status
                lines.append(f"   • {task.title}")
            if len(tasks) > 5:
                lines.append(f"   ... and {len(tasks)-5} more")
            lines.append("")
        
        return "\n".join(lines)


# Singleton instance
_decomposer: Optional[TaskDecomposer] = None


def get_task_decomposer(ollama_client=None) -> TaskDecomposer:
    """Get or create the task decomposer singleton"""
    global _decomposer
    if _decomposer is None:
        _decomposer = TaskDecomposer(ollama_client=ollama_client)
    return _decomposer


# Test code
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    decomposer = TaskDecomposer()
    
    # Test with SafeConnect-like request
    test_request = """
    Build a dating app with:
    1. Login page
    2. Character creator with hair and clothing options
    3. Discovery page with tavern theme
    4. Matches page with chat functionality
    5. SafeConnect feature for safe dates
    
    The app should work on iOS and Android.
    Create placeholder graphics where needed.
    """
    
    plan = decomposer.decompose(test_request)
    
    print(decomposer.get_status_report())
    print("\nNext tasks:")
    for task in plan.get_next_tasks():
        print(f"  - [{task.category}] {task.title}")
