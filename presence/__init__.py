"""
Presence Module for Abby Unleashed

Provides user tracking, identity awareness, presence detection,
and special handling for different users (like the boyfriend's chaos).
"""

from .user_tracker import UserTracker, UserSession, get_user_tracker
from .chaos_handler import ChaosDetector, BoyfriendHandler, get_chaos_detector, get_boyfriend_handler

__all__ = [
    'UserTracker', 
    'UserSession', 
    'get_user_tracker',
    'ChaosDetector',
    'BoyfriendHandler',
    'get_chaos_detector',
    'get_boyfriend_handler'
]
