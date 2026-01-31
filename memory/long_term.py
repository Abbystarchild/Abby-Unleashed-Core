"""
Long-term memory for persistent storage

Stores conversation history, task outcomes, and learnings
Uses simple JSON file storage (can be extended to use SQLite or vector DB)
"""
import logging
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class LongTermMemory:
    """
    Long-term memory for persistent storage
    
    Stores:
    - Conversation history
    - Task outcomes
    - Agent performance data
    - Learnings and patterns
    """
    
    def __init__(self, storage_path: str = "memory/storage", max_items: int = 10000):
        """
        Initialize long-term memory
        
        Args:
            storage_path: Path to storage directory
            max_items: Maximum items per collection before archival (performance)
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.max_items = max_items
        
        self.conversations_file = self.storage_path / "conversations.json"
        self.tasks_file = self.storage_path / "tasks.json"
        self.learnings_file = self.storage_path / "learnings.json"
        
        # Load or initialize storage
        self.conversations = self._load_json(self.conversations_file, [])
        self.tasks = self._load_json(self.tasks_file, [])
        self.learnings = self._load_json(self.learnings_file, [])
        
        logger.info(f"Long-term memory initialized at {storage_path}")
    
    def _load_json(self, filepath: Path, default: Any) -> Any:
        """Load JSON file or return default"""
        if filepath.exists():
            try:
                with open(filepath, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading {filepath}: {e}")
                return default
        return default
    
    def _save_json(self, filepath: Path, data: Any):
        """Save data to JSON file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving {filepath}: {e}")
    
    def store_conversation(
        self,
        conversation_id: str,
        turns: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Store a conversation
        
        Args:
            conversation_id: Unique conversation identifier
            turns: List of conversation turns
            metadata: Optional metadata
        """
        conversation = {
            "id": conversation_id,
            "turns": turns,
            "metadata": metadata or {},
            "stored_at": datetime.now().isoformat()
        }
        
        self.conversations.append(conversation)
        self._auto_archive(self.conversations, self.conversations_file, "conversations")
        self._save_json(self.conversations_file, self.conversations)
        
        logger.debug(f"Stored conversation: {conversation_id}")
    
    def get_conversations(
        self,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get conversations
        
        Args:
            limit: Maximum number to return
            offset: Offset for pagination
            
        Returns:
            List of conversations
        """
        return self.conversations[offset:offset + limit]
    
    def search_conversations(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search conversations (simple text search)
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of matching conversations
        """
        results = []
        query_lower = query.lower()
        
        for conv in self.conversations:
            # Search in turns
            for turn in conv.get("turns", []):
                if query_lower in turn.get("content", "").lower():
                    results.append(conv)
                    break
            
            if len(results) >= limit:
                break
        
        return results
    
    def store_task_outcome(
        self,
        task_id: str,
        description: str,
        result: Dict[str, Any],
        agent_id: Optional[str] = None,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Store task outcome
        
        Args:
            task_id: Task identifier
            description: Task description
            result: Task result
            agent_id: Agent that executed task
            success: Whether task succeeded
            metadata: Optional metadata
        """
        outcome = {
            "task_id": task_id,
            "description": description,
            "result": result,
            "agent_id": agent_id,
            "success": success,
            "metadata": metadata or {},
            "stored_at": datetime.now().isoformat()
        }
        
        self.tasks.append(outcome)
        self._auto_archive(self.tasks, self.tasks_file, "tasks")
        self._save_json(self.tasks_file, self.tasks)
        
        logger.debug(f"Stored task outcome: {task_id}")
    
    def get_task_outcomes(
        self,
        agent_id: Optional[str] = None,
        success_only: bool = False,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get task outcomes
        
        Args:
            agent_id: Filter by agent
            success_only: Only successful tasks
            limit: Maximum results
            
        Returns:
            List of task outcomes
        """
        results = []
        
        for task in self.tasks:
            if agent_id and task.get("agent_id") != agent_id:
                continue
            if success_only and not task.get("success"):
                continue
            
            results.append(task)
            
            if len(results) >= limit:
                break
        
        return results
    
    def store_learning(
        self,
        learning_type: str,
        content: str,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Store a learning or insight
        
        Args:
            learning_type: Type of learning (pattern, insight, rule, etc.)
            content: Learning content
            source: Source of learning
            metadata: Optional metadata
        """
        learning = {
            "type": learning_type,
            "content": content,
            "source": source,
            "metadata": metadata or {},
            "stored_at": datetime.now().isoformat()
        }
        
        self.learnings.append(learning)
        self._auto_archive(self.learnings, self.learnings_file, "learnings")
        self._save_json(self.learnings_file, self.learnings)
        
        logger.debug(f"Stored learning: {learning_type}")
    
    def get_learnings(
        self,
        learning_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get learnings
        
        Args:
            learning_type: Filter by type
            limit: Maximum results
            
        Returns:
            List of learnings
        """
        results = []
        
        for learning in self.learnings:
            if learning_type and learning.get("type") != learning_type:
                continue
            
            results.append(learning)
            
            if len(results) >= limit:
                break
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get memory statistics
        
        Returns:
            Statistics dictionary
        """
        successful_tasks = sum(1 for t in self.tasks if t.get("success"))
        
        return {
            "total_conversations": len(self.conversations),
            "total_tasks": len(self.tasks),
            "successful_tasks": successful_tasks,
            "success_rate": successful_tasks / len(self.tasks) if self.tasks else 0,
            "total_learnings": len(self.learnings),
            "storage_path": str(self.storage_path)
        }
    
    def _auto_archive(self, collection: List[Any], filepath: Path, name: str):
        """
        Automatically archive old items if collection exceeds max_items
        
        Args:
            collection: The collection to check
            filepath: File path for this collection
            name: Name of the collection for logging
        """
        if len(collection) > self.max_items:
            # Archive oldest 20% of items
            archive_count = int(self.max_items * 0.2)
            archive_items = collection[:archive_count]
            
            # Save to archive file
            archive_file = filepath.parent / f"{filepath.stem}_archive_{datetime.now().strftime('%Y%m')}.json"
            existing_archive = self._load_json(archive_file, [])
            existing_archive.extend(archive_items)
            self._save_json(archive_file, existing_archive)
            
            # Remove archived items from main collection
            del collection[:archive_count]
            
            logger.info(f"Archived {archive_count} {name} to {archive_file.name}")
    
    def clear_all(self, confirm: bool = False):
        """
        Clear all long-term memory (use with caution!)
        
        Args:
            confirm: Must be True to actually clear
        """
        if not confirm:
            logger.warning("Clear all requires confirm=True")
            return
        
        self.conversations.clear()
        self.tasks.clear()
        self.learnings.clear()
        
        self._save_json(self.conversations_file, self.conversations)
        self._save_json(self.tasks_file, self.tasks)
        self._save_json(self.learnings_file, self.learnings)
        
        logger.warning("Cleared all long-term memory")
