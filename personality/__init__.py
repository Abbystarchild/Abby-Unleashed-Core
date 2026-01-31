"""
Personality package - Brain Clone and Engram Builder

This package provides tools for creating accurate digital personality clones:

1. BrainClone - Main personality manager that loads and applies configurations
2. EngramBuilder - Creates comprehensive personality profiles using:
   - Big Five (OCEAN) personality traits
   - HEXACO model extensions
   - Communication style analysis
   - Value hierarchies
   - Decision-making patterns
   - Linguistic pattern extraction from writing samples
"""
from personality.brain_clone import BrainClone
from personality.engram_builder import (
    EngramBuilder,
    Engram,
    OceanTraits,
    CommunicationStyle,
    ValueSystem,
    DecisionMakingStyle,
    KnowledgeBase,
    LinguisticPatterns,
    InteractiveEngramCreator,
    create_engram_interactive
)

__all__ = [
    'BrainClone',
    'EngramBuilder',
    'Engram',
    'OceanTraits',
    'CommunicationStyle',
    'ValueSystem',
    'DecisionMakingStyle',
    'KnowledgeBase',
    'LinguisticPatterns',
    'InteractiveEngramCreator',
    'create_engram_interactive'
]
