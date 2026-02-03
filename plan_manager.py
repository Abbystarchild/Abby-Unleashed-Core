"""
Plan Manager for Abby Unleashed

Provides:
1. Plan Queue Management - view, prioritize, pause, delete plans
2. Plan Editing - update tasks, add context, make corrections
3. Multi-Plan Decomposition - break huge tasks into multiple plans
4. Progress Tracking - see what's done, what's next
5. API endpoints for the GUI
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class PlanStatus(Enum):
    ACTIVE = "active"       # Currently being worked on
    QUEUED = "queued"       # In queue, waiting
    PAUSED = "paused"       # Paused by user
    COMPLETED = "completed" # All tasks done
    ARCHIVED = "archived"   # Saved for later


@dataclass
class PlanMetadata:
    """Metadata for a plan"""
    id: str
    name: str
    status: str = "queued"
    priority: int = 5  # 1-10, 1 is highest
    created_at: str = ""
    updated_at: str = ""
    total_tasks: int = 0
    completed_tasks: int = 0
    user_notes: str = ""
    tags: List[str] = field(default_factory=list)
    parent_plan_id: Optional[str] = None  # For sub-plans


class PlanManager:
    """
    Manages all task plans for Abby.
    
    Features:
    - Queue management with priorities
    - Plan editing and context updates
    - Pause/resume/archive functionality
    - Multi-plan decomposition support
    """
    
    def __init__(self, plans_dir: str = "session_state/task_plans"):
        self.plans_dir = Path(plans_dir)
        self.plans_dir.mkdir(parents=True, exist_ok=True)
        
        self.metadata_file = self.plans_dir / "_plan_metadata.json"
        self.metadata: Dict[str, PlanMetadata] = {}
        
        self._load_metadata()
    
    def _load_metadata(self):
        """Load plan metadata from disk"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)
                    for plan_id, meta in data.items():
                        self.metadata[plan_id] = PlanMetadata(**meta)
            except Exception as e:
                logger.warning(f"Error loading metadata: {e}")
        
        # Sync with actual plan files
        self._sync_metadata()
    
    def _sync_metadata(self):
        """Sync metadata with actual plan files on disk"""
        # Find all plan files
        plan_files = list(self.plans_dir.glob("plan_*.json"))
        
        for plan_file in plan_files:
            plan_id = plan_file.stem
            
            if plan_id not in self.metadata:
                # Load plan to get basic info
                try:
                    with open(plan_file, 'r') as f:
                        plan_data = json.load(f)
                    
                    # Create metadata from plan
                    self.metadata[plan_id] = PlanMetadata(
                        id=plan_id,
                        name=plan_data.get("summary", "Unnamed Plan")[:50],
                        status="queued",
                        created_at=plan_data.get("created_at", datetime.now().isoformat()),
                        updated_at=plan_data.get("updated_at", datetime.now().isoformat()),
                        total_tasks=len(plan_data.get("tasks", [])),
                        completed_tasks=len([t for t in plan_data.get("tasks", []) if t.get("status") == "completed"]),
                    )
                except Exception as e:
                    logger.warning(f"Error syncing plan {plan_id}: {e}")
        
        # Remove metadata for deleted plans
        existing_ids = {f.stem for f in plan_files}
        to_remove = [pid for pid in self.metadata if pid not in existing_ids]
        for pid in to_remove:
            del self.metadata[pid]
        
        self._save_metadata()
    
    def _save_metadata(self):
        """Save metadata to disk"""
        try:
            data = {pid: asdict(meta) for pid, meta in self.metadata.items()}
            with open(self.metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
    
    # =========================================================================
    # Plan Queue Operations
    # =========================================================================
    
    def get_all_plans(self) -> List[Dict[str, Any]]:
        """Get all plans with their metadata"""
        plans = []
        
        for plan_id, meta in self.metadata.items():
            plan_info = asdict(meta)
            
            # Load full plan for additional details
            plan_data = self.get_plan(plan_id)
            if plan_data:
                plan_info["original_request"] = plan_data.get("original_request", "")[:200]
                plan_info["tasks_preview"] = [
                    {"id": t["id"], "title": t["title"][:50], "status": t["status"]}
                    for t in plan_data.get("tasks", [])[:5]
                ]
            
            plans.append(plan_info)
        
        # Sort by priority then by created date
        plans.sort(key=lambda p: (p.get("priority", 5), p.get("created_at", "")))
        
        return plans
    
    def get_queue(self) -> List[Dict[str, Any]]:
        """Get plans in the active queue (active + queued)"""
        all_plans = self.get_all_plans()
        return [p for p in all_plans if p["status"] in ["active", "queued"]]
    
    def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get full plan data"""
        plan_file = self.plans_dir / f"{plan_id}.json"
        
        if not plan_file.exists():
            return None
        
        try:
            with open(plan_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading plan {plan_id}: {e}")
            return None
    
    def save_plan(self, plan_id: str, plan_data: Dict[str, Any]) -> bool:
        """Save plan data"""
        plan_file = self.plans_dir / f"{plan_id}.json"
        
        try:
            plan_data["updated_at"] = datetime.now().isoformat()
            
            with open(plan_file, 'w') as f:
                json.dump(plan_data, f, indent=2)
            
            # Update metadata
            if plan_id in self.metadata:
                self.metadata[plan_id].updated_at = plan_data["updated_at"]
                self.metadata[plan_id].total_tasks = len(plan_data.get("tasks", []))
                self.metadata[plan_id].completed_tasks = len([
                    t for t in plan_data.get("tasks", []) if t.get("status") == "completed"
                ])
                self._save_metadata()
            
            return True
        except Exception as e:
            logger.error(f"Error saving plan {plan_id}: {e}")
            return False
    
    # =========================================================================
    # Plan Status Management
    # =========================================================================
    
    def set_status(self, plan_id: str, status: str) -> bool:
        """Update plan status"""
        if plan_id not in self.metadata:
            return False
        
        if status not in [s.value for s in PlanStatus]:
            return False
        
        self.metadata[plan_id].status = status
        self.metadata[plan_id].updated_at = datetime.now().isoformat()
        self._save_metadata()
        
        return True
    
    def set_priority(self, plan_id: str, priority: int) -> bool:
        """Update plan priority (1-10, 1 is highest)"""
        if plan_id not in self.metadata:
            return False
        
        self.metadata[plan_id].priority = max(1, min(10, priority))
        self._save_metadata()
        
        return True
    
    def pause_plan(self, plan_id: str) -> bool:
        """Pause a plan"""
        return self.set_status(plan_id, PlanStatus.PAUSED.value)
    
    def resume_plan(self, plan_id: str) -> bool:
        """Resume a paused plan"""
        return self.set_status(plan_id, PlanStatus.QUEUED.value)
    
    def archive_plan(self, plan_id: str) -> bool:
        """Archive a plan for later"""
        return self.set_status(plan_id, PlanStatus.ARCHIVED.value)
    
    def delete_plan(self, plan_id: str) -> bool:
        """Delete a plan"""
        plan_file = self.plans_dir / f"{plan_id}.json"
        
        try:
            if plan_file.exists():
                plan_file.unlink()
            
            if plan_id in self.metadata:
                del self.metadata[plan_id]
                self._save_metadata()
            
            return True
        except Exception as e:
            logger.error(f"Error deleting plan {plan_id}: {e}")
            return False
    
    # =========================================================================
    # Plan Editing
    # =========================================================================
    
    def update_plan_notes(self, plan_id: str, notes: str) -> bool:
        """Update user notes on a plan"""
        if plan_id not in self.metadata:
            return False
        
        self.metadata[plan_id].user_notes = notes
        self.metadata[plan_id].updated_at = datetime.now().isoformat()
        self._save_metadata()
        
        return True
    
    def update_task(self, plan_id: str, task_id: str, updates: Dict[str, Any]) -> bool:
        """Update a specific task in a plan"""
        plan_data = self.get_plan(plan_id)
        if not plan_data:
            return False
        
        # Find and update the task
        for task in plan_data.get("tasks", []):
            if task["id"] == task_id:
                # Allow updating specific fields
                allowed_fields = ["title", "description", "priority", "notes", "context", "status"]
                for field in allowed_fields:
                    if field in updates:
                        task[field] = updates[field]
                
                return self.save_plan(plan_id, plan_data)
        
        return False
    
    def add_task_context(self, plan_id: str, task_id: str, context: str) -> bool:
        """Add additional context to a task"""
        plan_data = self.get_plan(plan_id)
        if not plan_data:
            return False
        
        for task in plan_data.get("tasks", []):
            if task["id"] == task_id:
                existing_context = task.get("user_context", "")
                task["user_context"] = f"{existing_context}\n\n{context}".strip()
                return self.save_plan(plan_id, plan_data)
        
        return False
    
    def add_task_to_plan(self, plan_id: str, task_data: Dict[str, Any]) -> bool:
        """Add a new task to an existing plan"""
        plan_data = self.get_plan(plan_id)
        if not plan_data:
            return False
        
        # Generate task ID
        existing_ids = [t["id"] for t in plan_data.get("tasks", [])]
        task_num = len(existing_ids) + 1
        while f"task_{task_num:03d}" in existing_ids:
            task_num += 1
        
        new_task = {
            "id": f"task_{task_num:03d}",
            "title": task_data.get("title", "New Task"),
            "description": task_data.get("description", ""),
            "category": task_data.get("category", "general"),
            "priority": task_data.get("priority", 5),
            "status": "pending",
            "dependencies": task_data.get("dependencies", []),
            "estimated_complexity": task_data.get("estimated_complexity", 2),
            "result": None,
            "error": None,
            "notes": [],
            "user_context": task_data.get("context", ""),
            "files_to_create": [],
            "files_to_modify": []
        }
        
        plan_data["tasks"].append(new_task)
        return self.save_plan(plan_id, plan_data)
    
    def remove_task_from_plan(self, plan_id: str, task_id: str) -> bool:
        """Remove a task from a plan"""
        plan_data = self.get_plan(plan_id)
        if not plan_data:
            return False
        
        plan_data["tasks"] = [t for t in plan_data.get("tasks", []) if t["id"] != task_id]
        
        # Also remove from dependencies
        for task in plan_data["tasks"]:
            if task_id in task.get("dependencies", []):
                task["dependencies"].remove(task_id)
        
        return self.save_plan(plan_id, plan_data)
    
    # =========================================================================
    # Multi-Plan Operations
    # =========================================================================
    
    def split_plan(self, plan_id: str, split_at_task: str) -> Optional[str]:
        """Split a plan into two at a specific task"""
        plan_data = self.get_plan(plan_id)
        if not plan_data:
            return None
        
        tasks = plan_data.get("tasks", [])
        split_index = None
        
        for i, task in enumerate(tasks):
            if task["id"] == split_at_task:
                split_index = i
                break
        
        if split_index is None or split_index == 0:
            return None
        
        # Create new plan with tasks from split point
        new_plan_id = f"plan_{int(datetime.now().timestamp())}"
        new_tasks = tasks[split_index:]
        
        # Adjust task IDs for new plan
        id_mapping = {}
        for i, task in enumerate(new_tasks):
            old_id = task["id"]
            new_id = f"task_{i+1:03d}"
            id_mapping[old_id] = new_id
            task["id"] = new_id
        
        # Update dependencies
        for task in new_tasks:
            task["dependencies"] = [
                id_mapping.get(dep, dep) for dep in task.get("dependencies", [])
                if dep in id_mapping
            ]
        
        new_plan_data = {
            "id": new_plan_id,
            "original_request": f"[Split from {plan_id}] {plan_data.get('original_request', '')}",
            "summary": f"Part 2: {plan_data.get('summary', '')}",
            "tasks": new_tasks,
            "created_at": datetime.now().isoformat(),
            "parent_plan_id": plan_id,
        }
        
        # Save new plan
        self.save_plan(new_plan_id, new_plan_data)
        
        # Update original plan
        plan_data["tasks"] = tasks[:split_index]
        plan_data["summary"] = f"Part 1: {plan_data.get('summary', '')}"
        self.save_plan(plan_id, plan_data)
        
        # Create metadata for new plan
        self.metadata[new_plan_id] = PlanMetadata(
            id=new_plan_id,
            name=new_plan_data["summary"][:50],
            status="queued",
            created_at=new_plan_data["created_at"],
            updated_at=new_plan_data["created_at"],
            total_tasks=len(new_tasks),
            completed_tasks=0,
            parent_plan_id=plan_id,
        )
        self._save_metadata()
        
        return new_plan_id
    
    def get_active_plan(self) -> Optional[Dict[str, Any]]:
        """Get the currently active plan (highest priority queued plan)"""
        queue = self.get_queue()
        
        # First check for explicitly active plan
        for plan in queue:
            if plan["status"] == "active":
                return self.get_plan(plan["id"])
        
        # Otherwise get highest priority queued plan
        for plan in queue:
            if plan["status"] == "queued":
                # Set it as active
                self.set_status(plan["id"], "active")
                return self.get_plan(plan["id"])
        
        return None
    
    def get_next_task(self) -> Optional[Dict[str, Any]]:
        """Get the next task to work on from the active plan"""
        plan = self.get_active_plan()
        if not plan:
            return None
        
        # Find next pending task with satisfied dependencies
        for task in plan.get("tasks", []):
            if task.get("status") == "pending":
                deps = task.get("dependencies", [])
                
                # Check if all dependencies are complete
                deps_satisfied = True
                for dep in deps:
                    dep_task = next((t for t in plan["tasks"] if t["id"] == dep), None)
                    if dep_task and dep_task.get("status") != "completed":
                        deps_satisfied = False
                        break
                
                if deps_satisfied:
                    return {
                        "plan_id": plan["id"],
                        "task": task,
                        "plan_name": plan.get("summary", "")[:50],
                    }
        
        return None


# Singleton
_plan_manager: Optional[PlanManager] = None

def get_plan_manager() -> PlanManager:
    """Get or create the plan manager singleton"""
    global _plan_manager
    if _plan_manager is None:
        _plan_manager = PlanManager()
    return _plan_manager
