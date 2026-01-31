"""
Message Bus for inter-agent communication
"""
import logging
import queue
import threading
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of messages in the system"""
    TASK_ASSIGNED = "task_assigned"
    TASK_STARTED = "task_started"
    TASK_PROGRESS = "task_progress"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    AGENT_REQUEST = "agent_request"
    AGENT_RESPONSE = "agent_response"
    SYSTEM_EVENT = "system_event"


class Message:
    """Message object for inter-agent communication"""
    
    def __init__(
        self,
        msg_type: MessageType,
        sender: str,
        recipient: Optional[str] = None,
        content: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.msg_type = msg_type
        self.sender = sender
        self.recipient = recipient  # None for broadcast
        self.content = content or {}
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
        self.id = f"{sender}_{self.timestamp.timestamp()}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            "id": self.id,
            "type": self.msg_type.value,
            "sender": self.sender,
            "recipient": self.recipient,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


class MessageBus:
    """
    Message bus for inter-agent communication
    
    Provides pub/sub messaging between agents and system components
    """
    
    def __init__(self):
        """Initialize message bus"""
        self.message_queue = queue.Queue()
        self.subscribers: Dict[str, List[Callable]] = {}
        self.message_history: List[Message] = []
        self.running = False
        self.worker_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        logger.info("Message bus initialized")
    
    def start(self):
        """Start message bus processing"""
        if self.running:
            logger.warning("Message bus already running")
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._process_messages, daemon=True)
        self.worker_thread.start()
        logger.info("Message bus started")
    
    def stop(self):
        """Stop message bus processing"""
        if not self.running:
            return
        
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=2.0)
        logger.info("Message bus stopped")
    
    def publish(self, message: Message):
        """
        Publish a message to the bus
        
        Args:
            message: Message to publish
        """
        self.message_queue.put(message)
        
        # Store in history
        with self._lock:
            self.message_history.append(message)
            # Keep only last 1000 messages
            if len(self.message_history) > 1000:
                self.message_history = self.message_history[-1000:]
        
        logger.debug(f"Published message: {message.id} from {message.sender}")
    
    def subscribe(self, msg_type: MessageType, callback: Callable[[Message], None], subscriber_id: str):
        """
        Subscribe to messages of a specific type
        
        Args:
            msg_type: Type of messages to subscribe to
            callback: Function to call when message arrives
            subscriber_id: Unique subscriber identifier
        """
        key = f"{msg_type.value}:{subscriber_id}"
        
        with self._lock:
            if key not in self.subscribers:
                self.subscribers[key] = []
            self.subscribers[key].append(callback)
        
        logger.debug(f"Subscriber {subscriber_id} registered for {msg_type.value}")
    
    def unsubscribe(self, msg_type: MessageType, subscriber_id: str):
        """
        Unsubscribe from messages
        
        Args:
            msg_type: Type of messages to unsubscribe from
            subscriber_id: Subscriber identifier
        """
        key = f"{msg_type.value}:{subscriber_id}"
        
        with self._lock:
            if key in self.subscribers:
                del self.subscribers[key]
        
        logger.debug(f"Subscriber {subscriber_id} unsubscribed from {msg_type.value}")
    
    def _process_messages(self):
        """Process messages from queue (runs in worker thread)"""
        while self.running:
            try:
                # Get message with timeout
                message = self.message_queue.get(timeout=0.1)
                self._deliver_message(message)
                self.message_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing message: {e}")
    
    def _deliver_message(self, message: Message):
        """
        Deliver message to subscribers
        
        Args:
            message: Message to deliver
        """
        delivered = 0
        
        with self._lock:
            # Find all subscribers for this message type
            for key, callbacks in self.subscribers.items():
                msg_type_str, subscriber_id = key.split(":", 1)
                
                if msg_type_str != message.msg_type.value:
                    continue
                
                # Check if message is for this subscriber (or broadcast)
                if message.recipient and message.recipient != subscriber_id:
                    continue
                
                # Deliver to all callbacks
                for callback in callbacks:
                    try:
                        callback(message)
                        delivered += 1
                    except Exception as e:
                        logger.error(f"Error in subscriber callback {subscriber_id}: {e}")
        
        logger.debug(f"Delivered message {message.id} to {delivered} subscribers")
    
    def get_message_history(
        self,
        msg_type: Optional[MessageType] = None,
        sender: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get message history
        
        Args:
            msg_type: Filter by message type
            sender: Filter by sender
            limit: Maximum number of messages to return
            
        Returns:
            List of message dictionaries
        """
        with self._lock:
            messages = self.message_history.copy()
        
        # Filter
        if msg_type:
            messages = [m for m in messages if m.msg_type == msg_type]
        if sender:
            messages = [m for m in messages if m.sender == sender]
        
        # Limit
        messages = messages[-limit:]
        
        return [m.to_dict() for m in messages]
    
    def clear_history(self):
        """Clear message history"""
        with self._lock:
            self.message_history.clear()
        logger.info("Message history cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get message bus statistics
        
        Returns:
            Statistics dictionary
        """
        with self._lock:
            return {
                "running": self.running,
                "queue_size": self.message_queue.qsize(),
                "history_size": len(self.message_history),
                "subscribers": len(self.subscribers)
            }
