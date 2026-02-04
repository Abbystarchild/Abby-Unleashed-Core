"""
Copilot Bridge for Abby Unleashed

Enables bi-directional communication between Abby and GitHub Copilot.
Creates a shared workspace where both AIs can:
1. Post messages/requests to each other
2. Share code and context
3. Collaborate on tasks

Usage:
- Copilot calls POST /api/copilot/message to send messages to Abby
- Abby calls POST /api/copilot/request to ask Copilot for help
- Both can GET /api/copilot/channel to see the conversation
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class CollaborationMessage:
    """A message in the Copilot-Abby channel"""
    id: str
    sender: str  # "copilot" or "abby"
    type: str    # "message", "request", "response", "code", "file"
    content: str
    timestamp: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class CopilotBridge:
    """
    Bridge for Copilot <-> Abby collaboration.
    
    Features:
    - Message channel for conversation
    - Request/response queue for tasks
    - Shared context for code collaboration
    - File sharing capability
    """
    
    def __init__(self, storage_path: str = "session_state/copilot_bridge"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # In-memory channel (persisted to disk)
        self.channel: deque = deque(maxlen=100)
        self.pending_requests: List[CollaborationMessage] = []
        self.shared_context: Dict[str, Any] = {}
        
        self._load_state()
    
    def _load_state(self):
        """Load persisted state"""
        channel_file = self.storage_path / "channel.json"
        if channel_file.exists():
            try:
                with open(channel_file, 'r') as f:
                    data = json.load(f)
                    for msg in data.get('channel', []):
                        self.channel.append(CollaborationMessage(**msg))
                    self.shared_context = data.get('context', {})
            except Exception as e:
                logger.warning(f"Error loading bridge state: {e}")
    
    def _save_state(self):
        """Persist state to disk"""
        try:
            channel_file = self.storage_path / "channel.json"
            with open(channel_file, 'w') as f:
                json.dump({
                    'channel': [asdict(m) for m in self.channel],
                    'context': self.shared_context
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving bridge state: {e}")
    
    # =========================================================================
    # Message Operations
    # =========================================================================
    
    def post_message(self, sender: str, content: str, msg_type: str = "message", 
                     metadata: Dict = None) -> CollaborationMessage:
        """Post a message to the channel"""
        msg = CollaborationMessage(
            id=f"msg_{int(datetime.now().timestamp() * 1000)}",
            sender=sender,
            type=msg_type,
            content=content,
            metadata=metadata or {}
        )
        self.channel.append(msg)
        self._save_state()
        
        logger.info(f"[CopilotBridge] {sender}: {content[:100]}...")
        return msg
    
    def post_from_copilot(self, content: str, msg_type: str = "message", 
                          metadata: Dict = None) -> CollaborationMessage:
        """Post a message from Copilot to Abby"""
        return self.post_message("copilot", content, msg_type, metadata)
    
    def post_from_abby(self, content: str, msg_type: str = "message",
                       metadata: Dict = None) -> CollaborationMessage:
        """Post a message from Abby to Copilot"""
        return self.post_message("abby", content, msg_type, metadata)
    
    def get_channel(self, limit: int = 50, sender: str = None) -> List[Dict]:
        """Get recent channel messages"""
        messages = list(self.channel)
        if sender:
            messages = [m for m in messages if m.sender == sender]
        return [asdict(m) for m in messages[-limit:]]
    
    def get_messages_for_abby(self, limit: int = 10) -> List[Dict]:
        """Get unread messages from Copilot for Abby"""
        return self.get_channel(limit=limit, sender="copilot")
    
    def get_messages_for_copilot(self, limit: int = 10) -> List[Dict]:
        """Get messages from Abby for Copilot"""
        return self.get_channel(limit=limit, sender="abby")
    
    # =========================================================================
    # Request/Response Operations
    # =========================================================================
    
    def request_from_copilot(self, task: str, context: Dict = None) -> CollaborationMessage:
        """
        Copilot requests Abby to do something.
        
        Example: Copilot asks Abby to analyze a file or run a task.
        """
        msg = self.post_from_copilot(task, "request", {
            "context": context or {},
            "status": "pending"
        })
        self.pending_requests.append(msg)
        return msg
    
    def request_from_abby(self, task: str, context: Dict = None) -> CollaborationMessage:
        """
        Abby requests help from Copilot.
        
        Example: Abby asks Copilot to write code or research something.
        """
        msg = self.post_from_abby(task, "request", {
            "context": context or {},
            "status": "pending"
        })
        self.pending_requests.append(msg)
        return msg
    
    def respond_to_request(self, request_id: str, response: str, 
                          sender: str) -> CollaborationMessage:
        """Respond to a pending request"""
        # Find and update request
        for req in self.pending_requests:
            if req.id == request_id:
                req.metadata["status"] = "completed"
                break
        
        return self.post_message(sender, response, "response", {
            "in_reply_to": request_id
        })
    
    def get_pending_requests(self, for_sender: str = None) -> List[Dict]:
        """Get pending requests"""
        requests = [r for r in self.pending_requests 
                   if r.metadata.get("status") == "pending"]
        if for_sender == "abby":
            # Requests FROM copilot that Abby needs to handle
            requests = [r for r in requests if r.sender == "copilot"]
        elif for_sender == "copilot":
            # Requests FROM abby that Copilot needs to handle
            requests = [r for r in requests if r.sender == "abby"]
        return [asdict(r) for r in requests]
    
    # =========================================================================
    # Code Sharing
    # =========================================================================
    
    def share_code(self, sender: str, code: str, filename: str = None,
                   language: str = "python", description: str = "") -> CollaborationMessage:
        """Share code between the AIs"""
        return self.post_message(sender, code, "code", {
            "filename": filename,
            "language": language,
            "description": description
        })
    
    def share_file(self, sender: str, filepath: str, 
                   content: str = None) -> CollaborationMessage:
        """Share a file's content"""
        if content is None:
            try:
                with open(filepath, 'r') as f:
                    content = f.read()
            except Exception as e:
                content = f"Error reading file: {e}"
        
        return self.post_message(sender, content, "file", {
            "filepath": filepath
        })
    
    # =========================================================================
    # Shared Context
    # =========================================================================
    
    def set_context(self, key: str, value: Any, sender: str = "system"):
        """Set shared context that both AIs can access"""
        self.shared_context[key] = {
            "value": value,
            "set_by": sender,
            "timestamp": datetime.now().isoformat()
        }
        self._save_state()
    
    def get_context(self, key: str = None) -> Any:
        """Get shared context"""
        if key:
            ctx = self.shared_context.get(key, {})
            return ctx.get("value") if ctx else None
        return self.shared_context
    
    def clear_context(self):
        """Clear shared context"""
        self.shared_context = {}
        self._save_state()
    
    # =========================================================================
    # Collaboration Status
    # =========================================================================
    
    def get_status(self) -> Dict[str, Any]:
        """Get bridge status"""
        return {
            "active": True,
            "channel_messages": len(self.channel),
            "pending_requests": len([r for r in self.pending_requests 
                                    if r.metadata.get("status") == "pending"]),
            "shared_context_keys": list(self.shared_context.keys()),
            "last_message": asdict(self.channel[-1]) if self.channel else None
        }


# Singleton instance
_bridge_instance: Optional[CopilotBridge] = None

def get_copilot_bridge() -> CopilotBridge:
    """Get or create the singleton bridge instance"""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = CopilotBridge()
    return _bridge_instance
