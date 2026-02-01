"""
User Presence & Identity Tracker for Abby Unleashed

Tracks who is connected, what device they're on, and provides
context-aware personality adjustments for each recognized user.
"""

import os
import yaml
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import hashlib
import json

logger = logging.getLogger(__name__)


@dataclass
class UserSession:
    """Represents an active user session"""
    session_id: str
    user_id: str
    display_name: str
    device_info: str
    connected_at: datetime
    last_activity: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    message_count: int = 0
    
    def is_active(self, timeout_hours: int = 24) -> bool:
        """Check if session is still active"""
        return datetime.now() - self.last_activity < timedelta(hours=timeout_hours)
    
    def touch(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()
        self.message_count += 1


class UserTracker:
    """
    Tracks connected users and provides identity-aware context for responses.
    
    Key responsibilities:
    1. Track who is currently connected
    2. Allow users to identify themselves
    3. Provide personality context for each user
    4. Generate appropriate greetings and response styles
    """
    
    def __init__(self, profiles_path: str = None):
        """
        Initialize the user tracker.
        
        Args:
            profiles_path: Path to user_profiles.yaml
        """
        if profiles_path is None:
            profiles_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "data", "user_profiles.yaml"
            )
        
        self.profiles_path = profiles_path
        self.profiles = self._load_profiles()
        
        # Active sessions: session_id -> UserSession
        self.sessions: Dict[str, UserSession] = {}
        
        # Session to user mapping persistence (simple JSON file)
        self.session_store_path = os.path.join(
            os.path.dirname(self.profiles_path),
            "active_sessions.json"
        )
        self._load_sessions()
        
        logger.info(f"UserTracker initialized with {len(self.profiles.get('users', {}))} user profiles")
    
    def _load_profiles(self) -> Dict[str, Any]:
        """Load user profiles from YAML"""
        try:
            with open(self.profiles_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"User profiles not found at {self.profiles_path}, using defaults")
            return self._get_default_profiles()
        except Exception as e:
            logger.error(f"Error loading user profiles: {e}")
            return self._get_default_profiles()
    
    def _get_default_profiles(self) -> Dict[str, Any]:
        """Return minimal default profiles"""
        return {
            "users": {
                "unknown": {
                    "id": "unknown",
                    "display_name": "Unknown User",
                    "relationship": "stranger",
                    "communication_style": {
                        "tone": "friendly",
                        "formality": "moderate"
                    },
                    "greetings": ["Hello! I'm Abby Unleashed. Who do I have the pleasure of speaking with?"]
                }
            },
            "session_settings": {
                "session_timeout_hours": 24,
                "default_user": "unknown"
            }
        }
    
    def _load_sessions(self):
        """Load persisted sessions"""
        try:
            if os.path.exists(self.session_store_path):
                with open(self.session_store_path, 'r') as f:
                    data = json.load(f)
                    for sid, sdata in data.items():
                        self.sessions[sid] = UserSession(
                            session_id=sid,
                            user_id=sdata['user_id'],
                            display_name=sdata['display_name'],
                            device_info=sdata.get('device_info', 'unknown'),
                            connected_at=datetime.fromisoformat(sdata['connected_at']),
                            last_activity=datetime.fromisoformat(sdata['last_activity']),
                            ip_address=sdata.get('ip_address'),
                            user_agent=sdata.get('user_agent'),
                            message_count=sdata.get('message_count', 0)
                        )
        except Exception as e:
            logger.warning(f"Could not load sessions: {e}")
    
    def _save_sessions(self):
        """Persist sessions to disk"""
        try:
            data = {}
            for sid, session in self.sessions.items():
                if session.is_active():
                    data[sid] = {
                        'user_id': session.user_id,
                        'display_name': session.display_name,
                        'device_info': session.device_info,
                        'connected_at': session.connected_at.isoformat(),
                        'last_activity': session.last_activity.isoformat(),
                        'ip_address': session.ip_address,
                        'user_agent': session.user_agent,
                        'message_count': session.message_count
                    }
            
            os.makedirs(os.path.dirname(self.session_store_path), exist_ok=True)
            with open(self.session_store_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save sessions: {e}")
    
    def generate_session_id(self, ip_address: str = None, user_agent: str = None) -> str:
        """Generate a unique session ID based on connection info"""
        unique_data = f"{ip_address or 'unknown'}-{user_agent or 'unknown'}-{datetime.now().isoformat()}"
        return hashlib.sha256(unique_data.encode()).hexdigest()[:16]
    
    def get_or_create_session(
        self,
        session_id: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> UserSession:
        """
        Get existing session or create a new one.
        
        Args:
            session_id: Optional existing session ID
            ip_address: Client IP address
            user_agent: Client user agent string
            
        Returns:
            UserSession object
        """
        # Try to find existing session
        if session_id and session_id in self.sessions:
            session = self.sessions[session_id]
            if session.is_active():
                session.touch()
                return session
        
        # Create new session
        new_session_id = session_id or self.generate_session_id(ip_address, user_agent)
        default_user = self.profiles.get('session_settings', {}).get('default_user', 'unknown')
        
        # Try to detect device type from user agent
        device_info = self._detect_device(user_agent)
        
        session = UserSession(
            session_id=new_session_id,
            user_id=default_user,
            display_name=self.profiles.get('users', {}).get(default_user, {}).get('display_name', 'Unknown'),
            device_info=device_info,
            connected_at=datetime.now(),
            last_activity=datetime.now(),
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.sessions[new_session_id] = session
        self._save_sessions()
        
        logger.info(f"New session created: {new_session_id} from {device_info}")
        return session
    
    def _detect_device(self, user_agent: str = None) -> str:
        """Detect device type from user agent"""
        if not user_agent:
            return "unknown device"
        
        ua_lower = user_agent.lower()
        
        if 'iphone' in ua_lower or 'ipad' in ua_lower:
            return "iOS device"
        elif 'android' in ua_lower:
            return "Android device"
        elif 'mobile' in ua_lower:
            return "mobile device"
        elif 'windows' in ua_lower:
            return "Windows PC"
        elif 'mac' in ua_lower:
            return "Mac"
        elif 'linux' in ua_lower:
            return "Linux machine"
        else:
            return "unknown device"
    
    def identify_user(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """
        Identify who is using a session.
        
        Args:
            session_id: The session to update
            user_id: The user ID (e.g., 'organic_abby', 'boyfriend')
            
        Returns:
            Dict with status and greeting
        """
        if session_id not in self.sessions:
            return {"success": False, "error": "Session not found"}
        
        user_profile = self.profiles.get('users', {}).get(user_id)
        if not user_profile:
            return {"success": False, "error": f"Unknown user: {user_id}"}
        
        session = self.sessions[session_id]
        old_user = session.user_id
        session.user_id = user_id
        session.display_name = user_profile.get('display_name', user_id)
        session.touch()
        
        self._save_sessions()
        
        # Generate a greeting
        greetings = user_profile.get('greetings', ["Hello!"])
        greeting = random.choice(greetings)
        
        logger.info(f"Session {session_id} identified as {user_id} (was {old_user})")
        
        return {
            "success": True,
            "user_id": user_id,
            "display_name": session.display_name,
            "greeting": greeting,
            "relationship": user_profile.get('relationship', 'unknown')
        }
    
    def get_user_context(self, session_id: str) -> Dict[str, Any]:
        """
        Get the full context for a user session.
        
        Returns everything needed to customize Abby's responses.
        """
        if session_id not in self.sessions:
            # Return unknown user context
            return self._get_unknown_context()
        
        session = self.sessions[session_id]
        session.touch()
        
        user_profile = self.profiles.get('users', {}).get(session.user_id, {})
        
        return {
            "user_id": session.user_id,
            "display_name": session.display_name,
            "relationship": user_profile.get('relationship', 'unknown'),
            "device": session.device_info,
            "connected_at": session.connected_at.isoformat(),
            "message_count": session.message_count,
            "communication_style": user_profile.get('communication_style', {}),
            "special_behaviors": user_profile.get('special_behaviors', []),
            "personality_notes": user_profile.get('personality_notes', []),
            "is_known_user": session.user_id != 'unknown'
        }
    
    def _get_unknown_context(self) -> Dict[str, Any]:
        """Get context for unknown users"""
        unknown_profile = self.profiles.get('users', {}).get('unknown', {})
        return {
            "user_id": "unknown",
            "display_name": "Unknown User",
            "relationship": "stranger",
            "device": "unknown",
            "communication_style": unknown_profile.get('communication_style', {}),
            "special_behaviors": [],
            "personality_notes": [],
            "is_known_user": False
        }
    
    def get_system_prompt_addition(self, session_id: str) -> str:
        """
        Generate additional system prompt text based on who is connected.
        KEEP THIS SHORT - it gets added to every prompt!
        """
        ctx = self.get_user_context(session_id)
        
        # Keep it minimal!
        parts = []
        
        # Just identify who we're talking to
        if ctx.get('is_known_user'):
            parts.append(f"Talking to: {ctx['display_name']} ({ctx['relationship']})")
            
            # Only add tone hint
            style = ctx.get('communication_style', {})
            if style.get('tone'):
                parts.append(f"Tone: {style['tone']}")
        else:
            parts.append("Talking to: someone new")
        
        return ' | '.join(parts) if parts else ""
    
    def get_chaos_response(self) -> str:
        """Get a pre-made response for handling chaotic/wild statements from the boyfriend"""
        user_profile = self.profiles.get('users', {}).get('boyfriend', {})
        chaos_responses = user_profile.get('chaos_responses', [
            "That's certainly... something!",
            "I'm going to need more context on that one.",
            "My creator warned me about you... 😄"
        ])
        return random.choice(chaos_responses)
    
    def get_greeting(self, session_id: str) -> str:
        """Get an appropriate greeting for the current user"""
        if session_id not in self.sessions:
            unknown = self.profiles.get('users', {}).get('unknown', {})
            return random.choice(unknown.get('greetings', ["Hello!"]))
        
        session = self.sessions[session_id]
        user_profile = self.profiles.get('users', {}).get(session.user_id, {})
        greetings = user_profile.get('greetings', ["Hello!"])
        return random.choice(greetings)
    
    def list_active_sessions(self) -> List[Dict[str, Any]]:
        """List all active sessions"""
        active = []
        timeout = self.profiles.get('session_settings', {}).get('session_timeout_hours', 24)
        
        for session in self.sessions.values():
            if session.is_active(timeout):
                active.append({
                    "session_id": session.session_id,
                    "user_id": session.user_id,
                    "display_name": session.display_name,
                    "device": session.device_info,
                    "connected_at": session.connected_at.isoformat(),
                    "last_activity": session.last_activity.isoformat(),
                    "message_count": session.message_count
                })
        
        return active
    
    def list_available_users(self) -> List[Dict[str, str]]:
        """List users that can be selected"""
        users = []
        for user_id, profile in self.profiles.get('users', {}).items():
            if user_id != 'unknown':  # Don't list 'unknown' as a selectable option
                users.append({
                    "id": user_id,
                    "display_name": profile.get('display_name', user_id),
                    "relationship": profile.get('relationship', 'unknown')
                })
        return users
    
    def is_boyfriend(self, session_id: str) -> bool:
        """Check if current session is the boyfriend (for chaos handling)"""
        if session_id not in self.sessions:
            return False
        return self.sessions[session_id].user_id == 'boyfriend'
    
    def is_creator(self, session_id: str) -> bool:
        """Check if current session is Organic Abby (the creator)"""
        if session_id not in self.sessions:
            return False
        return self.sessions[session_id].user_id == 'organic_abby'


# Singleton instance
_tracker_instance: Optional[UserTracker] = None


def get_user_tracker() -> UserTracker:
    """Get or create the singleton UserTracker instance"""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = UserTracker()
    return _tracker_instance
