"""
Presence Module for Abby Unleashed

Provides user tracking, identity awareness, presence detection,
and special handling for different users (like the boyfriend's chaos).
"""

from .user_tracker import UserTracker, UserSession, get_user_tracker
from .chaos_handler import ChaosDetector, BoyfriendHandler, get_chaos_detector, get_boyfriend_handler

# Optional imports - these require additional dependencies
try:
    from .face_recognition import FaceRecognizer, get_face_recognizer
    _FACE_AVAILABLE = True
except ImportError:
    FaceRecognizer = None
    get_face_recognizer = None
    _FACE_AVAILABLE = False

try:
    from .visual_awareness import VisualAwareness, get_visual_awareness
    _VISUAL_AVAILABLE = True
except ImportError:
    VisualAwareness = None
    get_visual_awareness = None
    _VISUAL_AVAILABLE = False

__all__ = [
    'UserTracker', 
    'UserSession', 
    'get_user_tracker',
    'ChaosDetector',
    'BoyfriendHandler',
    'get_chaos_detector',
    'get_boyfriend_handler',
    'FaceRecognizer',
    'get_face_recognizer',
    'VisualAwareness',
    'get_visual_awareness',
    '_FACE_AVAILABLE',
    '_VISUAL_AVAILABLE'
]
