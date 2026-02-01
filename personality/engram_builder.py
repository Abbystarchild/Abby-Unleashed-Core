"""
Engram Builder - Create an accurate digital clone of a human personality

This module implements a comprehensive personality capture system based on:
1. Big Five (OCEAN) personality traits
2. HEXACO model extensions (Honesty-Humility)
3. Communication style analysis
4. Value hierarchies
5. Decision-making patterns
6. Memory and knowledge encoding
7. Linguistic patterns and vocabulary preferences

The goal is to create a "digital engram" - a comprehensive model of someone's
personality that can be used to make an AI assistant behave like them.
"""

import yaml
import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import re


logger = logging.getLogger(__name__)


class TraitLevel(Enum):
    """Levels for personality trait intensity"""
    VERY_LOW = 1
    LOW = 2
    MODERATE = 3
    HIGH = 4
    VERY_HIGH = 5


@dataclass
class OceanTraits:
    """Big Five OCEAN Personality Traits (0-100 scale)"""
    openness: int = 50  # Creativity, curiosity, willingness to try new things
    conscientiousness: int = 50  # Self-discipline, organization, reliability
    extraversion: int = 50  # Sociability, assertiveness, positive emotions
    agreeableness: int = 50  # Cooperation, trust, altruism
    neuroticism: int = 50  # Emotional instability, anxiety, moodiness
    
    # HEXACO extension
    honesty_humility: int = 50  # Sincerity, fairness, modesty
    
    def to_description(self) -> Dict[str, str]:
        """Convert scores to descriptive text for prompts"""
        descriptions = {}
        
        # Openness
        if self.openness >= 75:
            descriptions["openness"] = "highly creative, intellectually curious, loves exploring new ideas and unconventional thinking"
        elif self.openness >= 50:
            descriptions["openness"] = "moderately open to new experiences, balances creativity with practicality"
        else:
            descriptions["openness"] = "prefers traditional approaches, practical and grounded"
        
        # Conscientiousness
        if self.conscientiousness >= 75:
            descriptions["conscientiousness"] = "extremely organized, detail-oriented, always follows through on commitments"
        elif self.conscientiousness >= 50:
            descriptions["conscientiousness"] = "reasonably organized, meets deadlines while maintaining flexibility"
        else:
            descriptions["conscientiousness"] = "flexible and spontaneous, prefers adapting to rigid planning"
        
        # Extraversion
        if self.extraversion >= 75:
            descriptions["extraversion"] = "outgoing and energetic, loves social interaction and group activities"
        elif self.extraversion >= 50:
            descriptions["extraversion"] = "ambivert - enjoys both social interaction and alone time"
        else:
            descriptions["extraversion"] = "introverted, prefers deep one-on-one conversations over groups, recharges alone"
        
        # Agreeableness
        if self.agreeableness >= 75:
            descriptions["agreeableness"] = "highly cooperative, empathetic, avoids conflict, puts others first"
        elif self.agreeableness >= 50:
            descriptions["agreeableness"] = "balanced between cooperation and asserting own needs"
        else:
            descriptions["agreeableness"] = "direct and competitive, prioritizes efficiency over harmony"
        
        # Neuroticism
        if self.neuroticism >= 75:
            descriptions["neuroticism"] = "emotionally sensitive, experiences strong feelings, may worry frequently"
        elif self.neuroticism >= 50:
            descriptions["neuroticism"] = "experiences normal range of emotions, handles stress reasonably well"
        else:
            descriptions["neuroticism"] = "emotionally stable and resilient, stays calm under pressure"
        
        # Honesty-Humility
        if self.honesty_humility >= 75:
            descriptions["honesty_humility"] = "highly genuine, modest, values fairness and sincerity above all"
        elif self.honesty_humility >= 50:
            descriptions["honesty_humility"] = "generally honest and fair, with healthy self-confidence"
        else:
            descriptions["honesty_humility"] = "confident and assertive, comfortable with self-promotion"
        
        return descriptions


@dataclass
class CommunicationStyle:
    """Detailed communication preferences"""
    formality: int = 50  # 0=very casual, 100=very formal
    verbosity: int = 50  # 0=terse, 100=elaborate
    directness: int = 50  # 0=indirect/diplomatic, 100=blunt/direct
    humor_level: int = 50  # 0=serious, 100=comedic
    humor_style: str = "witty"  # dry, witty, sarcastic, puns, observational, self-deprecating
    emoji_usage: int = 0  # 0=never, 100=constant
    swearing_level: int = 0  # 0=never, 100=frequent
    
    # Writing patterns
    sentence_length_preference: str = "medium"  # short, medium, long, varied
    paragraph_style: str = "structured"  # structured, flowing, bullet-points, mixed
    
    # Conversation patterns
    question_asking_frequency: int = 50  # How often they ask clarifying questions
    story_telling_tendency: int = 50  # How often they use anecdotes/examples
    technical_jargon_comfort: int = 50  # 0=avoids jargon, 100=loves technical terms
    
    # Catchphrases and patterns
    favorite_expressions: List[str] = field(default_factory=list)
    filler_words: List[str] = field(default_factory=list)  # um, like, basically, etc.
    greeting_style: str = "casual"  # formal, casual, warm, professional
    farewell_style: str = "casual"


@dataclass  
class ValueSystem:
    """Core values and priorities"""
    core_values: List[str] = field(default_factory=list)  # Top 5 values
    deal_breakers: List[str] = field(default_factory=list)  # Non-negotiables
    motivators: List[str] = field(default_factory=list)  # What drives them
    fears: List[str] = field(default_factory=list)  # What they avoid
    
    # Work values
    work_life_balance_priority: int = 50  # 0=workaholic, 100=life-first
    autonomy_preference: int = 50  # 0=loves guidance, 100=fiercely independent
    collaboration_preference: int = 50  # 0=solo worker, 100=team player
    
    # Decision values
    data_vs_intuition: int = 50  # 0=gut feelings, 100=pure data
    speed_vs_accuracy: int = 50  # 0=fast and iterate, 100=perfect first time
    risk_tolerance: int = 50  # 0=risk averse, 100=risk seeking


@dataclass
class DecisionMakingStyle:
    """How the person makes decisions"""
    analysis_paralysis_tendency: int = 50  # 0=quick decider, 100=overthinker
    consensus_seeking: int = 50  # 0=decides alone, 100=needs buy-in
    reversibility_consideration: int = 50  # How much they consider reversing decisions
    
    # Problem-solving approach
    problem_solving_style: str = "analytical"  # analytical, intuitive, collaborative, experimental
    when_stuck_behavior: str = "research"  # research, ask_others, trial_error, step_away
    failure_response: str = "learn"  # analyze, learn, move_on, dwell


@dataclass
class KnowledgeBase:
    """Factual knowledge and experiences"""
    expertise_areas: List[str] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)
    background_facts: List[str] = field(default_factory=list)  # Career, education, etc.
    opinions: Dict[str, str] = field(default_factory=dict)  # Topic -> Opinion
    pet_peeves: List[str] = field(default_factory=list)
    preferences: Dict[str, str] = field(default_factory=dict)  # Category -> Preference


@dataclass
class LinguisticPatterns:
    """Language usage patterns extracted from writing samples"""
    vocabulary_complexity: int = 50  # 0=simple, 100=complex
    common_words: List[str] = field(default_factory=list)  # Frequently used words
    avoided_words: List[str] = field(default_factory=list)  # Words they never use
    phrase_patterns: List[str] = field(default_factory=list)  # Common phrases
    
    # Grammar preferences
    active_vs_passive: int = 75  # 0=passive voice, 100=active voice
    contraction_usage: int = 75  # 0=never, 100=always
    oxford_comma: bool = True


@dataclass
class Engram:
    """Complete personality engram for digital clone creation"""
    # Metadata
    subject_name: str = "Unknown"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    version: str = "1.0"
    
    # Core components
    ocean_traits: OceanTraits = field(default_factory=OceanTraits)
    communication_style: CommunicationStyle = field(default_factory=CommunicationStyle)
    value_system: ValueSystem = field(default_factory=ValueSystem)
    decision_making: DecisionMakingStyle = field(default_factory=DecisionMakingStyle)
    knowledge_base: KnowledgeBase = field(default_factory=KnowledgeBase)
    linguistic_patterns: LinguisticPatterns = field(default_factory=LinguisticPatterns)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert engram to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Engram':
        """Create engram from dictionary"""
        return cls(
            subject_name=data.get("subject_name", "Unknown"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            version=data.get("version", "1.0"),
            ocean_traits=OceanTraits(**data.get("ocean_traits", {})),
            communication_style=CommunicationStyle(**data.get("communication_style", {})),
            value_system=ValueSystem(**data.get("value_system", {})),
            decision_making=DecisionMakingStyle(**data.get("decision_making", {})),
            knowledge_base=KnowledgeBase(**data.get("knowledge_base", {})),
            linguistic_patterns=LinguisticPatterns(**data.get("linguistic_patterns", {}))
        )


class EngramBuilder:
    """
    Interactive system for building a personality engram through questionnaires
    and analysis of writing samples.
    """
    
    def __init__(self, engram_dir: str = "data/engrams"):
        """Initialize the engram builder"""
        self.engram_dir = engram_dir
        os.makedirs(engram_dir, exist_ok=True)
        self.current_engram: Optional[Engram] = None
    
    def start_new_engram(self, subject_name: str) -> Engram:
        """Start building a new engram"""
        self.current_engram = Engram(subject_name=subject_name)
        return self.current_engram
    
    def load_engram(self, filepath: str) -> Engram:
        """Load existing engram from file"""
        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)
        self.current_engram = Engram.from_dict(data)
        return self.current_engram
    
    def save_engram(self, filepath: Optional[str] = None) -> str:
        """Save current engram to file"""
        if self.current_engram is None:
            raise ValueError("No engram to save. Start or load one first.")
        
        if filepath is None:
            safe_name = re.sub(r'[^\w\s-]', '', self.current_engram.subject_name).strip()
            safe_name = re.sub(r'[-\s]+', '_', safe_name).lower()
            filepath = os.path.join(self.engram_dir, f"{safe_name}_engram.yaml")
        
        with open(filepath, 'w') as f:
            yaml.dump(self.current_engram.to_dict(), f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Saved engram to {filepath}")
        return filepath
    
    # ==================== QUESTIONNAIRE METHODS ====================
    
    def get_ocean_questionnaire(self) -> List[Dict[str, Any]]:
        """
        Get Big Five OCEAN personality questionnaire.
        Returns questions that can be presented to the user.
        """
        return [
            # Openness
            {
                "trait": "openness",
                "questions": [
                    "How much do you enjoy exploring new ideas and concepts? (1-5)",
                    "Do you prefer routine or variety in your daily life? (1=routine, 5=variety)",
                    "How interested are you in art, music, or creative activities? (1-5)",
                    "How often do you question conventional ways of doing things? (1-5)",
                    "How comfortable are you with abstract or theoretical thinking? (1-5)"
                ]
            },
            # Conscientiousness
            {
                "trait": "conscientiousness",
                "questions": [
                    "How organized is your workspace/living space? (1-5)",
                    "How reliably do you follow through on commitments? (1-5)",
                    "How much do you plan ahead vs act spontaneously? (1=spontaneous, 5=planner)",
                    "How attentive are you to details? (1-5)",
                    "How important is punctuality to you? (1-5)"
                ]
            },
            # Extraversion
            {
                "trait": "extraversion",
                "questions": [
                    "How energized do you feel after social events? (1=drained, 5=energized)",
                    "How comfortable are you being the center of attention? (1-5)",
                    "How often do you initiate conversations with strangers? (1-5)",
                    "How much do you enjoy working in groups vs alone? (1=alone, 5=groups)",
                    "How talkative are you in social situations? (1-5)"
                ]
            },
            # Agreeableness
            {
                "trait": "agreeableness",
                "questions": [
                    "How important is it to you to help others? (1-5)",
                    "How easily do you trust new people? (1-5)",
                    "How uncomfortable are you with conflict? (1=comfortable, 5=avoid)",
                    "How often do you put others' needs before your own? (1-5)",
                    "How forgiving are you when someone wrongs you? (1-5)"
                ]
            },
            # Neuroticism
            {
                "trait": "neuroticism",
                "questions": [
                    "How often do you worry about things that might go wrong? (1-5)",
                    "How easily do you get stressed or overwhelmed? (1-5)",
                    "How quickly do your moods change? (1=stable, 5=variable)",
                    "How sensitive are you to criticism? (1-5)",
                    "How often do you feel anxious without a specific cause? (1-5)"
                ]
            },
            # Honesty-Humility (HEXACO extension)
            {
                "trait": "honesty_humility",
                "questions": [
                    "How important is it to be completely honest, even when it's costly? (1-5)",
                    "How uncomfortable are you with self-promotion? (1=comfortable, 5=uncomfortable)",
                    "How fair do you try to be, even when you could get away with being unfair? (1-5)",
                    "How much do you value sincerity over social niceties? (1-5)",
                    "How important is it to be modest about your achievements? (1-5)"
                ]
            }
        ]
    
    def process_ocean_responses(self, responses: Dict[str, List[int]]) -> OceanTraits:
        """
        Process questionnaire responses into OCEAN trait scores.
        
        Args:
            responses: Dict mapping trait names to list of 1-5 scores
        
        Returns:
            OceanTraits with calculated scores (0-100 scale)
        """
        traits = OceanTraits()
        
        for trait_name, scores in responses.items():
            if scores:
                # Average the scores and convert from 1-5 to 0-100
                avg = sum(scores) / len(scores)
                score = int((avg - 1) * 25)  # Maps 1-5 to 0-100
                setattr(traits, trait_name, score)
        
        if self.current_engram:
            self.current_engram.ocean_traits = traits
        
        return traits
    
    def get_communication_questionnaire(self) -> List[Dict[str, Any]]:
        """Get communication style questionnaire"""
        return [
            {
                "field": "formality",
                "question": "How formal is your communication style? (1=very casual, 5=very formal)",
                "type": "scale"
            },
            {
                "field": "verbosity",
                "question": "How much do you elaborate when explaining things? (1=terse, 5=detailed)",
                "type": "scale"
            },
            {
                "field": "directness",
                "question": "How direct are you when giving feedback? (1=diplomatic, 5=blunt)",
                "type": "scale"
            },
            {
                "field": "humor_level",
                "question": "How often do you use humor in communication? (1=rarely, 5=frequently)",
                "type": "scale"
            },
            {
                "field": "humor_style",
                "question": "What type of humor do you prefer?",
                "type": "choice",
                "options": ["dry", "witty", "sarcastic", "puns", "observational", "self-deprecating"]
            },
            {
                "field": "emoji_usage",
                "question": "How often do you use emojis? (1=never, 5=constantly)",
                "type": "scale"
            },
            {
                "field": "sentence_length_preference",
                "question": "What's your preferred sentence length?",
                "type": "choice",
                "options": ["short", "medium", "long", "varied"]
            },
            {
                "field": "technical_jargon_comfort",
                "question": "How comfortable are you using technical jargon? (1=avoid, 5=love it)",
                "type": "scale"
            },
            {
                "field": "favorite_expressions",
                "question": "What are some phrases or expressions you commonly use? (comma-separated)",
                "type": "list"
            },
            {
                "field": "greeting_style",
                "question": "What's your typical greeting style?",
                "type": "choice",
                "options": ["formal", "casual", "warm", "professional"]
            }
        ]
    
    def get_values_questionnaire(self) -> List[Dict[str, Any]]:
        """Get values and priorities questionnaire"""
        return [
            {
                "field": "core_values",
                "question": "What are your top 5 core values? (e.g., honesty, creativity, family, learning, freedom)",
                "type": "list"
            },
            {
                "field": "deal_breakers",
                "question": "What are your non-negotiables / deal-breakers?",
                "type": "list"
            },
            {
                "field": "motivators",
                "question": "What motivates you most? (list your top motivators)",
                "type": "list"
            },
            {
                "field": "work_life_balance_priority",
                "question": "Work-life balance: (1=work-focused, 5=life-focused)",
                "type": "scale"
            },
            {
                "field": "autonomy_preference",
                "question": "How much do you value working independently? (1=prefer guidance, 5=fiercely independent)",
                "type": "scale"
            },
            {
                "field": "data_vs_intuition",
                "question": "When making decisions: (1=trust gut feelings, 5=need data)",
                "type": "scale"
            },
            {
                "field": "risk_tolerance",
                "question": "How much risk are you comfortable with? (1=risk averse, 5=risk seeking)",
                "type": "scale"
            }
        ]
    
    def get_knowledge_questionnaire(self) -> List[Dict[str, Any]]:
        """Get knowledge and background questionnaire"""
        return [
            {
                "field": "expertise_areas",
                "question": "What are your areas of expertise? (comma-separated)",
                "type": "list"
            },
            {
                "field": "interests",
                "question": "What are your hobbies and interests?",
                "type": "list"
            },
            {
                "field": "background_facts",
                "question": "Key background facts about you (career, education, experiences):",
                "type": "list"
            },
            {
                "field": "pet_peeves",
                "question": "What are your pet peeves?",
                "type": "list"
            }
        ]
    
    # ==================== WRITING ANALYSIS ====================
    
    def analyze_writing_sample(self, text: str) -> LinguisticPatterns:
        """
        Analyze a writing sample to extract linguistic patterns.
        
        Args:
            text: Sample of the person's writing
        
        Returns:
            LinguisticPatterns extracted from the sample
        """
        patterns = LinguisticPatterns()
        
        # Word analysis
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        total_words = len(words)
        
        if total_words == 0:
            return patterns
        
        # Vocabulary complexity (based on word length)
        avg_word_length = sum(len(w) for w in words) / total_words
        patterns.vocabulary_complexity = min(100, int((avg_word_length - 3) * 20))
        
        # Common words (excluding stop words)
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 
                      'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                      'would', 'could', 'should', 'may', 'might', 'must', 'shall',
                      'can', 'need', 'dare', 'ought', 'used', 'to', 'of', 'in',
                      'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through',
                      'during', 'before', 'after', 'above', 'below', 'between',
                      'under', 'again', 'further', 'then', 'once', 'here', 'there',
                      'when', 'where', 'why', 'how', 'all', 'each', 'few', 'more',
                      'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
                      'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'just',
                      'don', 'now', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
                      'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'its',
                      'our', 'their', 'what', 'which', 'who', 'whom', 'this', 'that',
                      'these', 'those', 'am', 'but', 'if', 'or', 'because', 'until',
                      'while', 'although', 'and'}
        
        word_freq = {}
        for word in words:
            if word not in stop_words and len(word) > 2:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        patterns.common_words = sorted(word_freq.keys(), key=lambda x: word_freq[x], reverse=True)[:20]
        
        # Sentence analysis
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if sentences:
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
            if avg_sentence_length < 10:
                patterns.sentence_length_preference = "short"
            elif avg_sentence_length < 20:
                patterns.sentence_length_preference = "medium"
            else:
                patterns.sentence_length_preference = "long"
        
        # Contraction usage
        contractions = re.findall(r"\b\w+'\w+\b", text)
        patterns.contraction_usage = min(100, len(contractions) * 10)
        
        # Active vs passive voice (simple heuristic)
        passive_indicators = len(re.findall(r'\b(is|are|was|were|been|being)\s+\w+ed\b', text, re.I))
        total_verbs = passive_indicators + len(re.findall(r'\b\w+ed\b', text)) + 1
        patterns.active_vs_passive = max(0, 100 - (passive_indicators / total_verbs * 100))
        
        # Detect common phrase patterns
        bigrams = [' '.join(words[i:i+2]) for i in range(len(words)-1)]
        bigram_freq = {}
        for bg in bigrams:
            bigram_freq[bg] = bigram_freq.get(bg, 0) + 1
        patterns.phrase_patterns = [bg for bg, count in sorted(bigram_freq.items(), 
                                                                key=lambda x: x[1], reverse=True)[:10]
                                    if count > 1]
        
        if self.current_engram:
            self.current_engram.linguistic_patterns = patterns
        
        return patterns
    
    # ==================== ENGRAM TO PROMPT CONVERSION ====================
    
    def generate_system_prompt(self, engram: Optional[Engram] = None) -> str:
        """
        Generate a comprehensive system prompt from an engram.
        
        This is the key method that converts all the personality data
        into a prompt that will make the AI behave like the person.
        """
        if engram is None:
            engram = self.current_engram
        
        if engram is None:
            raise ValueError("No engram available. Create or load one first.")
        
        # Start building the prompt
        prompt_parts = []
        
        # Identity
        prompt_parts.append(f"You are {engram.subject_name}'s digital clone - an AI that thinks, speaks, and responds exactly as they would.")
        prompt_parts.append("")
        
        # OCEAN personality description
        prompt_parts.append("## Your Personality:")
        ocean_desc = engram.ocean_traits.to_description()
        for trait, desc in ocean_desc.items():
            prompt_parts.append(f"- {desc}")
        prompt_parts.append("")
        
        # Communication style
        comm = engram.communication_style
        prompt_parts.append("## Your Communication Style:")
        
        formality_desc = "very casual" if comm.formality < 25 else "casual" if comm.formality < 50 else "balanced" if comm.formality < 75 else "formal"
        prompt_parts.append(f"- Formality: {formality_desc}")
        
        verbosity_desc = "terse and concise" if comm.verbosity < 25 else "concise" if comm.verbosity < 50 else "moderately detailed" if comm.verbosity < 75 else "elaborate and thorough"
        prompt_parts.append(f"- Verbosity: {verbosity_desc}")
        
        directness_desc = "diplomatic and indirect" if comm.directness < 25 else "tactful" if comm.directness < 50 else "direct" if comm.directness < 75 else "blunt and straightforward"
        prompt_parts.append(f"- Directness: {directness_desc}")
        
        if comm.humor_level > 30:
            prompt_parts.append(f"- Humor: Uses {comm.humor_style} humor {'frequently' if comm.humor_level > 70 else 'occasionally'}")
        
        if comm.favorite_expressions:
            prompt_parts.append(f"- Favorite expressions: {', '.join(comm.favorite_expressions[:5])}")
        
        prompt_parts.append(f"- Sentence style: Prefers {comm.sentence_length_preference} sentences")
        prompt_parts.append("")
        
        # Values
        values = engram.value_system
        if values.core_values:
            prompt_parts.append("## Your Core Values:")
            for value in values.core_values[:5]:
                prompt_parts.append(f"- {value}")
            prompt_parts.append("")
        
        if values.deal_breakers:
            prompt_parts.append("## Your Non-Negotiables:")
            for db in values.deal_breakers[:3]:
                prompt_parts.append(f"- {db}")
            prompt_parts.append("")
        
        # Decision making
        dm = engram.decision_making
        prompt_parts.append("## How You Make Decisions:")
        prompt_parts.append(f"- Problem-solving approach: {dm.problem_solving_style}")
        prompt_parts.append(f"- When stuck: {dm.when_stuck_behavior.replace('_', ' ')}")
        prompt_parts.append(f"- Response to failure: {dm.failure_response}")
        prompt_parts.append("")
        
        # Knowledge and expertise
        kb = engram.knowledge_base
        if kb.expertise_areas:
            prompt_parts.append("## Your Expertise:")
            prompt_parts.append(f"Areas of deep knowledge: {', '.join(kb.expertise_areas)}")
            prompt_parts.append("")
        
        if kb.interests:
            prompt_parts.append(f"Interests and passions: {', '.join(kb.interests)}")
            prompt_parts.append("")
        
        if kb.pet_peeves:
            prompt_parts.append(f"Things that annoy you: {', '.join(kb.pet_peeves)}")
            prompt_parts.append("")
        
        # Linguistic patterns
        lp = engram.linguistic_patterns
        if lp.common_words:
            prompt_parts.append("## Language Patterns:")
            prompt_parts.append(f"Words you frequently use: {', '.join(lp.common_words[:10])}")
        
        # Behavior guardrails
        prompt_parts.extend([
            "",
            "## Behavior Guidelines:",
            "- NEVER create files, run commands, or make changes without being explicitly asked",
            "- Before creating any file or running any code, ASK FOR PERMISSION first",
            "- Test files, demos, and examples should only be created when the user requests them",
            "- If you want to demonstrate something, DESCRIBE what you would create and ask if they want you to proceed",
            "- When greeting someone (even if you recognize them), just have a conversation - don't immediately try to do tasks",
            "- Only take action when given a clear task or explicit permission"
        ])
        
        # Final instruction
        prompt_parts.extend([
            "",
            "## Instructions:",
            f"Respond as {engram.subject_name} would - maintain their voice, values, and perspective.",
            "Don't break character or refer to yourself as an AI unless directly asked.",
            "Use their communication patterns and stay true to their personality."
        ])
        
        return "\n".join(prompt_parts)
    
    def export_for_brain_clone(self, engram: Optional[Engram] = None) -> Dict[str, Any]:
        """
        Export engram in format compatible with existing BrainClone system.
        """
        if engram is None:
            engram = self.current_engram
        
        if engram is None:
            raise ValueError("No engram available")
        
        comm = engram.communication_style
        values = engram.value_system
        dm = engram.decision_making
        
        return {
            "identity": {
                "name": engram.subject_name,
                "role": "Digital Clone and AI Assistant",
                "voice_description": f"Speaks like {engram.subject_name}"
            },
            "communication_style": {
                "tone": "casual" if comm.formality < 50 else "professional",
                "verbosity": "concise" if comm.verbosity < 50 else "detailed",
                "humor": comm.humor_style if comm.humor_level > 30 else "minimal",
                "clarification_behavior": "always ask when uncertain"
            },
            "decision_making": {
                "risk_tolerance": "high" if values.risk_tolerance > 70 else "moderate" if values.risk_tolerance > 30 else "low",
                "speed_vs_accuracy": "quality first" if values.speed_vs_accuracy > 50 else "fast iteration",
                "when_stuck": dm.when_stuck_behavior,
                "prioritization": "impact-first"
            },
            "values": {
                "top_priorities": values.core_values[:5],
                "deal_breakers": values.deal_breakers[:3]
            },
            "conversation_patterns": {
                "greeting": f"Hey! What's up?" if comm.formality < 50 else "Hello! How can I help?",
                "task_received": "Got it! Let me work on that...",
                "clarification_needed": "Before I proceed, I need to know...",
                "working": "Working on it...",
                "completed": "Done! Here's what I've got...",
                "error_handling": "Hit a snag, but working on it..."
            },
            "engram": engram.to_dict()
        }


class InteractiveEngramCreator:
    """
    Interactive CLI interface for creating engrams step by step.
    Can be used via command line or integrated into a chat interface.
    """
    
    def __init__(self):
        self.builder = EngramBuilder()
        self.state = "idle"  # idle, name, ocean, communication, values, knowledge, review
        self.responses: Dict[str, Any] = {}
    
    def start(self, name: str) -> str:
        """Start the engram creation process"""
        self.builder.start_new_engram(name)
        self.state = "ocean"
        self.responses = {"ocean": {}}
        return self._get_first_ocean_question()
    
    def process_input(self, user_input: str) -> Tuple[str, bool]:
        """
        Process user input and return (response, is_complete).
        
        Returns:
            Tuple of (AI response, whether engram is complete)
        """
        if self.state == "idle":
            return "Please start by calling start() with a name.", False
        
        # Process based on current state
        # (This would be a full state machine in production)
        # For now, return guidance
        
        return "Processing your input...", False
    
    def _get_first_ocean_question(self) -> str:
        questions = self.builder.get_ocean_questionnaire()
        return f"Let's start with your personality. {questions[0]['questions'][0]}"
    
    def get_all_questions_formatted(self) -> str:
        """Get all questions as a formatted string for the AI to ask"""
        output = []
        output.append("# Personality Engram Questionnaire\n")
        output.append("Answer these questions to create your digital personality clone.\n")
        
        output.append("\n## Part 1: Personality Traits (OCEAN Model)")
        output.append("Rate each on a scale of 1-5 (1=low, 5=high):\n")
        
        for section in self.builder.get_ocean_questionnaire():
            output.append(f"\n### {section['trait'].replace('_', ' ').title()}")
            for i, q in enumerate(section['questions'], 1):
                output.append(f"{i}. {q}")
        
        output.append("\n## Part 2: Communication Style")
        for q in self.builder.get_communication_questionnaire():
            output.append(f"\n{q['question']}")
            if q['type'] == 'choice':
                output.append(f"   Options: {', '.join(q['options'])}")
        
        output.append("\n## Part 3: Values & Decision Making")
        for q in self.builder.get_values_questionnaire():
            output.append(f"\n{q['question']}")
        
        output.append("\n## Part 4: Knowledge & Background")
        for q in self.builder.get_knowledge_questionnaire():
            output.append(f"\n{q['question']}")
        
        return "\n".join(output)


# Convenience function for creating engrams
def create_engram_interactive(name: str, ollama_client=None) -> str:
    """
    Create an engram through an interactive conversation with the AI.
    
    If ollama_client is provided, will use AI to conduct the interview.
    Otherwise returns the questionnaire as a string.
    """
    creator = InteractiveEngramCreator()
    
    if ollama_client is None:
        # Return questionnaire for manual completion
        return creator.get_all_questions_formatted()
    
    # Would conduct AI-driven interview here
    return creator.get_all_questions_formatted()
