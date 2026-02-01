"""
Abby Unleashed - Enhanced Server with Parallel Processing & Smart Output

This module provides:
1. Constant running daemon server
2. Hot reload capability (update code without restart)
3. Parallel thinking and speaking (shared context)
4. Smart output routing (display vs voice)
5. Background learning/refresh
6. WebSocket for real-time updates
7. Resource monitoring

Architecture:
┌─────────────────────────────────────────────────────────────────┐
│                    Abby Enhanced Server                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ HTTP API    │  │ WebSocket   │  │ Background Workers      │  │
│  │ /api/*      │  │ /ws         │  │ - Learning refresh      │  │
│  │             │  │             │  │ - Knowledge updates     │  │
│  └──────┬──────┘  └──────┬──────┘  │ - Hot reload watcher    │  │
│         │                │         └───────────┬─────────────┘  │
│         └────────┬───────┘                     │                │
│                  │                             │                │
│         ┌────────▼───────────────────┬─────────▼────┐           │
│         │      Shared Context Manager              │           │
│         │  - Conversation history                   │           │
│         │  - Thinking state                         │           │
│         │  - Display queue                          │           │
│         │  - Voice queue                            │           │
│         └────────┬───────────────────┬─────────────┘           │
│                  │                   │                          │
│         ┌────────▼─────┐    ┌────────▼─────┐                    │
│         │ Display      │    │ Voice        │                    │
│         │ Streamer     │    │ Synthesizer  │                    │
│         │ (All text)   │    │ (Summary)    │                    │
│         └──────────────┘    └──────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
"""

import asyncio
import logging
import os
import sys
import json
import time
import threading
import queue
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from enum import Enum
from dotenv import load_dotenv

# Load environment
load_dotenv()

logger = logging.getLogger(__name__)


class OutputMode(Enum):
    """How to output information"""
    DISPLAY_ONLY = "display"      # Show on screen, don't speak
    VOICE_ONLY = "voice"          # Speak, don't display much
    BOTH = "both"                 # Display and speak
    VOICE_SUMMARY = "summary"     # Display full, speak summary


@dataclass
class ThinkingState:
    """Current state of Abby's thinking process"""
    task_id: str
    task: str
    status: str = "thinking"  # thinking, speaking, displaying, complete
    full_response: str = ""
    voice_summary: str = ""
    display_chunks: List[str] = field(default_factory=list)
    progress: float = 0.0
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SharedContext:
    """
    Shared context between parallel processing streams.
    
    This ensures display and voice outputs are coherent.
    """
    conversation_id: str
    history: List[Dict[str, str]] = field(default_factory=list)
    current_thinking: Optional[ThinkingState] = None
    variables: Dict[str, Any] = field(default_factory=dict)
    last_activity: str = field(default_factory=lambda: datetime.now().isoformat())


class OutputRouter:
    """
    Routes output between display and voice intelligently.
    
    Saves ElevenLabs API usage by:
    - Sending full text to display
    - Sending condensed summaries to voice
    - Allowing user to choose voice mode
    """
    
    def __init__(self, voice_mode: OutputMode = OutputMode.VOICE_SUMMARY):
        self.voice_mode = voice_mode
        self.display_queue = queue.Queue()
        self.voice_queue = queue.Queue()
        self._summary_ratio = 0.3  # Voice summary = 30% of full text
        
    def set_mode(self, mode: OutputMode):
        """Change output mode"""
        self.voice_mode = mode
        logger.info(f"Output mode set to: {mode.value}")
    
    def route(self, text: str, task_state: ThinkingState) -> Dict[str, str]:
        """
        Route text to appropriate outputs.
        
        Returns:
            Dict with 'display' and 'voice' keys
        """
        result = {
            "display": text,
            "voice": None
        }
        
        if self.voice_mode == OutputMode.DISPLAY_ONLY:
            result["voice"] = None
            
        elif self.voice_mode == OutputMode.VOICE_ONLY:
            result["display"] = f"[Speaking...]\n{text[:100]}..."
            result["voice"] = text
            
        elif self.voice_mode == OutputMode.BOTH:
            result["voice"] = text
            
        elif self.voice_mode == OutputMode.VOICE_SUMMARY:
            # Generate a summary for voice
            result["voice"] = self._generate_summary(text)
        
        # Queue for async processing
        self.display_queue.put(result["display"])
        if result["voice"]:
            self.voice_queue.put(result["voice"])
        
        return result
    
    def _generate_summary(self, text: str) -> str:
        """
        Generate a concise voice summary.
        
        Rules:
        - First sentence is key
        - Keep action items
        - Skip code blocks (display only)
        - Keep conclusions
        """
        if len(text) < 200:
            return text
        
        lines = text.split('\n')
        summary_parts = []
        
        # Get first meaningful line
        for line in lines[:3]:
            line = line.strip()
            if line and not line.startswith('```') and not line.startswith('#'):
                summary_parts.append(line)
                break
        
        # Find key points (lines with important markers)
        key_markers = ['done', 'created', 'complete', 'error', 'important', 'note:', 'summary:', '✅', '❌', '⚠️']
        for line in lines:
            line_lower = line.lower().strip()
            if any(marker in line_lower for marker in key_markers):
                if line not in summary_parts:
                    summary_parts.append(line.strip())
        
        # Get last line if it's a conclusion
        if lines and lines[-1].strip() and not lines[-1].strip().startswith('```'):
            last = lines[-1].strip()
            if last not in summary_parts:
                summary_parts.append(last)
        
        summary = ' '.join(summary_parts)
        
        # Truncate if still too long
        max_voice_chars = int(len(text) * self._summary_ratio)
        if len(summary) > max_voice_chars:
            summary = summary[:max_voice_chars] + "... more details on screen."
        
        return summary


class HotReloader:
    """
    Watches for file changes and triggers reload.
    
    Allows updating Abby's code without restart.
    """
    
    def __init__(self, watch_paths: List[str], callback: Callable):
        self.watch_paths = [Path(p) for p in watch_paths]
        self.callback = callback
        self._file_mtimes: Dict[str, float] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
    def start(self):
        """Start watching for changes"""
        self._running = True
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()
        logger.info(f"Hot reloader watching: {self.watch_paths}")
    
    def stop(self):
        """Stop watching"""
        self._running = False
    
    def _watch_loop(self):
        """Main watch loop"""
        # Initial scan
        self._scan_files()
        
        while self._running:
            time.sleep(2)  # Check every 2 seconds
            if self._check_changes():
                logger.info("File changes detected - triggering reload")
                try:
                    self.callback()
                except Exception as e:
                    logger.error(f"Reload error: {e}")
    
    def _scan_files(self):
        """Scan all watched files"""
        self._file_mtimes.clear()
        for base_path in self.watch_paths:
            if base_path.is_dir():
                for py_file in base_path.rglob("*.py"):
                    self._file_mtimes[str(py_file)] = py_file.stat().st_mtime
            elif base_path.exists():
                self._file_mtimes[str(base_path)] = base_path.stat().st_mtime
    
    def _check_changes(self) -> bool:
        """Check for file changes"""
        changed = False
        for filepath, old_mtime in list(self._file_mtimes.items()):
            path = Path(filepath)
            if path.exists():
                new_mtime = path.stat().st_mtime
                if new_mtime > old_mtime:
                    logger.info(f"Changed: {filepath}")
                    self._file_mtimes[filepath] = new_mtime
                    changed = True
        return changed


class BackgroundLearner:
    """
    Background worker that refreshes knowledge.
    
    Periodically:
    - Updates knowledge bases
    - Refreshes agent expertise
    - Checks for new information
    """
    
    def __init__(self, refresh_interval: int = 3600):  # 1 hour default
        self.refresh_interval = refresh_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.last_refresh: Optional[datetime] = None
        self._tasks: List[Callable] = []
    
    def add_task(self, task: Callable):
        """Add a learning task to run periodically"""
        self._tasks.append(task)
    
    def start(self):
        """Start background learning"""
        self._running = True
        self._thread = threading.Thread(target=self._learning_loop, daemon=True)
        self._thread.start()
        logger.info(f"Background learner started (interval: {self.refresh_interval}s)")
    
    def stop(self):
        """Stop background learning"""
        self._running = False
    
    def trigger_refresh(self):
        """Manually trigger a refresh"""
        self._run_tasks()
    
    def _learning_loop(self):
        """Main learning loop"""
        while self._running:
            time.sleep(self.refresh_interval)
            self._run_tasks()
    
    def _run_tasks(self):
        """Run all learning tasks"""
        self.last_refresh = datetime.now()
        logger.info("Running background learning tasks...")
        
        for task in self._tasks:
            try:
                task()
            except Exception as e:
                logger.error(f"Learning task error: {e}")
        
        logger.info("Background learning complete")


class ParallelProcessor:
    """
    Processes thinking and output in parallel with shared context.
    
    Ensures:
    - Display updates stream in real-time
    - Voice synthesis happens for summaries
    - Context stays synchronized
    """
    
    def __init__(self, output_router: OutputRouter):
        self.output_router = output_router
        self.contexts: Dict[str, SharedContext] = {}
        self._active_tasks: Dict[str, ThinkingState] = {}
        
    def create_context(self, conversation_id: str) -> SharedContext:
        """Create or get a shared context"""
        if conversation_id not in self.contexts:
            self.contexts[conversation_id] = SharedContext(conversation_id=conversation_id)
        return self.contexts[conversation_id]
    
    def start_thinking(self, conversation_id: str, task_id: str, task: str) -> ThinkingState:
        """Start a new thinking process"""
        context = self.create_context(conversation_id)
        
        state = ThinkingState(
            task_id=task_id,
            task=task,
            status="thinking"
        )
        
        context.current_thinking = state
        self._active_tasks[task_id] = state
        
        return state
    
    def update_thinking(
        self,
        task_id: str,
        chunk: str = None,
        progress: float = None,
        status: str = None
    ):
        """Update thinking state with new content"""
        if task_id not in self._active_tasks:
            return
        
        state = self._active_tasks[task_id]
        
        if chunk:
            state.full_response += chunk
            state.display_chunks.append(chunk)
        
        if progress is not None:
            state.progress = progress
        
        if status:
            state.status = status
    
    def complete_thinking(self, task_id: str, final_response: str = None) -> Dict[str, str]:
        """
        Complete thinking and route to outputs.
        
        Returns routed output for display and voice.
        """
        if task_id not in self._active_tasks:
            return {"display": "", "voice": None}
        
        state = self._active_tasks[task_id]
        
        if final_response:
            state.full_response = final_response
        
        state.status = "complete"
        
        # Route to appropriate outputs
        routed = self.output_router.route(state.full_response, state)
        
        # Clean up
        del self._active_tasks[task_id]
        
        return routed
    
    def get_state(self, task_id: str) -> Optional[ThinkingState]:
        """Get current thinking state"""
        return self._active_tasks.get(task_id)


class EnhancedAbbyServer:
    """
    Enhanced server with all the features:
    - Hot reload
    - Background learning
    - Parallel processing
    - Smart output routing
    - WebSocket streaming
    """
    
    def __init__(self, workspace_path: str = None):
        self.workspace_path = workspace_path or os.getcwd()
        
        # Core components
        self.output_router = OutputRouter(OutputMode.VOICE_SUMMARY)
        self.parallel_processor = ParallelProcessor(self.output_router)
        self.hot_reloader = HotReloader(
            watch_paths=[
                os.path.join(self.workspace_path, "agents"),
                os.path.join(self.workspace_path, "speech_interface"),
                os.path.join(self.workspace_path, "cli.py"),
            ],
            callback=self._on_reload
        )
        self.background_learner = BackgroundLearner(refresh_interval=3600)
        
        # Abby instance (will be loaded)
        self._abby = None
        self._abby_lock = threading.Lock()
        
        # WebSocket clients
        self._ws_clients: List[Any] = []
        
        # Server state
        self.started_at: Optional[datetime] = None
        self.request_count = 0
        
    def _on_reload(self):
        """Handle hot reload"""
        logger.info("Hot reloading Abby modules...")
        
        # Reload key modules
        modules_to_reload = [
            'agents.base_agent',
            'agents.agent_factory',
            'agents.action_executor',
            'agents.task_planner',
            'agents.task_runner',
            'cli',
        ]
        
        for mod_name in modules_to_reload:
            if mod_name in sys.modules:
                try:
                    import importlib
                    importlib.reload(sys.modules[mod_name])
                    logger.info(f"  Reloaded: {mod_name}")
                except Exception as e:
                    logger.error(f"  Failed to reload {mod_name}: {e}")
        
        # Recreate Abby instance with new code
        with self._abby_lock:
            self._abby = None
            self._get_abby()
        
        # Notify WebSocket clients
        self._broadcast({
            "type": "reload",
            "message": "Abby has been updated!"
        })
    
    def _get_abby(self):
        """Get or create Abby instance (thread-safe)"""
        if self._abby is None:
            with self._abby_lock:
                if self._abby is None:
                    from cli import AbbyUnleashed
                    self._abby = AbbyUnleashed()
                    logger.info("Abby instance created")
        return self._abby
    
    def _broadcast(self, message: Dict[str, Any]):
        """Broadcast to all WebSocket clients"""
        # Implementation depends on WebSocket library used
        pass
    
    def start(self):
        """Start the enhanced server"""
        self.started_at = datetime.now()
        
        # Start background services
        self.hot_reloader.start()
        self.background_learner.start()
        
        # Add learning tasks
        self.background_learner.add_task(self._refresh_knowledge)
        
        logger.info("Enhanced Abby Server started")
    
    def stop(self):
        """Stop the server"""
        self.hot_reloader.stop()
        self.background_learner.stop()
        logger.info("Enhanced Abby Server stopped")
    
    def _refresh_knowledge(self):
        """Refresh knowledge bases"""
        abby = self._get_abby()
        # Trigger knowledge refresh on agents
        logger.info("Refreshing knowledge bases...")
    
    async def process_task(
        self,
        task: str,
        conversation_id: str,
        output_mode: OutputMode = None,
        user_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Process a task with parallel output.
        
        Args:
            task: User's task/question
            conversation_id: ID for conversation context
            output_mode: Override output mode for this task
            user_context: Additional context (user name, visual info, etc.)
        
        Returns:
            Dict with display and voice outputs
        """
        import uuid
        task_id = str(uuid.uuid4())[:8]
        
        # Set output mode if specified
        if output_mode:
            self.output_router.set_mode(output_mode)
        
        # Start thinking
        state = self.parallel_processor.start_thinking(
            conversation_id, task_id, task
        )
        
        # Broadcast thinking started
        self._broadcast({
            "type": "thinking_start",
            "task_id": task_id,
            "task": task
        })
        
        # Execute task
        abby = self._get_abby()
        
        # Get context
        context = self.parallel_processor.create_context(conversation_id)
        
        # Add user context if provided
        execution_context = {"conversation_id": conversation_id}
        if user_context:
            execution_context["user_context"] = user_context
        
        # Execute with streaming updates
        result = abby.execute_task(task, context=execution_context)
        
        # Complete thinking and route output
        routed = self.parallel_processor.complete_thinking(
            task_id,
            result.get("output", "")
        )
        
        # Broadcast completion
        self._broadcast({
            "type": "thinking_complete",
            "task_id": task_id,
            "display": routed["display"],
            "has_voice": routed["voice"] is not None
        })
        
        self.request_count += 1
        
        return {
            "task_id": task_id,
            "display": routed["display"],
            "voice": routed["voice"],
            "voice_mode": self.output_router.voice_mode.value,
            "result": result
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get server status"""
        return {
            "status": "running",
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "uptime_seconds": (datetime.now() - self.started_at).total_seconds() if self.started_at else 0,
            "request_count": self.request_count,
            "active_tasks": len(self.parallel_processor._active_tasks),
            "output_mode": self.output_router.voice_mode.value,
            "last_knowledge_refresh": self.background_learner.last_refresh.isoformat() if self.background_learner.last_refresh else None,
            "hot_reload_enabled": self.hot_reloader._running
        }
    
    def set_output_mode(self, mode: str) -> bool:
        """Set the output mode"""
        try:
            output_mode = OutputMode(mode)
            self.output_router.set_mode(output_mode)
            return True
        except ValueError:
            return False


# Singleton instance
_enhanced_server: Optional[EnhancedAbbyServer] = None


def get_enhanced_server(workspace_path: str = None) -> EnhancedAbbyServer:
    """Get or create the enhanced server"""
    global _enhanced_server
    if _enhanced_server is None:
        _enhanced_server = EnhancedAbbyServer(workspace_path)
    return _enhanced_server


# ==================== TEST ====================

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    server = EnhancedAbbyServer()
    
    # Test output router
    router = OutputRouter(OutputMode.VOICE_SUMMARY)
    
    test_text = """
# Analysis Complete

I've analyzed your codebase and found the following:

```python
def example():
    pass
```

## Key Findings:
✅ Code structure is clean
✅ Tests are passing
⚠️ Consider adding more documentation

The overall code quality is good. I recommend focusing on documentation improvements.
"""
    
    state = ThinkingState(task_id="test", task="analyze code")
    result = router.route(test_text, state)
    
    print("=" * 50)
    print("DISPLAY OUTPUT:")
    print(result["display"])
    print("=" * 50)
    print("VOICE OUTPUT (Summary):")
    print(result["voice"])
    print("=" * 50)
    
    # Character savings
    display_len = len(result["display"])
    voice_len = len(result["voice"]) if result["voice"] else 0
    savings = ((display_len - voice_len) / display_len) * 100
    print(f"\nElevenLabs savings: {savings:.1f}% fewer characters")
