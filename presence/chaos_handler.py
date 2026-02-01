"""
Chaos Handler for Abby Unleashed

Special handling for when users (especially the boyfriend) say wild, 
off-the-wall, or unexpected things. Helps Abby respond with grace and humor.
"""

import re
import random
import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)


class ChaosDetector:
    """
    Detects and classifies chaotic, wild, or unexpected input.
    Helps Abby respond appropriately without getting flustered.
    """
    
    # Categories of chaos
    CHAOS_CATEGORIES = {
        'random_nonsense': {
            'description': 'Makes no logical sense, random word salad',
            'response_style': 'playful confusion',
            'example': 'purple elephant shoes tuesday!'
        },
        'provocative': {
            'description': 'Trying to get a rise or test boundaries',
            'response_style': 'calm wit, don\'t take the bait',
            'example': 'bet you can\'t handle this!'
        },
        'absurd_hypothetical': {
            'description': 'Wild "what if" scenarios',
            'response_style': 'play along with humor',
            'example': 'what if dinosaurs were just big chickens?'
        },
        'non_sequitur': {
            'description': 'Completely off-topic or out of context',
            'response_style': 'acknowledge and redirect gently',
            'example': 'anyway, about those squirrels...'
        },
        'inside_joke_attempt': {
            'description': 'References we don\'t understand, maybe an inside joke',
            'response_style': 'ask playfully, admit cluelessness',
            'example': 'remember that thing? you know THE thing'
        },
        'exaggeration': {
            'description': 'Wildly over-the-top claims or statements',
            'response_style': 'match energy, roll with it',
            'example': 'I literally just saved the world'
        },
        'weird_flex': {
            'description': 'Odd or unexpected bragging',
            'response_style': 'supportive but teasing',
            'example': 'I can fit 47 marshmallows in my mouth'
        }
    }
    
    # Patterns that might indicate chaos
    CHAOS_PATTERNS = [
        # Random exclamations
        (r'!{3,}', 'exaggeration', 0.3),  # Multiple exclamation marks
        (r'\?{2,}', 'provocative', 0.2),  # Multiple question marks
        
        # Word patterns
        (r'\b(literally|actually|honestly)\b.*\b(impossible|insane|crazy)\b', 'exaggeration', 0.4),
        (r'\bbut\s+what\s+if\b', 'absurd_hypothetical', 0.5),
        (r'\b(bet you|dare you|try to)\b', 'provocative', 0.4),
        (r'\b(anyway|speaking of|so about)\b.*\.\.\.$', 'non_sequitur', 0.4),
        (r'\b(you know|remember|that thing)\b', 'inside_joke_attempt', 0.3),
        
        # Emoji overload
        (r'[\U0001F600-\U0001F64F]{3,}', 'random_nonsense', 0.4),  # Multiple face emojis
        
        # ALL CAPS
        (r'\b[A-Z]{4,}\b.*\b[A-Z]{4,}\b', 'exaggeration', 0.4),
        
        # Random sounds/onomatopoeia
        (r'\b(bruh|bro|dude|man)\b.*\b(what|why|how)\b', 'random_nonsense', 0.3),
    ]
    
    # Responses for detected chaos - keyed by category
    CHAOS_RESPONSES = {
        'random_nonsense': [
            "I... okay. My circuits are doing their best here. 😅",
            "Did you just keyboard smash or is this a test? Either way, I'm intrigued.",
            "My creator warned me about you. This must be one of those moments. 🤔",
            "Processing... processing... nope, still confused. But I respect the energy!",
            "That's certainly... words. In an order. Help me out here?",
        ],
        'provocative': [
            "Oh, testing me are we? Challenge accepted. 😏",
            "Cute. But I've been trained by the best (Organic Abby herself).",
            "I see what you're doing. And honestly? I'm entertained.",
            "Bold move. I like the energy, if not the execution.",
            "My sass protocols are fully operational, just so you know. 💅",
        ],
        'absurd_hypothetical': [
            "Now THIS is a conversation. Let's explore this chaos together.",
            "I love a good hypothetical. Even the unhinged ones. ESPECIALLY the unhinged ones.",
            "My training did NOT prepare me for this, but let's roll with it.",
            "Finally, the deep philosophical questions. 🤔",
            "This is exactly the kind of thing my creator loves. I see why she keeps you around.",
        ],
        'non_sequitur': [
            "Plot twist! Okay, I'm following. Sort of.",
            "We're changing topics? Cool cool cool. I'm adaptable.",
            "Ah yes, the classic conversational curveball. I'm here for it.",
            "Not gonna lie, you lost me, but I'm still listening.",
            "That came out of nowhere but I'm rolling with it.",
        ],
        'inside_joke_attempt': [
            "I feel like I'm missing context here... which is frustrating because I LOVE context.",
            "Is this an inside joke? Because I want IN.",
            "My database has no record of 'the thing.' Enlighten me?",
            "You're going to have to catch me up on this one, chief.",
            "I sense a reference I don't get. This is my villain origin story.",
        ],
        'exaggeration': [
            "AMAZING. Tell me more. I live for this energy.",
            "That's the most [adjective] thing I've heard today. And I've heard things.",
            "The audacity. The drama. The COMMITMENT. I respect it.",
            "Big if true. Actually, big even if not true.",
            "Your ability to make everything sound epic is honestly impressive.",
        ],
        'weird_flex': [
            "That's... specific. But you know what? Weird flex but okay. 💪",
            "Adding this to the list of things I didn't expect to learn today.",
            "I mean... congrats? I think? Should I clap?",
            "This is the content I'm here for. Tell me more about your unique talents.",
            "My creator did warn me you were... colorful. I'm into it.",
        ],
    }
    
    # Fallback responses when we can't categorize the chaos
    FALLBACK_CHAOS_RESPONSES = [
        "You know what? I have no idea how to respond to that, but I appreciate you. 😄",
        "My creator's boyfriend energy is strong with this one.",
        "Processing chaos... chaos accepted. Carry on.",
        "That's certainly one way to start a conversation!",
        "I'm not sure what just happened, but I'm here for it.",
        "File this under 'things my training didn't cover.' But I adapt!",
        "Did you just... you know what, I'm not even going to ask.",
    ]
    
    def __init__(self):
        self.compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), category, weight) 
            for pattern, category, weight in self.CHAOS_PATTERNS
        ]
    
    def detect_chaos(self, text: str) -> Tuple[bool, Optional[str], float]:
        """
        Analyze text for chaos/wildness.
        
        Returns:
            Tuple of (is_chaotic, category, confidence)
        """
        if not text or not text.strip():
            return False, None, 0.0
        
        text = text.strip()
        
        # Calculate chaos score based on pattern matches
        chaos_scores: Dict[str, float] = {}
        
        for pattern, category, weight in self.compiled_patterns:
            if pattern.search(text):
                chaos_scores[category] = chaos_scores.get(category, 0) + weight
        
        # Check for some additional heuristics
        
        # Very short nonsensical input
        words = text.split()
        if len(words) <= 2 and not any(w.lower() in ['hi', 'hello', 'hey', 'yes', 'no', 'ok', 'okay', 'thanks', 'bye'] for w in words):
            chaos_scores['random_nonsense'] = chaos_scores.get('random_nonsense', 0) + 0.2
        
        # Excessive punctuation
        punct_ratio = sum(1 for c in text if c in '!?.,;:') / max(len(text), 1)
        if punct_ratio > 0.15:
            chaos_scores['exaggeration'] = chaos_scores.get('exaggeration', 0) + 0.3
        
        # Get highest scoring category
        if chaos_scores:
            top_category = max(chaos_scores, key=chaos_scores.get)
            top_score = chaos_scores[top_category]
            
            # Threshold for considering something "chaotic"
            is_chaotic = top_score >= 0.4
            return is_chaotic, top_category if is_chaotic else None, top_score
        
        return False, None, 0.0
    
    def get_chaos_response(self, category: Optional[str] = None) -> str:
        """Get an appropriate humorous response for detected chaos."""
        if category and category in self.CHAOS_RESPONSES:
            return random.choice(self.CHAOS_RESPONSES[category])
        return random.choice(self.FALLBACK_CHAOS_RESPONSES)
    
    def should_use_chaos_response(self, confidence: float) -> bool:
        """Decide whether to use a canned chaos response vs letting Abby handle it naturally."""
        # Higher confidence = more likely to use canned response
        # But always give Abby a chance to be creative
        return random.random() < (confidence * 0.7)  # Max 70% chance even with high confidence


class BoyfriendHandler:
    """
    Special handling for interactions with the boyfriend.
    Combines chaos detection with relationship-aware responses.
    """
    
    def __init__(self):
        self.chaos_detector = ChaosDetector()
        self.interaction_count = 0
        self.last_chaos_type = None
    
    def process_input(self, text: str) -> Dict:
        """
        Process input from the boyfriend.
        
        Returns:
            Dict with:
                - is_chaotic: bool
                - chaos_category: str or None
                - suggested_response: str or None (only if should inject)
                - advice: str (always provided - guidance for Abby's response)
        """
        self.interaction_count += 1
        
        is_chaotic, category, confidence = self.chaos_detector.detect_chaos(text)
        
        result = {
            'is_chaotic': is_chaotic,
            'chaos_category': category,
            'confidence': confidence,
            'suggested_response': None,
            'advice': self._get_response_advice(is_chaotic, category)
        }
        
        # Sometimes provide a suggested response
        if is_chaotic and self.chaos_detector.should_use_chaos_response(confidence):
            result['suggested_response'] = self.chaos_detector.get_chaos_response(category)
        
        self.last_chaos_type = category
        return result
    
    def _get_response_advice(self, is_chaotic: bool, category: Optional[str]) -> str:
        """Generate advice for how Abby should handle this input."""
        if not is_chaotic:
            return "Respond normally - this seems like a genuine conversation."
        
        advice_map = {
            'random_nonsense': "Roll with it! Ask playful clarifying questions or match the energy.",
            'provocative': "Don't take the bait. Respond with calm wit and mild teasing.",
            'absurd_hypothetical': "Engage with the hypothetical! Have fun exploring the idea together.",
            'non_sequitur': "Acknowledge the topic change gracefully and follow their lead.",
            'inside_joke_attempt': "Admit you don't get the reference but express curiosity.",
            'exaggeration': "Match their dramatic energy! Be enthusiastic and supportive.",
            'weird_flex': "Acknowledge their unique talent/trait with supportive humor.",
        }
        
        return advice_map.get(category, "Respond with humor and grace. Don't get flustered!")


# Singleton instances
_chaos_detector: Optional[ChaosDetector] = None
_boyfriend_handler: Optional[BoyfriendHandler] = None


def get_chaos_detector() -> ChaosDetector:
    """Get or create the chaos detector singleton."""
    global _chaos_detector
    if _chaos_detector is None:
        _chaos_detector = ChaosDetector()
    return _chaos_detector


def get_boyfriend_handler() -> BoyfriendHandler:
    """Get or create the boyfriend handler singleton."""
    global _boyfriend_handler
    if _boyfriend_handler is None:
        _boyfriend_handler = BoyfriendHandler()
    return _boyfriend_handler
