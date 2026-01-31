"""
Short-term memory for conversation context

Stores recent conversation turns and maintains context window
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)


class ConversationTurn:
    """A single conversation turn"""
    
    def __init__(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.role = role  # "user", "assistant", "system"
        self.content = content
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "role": self.role,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


class ShortTermMemory:
    """
    Short-term memory for conversation context
    
    Maintains a sliding window of recent conversation turns
    """
    
    def __init__(self, max_turns: int = 10):
        """
        Initialize short-term memory
        
        Args:
            max_turns: Maximum number of turns to keep
        """
        self.max_turns = max_turns
        self.turns: deque = deque(maxlen=max_turns)
        logger.info(f"Short-term memory initialized (max_turns={max_turns})")
    
    def add_turn(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add a conversation turn
        
        Args:
            role: Speaker role (user, assistant, system)
            content: Message content
            metadata: Optional metadata
        """
        turn = ConversationTurn(role, content, metadata)
        self.turns.append(turn)
        logger.debug(f"Added turn: {role}")
    
    def get_recent_turns(self, n: Optional[int] = None) -> List[ConversationTurn]:
        """
        Get recent conversation turns
        
        Args:
            n: Number of turns to retrieve (all if None)
            
        Returns:
            List of conversation turns
        """
        if n is None:
            return list(self.turns)
        return list(self.turns)[-n:]
    
    def get_context_string(self, n: Optional[int] = None) -> str:
        """
        Get conversation context as formatted string
        
        Args:
            n: Number of recent turns to include
            
        Returns:
            Formatted context string
        """
        turns = self.get_recent_turns(n)
        lines = []
        
        for turn in turns:
            lines.append(f"{turn.role.upper()}: {turn.content}")
        
        return "\n".join(lines)
    
    def get_messages_for_llm(
        self,
        n: Optional[int] = None,
        include_system: bool = True
    ) -> List[Dict[str, str]]:
        """
        Get messages formatted for LLM API
        
        Args:
            n: Number of recent turns to include
            include_system: Include system messages
            
        Returns:
            List of message dictionaries
        """
        turns = self.get_recent_turns(n)
        messages = []
        
        for turn in turns:
            if not include_system and turn.role == "system":
                continue
            
            messages.append({
                "role": turn.role,
                "content": turn.content
            })
        
        return messages
    
    def clear(self):
        """Clear all conversation history"""
        self.turns.clear()
        logger.info("Short-term memory cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get memory statistics
        
        Returns:
            Statistics dictionary
        """
        role_counts = {}
        for turn in self.turns:
            role_counts[turn.role] = role_counts.get(turn.role, 0) + 1
        
        return {
            "total_turns": len(self.turns),
            "max_turns": self.max_turns,
            "role_counts": role_counts,
            "oldest_turn": self.turns[0].timestamp.isoformat() if self.turns else None,
            "newest_turn": self.turns[-1].timestamp.isoformat() if self.turns else None
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Export memory to dictionary
        
        Returns:
            Dictionary representation
        """
        return {
            "max_turns": self.max_turns,
            "turns": [turn.to_dict() for turn in self.turns]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ShortTermMemory':
        """
        Load memory from dictionary
        
        Args:
            data: Dictionary representation
            
        Returns:
            ShortTermMemory instance
        """
        memory = cls(max_turns=data["max_turns"])
        
        for turn_data in data["turns"]:
            memory.add_turn(
                role=turn_data["role"],
                content=turn_data["content"],
                metadata=turn_data.get("metadata", {})
            )
        
        return memory
