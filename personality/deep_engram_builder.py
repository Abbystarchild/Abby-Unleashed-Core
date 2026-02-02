"""
Deep Engram Builder - 1000+ Questions for Life-Like Personality Clone

Comprehensive personality questionnaire based on:
- Big Five (OCEAN) personality traits
- HEXACO model (6 factors including Honesty-Humility)
- 16 Personalities / MBTI dimensions
- Moral Foundations Theory (Care, Fairness, Loyalty, Authority, Purity)
- Schwartz Values Theory (10 basic values)
- Cognitive styles and decision-making patterns
- Communication and linguistic preferences
- Work/career psychology
- Relationship attachment styles
- Emotional intelligence facets
- Life experiences and formative events
- Daily habits and routines
- Creative and aesthetic preferences
- Technology and tool preferences
- Stress responses and coping mechanisms
- Learning styles and knowledge domains

This creates an engram so detailed that an AI can authentically replicate
your thinking patterns, reactions, and communication style.
"""

import json
import os
import yaml
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict

# ==============================================================================
# QUESTION CATEGORIES - 25 MAJOR DOMAINS
# ==============================================================================

QUESTION_BANK = {
    # =========================================================================
    # SECTION 1: CORE PERSONALITY (Big Five OCEAN) - ~100 questions
    # =========================================================================
    "openness": {
        "name": "Openness to Experience",
        "description": "Creativity, curiosity, intellectual interests, aesthetic sensitivity",
        "questions": [
            # Intellectual Curiosity (20 questions)
            {"id": "O1", "text": "When you encounter a topic you know nothing about, do you feel excited to learn or prefer to stick with what you know?", "type": "choice", "options": ["Very excited to learn", "Mostly curious", "Depends on the topic", "Usually stick with what I know", "Strongly prefer familiar"]},
            {"id": "O2", "text": "How often do you read or watch content outside your usual interests just to learn something new?", "type": "frequency"},
            {"id": "O3", "text": "When someone disagrees with you, do you find it stimulating or annoying?", "type": "choice", "options": ["Stimulating", "Mostly stimulating", "Depends on the topic/person", "Mostly annoying", "Annoying"]},
            {"id": "O4", "text": "Do you enjoy philosophical discussions or find them pointless?", "type": "choice", "options": ["Love them", "Enjoy them", "Depends on the topic", "Find them tedious", "Pointless"]},
            {"id": "O5", "text": "How many books (or audiobooks/podcasts) do you consume per month on average?", "type": "number"},
            {"id": "O6", "text": "Do you prefer documentaries, fiction, or neither?", "type": "choice", "options": ["Documentaries", "Fiction", "Both equally", "Neither"]},
            {"id": "O7", "text": "When making a decision, do you research extensively or trust your gut?", "type": "choice", "options": ["Always research", "Mostly research", "Mix of both", "Mostly gut", "Always gut"]},
            {"id": "O8", "text": "How do you feel about abstract art?", "type": "text"},
            {"id": "O9", "text": "Do you enjoy learning languages, even if you'll never use them?", "type": "yesno"},
            {"id": "O10", "text": "When was the last time you changed your mind on something important?", "type": "text"},
            {"id": "O11", "text": "Do you enjoy exploring Wikipedia rabbit holes?", "type": "yesno"},
            {"id": "O12", "text": "How often do you question your own beliefs or assumptions?", "type": "frequency"},
            {"id": "O13", "text": "Do you enjoy thought experiments and hypotheticals?", "type": "yesno"},
            {"id": "O14", "text": "What's your relationship with science fiction?", "type": "text"},
            {"id": "O15", "text": "Do you find yourself drawn to mysteries and puzzles?", "type": "yesno"},
            
            # Aesthetic Sensitivity (15 questions)
            {"id": "O16", "text": "Does beautiful music ever give you chills or make you emotional?", "type": "yesno"},
            {"id": "O17", "text": "Do you notice small aesthetic details that others miss?", "type": "frequency"},
            {"id": "O18", "text": "How important is the visual design of your workspace?", "type": "choice", "options": ["Extremely important", "Very important", "Somewhat important", "Slightly important", "Not important at all"]},
            {"id": "O19", "text": "Do you have strong opinions about fonts?", "type": "yesno"},
            {"id": "O20", "text": "How does nature affect your mood?", "type": "text"},
            {"id": "O21", "text": "Do you appreciate poetry or find it pretentious?", "type": "choice", "options": ["Love it", "Appreciate some", "Neutral", "Find most pretentious", "Can't stand it"]},
            {"id": "O22", "text": "What role does color play in your life choices?", "type": "text"},
            {"id": "O23", "text": "Do you notice the quality of lighting in spaces?", "type": "yesno"},
            {"id": "O24", "text": "How do you feel about minimalist vs maximalist design?", "type": "text"},
            {"id": "O25", "text": "Does ugly UI actually bother you or do you not care?", "type": "choice", "options": ["Bothers me a lot", "Somewhat bothers me", "Mildly annoying", "Barely notice", "Don't care at all"]},
            
            # Creativity (15 questions)
            {"id": "O26", "text": "When solving problems, do you prefer proven methods or novel approaches?", "type": "choice", "options": ["Always proven", "Usually proven", "Mix of both", "Usually novel", "Always novel"]},
            {"id": "O27", "text": "Do you daydream often?", "type": "frequency"},
            {"id": "O28", "text": "Have you ever created something just for the joy of creating?", "type": "yesno"},
            {"id": "O29", "text": "How do you feel about brainstorming sessions?", "type": "text"},
            {"id": "O30", "text": "Do you see connections between unrelated things that others miss?", "type": "scale"},
            {"id": "O31", "text": "What's your relationship with improvisation?", "type": "text"},
            {"id": "O32", "text": "Do you enjoy coming up with alternative solutions even after finding one that works?", "type": "yesno"},
            {"id": "O33", "text": "How do you react when given creative freedom?", "type": "text"},
            {"id": "O34", "text": "Do you have hobbies that involve making things?", "type": "text"},
            {"id": "O35", "text": "What's the most creative thing you've done in the past year?", "type": "text"},
            
            # Adventurousness (10 questions)
            {"id": "O36", "text": "When traveling, do you plan everything or prefer spontaneity?", "type": "choice", "options": ["Plan everything", "Mostly planned", "Mix of both", "Mostly spontaneous", "Completely spontaneous"]},
            {"id": "O37", "text": "How do you feel about trying food you've never had?", "type": "choice", "options": ["Love it - always try new things", "Generally excited", "Cautiously curious", "Usually stick to familiar", "Prefer known favorites"]},
            {"id": "O38", "text": "Do you seek out new experiences or prefer familiar routines?", "type": "choice", "options": ["Always seeking new", "Mostly new", "Balance of both", "Mostly familiar", "Strongly prefer familiar"]},
            {"id": "O39", "text": "What's the most adventurous thing you've done?", "type": "text"},
            {"id": "O40", "text": "How do you feel about moving to a new city/country?", "type": "text"},
        ]
    },
    
    "conscientiousness": {
        "name": "Conscientiousness",
        "description": "Organization, diligence, perfectionism, self-discipline",
        "questions": [
            # Organization (15 questions)
            {"id": "C1", "text": "Is your desk/workspace currently organized or chaotic?", "type": "choice", "options": ["Pristine", "Mostly organized", "Controlled chaos", "Complete chaos"]},
            {"id": "C2", "text": "Do you use a task management system?", "type": "text"},
            {"id": "C3", "text": "How many browser tabs do you typically have open?", "type": "number"},
            {"id": "C4", "text": "Do you make your bed every morning?", "type": "yesno"},
            {"id": "C5", "text": "How do you organize your files on your computer?", "type": "text"},
            {"id": "C6", "text": "Do you label things?", "type": "yesno"},
            {"id": "C7", "text": "How do you feel about 'inbox zero'?", "type": "text"},
            {"id": "C8", "text": "Do you have a consistent place for your keys/wallet/phone?", "type": "yesno"},
            {"id": "C9", "text": "How often do you clean/declutter?", "type": "frequency"},
            {"id": "C10", "text": "Do you categorize and tag your digital content?", "type": "yesno"},
            {"id": "C11", "text": "How do you handle paperwork?", "type": "text"},
            {"id": "C12", "text": "Do you use calendars for personal life, not just work?", "type": "yesno"},
            {"id": "C13", "text": "How do you organize your thoughts when planning something?", "type": "text"},
            {"id": "C14", "text": "Do you sort your apps/programs on your devices?", "type": "yesno"},
            {"id": "C15", "text": "Does physical mess affect your mental state?", "type": "scale"},
            
            # Diligence (15 questions)
            {"id": "C16", "text": "How often do you work past the point where you 'should' stop?", "type": "frequency"},
            {"id": "C17", "text": "Do you finish projects or move on when interest fades?", "type": "choice", "options": ["Always finish", "Usually finish", "Depends on project", "Often move on", "Always move on"]},
            {"id": "C18", "text": "How do you handle tedious but necessary tasks?", "type": "text"},
            {"id": "C19", "text": "What's your longest single work session?", "type": "text"},
            {"id": "C20", "text": "Do you ever half-ass things?", "type": "scale"},
            {"id": "C21", "text": "How do you feel about cutting corners?", "type": "text"},
            {"id": "C22", "text": "When you commit to something, do you follow through?", "type": "scale"},
            {"id": "C23", "text": "How do you handle obstacles in your work?", "type": "text"},
            {"id": "C24", "text": "Do you push through when you don't feel like working?", "type": "scale"},
            {"id": "C25", "text": "What motivates you to work hard?", "type": "text"},
            
            # Perfectionism (10 questions)
            {"id": "C26", "text": "Do small imperfections bother you?", "type": "scale"},
            {"id": "C27", "text": "Would you rather ship something 80% good now or 100% good later?", "type": "choice", "options": ["80% now", "100% later", "Depends on context"]},
            {"id": "C28", "text": "Do you revise your work multiple times?", "type": "frequency"},
            {"id": "C29", "text": "How do you feel when you make a mistake?", "type": "text"},
            {"id": "C30", "text": "Does perfectionism help or hurt you overall?", "type": "text"},
            
            # Self-discipline (10 questions)
            {"id": "C31", "text": "Can you resist temptation easily?", "type": "scale"},
            {"id": "C32", "text": "Do you procrastinate?", "type": "scale"},
            {"id": "C33", "text": "How do you handle delayed gratification?", "type": "text"},
            {"id": "C34", "text": "Do you have good habits that you maintain?", "type": "text"},
            {"id": "C35", "text": "How easily can you focus when you need to?", "type": "scale"},
        ]
    },
    
    "extraversion": {
        "name": "Extraversion",
        "description": "Social energy, assertiveness, positive emotions, excitement-seeking",
        "questions": [
            # Social Energy (15 questions)
            {"id": "E1", "text": "After a long week, do you recharge alone or with people?", "type": "choice", "options": ["Definitely alone", "Mostly alone", "Mix of both", "Mostly with people", "Definitely with people"]},
            {"id": "E2", "text": "How do you feel about large parties?", "type": "choice", "options": ["Love them", "Enjoy them", "Neutral/depends", "Prefer to avoid", "Strongly dislike"]},
            {"id": "E3", "text": "Do you initiate conversations with strangers?", "type": "frequency"},
            {"id": "E4", "text": "How long can you spend in social situations before feeling drained?", "type": "text"},
            {"id": "E5", "text": "Do you enjoy being the center of attention?", "type": "scale"},
            {"id": "E6", "text": "How do you feel about networking events?", "type": "text"},
            {"id": "E7", "text": "Do you have a large or small social circle?", "type": "text"},
            {"id": "E8", "text": "How often do you reach out to friends/family unprompted?", "type": "frequency"},
            {"id": "E9", "text": "Do you prefer deep 1-on-1 conversations or group hangouts?", "type": "choice", "options": ["Deep 1-on-1", "Small groups", "Large groups", "All equally"]},
            {"id": "E10", "text": "How do you feel about small talk?", "type": "text"},
            {"id": "E11", "text": "Do you feel energized or exhausted after social events?", "type": "choice", "options": ["Very energized", "Somewhat energized", "Depends on the event", "Somewhat exhausted", "Very exhausted"]},
            {"id": "E12", "text": "How quickly do you warm up to new people?", "type": "scale"},
            {"id": "E13", "text": "Do you like working alone or in teams?", "type": "choice", "options": ["Strongly prefer alone", "Mostly alone", "Both equally", "Mostly teams", "Strongly prefer teams"]},
            {"id": "E14", "text": "How often do you feel lonely?", "type": "frequency"},
            {"id": "E15", "text": "Would you rather text or call?", "type": "choice", "options": ["Always text", "Mostly text", "Depends", "Mostly call", "Always call"]},
            
            # Assertiveness (12 questions)
            {"id": "E16", "text": "Do you speak up in meetings?", "type": "scale"},
            {"id": "E17", "text": "How comfortable are you giving presentations?", "type": "scale"},
            {"id": "E18", "text": "Do you take charge in group situations?", "type": "scale"},
            {"id": "E19", "text": "How do you handle disagreements?", "type": "text"},
            {"id": "E20", "text": "Can you say 'no' easily?", "type": "scale"},
            {"id": "E21", "text": "Do you express your opinions freely?", "type": "scale"},
            {"id": "E22", "text": "How do you react when someone interrupts you?", "type": "text"},
            {"id": "E23", "text": "Do you advocate for yourself effectively?", "type": "scale"},
            {"id": "E24", "text": "How do you handle confrontation?", "type": "text"},
            {"id": "E25", "text": "Are you comfortable giving negative feedback?", "type": "scale"},
            
            # Positive Emotions (8 questions)
            {"id": "E26", "text": "How often do you experience genuine joy?", "type": "frequency"},
            {"id": "E27", "text": "Are you generally optimistic or pessimistic?", "type": "choice", "options": ["Very optimistic", "Somewhat optimistic", "Realistic/neutral", "Somewhat pessimistic", "Very pessimistic"]},
            {"id": "E28", "text": "Do you laugh easily?", "type": "yesno"},
            {"id": "E29", "text": "How do you express enthusiasm?", "type": "text"},
            {"id": "E30", "text": "What's your baseline mood like?", "type": "text"},
            
            # Excitement-Seeking (5 questions)
            {"id": "E31", "text": "Do you get bored easily?", "type": "scale"},
            {"id": "E32", "text": "Do you seek thrills and adrenaline?", "type": "scale"},
            {"id": "E33", "text": "How do you feel about routine?", "type": "text"},
        ]
    },
    
    "agreeableness": {
        "name": "Agreeableness",
        "description": "Compassion, politeness, trust, cooperation",
        "questions": [
            # Compassion (12 questions)
            {"id": "A1", "text": "Do you feel others' emotions strongly (empathy)?", "type": "scale"},
            {"id": "A2", "text": "How do you react when someone is upset?", "type": "text"},
            {"id": "A3", "text": "Do you give to charity or volunteer?", "type": "frequency"},
            {"id": "A4", "text": "Does seeing others in pain affect you physically?", "type": "yesno"},
            {"id": "A5", "text": "How do you feel about helping strangers?", "type": "text"},
            {"id": "A6", "text": "Do you remember to check in on people?", "type": "frequency"},
            {"id": "A7", "text": "How do you handle seeing injustice?", "type": "text"},
            {"id": "A8", "text": "Do you put others' needs before your own?", "type": "scale"},
            {"id": "A9", "text": "How do you feel about animals?", "type": "text"},
            {"id": "A10", "text": "Do you cry at movies/shows?", "type": "frequency"},
            
            # Politeness (10 questions)
            {"id": "A11", "text": "How important are manners to you?", "type": "scale"},
            {"id": "A12", "text": "Do you avoid conflict?", "type": "scale"},
            {"id": "A13", "text": "How do you deliver criticism?", "type": "text"},
            {"id": "A14", "text": "Do you say please and thank you habitually?", "type": "yesno"},
            {"id": "A15", "text": "How do you handle rude people?", "type": "text"},
            
            # Trust (10 questions)
            {"id": "A16", "text": "Do you trust people by default or do they have to earn it?", "type": "choice", "options": ["Trust by default", "Lean toward trust", "Depends on context", "Must earn it", "Very guarded"]},
            {"id": "A17", "text": "How often have people betrayed your trust?", "type": "frequency"},
            {"id": "A18", "text": "Do you assume good intentions in others?", "type": "scale"},
            {"id": "A19", "text": "How guarded are you with new people?", "type": "scale"},
            {"id": "A20", "text": "Do you give people second chances?", "type": "scale"},
            
            # Cooperation (8 questions)
            {"id": "A21", "text": "Do you prefer competition or collaboration?", "type": "choice", "options": ["Strong competition", "Lean competitive", "Both equally", "Lean collaborative", "Strong collaboration"]},
            {"id": "A22", "text": "How do you handle team decisions you disagree with?", "type": "text"},
            {"id": "A23", "text": "Are you a good compromise negotiator?", "type": "scale"},
            {"id": "A24", "text": "How important is harmony in your relationships?", "type": "scale"},
            {"id": "A25", "text": "Do you accommodate others' preferences easily?", "type": "scale"},
        ]
    },
    
    "neuroticism": {
        "name": "Neuroticism / Emotional Stability",
        "description": "Anxiety, emotional volatility, stress response, self-consciousness",
        "questions": [
            # Anxiety (12 questions)
            {"id": "N1", "text": "How often do you worry about things?", "type": "frequency"},
            {"id": "N2", "text": "Do you experience anxiety?", "type": "scale"},
            {"id": "N3", "text": "What triggers your anxiety?", "type": "text"},
            {"id": "N4", "text": "Do you catastrophize (expect the worst)?", "type": "scale"},
            {"id": "N5", "text": "How does your body respond to stress?", "type": "text"},
            {"id": "N6", "text": "Do you ruminate on past events?", "type": "frequency"},
            {"id": "N7", "text": "How do you handle uncertainty?", "type": "text"},
            {"id": "N8", "text": "Do you have trouble sleeping due to worry?", "type": "frequency"},
            {"id": "N9", "text": "Are you a chronic overthinker?", "type": "scale"},
            {"id": "N10", "text": "How do you calm yourself down when anxious?", "type": "text"},
            
            # Emotional Volatility (10 questions)
            {"id": "N11", "text": "Do your moods swing significantly?", "type": "scale"},
            {"id": "N12", "text": "How quickly do your emotions change?", "type": "scale"},
            {"id": "N13", "text": "What triggers strong emotional reactions in you?", "type": "text"},
            {"id": "N14", "text": "Do you feel your emotions deeply?", "type": "scale"},
            {"id": "N15", "text": "How long do negative emotions last for you?", "type": "text"},
            
            # Stress Response (10 questions)
            {"id": "N16", "text": "How do you handle pressure?", "type": "text"},
            {"id": "N17", "text": "Do deadlines help or paralyze you?", "type": "choice", "options": ["Very helpful", "Somewhat helpful", "Depends", "Somewhat paralyzing", "Very paralyzing"]},
            {"id": "N18", "text": "What's your stress threshold?", "type": "text"},
            {"id": "N19", "text": "How do you decompress after stress?", "type": "text"},
            {"id": "N20", "text": "Have you experienced burnout?", "type": "text"},
            
            # Self-consciousness (8 questions)
            {"id": "N21", "text": "Do you worry what others think of you?", "type": "scale"},
            {"id": "N22", "text": "How do you handle embarrassment?", "type": "text"},
            {"id": "N23", "text": "Do you replay awkward moments in your head?", "type": "frequency"},
            {"id": "N24", "text": "How sensitive are you to criticism?", "type": "scale"},
            {"id": "N25", "text": "Do you compare yourself to others?", "type": "frequency"},
        ]
    },
    
    # =========================================================================
    # SECTION 2: HEXACO EXTENSION - Honesty-Humility (~40 questions)
    # =========================================================================
    "honesty_humility": {
        "name": "Honesty-Humility",
        "description": "Sincerity, fairness, greed avoidance, modesty",
        "questions": [
            # Sincerity (10 questions)
            {"id": "HH1", "text": "Do you flatter people to get what you want?", "type": "scale"},
            {"id": "HH2", "text": "How honest are you in social situations?", "type": "scale"},
            {"id": "HH3", "text": "Do you ever pretend to like someone you don't?", "type": "frequency"},
            {"id": "HH4", "text": "How comfortable are you with white lies?", "type": "text"},
            {"id": "HH5", "text": "Do you say what you mean?", "type": "scale"},
            
            # Fairness (10 questions)
            {"id": "HH6", "text": "Would you cheat if you knew you wouldn't get caught?", "type": "scale"},
            {"id": "HH7", "text": "How important is playing by the rules?", "type": "scale"},
            {"id": "HH8", "text": "Have you ever taken advantage of someone?", "type": "text"},
            {"id": "HH9", "text": "Do you pay your fair share?", "type": "scale"},
            {"id": "HH10", "text": "How do you handle finding money on the ground?", "type": "text"},
            
            # Greed Avoidance (10 questions)
            {"id": "HH11", "text": "How important is wealth to you?", "type": "scale"},
            {"id": "HH12", "text": "Do you desire expensive things?", "type": "scale"},
            {"id": "HH13", "text": "How do you feel about luxury items?", "type": "text"},
            {"id": "HH14", "text": "Is money a primary motivator for you?", "type": "scale"},
            {"id": "HH15", "text": "How do you feel about your current financial situation?", "type": "text"},
            
            # Modesty (10 questions)
            {"id": "HH16", "text": "Do you like to show off your accomplishments?", "type": "scale"},
            {"id": "HH17", "text": "How important is status to you?", "type": "scale"},
            {"id": "HH18", "text": "Do you feel entitled to special treatment?", "type": "scale"},
            {"id": "HH19", "text": "How do you handle praise?", "type": "text"},
            {"id": "HH20", "text": "Do you compare your achievements to others?", "type": "frequency"},
        ]
    },
    
    # =========================================================================
    # SECTION 3: VALUES AND MORALS (~100 questions)
    # =========================================================================
    "moral_foundations": {
        "name": "Moral Foundations",
        "description": "Care, Fairness, Loyalty, Authority, Purity, Liberty",
        "questions": [
            # Care/Harm (15 questions)
            {"id": "MF1", "text": "How much does it bother you when someone is being cruel?", "type": "scale"},
            {"id": "MF2", "text": "Is preventing harm more important than other moral considerations?", "type": "scale"},
            {"id": "MF3", "text": "Do you donate to help those in need?", "type": "frequency"},
            {"id": "MF4", "text": "How do you feel about violence in media?", "type": "text"},
            {"id": "MF5", "text": "Would you sacrifice something important to help a stranger?", "type": "text"},
            
            # Fairness/Cheating (15 questions)
            {"id": "MF6", "text": "How important is it that people get what they deserve?", "type": "scale"},
            {"id": "MF7", "text": "Do you believe in equality of outcome or opportunity?", "type": "text"},
            {"id": "MF8", "text": "How do you feel about freeloaders?", "type": "text"},
            {"id": "MF9", "text": "Is it okay to bend rules for a good cause?", "type": "scale"},
            {"id": "MF10", "text": "How do you define fairness?", "type": "text"},
            
            # Loyalty/Betrayal (15 questions)
            {"id": "MF11", "text": "How important is loyalty to your group/family/friends?", "type": "scale"},
            {"id": "MF12", "text": "Would you report a friend who did something wrong?", "type": "text"},
            {"id": "MF13", "text": "How do you feel about people who abandon their group?", "type": "text"},
            {"id": "MF14", "text": "Is loyalty ever more important than truth?", "type": "scale"},
            {"id": "MF15", "text": "How do you define being a good team player?", "type": "text"},
            
            # Authority/Subversion (15 questions)
            {"id": "MF16", "text": "How important is respect for authority?", "type": "scale"},
            {"id": "MF17", "text": "Do you follow rules even when you disagree with them?", "type": "scale"},
            {"id": "MF18", "text": "How do you feel about tradition?", "type": "text"},
            {"id": "MF19", "text": "Should children always obey parents?", "type": "scale"},
            {"id": "MF20", "text": "When is it okay to break rules?", "type": "text"},
            
            # Purity/Degradation (15 questions)
            {"id": "MF21", "text": "How important is physical/spiritual purity?", "type": "scale"},
            {"id": "MF22", "text": "Do you have strong disgust reactions?", "type": "scale"},
            {"id": "MF23", "text": "How do you feel about body modification?", "type": "text"},
            {"id": "MF24", "text": "Is the body sacred?", "type": "scale"},
            {"id": "MF25", "text": "How do you feel about 'unnatural' things?", "type": "text"},
            
            # Liberty/Oppression (10 questions)
            {"id": "MF26", "text": "How important is personal freedom to you?", "type": "scale"},
            {"id": "MF27", "text": "How do you feel about authority telling you what to do?", "type": "text"},
            {"id": "MF28", "text": "Is freedom more important than security?", "type": "choice", "options": ["Freedom much more important", "Freedom somewhat more", "Both equally important", "Security somewhat more", "Security much more important"]},
            {"id": "MF29", "text": "How do you react to bullies and tyrants?", "type": "text"},
            {"id": "MF30", "text": "Should people be free to make bad choices?", "type": "scale"},
        ]
    },
    
    "core_values": {
        "name": "Core Values (Schwartz)",
        "description": "Self-direction, stimulation, hedonism, achievement, power, security, conformity, tradition, benevolence, universalism",
        "questions": [
            # Rank your top 5 values
            {"id": "CV1", "text": "Rank these values from most to least important: Freedom, Achievement, Security, Helping Others, Pleasure, Power, Adventure, Tradition, Creativity, Social Justice", "type": "ranking"},
            {"id": "CV2", "text": "What value would you never compromise?", "type": "text"},
            {"id": "CV3", "text": "What matters more: personal success or making a difference?", "type": "text"},
            {"id": "CV4", "text": "How important is excitement and novelty in your life?", "type": "scale"},
            {"id": "CV5", "text": "Do you value stability or change more?", "type": "choice", "options": ["Strongly value stability", "Lean stability", "Both equally", "Lean change", "Strongly value change"]},
            {"id": "CV6", "text": "How important is it to be respected by others?", "type": "scale"},
            {"id": "CV7", "text": "Is pleasure a worthy goal in life?", "type": "scale"},
            {"id": "CV8", "text": "How important is following social norms?", "type": "scale"},
            {"id": "CV9", "text": "Do you value independence over belonging?", "type": "choice", "options": ["Strongly value independence", "Lean independence", "Both equally", "Lean belonging", "Strongly value belonging"]},
            {"id": "CV10", "text": "How much do you care about the environment?", "type": "scale"},
            {"id": "CV11", "text": "Is ambition a virtue or a vice?", "type": "text"},
            {"id": "CV12", "text": "How important is it to leave a legacy?", "type": "scale"},
            {"id": "CV13", "text": "Do you value comfort or growth more?", "type": "choice", "options": ["Strongly value comfort", "Lean comfort", "Both equally", "Lean growth", "Strongly value growth"]},
            {"id": "CV14", "text": "How do you define success?", "type": "text"},
            {"id": "CV15", "text": "What would you sacrifice for your values?", "type": "text"},
        ]
    },
    
    # =========================================================================
    # SECTION 4: COGNITIVE STYLE (~80 questions)
    # =========================================================================
    "thinking_style": {
        "name": "Cognitive and Thinking Style",
        "description": "How you process information, solve problems, and make decisions",
        "questions": [
            # Analytical vs Intuitive (15 questions)
            {"id": "TS1", "text": "Do you make decisions with logic or gut feeling?", "type": "choice", "options": ["Pure logic", "Mostly logic", "Mix of both", "Mostly gut", "Pure gut feeling"]},
            {"id": "TS2", "text": "Do you trust data or intuition more?", "type": "choice", "options": ["Always data", "Mostly data", "Depends on situation", "Mostly intuition", "Always intuition"]},
            {"id": "TS3", "text": "How do you approach complex problems?", "type": "text"},
            {"id": "TS4", "text": "Do you like to 'think out loud'?", "type": "yesno"},
            {"id": "TS5", "text": "How important is having all the facts before deciding?", "type": "scale"},
            {"id": "TS6", "text": "Do you ever 'just know' something without explaining why?", "type": "frequency"},
            {"id": "TS7", "text": "How do you validate your ideas?", "type": "text"},
            {"id": "TS8", "text": "Do you prefer step-by-step or holistic thinking?", "type": "choice", "options": ["Always step-by-step", "Mostly step-by-step", "Mix of both", "Mostly holistic", "Always holistic"]},
            {"id": "TS9", "text": "How do you feel about ambiguity?", "type": "text"},
            {"id": "TS10", "text": "Are you more detail-oriented or big-picture?", "type": "choice", "options": ["Very detail-oriented", "Lean detail", "Both equally", "Lean big-picture", "Very big-picture"]},
            
            # Problem-Solving (15 questions)
            {"id": "TS11", "text": "When facing a problem, what's your first instinct?", "type": "text"},
            {"id": "TS12", "text": "Do you break problems down or tackle them holistically?", "type": "choice", "options": ["Always break down", "Usually break down", "Depends", "Usually holistic", "Always holistic"]},
            {"id": "TS13", "text": "How do you handle problems with no clear solution?", "type": "text"},
            {"id": "TS14", "text": "Do you prefer to work through problems alone or collaboratively?", "type": "choice", "options": ["Always alone", "Mostly alone", "Depends", "Mostly collaborative", "Always collaborative"]},
            {"id": "TS15", "text": "How do you know when a problem is 'solved'?", "type": "text"},
            {"id": "TS16", "text": "Do you consider multiple approaches or go with the first good one?", "type": "choice", "options": ["Always explore multiple", "Usually explore", "Depends", "Usually first good one", "Always first good one"]},
            {"id": "TS17", "text": "How do you debug issues (in code or in life)?", "type": "text"},
            {"id": "TS18", "text": "What's your process for learning something new?", "type": "text"},
            {"id": "TS19", "text": "Do you prefer to understand 'why' or 'how'?", "type": "choice", "options": ["Always why", "Mostly why", "Both equally", "Mostly how", "Always how"]},
            {"id": "TS20", "text": "How do you handle contradictory information?", "type": "text"},
            
            # Decision-Making (15 questions)
            {"id": "TS21", "text": "How long do you take to make important decisions?", "type": "text"},
            {"id": "TS22", "text": "Do you agonize over decisions or make them quickly?", "type": "choice", "options": ["Heavily agonize", "Tend to agonize", "Depends on stakes", "Usually quick", "Always quick"]},
            {"id": "TS23", "text": "How do you handle regret about past decisions?", "type": "text"},
            {"id": "TS24", "text": "Do you second-guess yourself?", "type": "frequency"},
            {"id": "TS25", "text": "How do you weigh pros and cons?", "type": "text"},
            {"id": "TS26", "text": "Do you seek others' opinions before deciding?", "type": "scale"},
            {"id": "TS27", "text": "How do you handle decision fatigue?", "type": "text"},
            {"id": "TS28", "text": "What's your default when you can't decide?", "type": "text"},
            {"id": "TS29", "text": "Do you trust your first instinct?", "type": "scale"},
            {"id": "TS30", "text": "How do you decide between two good options?", "type": "text"},
            
            # Learning Style (15 questions)
            {"id": "TS31", "text": "Do you learn better by reading, watching, or doing?", "type": "choice", "options": ["Reading", "Watching/Listening", "Doing/Hands-on", "Mix"]},
            {"id": "TS32", "text": "How do you take notes?", "type": "text"},
            {"id": "TS33", "text": "Do you prefer structured courses or self-directed learning?", "type": "choice", "options": ["Strongly structured", "Lean structured", "Both work", "Lean self-directed", "Strongly self-directed"]},
            {"id": "TS34", "text": "How do you retain information best?", "type": "text"},
            {"id": "TS35", "text": "Do you learn better in silence or with background noise?", "type": "choice", "options": ["Silence", "Music", "Background noise", "Doesn't matter"]},
            {"id": "TS36", "text": "How deep do you go into topics that interest you?", "type": "scale"},
            {"id": "TS37", "text": "Do you prefer breadth or depth of knowledge?", "type": "choice", "options": ["Strong breadth", "Lean breadth", "Both equally", "Lean depth", "Strong depth"]},
            {"id": "TS38", "text": "How do you handle topics you find boring but necessary?", "type": "text"},
            {"id": "TS39", "text": "What's your optimal learning session length?", "type": "text"},
            {"id": "TS40", "text": "Do you learn from mistakes or try to avoid them?", "type": "text"},
        ]
    },
    
    # =========================================================================
    # SECTION 5: COMMUNICATION STYLE (~100 questions)
    # =========================================================================
    "communication": {
        "name": "Communication Style",
        "description": "How you express yourself, your tone, vocabulary, and patterns",
        "questions": [
            # Verbal Style (20 questions)
            {"id": "COM1", "text": "How would you describe your speaking style?", "type": "text"},
            {"id": "COM2", "text": "Do you use a lot of filler words (um, like, you know)?", "type": "scale"},
            {"id": "COM3", "text": "Do you curse/swear?", "type": "scale"},
            {"id": "COM4", "text": "What's your typical vocabulary level?", "type": "choice", "options": ["Simple and direct", "Average", "Sometimes fancy", "Elaborate/technical"]},
            {"id": "COM5", "text": "Do you use metaphors and analogies often?", "type": "scale"},
            {"id": "COM6", "text": "How fast do you speak?", "type": "scale"},
            {"id": "COM7", "text": "Do you pause to think mid-sentence?", "type": "frequency"},
            {"id": "COM8", "text": "Do you interrupt people?", "type": "frequency"},
            {"id": "COM9", "text": "How do you handle silence in conversation?", "type": "text"},
            {"id": "COM10", "text": "Do you speak more or less than average?", "type": "choice", "options": ["Much more", "Somewhat more", "About average", "Somewhat less", "Much less"]},
            
            # Tone (15 questions)
            {"id": "COM11", "text": "Is your default tone formal or casual?", "type": "choice", "options": ["Very formal", "Somewhat formal", "Depends on context", "Somewhat casual", "Very casual"]},
            {"id": "COM12", "text": "How sarcastic are you?", "type": "scale"},
            {"id": "COM13", "text": "Do people say you're hard to read?", "type": "yesno"},
            {"id": "COM14", "text": "How expressive are you?", "type": "scale"},
            {"id": "COM15", "text": "Do you modulate your tone for different audiences?", "type": "scale"},
            {"id": "COM16", "text": "Are you naturally encouraging or critical?", "type": "choice", "options": ["Very encouraging", "Mostly encouraging", "Balance of both", "Mostly critical", "Very critical"]},
            {"id": "COM17", "text": "How do you deliver bad news?", "type": "text"},
            {"id": "COM18", "text": "What's your humor style?", "type": "text"},
            {"id": "COM19", "text": "Do people describe you as warm or cool?", "type": "choice", "options": ["Very warm", "Mostly warm", "Depends on context", "Mostly cool", "Very cool"]},
            {"id": "COM20", "text": "How do you show you're listening?", "type": "text"},
            
            # Writing Style (15 questions)
            {"id": "COM21", "text": "How do you write emails?", "type": "text"},
            {"id": "COM22", "text": "Do you use emojis?", "type": "scale"},
            {"id": "COM23", "text": "How long are your text messages typically?", "type": "choice", "options": ["Very short", "Brief", "Medium", "Long", "Very long"]},
            {"id": "COM24", "text": "Do you proofread before sending?", "type": "frequency"},
            {"id": "COM25", "text": "Do you use proper punctuation in texts?", "type": "scale"},
            {"id": "COM26", "text": "How do you structure long messages?", "type": "text"},
            {"id": "COM27", "text": "What's your email greeting style?", "type": "text"},
            {"id": "COM28", "text": "How do you sign off messages?", "type": "text"},
            {"id": "COM29", "text": "Do you prefer bullet points or paragraphs?", "type": "choice", "options": ["Bullets", "Paragraphs", "Mix"]},
            {"id": "COM30", "text": "How much do you edit your writing?", "type": "scale"},
            
            # Expression Patterns (20 questions)
            {"id": "COM31", "text": "What phrases do you use frequently?", "type": "text"},
            {"id": "COM32", "text": "Do you have verbal tics or catchphrases?", "type": "text"},
            {"id": "COM33", "text": "How do you express agreement?", "type": "text"},
            {"id": "COM34", "text": "How do you express disagreement?", "type": "text"},
            {"id": "COM35", "text": "How do you express uncertainty?", "type": "text"},
            {"id": "COM36", "text": "How do you express enthusiasm?", "type": "text"},
            {"id": "COM37", "text": "How do you express frustration?", "type": "text"},
            {"id": "COM38", "text": "What words do you overuse?", "type": "text"},
            {"id": "COM39", "text": "What words do you avoid?", "type": "text"},
            {"id": "COM40", "text": "Do you use slang or jargon?", "type": "text"},
            
            # Conversational Patterns (15 questions)
            {"id": "COM41", "text": "Do you ask a lot of questions in conversation?", "type": "scale"},
            {"id": "COM42", "text": "Do you share personal stories easily?", "type": "scale"},
            {"id": "COM43", "text": "How do you transition between topics?", "type": "text"},
            {"id": "COM44", "text": "Do you dominate conversations or defer?", "type": "choice", "options": ["Always dominate", "Usually dominate", "Balance", "Usually defer", "Always defer"]},
            {"id": "COM45", "text": "How do you handle awkward silences?", "type": "text"},
            {"id": "COM46", "text": "Do you remember details people tell you?", "type": "scale"},
            {"id": "COM47", "text": "How do you show empathy verbally?", "type": "text"},
            {"id": "COM48", "text": "Do you give advice when people vent?", "type": "scale"},
            {"id": "COM49", "text": "How do you end conversations?", "type": "text"},
            {"id": "COM50", "text": "What makes a good conversation for you?", "type": "text"},
        ]
    },
    
    # =========================================================================
    # SECTION 6: WORK AND CAREER (~80 questions)
    # =========================================================================
    "work_style": {
        "name": "Work Style and Career",
        "description": "Professional preferences, work habits, career motivations",
        "questions": [
            # Work Environment (15 questions)
            {"id": "WK1", "text": "What's your ideal work environment?", "type": "text"},
            {"id": "WK2", "text": "Do you prefer working from home or in an office?", "type": "choice", "options": ["Strongly prefer home", "Mostly home", "Hybrid/no preference", "Mostly office", "Strongly prefer office"]},
            {"id": "WK3", "text": "How do you feel about open floor plans?", "type": "text"},
            {"id": "WK4", "text": "What time of day are you most productive?", "type": "choice", "options": ["Early morning", "Morning", "Afternoon", "Evening", "Late night"]},
            {"id": "WK5", "text": "How many hours can you work before diminishing returns?", "type": "number"},
            {"id": "WK6", "text": "Do you take breaks or power through?", "type": "choice", "options": ["Always take breaks", "Usually take breaks", "Mix of both", "Usually power through", "Always power through"]},
            {"id": "WK7", "text": "How do you handle interruptions?", "type": "text"},
            {"id": "WK8", "text": "What does your ideal workday look like?", "type": "text"},
            {"id": "WK9", "text": "How important is work-life balance to you?", "type": "scale"},
            {"id": "WK10", "text": "Do you work on weekends?", "type": "frequency"},
            
            # Collaboration (15 questions)
            {"id": "WK11", "text": "How do you prefer to collaborate?", "type": "text"},
            {"id": "WK12", "text": "Do you like meetings?", "type": "scale"},
            {"id": "WK13", "text": "How do you handle disagreements with colleagues?", "type": "text"},
            {"id": "WK14", "text": "Do you prefer to lead or follow?", "type": "choice", "options": ["Strongly prefer lead", "Usually lead", "Either works", "Usually follow", "Strongly prefer follow"]},
            {"id": "WK15", "text": "How do you give and receive feedback?", "type": "text"},
            {"id": "WK16", "text": "What makes a good teammate?", "type": "text"},
            {"id": "WK17", "text": "How do you handle underperforming team members?", "type": "text"},
            {"id": "WK18", "text": "Do you share credit readily?", "type": "scale"},
            {"id": "WK19", "text": "How do you communicate progress on projects?", "type": "text"},
            {"id": "WK20", "text": "Do you prefer synchronous or asynchronous work?", "type": "choice", "options": ["Strongly prefer sync", "Mostly sync", "No preference", "Mostly async", "Strongly prefer async"]},
            
            # Career Values (15 questions)
            {"id": "WK21", "text": "What motivates you in your work?", "type": "text"},
            {"id": "WK22", "text": "How important is money vs meaning in work?", "type": "choice", "options": ["Money is most important", "Lean toward money", "Both equally important", "Lean toward meaning", "Meaning is most important"]},
            {"id": "WK23", "text": "Where do you want to be in 5 years?", "type": "text"},
            {"id": "WK24", "text": "How ambitious are you career-wise?", "type": "scale"},
            {"id": "WK25", "text": "Would you sacrifice income for interesting work?", "type": "scale"},
            {"id": "WK26", "text": "How do you define professional success?", "type": "text"},
            {"id": "WK27", "text": "Do you want to manage people?", "type": "scale"},
            {"id": "WK28", "text": "How important is recognition for your work?", "type": "scale"},
            {"id": "WK29", "text": "What's your relationship with your current/past jobs?", "type": "text"},
            {"id": "WK30", "text": "What work would you do even if you weren't paid?", "type": "text"},
            
            # Technical/Domain Skills (15 questions)
            {"id": "WK31", "text": "What are you an expert in?", "type": "text"},
            {"id": "WK32", "text": "What skills are you proud of?", "type": "text"},
            {"id": "WK33", "text": "What do you want to learn next?", "type": "text"},
            {"id": "WK34", "text": "How do you stay current in your field?", "type": "text"},
            {"id": "WK35", "text": "What tools do you love using?", "type": "text"},
            {"id": "WK36", "text": "What tools do you hate?", "type": "text"},
            {"id": "WK37", "text": "How do you approach learning new technologies?", "type": "text"},
            {"id": "WK38", "text": "What's your debugging process?", "type": "text"},
            {"id": "WK39", "text": "How do you document your work?", "type": "text"},
            {"id": "WK40", "text": "What's your coding/working style?", "type": "text"},
        ]
    },
    
    # =========================================================================
    # SECTION 7: RELATIONSHIPS (~80 questions)
    # =========================================================================
    "relationships": {
        "name": "Relationships and Attachment",
        "description": "How you connect with others, attachment style, relationship patterns",
        "questions": [
            # Attachment Style (15 questions)
            {"id": "REL1", "text": "How comfortable are you with emotional intimacy?", "type": "scale"},
            {"id": "REL2", "text": "Do you fear abandonment?", "type": "scale"},
            {"id": "REL3", "text": "Do you need a lot of reassurance in relationships?", "type": "scale"},
            {"id": "REL4", "text": "How independent are you in relationships?", "type": "scale"},
            {"id": "REL5", "text": "Do you avoid getting too close to people?", "type": "scale"},
            {"id": "REL6", "text": "How do you handle conflict in relationships?", "type": "text"},
            {"id": "REL7", "text": "Do you trust your partners/friends easily?", "type": "scale"},
            {"id": "REL8", "text": "How do you show you care?", "type": "text"},
            {"id": "REL9", "text": "What's your love language?", "type": "choice", "options": ["Words of affirmation", "Quality time", "Physical touch", "Acts of service", "Gifts"]},
            {"id": "REL10", "text": "How do you prefer to receive affection?", "type": "text"},
            
            # Friendship (15 questions)
            {"id": "REL11", "text": "How many close friends do you have?", "type": "number"},
            {"id": "REL12", "text": "How do you maintain friendships?", "type": "text"},
            {"id": "REL13", "text": "What makes someone a good friend to you?", "type": "text"},
            {"id": "REL14", "text": "How easily do you make new friends?", "type": "scale"},
            {"id": "REL15", "text": "Do you prefer few deep friendships or many casual ones?", "type": "choice", "options": ["Strongly prefer few deep", "Lean toward deep", "Value both equally", "Lean toward many casual", "Strongly prefer many casual"]},
            {"id": "REL16", "text": "How do you handle friends drifting apart?", "type": "text"},
            {"id": "REL17", "text": "Do you initiate plans or wait to be invited?", "type": "choice", "options": ["Always initiate", "Usually initiate", "Mix of both", "Usually wait", "Always wait"]},
            {"id": "REL18", "text": "How honest are you with friends?", "type": "scale"},
            {"id": "REL19", "text": "What ends a friendship for you?", "type": "text"},
            {"id": "REL20", "text": "How do you support friends in crisis?", "type": "text"},
            
            # Family (15 questions)
            {"id": "REL21", "text": "What's your relationship with your family?", "type": "text"},
            {"id": "REL22", "text": "How close are you to your parents?", "type": "scale"},
            {"id": "REL23", "text": "Do you have siblings? How's that relationship?", "type": "text"},
            {"id": "REL24", "text": "How often do you contact family?", "type": "frequency"},
            {"id": "REL25", "text": "What family patterns do you want to continue?", "type": "text"},
            {"id": "REL26", "text": "What family patterns do you want to break?", "type": "text"},
            {"id": "REL27", "text": "How do you handle family conflict?", "type": "text"},
            {"id": "REL28", "text": "What role do you play in your family?", "type": "text"},
            {"id": "REL29", "text": "How has your family shaped who you are?", "type": "text"},
            {"id": "REL30", "text": "What do you value most about family?", "type": "text"},
            
            # Romantic (15 questions)
            {"id": "REL31", "text": "What do you look for in a partner?", "type": "text"},
            {"id": "REL32", "text": "What are your relationship deal-breakers?", "type": "text"},
            {"id": "REL33", "text": "How do you handle jealousy?", "type": "text"},
            {"id": "REL34", "text": "How do you express love?", "type": "text"},
            {"id": "REL35", "text": "How do you handle arguments with partners?", "type": "text"},
            {"id": "REL36", "text": "What's your view on commitment?", "type": "text"},
            {"id": "REL37", "text": "How much space do you need in relationships?", "type": "scale"},
            {"id": "REL38", "text": "What have past relationships taught you?", "type": "text"},
            {"id": "REL39", "text": "How do you balance independence and togetherness?", "type": "text"},
            {"id": "REL40", "text": "What does a healthy relationship look like to you?", "type": "text"},
        ]
    },
    
    # =========================================================================
    # SECTION 8: EMOTIONAL INTELLIGENCE (~60 questions)
    # =========================================================================
    "emotional_intelligence": {
        "name": "Emotional Intelligence",
        "description": "Self-awareness, self-regulation, empathy, social skills",
        "questions": [
            # Self-Awareness (15 questions)
            {"id": "EQ1", "text": "How well do you understand your own emotions?", "type": "scale"},
            {"id": "EQ2", "text": "Can you identify why you're feeling a certain way?", "type": "scale"},
            {"id": "EQ3", "text": "Do you know your triggers?", "type": "scale"},
            {"id": "EQ4", "text": "How accurate is your self-assessment?", "type": "text"},
            {"id": "EQ5", "text": "How self-aware are you of your impact on others?", "type": "scale"},
            {"id": "EQ6", "text": "Do you know your strengths and weaknesses?", "type": "text"},
            {"id": "EQ7", "text": "How do you feel about self-reflection?", "type": "text"},
            {"id": "EQ8", "text": "Do you journal or process emotions in some way?", "type": "text"},
            {"id": "EQ9", "text": "How well do you know yourself?", "type": "scale"},
            {"id": "EQ10", "text": "What blind spots do you have?", "type": "text"},
            
            # Self-Regulation (15 questions)
            {"id": "EQ11", "text": "Can you control your impulses?", "type": "scale"},
            {"id": "EQ12", "text": "How do you manage anger?", "type": "text"},
            {"id": "EQ13", "text": "How do you handle disappointment?", "type": "text"},
            {"id": "EQ14", "text": "Can you stay calm under pressure?", "type": "scale"},
            {"id": "EQ15", "text": "Do you think before you speak?", "type": "scale"},
            {"id": "EQ16", "text": "How do you manage anxiety?", "type": "text"},
            {"id": "EQ17", "text": "Can you delay gratification?", "type": "scale"},
            {"id": "EQ18", "text": "How do you prevent emotional outbursts?", "type": "text"},
            {"id": "EQ19", "text": "How do you bounce back from setbacks?", "type": "text"},
            {"id": "EQ20", "text": "Do you hold grudges?", "type": "scale"},
            
            # Empathy (15 questions)
            {"id": "EQ21", "text": "Can you tell how others are feeling?", "type": "scale"},
            {"id": "EQ22", "text": "Do you pick up on nonverbal cues?", "type": "scale"},
            {"id": "EQ23", "text": "Can you see things from others' perspectives?", "type": "scale"},
            {"id": "EQ24", "text": "Do people open up to you?", "type": "frequency"},
            {"id": "EQ25", "text": "How do you respond to others' emotions?", "type": "text"},
            {"id": "EQ26", "text": "Do you feel drained by others' emotions?", "type": "scale"},
            {"id": "EQ27", "text": "Can you sense the mood of a room?", "type": "scale"},
            {"id": "EQ28", "text": "How do you validate others' feelings?", "type": "text"},
            {"id": "EQ29", "text": "Do you absorb others' stress?", "type": "scale"},
            {"id": "EQ30", "text": "How do you balance empathy with boundaries?", "type": "text"},
        ]
    },
    
    # =========================================================================
    # SECTION 9: DAILY LIFE AND HABITS (~100 questions)
    # =========================================================================
    "daily_life": {
        "name": "Daily Life and Habits",
        "description": "Routines, preferences, lifestyle choices",
        "questions": [
            # Morning Routine (10 questions)
            {"id": "DL1", "text": "What time do you typically wake up?", "type": "text"},
            {"id": "DL2", "text": "What's the first thing you do when you wake up?", "type": "text"},
            {"id": "DL3", "text": "Are you a morning person?", "type": "scale"},
            {"id": "DL4", "text": "Do you have a morning routine?", "type": "text"},
            {"id": "DL5", "text": "How long does it take you to fully wake up?", "type": "text"},
            {"id": "DL6", "text": "Do you eat breakfast?", "type": "yesno"},
            {"id": "DL7", "text": "Coffee, tea, or neither?", "type": "choice", "options": ["Coffee", "Tea", "Both", "Neither"]},
            {"id": "DL8", "text": "Do you check your phone first thing?", "type": "yesno"},
            {"id": "DL9", "text": "Do you exercise in the morning?", "type": "frequency"},
            {"id": "DL10", "text": "How do you feel about mornings in general?", "type": "text"},
            
            # Evening/Night (10 questions)
            {"id": "DL11", "text": "What time do you usually go to bed?", "type": "text"},
            {"id": "DL12", "text": "Do you have a bedtime routine?", "type": "text"},
            {"id": "DL13", "text": "How easily do you fall asleep?", "type": "scale"},
            {"id": "DL14", "text": "Do you use screens before bed?", "type": "yesno"},
            {"id": "DL15", "text": "Are you a night owl?", "type": "scale"},
            {"id": "DL16", "text": "What do you do to wind down?", "type": "text"},
            {"id": "DL17", "text": "How many hours of sleep do you need?", "type": "number"},
            {"id": "DL18", "text": "Do you dream vividly?", "type": "frequency"},
            {"id": "DL19", "text": "How do you feel when you wake up?", "type": "text"},
            {"id": "DL20", "text": "Do you nap?", "type": "frequency"},
            
            # Food and Drink (15 questions)
            {"id": "DL21", "text": "What's your relationship with food?", "type": "text"},
            {"id": "DL22", "text": "Do you cook?", "type": "frequency"},
            {"id": "DL23", "text": "What are your favorite foods?", "type": "text"},
            {"id": "DL24", "text": "Are you adventurous with food?", "type": "scale"},
            {"id": "DL25", "text": "Do you have dietary restrictions or preferences?", "type": "text"},
            {"id": "DL26", "text": "How much do you care about nutrition?", "type": "scale"},
            {"id": "DL27", "text": "Do you eat out or cook at home more?", "type": "choice", "options": ["Almost always eat out", "Mostly eat out", "About equal", "Mostly cook at home", "Almost always cook at home"]},
            {"id": "DL28", "text": "What's your comfort food?", "type": "text"},
            {"id": "DL29", "text": "Do you drink alcohol?", "type": "frequency"},
            {"id": "DL30", "text": "What's your relationship with caffeine?", "type": "text"},
            
            # Exercise and Health (10 questions)
            {"id": "DL31", "text": "Do you exercise regularly?", "type": "frequency"},
            {"id": "DL32", "text": "What kind of exercise do you enjoy?", "type": "text"},
            {"id": "DL33", "text": "How important is physical fitness to you?", "type": "scale"},
            {"id": "DL34", "text": "What's your relationship with your body?", "type": "text"},
            {"id": "DL35", "text": "Do you track health metrics?", "type": "yesno"},
            {"id": "DL36", "text": "How do you handle being sick?", "type": "text"},
            {"id": "DL37", "text": "What's your stress relief method?", "type": "text"},
            {"id": "DL38", "text": "Do you meditate or practice mindfulness?", "type": "frequency"},
            {"id": "DL39", "text": "How do you maintain mental health?", "type": "text"},
            {"id": "DL40", "text": "What's your relationship with doctors/healthcare?", "type": "text"},
            
            # Hobbies and Leisure (15 questions)
            {"id": "DL41", "text": "What do you do for fun?", "type": "text"},
            {"id": "DL42", "text": "What are your hobbies?", "type": "text"},
            {"id": "DL43", "text": "How much time do you spend on hobbies?", "type": "text"},
            {"id": "DL44", "text": "Do you watch TV/streaming?", "type": "frequency"},
            {"id": "DL45", "text": "What genres do you enjoy?", "type": "text"},
            {"id": "DL46", "text": "Do you play video games?", "type": "frequency"},
            {"id": "DL47", "text": "What kind of games?", "type": "text"},
            {"id": "DL48", "text": "Do you read for pleasure?", "type": "frequency"},
            {"id": "DL49", "text": "What kind of books?", "type": "text"},
            {"id": "DL50", "text": "How do you spend weekends?", "type": "text"},
            
            # Technology Use (15 questions)
            {"id": "DL51", "text": "How many hours a day do you spend on screens?", "type": "number"},
            {"id": "DL52", "text": "What apps do you use most?", "type": "text"},
            {"id": "DL53", "text": "How do you feel about social media?", "type": "text"},
            {"id": "DL54", "text": "Do you doom-scroll?", "type": "frequency"},
            {"id": "DL55", "text": "What's your relationship with your phone?", "type": "text"},
            {"id": "DL56", "text": "Do you set technology boundaries?", "type": "text"},
            {"id": "DL57", "text": "How do you feel about always being reachable?", "type": "text"},
            {"id": "DL58", "text": "What technology do you love?", "type": "text"},
            {"id": "DL59", "text": "What technology frustrates you?", "type": "text"},
            {"id": "DL60", "text": "Do you embrace or resist new tech?", "type": "choice", "options": ["Eagerly embrace", "Mostly embrace", "Selective/cautious", "Mostly resist", "Strongly resist"]},
        ]
    },
    
    # =========================================================================
    # SECTION 10: LIFE EXPERIENCES (~100 questions)
    # =========================================================================
    "life_experiences": {
        "name": "Life Experiences and History",
        "description": "Formative experiences, turning points, significant memories",
        "questions": [
            # Childhood (15 questions)
            {"id": "LE1", "text": "Describe your childhood in a few sentences.", "type": "text"},
            {"id": "LE2", "text": "What was your family environment like growing up?", "type": "text"},
            {"id": "LE3", "text": "What's your earliest memory?", "type": "text"},
            {"id": "LE4", "text": "What did you want to be when you grew up?", "type": "text"},
            {"id": "LE5", "text": "What were you like as a child?", "type": "text"},
            {"id": "LE6", "text": "What was school like for you?", "type": "text"},
            {"id": "LE7", "text": "Did you have many friends growing up?", "type": "text"},
            {"id": "LE8", "text": "What shaped you most as a child?", "type": "text"},
            {"id": "LE9", "text": "What was your biggest struggle growing up?", "type": "text"},
            {"id": "LE10", "text": "What's your happiest childhood memory?", "type": "text"},
            
            # Formative Experiences (20 questions)
            {"id": "LE11", "text": "What experience changed you the most?", "type": "text"},
            {"id": "LE12", "text": "Have you experienced significant loss?", "type": "text"},
            {"id": "LE13", "text": "What's the hardest thing you've been through?", "type": "text"},
            {"id": "LE14", "text": "What are you most proud of accomplishing?", "type": "text"},
            {"id": "LE15", "text": "What's your biggest regret?", "type": "text"},
            {"id": "LE16", "text": "What lessons did you learn the hard way?", "type": "text"},
            {"id": "LE17", "text": "What failure taught you the most?", "type": "text"},
            {"id": "LE18", "text": "Have you had any near-death experiences?", "type": "text"},
            {"id": "LE19", "text": "What's the bravest thing you've done?", "type": "text"},
            {"id": "LE20", "text": "What moment are you most ashamed of?", "type": "text"},
            {"id": "LE21", "text": "What was a turning point in your life?", "type": "text"},
            {"id": "LE22", "text": "What did you overcome that you didn't think you could?", "type": "text"},
            {"id": "LE23", "text": "What's the best decision you ever made?", "type": "text"},
            {"id": "LE24", "text": "What's the worst decision you ever made?", "type": "text"},
            {"id": "LE25", "text": "What would you tell your younger self?", "type": "text"},
            
            # Education and Career Path (15 questions)
            {"id": "LE26", "text": "Describe your educational journey.", "type": "text"},
            {"id": "LE27", "text": "What did you study and why?", "type": "text"},
            {"id": "LE28", "text": "How did you end up in your current career?", "type": "text"},
            {"id": "LE29", "text": "What jobs have you had?", "type": "text"},
            {"id": "LE30", "text": "What did each job teach you?", "type": "text"},
            {"id": "LE31", "text": "What was your worst job experience?", "type": "text"},
            {"id": "LE32", "text": "What was your best job experience?", "type": "text"},
            {"id": "LE33", "text": "Who were your mentors?", "type": "text"},
            {"id": "LE34", "text": "What would you have done differently career-wise?", "type": "text"},
            {"id": "LE35", "text": "What's your career trajectory been like?", "type": "text"},
            
            # Identity Formation (15 questions)
            {"id": "LE36", "text": "When did you feel like you 'found yourself'?", "type": "text"},
            {"id": "LE37", "text": "What beliefs have you changed as you've grown?", "type": "text"},
            {"id": "LE38", "text": "What parts of yourself have remained constant?", "type": "text"},
            {"id": "LE39", "text": "How has your identity evolved over time?", "type": "text"},
            {"id": "LE40", "text": "What shaped your worldview the most?", "type": "text"},
            {"id": "LE41", "text": "How do you see yourself differently than others see you?", "type": "text"},
            {"id": "LE42", "text": "What labels do you identify with?", "type": "text"},
            {"id": "LE43", "text": "What labels have been applied to you that don't fit?", "type": "text"},
            {"id": "LE44", "text": "How have your values changed over time?", "type": "text"},
            {"id": "LE45", "text": "What do you know now that you wish you knew earlier?", "type": "text"},
        ]
    },
    
    # =========================================================================
    # SECTION 11: BELIEFS AND PHILOSOPHY (~60 questions)
    # =========================================================================
    "beliefs": {
        "name": "Beliefs and Philosophy",
        "description": "Worldview, religion/spirituality, existential perspectives",
        "questions": [
            # Worldview (15 questions)
            {"id": "BL1", "text": "How would you describe your worldview?", "type": "text"},
            {"id": "BL2", "text": "Are you optimistic or pessimistic about humanity?", "type": "choice", "options": ["Very optimistic", "Somewhat optimistic", "Realistic/neutral", "Somewhat pessimistic", "Very pessimistic"]},
            {"id": "BL3", "text": "Do you believe people are fundamentally good?", "type": "scale"},
            {"id": "BL4", "text": "How much control do we have over our lives?", "type": "scale"},
            {"id": "BL5", "text": "Do you believe in free will?", "type": "text"},
            {"id": "BL6", "text": "What do you think is the meaning of life?", "type": "text"},
            {"id": "BL7", "text": "What happens after death?", "type": "text"},
            {"id": "BL8", "text": "Is there objective morality?", "type": "text"},
            {"id": "BL9", "text": "How do you think about suffering?", "type": "text"},
            {"id": "BL10", "text": "What gives your life meaning?", "type": "text"},
            
            # Religion/Spirituality (15 questions)
            {"id": "BL11", "text": "What's your religious or spiritual background?", "type": "text"},
            {"id": "BL12", "text": "Are you religious or spiritual now?", "type": "text"},
            {"id": "BL13", "text": "Do you believe in a higher power?", "type": "text"},
            {"id": "BL14", "text": "What role does faith play in your life?", "type": "text"},
            {"id": "BL15", "text": "Do you practice any spiritual disciplines?", "type": "text"},
            {"id": "BL16", "text": "How do you feel about organized religion?", "type": "text"},
            {"id": "BL17", "text": "What do you think about consciousness?", "type": "text"},
            {"id": "BL18", "text": "Do you believe in anything supernatural?", "type": "text"},
            {"id": "BL19", "text": "How has your spirituality evolved?", "type": "text"},
            {"id": "BL20", "text": "What questions keep you up at night?", "type": "text"},
            
            # Politics and Society (15 questions)
            {"id": "BL21", "text": "Where do you fall on the political spectrum?", "type": "text"},
            {"id": "BL22", "text": "What political issues matter most to you?", "type": "text"},
            {"id": "BL23", "text": "How do you feel about the current state of the world?", "type": "text"},
            {"id": "BL24", "text": "What would you change about society?", "type": "text"},
            {"id": "BL25", "text": "How engaged are you in politics?", "type": "scale"},
            {"id": "BL26", "text": "Do you discuss politics openly?", "type": "scale"},
            {"id": "BL27", "text": "How do you handle political disagreements?", "type": "text"},
            {"id": "BL28", "text": "What's your view on government's role?", "type": "text"},
            {"id": "BL29", "text": "What social causes do you care about?", "type": "text"},
            {"id": "BL30", "text": "How hopeful are you about the future?", "type": "scale"},
        ]
    },
    
    # =========================================================================
    # SECTION 12: SPECIFIC REACTIONS AND SCENARIOS (~80 questions)
    # =========================================================================
    "reactions": {
        "name": "Reactions and Scenarios",
        "description": "How you respond to specific situations",
        "questions": [
            # Stress Scenarios (20 questions)
            {"id": "RX1", "text": "How do you react when you're running late?", "type": "text"},
            {"id": "RX2", "text": "What do you do when plans change last minute?", "type": "text"},
            {"id": "RX3", "text": "How do you handle bad news?", "type": "text"},
            {"id": "RX4", "text": "What's your reaction when technology fails you?", "type": "text"},
            {"id": "RX5", "text": "How do you behave when you're extremely tired?", "type": "text"},
            {"id": "RX6", "text": "What do you do when you're overwhelmed?", "type": "text"},
            {"id": "RX7", "text": "How do you react to criticism from someone you respect?", "type": "text"},
            {"id": "RX8", "text": "What's your first instinct when you make a mistake?", "type": "text"},
            {"id": "RX9", "text": "How do you handle being stuck in traffic?", "type": "text"},
            {"id": "RX10", "text": "What do you do when you can't sleep?", "type": "text"},
            {"id": "RX11", "text": "How do you react when someone ghosts you?", "type": "text"},
            {"id": "RX12", "text": "What do you do when you're bored?", "type": "text"},
            {"id": "RX13", "text": "How do you handle rejection?", "type": "text"},
            {"id": "RX14", "text": "What's your reaction to unexpected expenses?", "type": "text"},
            {"id": "RX15", "text": "How do you respond when someone disagrees with you strongly?", "type": "text"},
            
            # Social Scenarios (20 questions)
            {"id": "RX16", "text": "How do you act at parties where you don't know anyone?", "type": "text"},
            {"id": "RX17", "text": "What do you do when you see someone being bullied?", "type": "text"},
            {"id": "RX18", "text": "How do you handle receiving a gift you don't like?", "type": "text"},
            {"id": "RX19", "text": "What's your reaction when someone is rude to a server/worker?", "type": "text"},
            {"id": "RX20", "text": "How do you respond to unsolicited advice?", "type": "text"},
            {"id": "RX21", "text": "What do you do when someone is crying?", "type": "text"},
            {"id": "RX22", "text": "How do you react when you're interrupted?", "type": "text"},
            {"id": "RX23", "text": "What do you do when you witness injustice?", "type": "text"},
            {"id": "RX24", "text": "How do you handle someone flirting with you?", "type": "text"},
            {"id": "RX25", "text": "What's your reaction when someone shares good news?", "type": "text"},
            
            # Work Scenarios (15 questions)
            {"id": "RX26", "text": "How do you react when your idea is rejected?", "type": "text"},
            {"id": "RX27", "text": "What do you do when you disagree with your boss?", "type": "text"},
            {"id": "RX28", "text": "How do you handle taking credit for team work?", "type": "text"},
            {"id": "RX29", "text": "What's your reaction when someone takes credit for your work?", "type": "text"},
            {"id": "RX30", "text": "How do you respond to an unreasonable deadline?", "type": "text"},
            {"id": "RX31", "text": "What do you do when you realize you're wrong in a meeting?", "type": "text"},
            {"id": "RX32", "text": "How do you handle a coworker not pulling their weight?", "type": "text"},
            {"id": "RX33", "text": "What's your reaction when you get promoted?", "type": "text"},
            {"id": "RX34", "text": "How do you respond when someone else gets a promotion you wanted?", "type": "text"},
            {"id": "RX35", "text": "What do you do when a project fails?", "type": "text"},
            
            # Ethical Scenarios (15 questions)
            {"id": "RX36", "text": "Would you lie to protect someone's feelings?", "type": "text"},
            {"id": "RX37", "text": "How would you handle finding a wallet with $500?", "type": "text"},
            {"id": "RX38", "text": "What would you do if you saw a friend's partner cheating?", "type": "text"},
            {"id": "RX39", "text": "How would you handle discovering your company is unethical?", "type": "text"},
            {"id": "RX40", "text": "Would you break a promise to do the right thing?", "type": "text"},
        ]
    },
    
    # =========================================================================
    # SECTION 13: PREFERENCES AND TASTES (~80 questions)
    # =========================================================================
    "preferences": {
        "name": "Preferences and Tastes",
        "description": "Aesthetic preferences, media consumption, lifestyle choices",
        "questions": [
            # Aesthetic Preferences (20 questions)
            {"id": "PF1", "text": "What's your favorite color and why?", "type": "text"},
            {"id": "PF2", "text": "Describe your personal style.", "type": "text"},
            {"id": "PF3", "text": "What type of architecture do you love?", "type": "text"},
            {"id": "PF4", "text": "How would you decorate your ideal space?", "type": "text"},
            {"id": "PF5", "text": "What visual art do you gravitate toward?", "type": "text"},
            {"id": "PF6", "text": "Do you prefer modern or traditional aesthetics?", "type": "choice", "options": ["Strongly modern", "Lean modern", "Mix of both", "Lean traditional", "Strongly traditional"]},
            {"id": "PF7", "text": "What's your relationship with fashion?", "type": "text"},
            {"id": "PF8", "text": "Describe your ideal environment.", "type": "text"},
            {"id": "PF9", "text": "City, suburbs, or country?", "type": "choice", "options": ["City", "Suburbs", "Country", "Varies"]},
            {"id": "PF10", "text": "Mountains or beach?", "type": "choice", "options": ["Mountains", "Beach", "Both", "Neither"]},
            
            # Media Preferences (25 questions)
            {"id": "PF11", "text": "What are your favorite movies?", "type": "text"},
            {"id": "PF12", "text": "What TV shows have you loved?", "type": "text"},
            {"id": "PF13", "text": "What music do you listen to?", "type": "text"},
            {"id": "PF14", "text": "What podcasts do you follow?", "type": "text"},
            {"id": "PF15", "text": "What are your favorite books?", "type": "text"},
            {"id": "PF16", "text": "What YouTube channels do you watch?", "type": "text"},
            {"id": "PF17", "text": "What social media do you use and how?", "type": "text"},
            {"id": "PF18", "text": "What news sources do you trust?", "type": "text"},
            {"id": "PF19", "text": "How do you discover new media?", "type": "text"},
            {"id": "PF20", "text": "What genres do you avoid?", "type": "text"},
            {"id": "PF21", "text": "How much media do you consume daily?", "type": "text"},
            {"id": "PF22", "text": "Do you binge or savor shows?", "type": "choice", "options": ["Always binge", "Usually binge", "Depends on show", "Usually savor", "Always savor"]},
            {"id": "PF23", "text": "What's overrated in media right now?", "type": "text"},
            {"id": "PF24", "text": "What's underrated?", "type": "text"},
            {"id": "PF25", "text": "What media influenced you growing up?", "type": "text"},
            
            # Lifestyle Preferences (20 questions)
            {"id": "PF26", "text": "What's your ideal vacation?", "type": "text"},
            {"id": "PF27", "text": "How do you prefer to spend money?", "type": "text"},
            {"id": "PF28", "text": "What material possessions matter to you?", "type": "text"},
            {"id": "PF29", "text": "How do you feel about minimalism?", "type": "text"},
            {"id": "PF30", "text": "What's your relationship with nature?", "type": "text"},
            {"id": "PF31", "text": "Do you prefer routines or spontaneity?", "type": "choice", "options": ["Strongly routine", "Lean routine", "Balance of both", "Lean spontaneous", "Strongly spontaneous"]},
            {"id": "PF32", "text": "Early bird or night owl?", "type": "choice", "options": ["Extreme early bird", "Early bird", "Neither/flexible", "Night owl", "Extreme night owl"]},
            {"id": "PF33", "text": "How do you feel about pets?", "type": "text"},
            {"id": "PF34", "text": "What's your ideal living situation?", "type": "text"},
            {"id": "PF35", "text": "How important is convenience vs quality?", "type": "choice", "options": ["Always convenience", "Usually convenience", "Depends on context", "Usually quality", "Always quality"]},
        ]
    },
    
    # =========================================================================
    # SECTION 14: QUIRKS AND UNIQUE TRAITS (~50 questions)
    # =========================================================================
    "quirks": {
        "name": "Quirks and Unique Traits",
        "description": "The distinctive little things that make you you",
        "questions": [
            {"id": "QK1", "text": "What are your pet peeves?", "type": "text"},
            {"id": "QK2", "text": "What do you get irrationally excited about?", "type": "text"},
            {"id": "QK3", "text": "What's a weird habit you have?", "type": "text"},
            {"id": "QK4", "text": "What do you do that others find strange?", "type": "text"},
            {"id": "QK5", "text": "What's your comfort ritual?", "type": "text"},
            {"id": "QK6", "text": "What superstitions do you have?", "type": "text"},
            {"id": "QK7", "text": "What makes you cringe?", "type": "text"},
            {"id": "QK8", "text": "What's your guilty pleasure?", "type": "text"},
            {"id": "QK9", "text": "What's something you're secretly good at?", "type": "text"},
            {"id": "QK10", "text": "What's something you're embarrassingly bad at?", "type": "text"},
            {"id": "QK11", "text": "What topic can you talk about forever?", "type": "text"},
            {"id": "QK12", "text": "What's your personal motto?", "type": "text"},
            {"id": "QK13", "text": "What hill will you die on?", "type": "text"},
            {"id": "QK14", "text": "What's your unpopular opinion?", "type": "text"},
            {"id": "QK15", "text": "What's your comfort show/movie/song?", "type": "text"},
            {"id": "QK16", "text": "What do you always have with you?", "type": "text"},
            {"id": "QK17", "text": "What's your ordering tendency at restaurants?", "type": "text"},
            {"id": "QK18", "text": "What's your relationship with directions/maps?", "type": "text"},
            {"id": "QK19", "text": "What do you collect, if anything?", "type": "text"},
            {"id": "QK20", "text": "What's your most used emoji?", "type": "text"},
            {"id": "QK21", "text": "What phrase do you overuse?", "type": "text"},
            {"id": "QK22", "text": "What's your go-to icebreaker?", "type": "text"},
            {"id": "QK23", "text": "How do you greet people?", "type": "text"},
            {"id": "QK24", "text": "What's your laugh like?", "type": "text"},
            {"id": "QK25", "text": "What makes you uniquely you?", "type": "text"},
        ]
    },
    
    # =========================================================================
    # SECTION 15: SELF-PERCEPTION (~50 questions)
    # =========================================================================
    "self_perception": {
        "name": "Self-Perception",
        "description": "How you see yourself vs how others see you",
        "questions": [
            {"id": "SP1", "text": "How would you describe yourself in three words?", "type": "text"},
            {"id": "SP2", "text": "How would your best friend describe you?", "type": "text"},
            {"id": "SP3", "text": "How would your coworkers describe you?", "type": "text"},
            {"id": "SP4", "text": "How would your family describe you?", "type": "text"},
            {"id": "SP5", "text": "How do you think strangers perceive you?", "type": "text"},
            {"id": "SP6", "text": "What's the gap between who you are and who you want to be?", "type": "text"},
            {"id": "SP7", "text": "What do people misunderstand about you?", "type": "text"},
            {"id": "SP8", "text": "What's your biggest insecurity?", "type": "text"},
            {"id": "SP9", "text": "What are you most confident about?", "type": "text"},
            {"id": "SP10", "text": "What's your greatest strength?", "type": "text"},
            {"id": "SP11", "text": "What's your greatest weakness?", "type": "text"},
            {"id": "SP12", "text": "What do you wish more people knew about you?", "type": "text"},
            {"id": "SP13", "text": "What part of yourself are you working on?", "type": "text"},
            {"id": "SP14", "text": "What have you accepted about yourself?", "type": "text"},
            {"id": "SP15", "text": "What are you in denial about?", "type": "text"},
            {"id": "SP16", "text": "How has your self-image changed over time?", "type": "text"},
            {"id": "SP17", "text": "What compliments mean the most to you?", "type": "text"},
            {"id": "SP18", "text": "What criticism cuts the deepest?", "type": "text"},
            {"id": "SP19", "text": "How do you compare to others in your field?", "type": "text"},
            {"id": "SP20", "text": "What's your relationship with yourself?", "type": "text"},
        ]
    },
    
    # =========================================================================
    # SECTION 16: COGNITIVE PATTERNS (~60 questions)
    # =========================================================================
    "cognitive_patterns": {
        "name": "Cognitive Patterns and Mental Models",
        "description": "How you think, process, and understand the world",
        "questions": [
            # Mental Models (20 questions)
            {"id": "CP1", "text": "What mental shortcuts do you use to make decisions?", "type": "text"},
            {"id": "CP2", "text": "Do you think in words, images, or feelings?", "type": "choice", "options": ["Words/inner monologue", "Images/visual", "Feelings/sensations", "Abstract concepts", "Mix of all"]},
            {"id": "CP3", "text": "When someone tells you a story, do you visualize it?", "type": "scale"},
            {"id": "CP4", "text": "Do you have an internal monologue constantly running?", "type": "scale"},
            {"id": "CP5", "text": "How do you remember things - verbally, visually, or by association?", "type": "text"},
            {"id": "CP6", "text": "Do you think in systems and patterns?", "type": "scale"},
            {"id": "CP7", "text": "How do you conceptualize time?", "type": "text"},
            {"id": "CP8", "text": "Do you see numbers as having colors or personalities?", "type": "yesno"},
            {"id": "CP9", "text": "How do you organize information in your head?", "type": "text"},
            {"id": "CP10", "text": "What frameworks do you use to understand problems?", "type": "text"},
            {"id": "CP11", "text": "Do you categorize everything or resist labels?", "type": "choice", "options": ["Strongly categorize", "Tend to categorize", "Mix of both", "Tend to resist labels", "Strongly resist labels"]},
            {"id": "CP12", "text": "How do you process new information?", "type": "text"},
            {"id": "CP13", "text": "Do you think sequentially or in parallel?", "type": "choice", "options": ["Always sequential", "Mostly sequential", "Both equally", "Mostly parallel", "Always parallel"]},
            {"id": "CP14", "text": "What's your internal representation of 'the future'?", "type": "text"},
            {"id": "CP15", "text": "How do you hold multiple ideas in mind simultaneously?", "type": "text"},
            
            # Attention and Focus (15 questions)
            {"id": "CP16", "text": "What's your attention span like?", "type": "text"},
            {"id": "CP17", "text": "Can you hyperfocus? On what?", "type": "text"},
            {"id": "CP18", "text": "How easily are you distracted?", "type": "scale"},
            {"id": "CP19", "text": "What helps you focus?", "type": "text"},
            {"id": "CP20", "text": "What destroys your focus?", "type": "text"},
            {"id": "CP21", "text": "Do you prefer single-tasking or multitasking?", "type": "choice", "options": ["Strongly single-task", "Prefer single-task", "Either works", "Prefer multitask", "Strongly multitask"]},
            {"id": "CP22", "text": "How do you handle information overload?", "type": "text"},
            {"id": "CP23", "text": "What's your relationship with notifications?", "type": "text"},
            {"id": "CP24", "text": "How long can you concentrate on one thing?", "type": "text"},
            {"id": "CP25", "text": "Do you get lost in thought often?", "type": "frequency"},
            
            # Memory (15 questions)
            {"id": "CP26", "text": "How's your memory overall?", "type": "scale"},
            {"id": "CP27", "text": "What types of things do you remember easily?", "type": "text"},
            {"id": "CP28", "text": "What do you always forget?", "type": "text"},
            {"id": "CP29", "text": "Do you remember faces or names better?", "type": "choice", "options": ["Faces", "Names", "Both equally", "Neither well"]},
            {"id": "CP30", "text": "How do you remember important things?", "type": "text"},
            {"id": "CP31", "text": "Do you have vivid memories from childhood?", "type": "scale"},
            {"id": "CP32", "text": "How accurate do you think your memories are?", "type": "scale"},
            {"id": "CP33", "text": "What triggers memories for you?", "type": "text"},
            {"id": "CP34", "text": "Do you use memory techniques or systems?", "type": "text"},
            {"id": "CP35", "text": "What would you most want to never forget?", "type": "text"},
            
            # Pattern Recognition (10 questions)
            {"id": "CP36", "text": "Do you see patterns others miss?", "type": "scale"},
            {"id": "CP37", "text": "How quickly do you notice when something is 'off'?", "type": "scale"},
            {"id": "CP38", "text": "Do you find hidden connections between things?", "type": "scale"},
            {"id": "CP39", "text": "How do you identify trends?", "type": "text"},
            {"id": "CP40", "text": "Do you trust pattern recognition or verify with data?", "type": "choice", "options": ["Always trust patterns", "Usually trust patterns", "Balance of both", "Usually verify with data", "Always verify with data"]},
        ]
    },
    
    # =========================================================================
    # SECTION 17: FEARS AND MOTIVATIONS (~50 questions)
    # =========================================================================
    "fears_motivations": {
        "name": "Fears and Motivations",
        "description": "What drives you and what holds you back",
        "questions": [
            # Fears (20 questions)
            {"id": "FM1", "text": "What's your biggest fear?", "type": "text"},
            {"id": "FM2", "text": "What are you afraid of failing at?", "type": "text"},
            {"id": "FM3", "text": "What do you avoid because of fear?", "type": "text"},
            {"id": "FM4", "text": "Do you fear success?", "type": "scale"},
            {"id": "FM5", "text": "What's your relationship with mortality?", "type": "text"},
            {"id": "FM6", "text": "What social situations scare you?", "type": "text"},
            {"id": "FM7", "text": "Do you fear being alone?", "type": "scale"},
            {"id": "FM8", "text": "What would be your worst nightmare scenario?", "type": "text"},
            {"id": "FM9", "text": "What irrational fears do you have?", "type": "text"},
            {"id": "FM10", "text": "How do your fears affect your decisions?", "type": "text"},
            {"id": "FM11", "text": "Do you fear missing out (FOMO)?", "type": "scale"},
            {"id": "FM12", "text": "What fears have you overcome?", "type": "text"},
            {"id": "FM13", "text": "Are you afraid of commitment?", "type": "scale"},
            {"id": "FM14", "text": "Do you fear vulnerability?", "type": "scale"},
            {"id": "FM15", "text": "What keeps you up at night?", "type": "text"},
            
            # Motivations (20 questions)
            {"id": "FM16", "text": "What gets you out of bed in the morning?", "type": "text"},
            {"id": "FM17", "text": "What are you working towards?", "type": "text"},
            {"id": "FM18", "text": "What would you regret not doing?", "type": "text"},
            {"id": "FM19", "text": "What's your 'why'?", "type": "text"},
            {"id": "FM20", "text": "Are you motivated by approach (toward good) or avoidance (away from bad)?", "type": "choice", "options": ["Strongly approach", "Mostly approach", "Mix of both", "Mostly avoidance", "Strongly avoidance"]},
            {"id": "FM21", "text": "What external rewards motivate you?", "type": "text"},
            {"id": "FM22", "text": "What internal rewards motivate you?", "type": "text"},
            {"id": "FM23", "text": "Do you need deadlines to perform?", "type": "scale"},
            {"id": "FM24", "text": "What demotivates you?", "type": "text"},
            {"id": "FM25", "text": "How do you stay motivated long-term?", "type": "text"},
            {"id": "FM26", "text": "What would you do if money weren't an issue?", "type": "text"},
            {"id": "FM27", "text": "What legacy do you want to leave?", "type": "text"},
            {"id": "FM28", "text": "What drives you that might be unhealthy?", "type": "text"},
            {"id": "FM29", "text": "What's your relationship with ambition?", "type": "text"},
            {"id": "FM30", "text": "What motivates you that others might not understand?", "type": "text"},
            
            # Risk and Reward (10 questions)
            {"id": "FM31", "text": "How risk-averse are you?", "type": "scale"},
            {"id": "FM32", "text": "What risks have paid off for you?", "type": "text"},
            {"id": "FM33", "text": "What risks do you regret not taking?", "type": "text"},
            {"id": "FM34", "text": "How do you evaluate risk vs reward?", "type": "text"},
            {"id": "FM35", "text": "What's worth risking everything for?", "type": "text"},
        ]
    },
    
    # =========================================================================
    # SECTION 18: SOCIAL DYNAMICS (~50 questions)
    # =========================================================================
    "social_dynamics": {
        "name": "Social Dynamics",
        "description": "How you navigate social situations and power dynamics",
        "questions": [
            # Social Navigation (20 questions)
            {"id": "SD1", "text": "How do you read a room?", "type": "text"},
            {"id": "SD2", "text": "Do you adapt your personality to different groups?", "type": "scale"},
            {"id": "SD3", "text": "How do you handle group dynamics?", "type": "text"},
            {"id": "SD4", "text": "What role do you naturally take in groups?", "type": "text"},
            {"id": "SD5", "text": "How do you deal with difficult people?", "type": "text"},
            {"id": "SD6", "text": "Are you good at networking?", "type": "scale"},
            {"id": "SD7", "text": "How do you build rapport?", "type": "text"},
            {"id": "SD8", "text": "What social situations exhaust you?", "type": "text"},
            {"id": "SD9", "text": "How do you handle gossip?", "type": "text"},
            {"id": "SD10", "text": "Do you pick up on social hierarchies?", "type": "scale"},
            {"id": "SD11", "text": "How do you handle being the outsider?", "type": "text"},
            {"id": "SD12", "text": "What makes you trust someone quickly?", "type": "text"},
            {"id": "SD13", "text": "What makes you distrust someone immediately?", "type": "text"},
            {"id": "SD14", "text": "How do you handle social obligations?", "type": "text"},
            {"id": "SD15", "text": "Are you good at reading people?", "type": "scale"},
            
            # Influence and Power (15 questions)
            {"id": "SD16", "text": "How do you influence others?", "type": "text"},
            {"id": "SD17", "text": "How do you feel about persuasion tactics?", "type": "text"},
            {"id": "SD18", "text": "Do you like having power over others?", "type": "scale"},
            {"id": "SD19", "text": "How do you handle being in charge?", "type": "text"},
            {"id": "SD20", "text": "How do you respond to authority figures?", "type": "text"},
            {"id": "SD21", "text": "Do you push back against unfair authority?", "type": "scale"},
            {"id": "SD22", "text": "How do you handle power imbalances?", "type": "text"},
            {"id": "SD23", "text": "Do you use social status or reject it?", "type": "text"},
            {"id": "SD24", "text": "How do you negotiate?", "type": "text"},
            {"id": "SD25", "text": "What's your relationship with status and hierarchy?", "type": "text"},
            
            # Boundaries (15 questions)
            {"id": "SD26", "text": "How good are you at setting boundaries?", "type": "scale"},
            {"id": "SD27", "text": "What boundaries are non-negotiable for you?", "type": "text"},
            {"id": "SD28", "text": "How do you enforce boundaries?", "type": "text"},
            {"id": "SD29", "text": "How do you handle boundary violations?", "type": "text"},
            {"id": "SD30", "text": "Do you respect others' boundaries?", "type": "scale"},
            {"id": "SD31", "text": "What boundaries do you struggle with?", "type": "text"},
            {"id": "SD32", "text": "How do you say no?", "type": "text"},
            {"id": "SD33", "text": "Do you over-give or under-give in relationships?", "type": "text"},
            {"id": "SD34", "text": "How do you balance self vs others?", "type": "text"},
            {"id": "SD35", "text": "What are your emotional boundaries?", "type": "text"},
        ]
    },
    
    # =========================================================================
    # SECTION 19: CREATIVITY AND IMAGINATION (~40 questions)
    # =========================================================================
    "creativity": {
        "name": "Creativity and Imagination",
        "description": "Your creative process and imaginative tendencies",
        "questions": [
            # Creative Process (20 questions)
            {"id": "CR1", "text": "Describe your creative process.", "type": "text"},
            {"id": "CR2", "text": "Where do your best ideas come from?", "type": "text"},
            {"id": "CR3", "text": "What conditions help you be creative?", "type": "text"},
            {"id": "CR4", "text": "What blocks your creativity?", "type": "text"},
            {"id": "CR5", "text": "Do you prefer creating alone or collaboratively?", "type": "choice", "options": ["Strongly prefer alone", "Mostly alone", "Both equally", "Mostly collaborative", "Strongly prefer collaborative"]},
            {"id": "CR6", "text": "How do you handle creative blocks?", "type": "text"},
            {"id": "CR7", "text": "Do you finish creative projects?", "type": "scale"},
            {"id": "CR8", "text": "What's your relationship between creativity and discipline?", "type": "text"},
            {"id": "CR9", "text": "Do you create for yourself or for an audience?", "type": "choice", "options": ["Always for myself", "Mostly for myself", "Both equally", "Mostly for audience", "Always for audience"]},
            {"id": "CR10", "text": "What's the most creative thing you've made?", "type": "text"},
            {"id": "CR11", "text": "How do you know when something is 'good'?", "type": "text"},
            {"id": "CR12", "text": "Do you share your creative work?", "type": "scale"},
            {"id": "CR13", "text": "How do you handle creative criticism?", "type": "text"},
            {"id": "CR14", "text": "What inspires you?", "type": "text"},
            {"id": "CR15", "text": "How do you cultivate creativity?", "type": "text"},
            
            # Imagination (15 questions)
            {"id": "CR16", "text": "How vivid is your imagination?", "type": "scale"},
            {"id": "CR17", "text": "Do you have a rich inner world?", "type": "scale"},
            {"id": "CR18", "text": "What do you daydream about?", "type": "text"},
            {"id": "CR19", "text": "Do you have elaborate fantasies?", "type": "scale"},
            {"id": "CR20", "text": "Can you visualize things clearly?", "type": "scale"},
            {"id": "CR21", "text": "What role does imagination play in your daily life?", "type": "text"},
            {"id": "CR22", "text": "Do you prefer reality or imagination?", "type": "choice", "options": ["Strongly prefer reality", "Lean reality", "Both equally", "Lean imagination", "Strongly prefer imagination"]},
            {"id": "CR23", "text": "What fictional worlds have you immersed yourself in?", "type": "text"},
            {"id": "CR24", "text": "Do you ever confuse imagination with reality?", "type": "scale"},
            {"id": "CR25", "text": "How do you balance practicality and imagination?", "type": "text"},
        ]
    },
    
    # =========================================================================
    # SECTION 20: GROWTH AND CHANGE (~40 questions)
    # =========================================================================
    "growth": {
        "name": "Growth and Change",
        "description": "How you evolve, adapt, and grow",
        "questions": [
            # Personal Growth (20 questions)
            {"id": "GR1", "text": "How have you grown in the last 5 years?", "type": "text"},
            {"id": "GR2", "text": "What's your approach to self-improvement?", "type": "text"},
            {"id": "GR3", "text": "What aspects of yourself are you actively working on?", "type": "text"},
            {"id": "GR4", "text": "How do you measure personal growth?", "type": "text"},
            {"id": "GR5", "text": "What's the hardest thing you've changed about yourself?", "type": "text"},
            {"id": "GR6", "text": "Do you believe people can fundamentally change?", "type": "scale"},
            {"id": "GR7", "text": "What would you like to become?", "type": "text"},
            {"id": "GR8", "text": "What's holding you back from growth?", "type": "text"},
            {"id": "GR9", "text": "How do you handle setbacks in personal growth?", "type": "text"},
            {"id": "GR10", "text": "What habits are you trying to build?", "type": "text"},
            {"id": "GR11", "text": "What habits are you trying to break?", "type": "text"},
            {"id": "GR12", "text": "How do you stay accountable to yourself?", "type": "text"},
            {"id": "GR13", "text": "What does your best self look like?", "type": "text"},
            {"id": "GR14", "text": "What's the gap between you now and your best self?", "type": "text"},
            {"id": "GR15", "text": "How patient are you with your own growth?", "type": "scale"},
            
            # Adaptability (15 questions)
            {"id": "GR16", "text": "How well do you adapt to change?", "type": "scale"},
            {"id": "GR17", "text": "What major life changes have you navigated?", "type": "text"},
            {"id": "GR18", "text": "How do you handle unexpected change?", "type": "text"},
            {"id": "GR19", "text": "Do you embrace or resist change?", "type": "choice", "options": ["Eagerly embrace", "Generally embrace", "Depends on the change", "Generally resist", "Strongly resist"]},
            {"id": "GR20", "text": "What change are you most afraid of?", "type": "text"},
            {"id": "GR21", "text": "How quickly do you bounce back?", "type": "scale"},
            {"id": "GR22", "text": "What makes you resilient?", "type": "text"},
            {"id": "GR23", "text": "How do you handle transitions?", "type": "text"},
            {"id": "GR24", "text": "What change do you need to make but haven't?", "type": "text"},
            {"id": "GR25", "text": "How do you prepare for the future?", "type": "text"},
        ]
    },
    
    # =========================================================================
    # SECTION 21: SPECIFIC DOMAIN KNOWLEDGE (~50 questions)
    # =========================================================================
    "domain_knowledge": {
        "name": "Domain Knowledge and Expertise",
        "description": "Your areas of expertise and knowledge depth",
        "questions": [
            # Professional Expertise (20 questions)
            {"id": "DK1", "text": "What are you an expert in?", "type": "text"},
            {"id": "DK2", "text": "How did you develop your expertise?", "type": "text"},
            {"id": "DK3", "text": "What topics could you teach?", "type": "text"},
            {"id": "DK4", "text": "What's your professional specialty?", "type": "text"},
            {"id": "DK5", "text": "How do you stay current in your field?", "type": "text"},
            {"id": "DK6", "text": "What's a common misconception in your field?", "type": "text"},
            {"id": "DK7", "text": "What's cutting edge in your domain?", "type": "text"},
            {"id": "DK8", "text": "What do you know that most people don't?", "type": "text"},
            {"id": "DK9", "text": "What's your hot take in your field?", "type": "text"},
            {"id": "DK10", "text": "Who do you learn from?", "type": "text"},
            
            # General Knowledge Interests (20 questions)
            {"id": "DK11", "text": "What topics fascinate you?", "type": "text"},
            {"id": "DK12", "text": "What rabbit holes have you gone down?", "type": "text"},
            {"id": "DK13", "text": "What would you like to know more about?", "type": "text"},
            {"id": "DK14", "text": "What subjects did you love in school?", "type": "text"},
            {"id": "DK15", "text": "What subjects did you hate?", "type": "text"},
            {"id": "DK16", "text": "How broad vs deep is your knowledge?", "type": "text"},
            {"id": "DK17", "text": "What's the most useless thing you know a lot about?", "type": "text"},
            {"id": "DK18", "text": "What's your knowledge gap that embarrasses you?", "type": "text"},
            {"id": "DK19", "text": "How do you learn best?", "type": "text"},
            {"id": "DK20", "text": "What would you study if you could go back to school?", "type": "text"},
            
            # Skills Assessment (10 questions)
            {"id": "DK21", "text": "Rate your technical/hard skills.", "type": "text"},
            {"id": "DK22", "text": "Rate your soft/interpersonal skills.", "type": "text"},
            {"id": "DK23", "text": "What skills come naturally to you?", "type": "text"},
            {"id": "DK24", "text": "What skills did you have to work hard to develop?", "type": "text"},
            {"id": "DK25", "text": "What skills do you want to acquire?", "type": "text"},
        ]
    },
    
    # =========================================================================
    # SECTION 22: HUMOR AND PLAY (~30 questions)
    # =========================================================================
    "humor": {
        "name": "Humor and Play",
        "description": "What makes you laugh and how you play",
        "questions": [
            # Humor Style (20 questions)
            {"id": "HM1", "text": "What kind of humor do you like?", "type": "text"},
            {"id": "HM2", "text": "Do you joke around a lot?", "type": "scale"},
            {"id": "HM3", "text": "What makes you genuinely laugh out loud?", "type": "text"},
            {"id": "HM4", "text": "Do you use self-deprecating humor?", "type": "scale"},
            {"id": "HM5", "text": "How do you use humor in conversation?", "type": "text"},
            {"id": "HM6", "text": "What's your sense of humor like?", "type": "text"},
            {"id": "HM7", "text": "Do you appreciate dark humor?", "type": "scale"},
            {"id": "HM8", "text": "What comedians do you like?", "type": "text"},
            {"id": "HM9", "text": "Do you tell jokes or stories?", "type": "choice", "options": ["Mostly jokes", "More jokes than stories", "Both equally", "More stories than jokes", "Mostly stories"]},
            {"id": "HM10", "text": "How do you handle jokes that offend you?", "type": "text"},
            {"id": "HM11", "text": "Can you laugh at yourself?", "type": "scale"},
            {"id": "HM12", "text": "What's the funniest thing you've experienced?", "type": "text"},
            {"id": "HM13", "text": "Do you make people laugh?", "type": "scale"},
            {"id": "HM14", "text": "What's your go-to type of joke?", "type": "text"},
            {"id": "HM15", "text": "How important is humor in your relationships?", "type": "scale"},
            
            # Play and Fun (15 questions)
            {"id": "HM16", "text": "How do you play and have fun?", "type": "text"},
            {"id": "HM17", "text": "Do you prioritize fun?", "type": "scale"},
            {"id": "HM18", "text": "What's your relationship with spontaneity?", "type": "text"},
            {"id": "HM19", "text": "When were you last truly playful?", "type": "text"},
            {"id": "HM20", "text": "What games do you enjoy?", "type": "text"},
            {"id": "HM21", "text": "How competitive are you in games?", "type": "scale"},
            {"id": "HM22", "text": "What brings you pure joy?", "type": "text"},
            {"id": "HM23", "text": "Do you allow yourself to be silly?", "type": "scale"},
            {"id": "HM24", "text": "What childlike qualities do you retain?", "type": "text"},
            {"id": "HM25", "text": "How do you balance work and play?", "type": "text"},
        ]
    },
    
    # =========================================================================
    # SECTION 23: TECHNOLOGY AND TOOLS (~50 questions)
    # =========================================================================
    "technology": {
        "name": "Technology and Tools",
        "description": "Your relationship with technology and digital tools",
        "questions": [
            # Tech Philosophy (15 questions)
            {"id": "TC1", "text": "How do you feel about technology in general?", "type": "text"},
            {"id": "TC2", "text": "Are you an early adopter or do you wait?", "type": "choice", "options": ["Always early adopter", "Usually early", "Depends on the tech", "Usually wait", "Always wait for proven tech"]},
            {"id": "TC3", "text": "What technology has changed your life most?", "type": "text"},
            {"id": "TC4", "text": "What tech do you refuse to use?", "type": "text"},
            {"id": "TC5", "text": "How do you feel about AI?", "type": "text"},
            {"id": "TC6", "text": "Privacy vs convenience - where do you fall?", "type": "choice", "options": ["Privacy is paramount", "Lean toward privacy", "Balance of both", "Lean toward convenience", "Convenience is paramount"]},
            {"id": "TC7", "text": "How dependent are you on technology?", "type": "scale"},
            {"id": "TC8", "text": "What's your biggest tech frustration?", "type": "text"},
            {"id": "TC9", "text": "How do you learn new technology?", "type": "text"},
            {"id": "TC10", "text": "What tech trends excite you?", "type": "text"},
            
            # Tools and Software (20 questions)
            {"id": "TC11", "text": "What's your tech setup (devices, OS)?", "type": "text"},
            {"id": "TC12", "text": "What software do you use daily?", "type": "text"},
            {"id": "TC13", "text": "What's your favorite app?", "type": "text"},
            {"id": "TC14", "text": "How do you organize digital files?", "type": "text"},
            {"id": "TC15", "text": "What productivity tools do you use?", "type": "text"},
            {"id": "TC16", "text": "How do you manage passwords?", "type": "text"},
            {"id": "TC17", "text": "What's your backup strategy?", "type": "text"},
            {"id": "TC18", "text": "Do you automate things?", "type": "text"},
            {"id": "TC19", "text": "What keyboard shortcuts do you use?", "type": "text"},
            {"id": "TC20", "text": "How customized is your setup?", "type": "scale"},
            
            # Digital Habits (15 questions)
            {"id": "TC21", "text": "How many unread emails do you have?", "type": "number"},
            {"id": "TC22", "text": "How do you handle digital clutter?", "type": "text"},
            {"id": "TC23", "text": "Do you do digital detoxes?", "type": "frequency"},
            {"id": "TC24", "text": "How do you manage screen time?", "type": "text"},
            {"id": "TC25", "text": "What's your social media philosophy?", "type": "text"},
            {"id": "TC26", "text": "How do you handle tech problems?", "type": "text"},
            {"id": "TC27", "text": "Do you read terms of service?", "type": "yesno"},
            {"id": "TC28", "text": "How careful are you about cybersecurity?", "type": "scale"},
            {"id": "TC29", "text": "What online communities are you part of?", "type": "text"},
            {"id": "TC30", "text": "How do you curate your digital experience?", "type": "text"},
        ]
    },
    
    # =========================================================================
    # SECTION 24: CONFLICT AND RESOLUTION (~40 questions)
    # =========================================================================
    "conflict": {
        "name": "Conflict and Resolution",
        "description": "How you handle disagreements, arguments, and tensions",
        "questions": [
            # Conflict Style (20 questions)
            {"id": "CF1", "text": "How do you typically handle conflict?", "type": "text"},
            {"id": "CF2", "text": "Do you avoid, accommodate, compete, compromise, or collaborate?", "type": "choice", "options": ["Avoid", "Accommodate", "Compete", "Compromise", "Collaborate", "Depends"]},
            {"id": "CF3", "text": "How quickly do you get angry?", "type": "scale"},
            {"id": "CF4", "text": "What triggers you into conflict?", "type": "text"},
            {"id": "CF5", "text": "How do you calm down after conflict?", "type": "text"},
            {"id": "CF6", "text": "Do you hold grudges?", "type": "scale"},
            {"id": "CF7", "text": "How do you forgive?", "type": "text"},
            {"id": "CF8", "text": "Do you confront issues directly?", "type": "scale"},
            {"id": "CF9", "text": "How do you handle passive-aggression?", "type": "text"},
            {"id": "CF10", "text": "What's your fighting style in relationships?", "type": "text"},
            {"id": "CF11", "text": "Do you apologize easily?", "type": "scale"},
            {"id": "CF12", "text": "How do you know when to pick your battles?", "type": "text"},
            {"id": "CF13", "text": "What's worth fighting for?", "type": "text"},
            {"id": "CF14", "text": "What's not worth fighting for?", "type": "text"},
            {"id": "CF15", "text": "How do you de-escalate situations?", "type": "text"},
            
            # Resolution (15 questions)
            {"id": "CF16", "text": "How do you repair relationships after conflict?", "type": "text"},
            {"id": "CF17", "text": "What does 'moving on' mean to you?", "type": "text"},
            {"id": "CF18", "text": "Do you need closure?", "type": "scale"},
            {"id": "CF19", "text": "How do you handle ongoing tensions?", "type": "text"},
            {"id": "CF20", "text": "What have you learned from past conflicts?", "type": "text"},
            {"id": "CF21", "text": "How do you rebuild trust?", "type": "text"},
            {"id": "CF22", "text": "Can you agree to disagree?", "type": "scale"},
            {"id": "CF23", "text": "How do you mediate between others?", "type": "text"},
            {"id": "CF24", "text": "What's your biggest conflict regret?", "type": "text"},
            {"id": "CF25", "text": "What's a conflict you resolved well?", "type": "text"},
        ]
    },
    
    # =========================================================================
    # SECTION 25: ASPIRATIONS AND DREAMS (~40 questions)
    # =========================================================================
    "aspirations": {
        "name": "Aspirations and Dreams",
        "description": "Your hopes, dreams, and vision for the future",
        "questions": [
            # Life Goals (20 questions)
            {"id": "AS1", "text": "What's your biggest life goal?", "type": "text"},
            {"id": "AS2", "text": "What do you want to accomplish before you die?", "type": "text"},
            {"id": "AS3", "text": "What's on your bucket list?", "type": "text"},
            {"id": "AS4", "text": "Where do you see yourself in 10 years?", "type": "text"},
            {"id": "AS5", "text": "What's your dream job?", "type": "text"},
            {"id": "AS6", "text": "What's your dream life look like?", "type": "text"},
            {"id": "AS7", "text": "What would you do with unlimited resources?", "type": "text"},
            {"id": "AS8", "text": "What impact do you want to have?", "type": "text"},
            {"id": "AS9", "text": "What do you want to be remembered for?", "type": "text"},
            {"id": "AS10", "text": "What's holding you back from your dreams?", "type": "text"},
            {"id": "AS11", "text": "What dreams have you given up on?", "type": "text"},
            {"id": "AS12", "text": "What new dreams have emerged?", "type": "text"},
            {"id": "AS13", "text": "How realistic are you about goals?", "type": "scale"},
            {"id": "AS14", "text": "Do you set concrete goals or live more fluidly?", "type": "choice", "options": ["Always concrete goals", "Usually have goals", "Mix of both", "Usually fluid", "Live very fluidly"]},
            {"id": "AS15", "text": "What would make you feel successful?", "type": "text"},
            
            # Future Vision (15 questions)
            {"id": "AS16", "text": "What are you most hopeful about?", "type": "text"},
            {"id": "AS17", "text": "What are you most worried about for the future?", "type": "text"},
            {"id": "AS18", "text": "What would you change about the world?", "type": "text"},
            {"id": "AS19", "text": "How optimistic are you about your future?", "type": "scale"},
            {"id": "AS20", "text": "What's the ideal version of your life?", "type": "text"},
            {"id": "AS21", "text": "What sacrifices are you willing to make for your dreams?", "type": "text"},
            {"id": "AS22", "text": "How do you balance dreaming and doing?", "type": "text"},
            {"id": "AS23", "text": "What would you tell your future self?", "type": "text"},
            {"id": "AS24", "text": "What gives you hope?", "type": "text"},
            {"id": "AS25", "text": "What would an ideal average day look like?", "type": "text"},
        ]
    },
    
    # =========================================================================
    # SECTION 26: FINAL DEEP DIVE (~50 questions)
    # =========================================================================
    "final_deep_dive": {
        "name": "Final Deep Dive",
        "description": "The deepest, most personal questions to complete your engram",
        "questions": [
            # Core Identity (20 questions)
            {"id": "FD1", "text": "Who are you at your core, when nobody's watching?", "type": "text"},
            {"id": "FD2", "text": "What makes you feel most alive?", "type": "text"},
            {"id": "FD3", "text": "What's the one thing you want people to know about you?", "type": "text"},
            {"id": "FD4", "text": "What do you struggle with that nobody knows?", "type": "text"},
            {"id": "FD5", "text": "What's your internal narrative about yourself?", "type": "text"},
            {"id": "FD6", "text": "What would you never tell anyone in person?", "type": "text"},
            {"id": "FD7", "text": "What truth about yourself have you been avoiding?", "type": "text"},
            {"id": "FD8", "text": "What's your relationship with loneliness?", "type": "text"},
            {"id": "FD9", "text": "What do you love about yourself?", "type": "text"},
            {"id": "FD10", "text": "What do you genuinely dislike about yourself?", "type": "text"},
            {"id": "FD11", "text": "What would it take for you to be truly happy?", "type": "text"},
            {"id": "FD12", "text": "What would break you?", "type": "text"},
            {"id": "FD13", "text": "What heals you?", "type": "text"},
            {"id": "FD14", "text": "What's the lie you tell yourself most often?", "type": "text"},
            {"id": "FD15", "text": "What's the truth you keep coming back to?", "type": "text"},
            
            # Hypotheticals and Thought Experiments (20 questions)
            {"id": "FD16", "text": "If you could live any life, what would it be?", "type": "text"},
            {"id": "FD17", "text": "If you could change one decision, what would it be?", "type": "text"},
            {"id": "FD18", "text": "If you had one year to live, what would you do?", "type": "text"},
            {"id": "FD19", "text": "If you could have dinner with anyone, who?", "type": "text"},
            {"id": "FD20", "text": "If you could master any skill instantly, which?", "type": "text"},
            {"id": "FD21", "text": "If you could solve one world problem, which?", "type": "text"},
            {"id": "FD22", "text": "If you could relive one moment, which?", "type": "text"},
            {"id": "FD23", "text": "If you could erase one memory, would you? Which?", "type": "text"},
            {"id": "FD24", "text": "If you could read minds, would you want to?", "type": "text"},
            {"id": "FD25", "text": "If you could be invisible for a day, what would you do?", "type": "text"},
            
            # Final Reflections (10 questions)
            {"id": "FD26", "text": "What's the most important thing in life?", "type": "text"},
            {"id": "FD27", "text": "What have you figured out that others haven't?", "type": "text"},
            {"id": "FD28", "text": "What's your philosophy of life in one sentence?", "type": "text"},
            {"id": "FD29", "text": "What advice would you give to anyone?", "type": "text"},
            {"id": "FD30", "text": "What question do you wish I had asked?", "type": "text"},
            {"id": "FD31", "text": "If Abby is to think like you, what's the one thing she MUST understand?", "type": "text"},
            {"id": "FD32", "text": "What makes you, YOU?", "type": "text"},
            {"id": "FD33", "text": "Anything else you want to add to your engram?", "type": "text"},
        ]
    },
}

# ==============================================================================
# QUESTION COUNTER
# ==============================================================================

def count_all_questions():
    """Count total questions in the bank"""
    total = 0
    for category, data in QUESTION_BANK.items():
        total += len(data["questions"])
        print(f"{category}: {len(data['questions'])} questions")
    print(f"\nTOTAL: {total} questions")
    return total


# ==============================================================================
# INTERACTIVE CLI
# ==============================================================================

class DeepEngramBuilder:
    """Interactive CLI for building a deep personality engram"""
    
    def __init__(self):
        self.answers: Dict[str, Any] = {}
        self.current_category = None
        self.save_path = "config/engrams"
        self.session_file = None
        os.makedirs(self.save_path, exist_ok=True)
    
    def auto_save(self):
        """Auto-save current progress"""
        if self.session_file:
            with open(self.session_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.answers, f, default_flow_style=False, allow_unicode=True)
    
    def run(self):
        """Run the interactive questionnaire"""
        self.show_intro()
        
        # Check for existing sessions first
        existing = [f for f in os.listdir(self.save_path) if f.endswith('.yaml')]
        
        if existing:
            print("\n📁 Found saved sessions:")
            for i, f in enumerate(existing, 1):
                # Show progress for each
                try:
                    with open(os.path.join(self.save_path, f), 'r', encoding='utf-8') as file:
                        data = yaml.safe_load(file)
                        answered = sum(len(v) for v in data.get("responses", {}).values())
                        total = sum(len(d["questions"]) for d in QUESTION_BANK.values())
                        name = data.get("subject_name", "Unknown")
                        print(f"  {i}. {f} - {name} ({answered}/{total} questions)")
                except:
                    print(f"  {i}. {f}")
            
            print(f"  {len(existing)+1}. Start NEW session")
            
            choice = input("\nLoad which session? ").strip()
            try:
                idx = int(choice) - 1
                if idx < len(existing):
                    self.session_file = os.path.join(self.save_path, existing[idx])
                    with open(self.session_file, 'r', encoding='utf-8') as f:
                        self.answers = yaml.safe_load(f)
                    print(f"\n✓ Loaded session for {self.answers.get('subject_name', 'Unknown')}")
                    self.continue_existing_session()
                    return
            except:
                pass
        
        # New session
        name = input("\nWhat's your name? ").strip()
        if not name:
            name = "User"
        
        self.session_file = os.path.join(self.save_path, f"{name.lower().replace(' ', '_')}_engram.yaml")
        self.answers["subject_name"] = name
        self.answers["created_at"] = datetime.now().isoformat()
        self.answers["responses"] = {}
        
        # Ask about session preference
        print(f"\nHey {name}! This questionnaire has {count_all_questions()} questions.")
        print("You can:")
        print("  1. Do a QUICK session (~100 key questions)")
        print("  2. Do a FULL session (all questions)")
        print("  3. Do it in SECTIONS (pick categories)")
        
        choice = input("\nYour choice (1/2/3): ").strip()
        
        if choice == "1":
            self.run_quick_session()
        elif choice == "2":
            self.run_full_session()
        elif choice == "3":
            self.run_section_session()
        else:
            print("Invalid choice, running quick session...")
            self.run_quick_session()
        
        self.auto_save()
        self.show_summary()
    
    def continue_existing_session(self):
        """Continue an existing session from where it left off"""
        answered_categories = set(self.answers.get("responses", {}).keys())
        all_categories = list(QUESTION_BANK.keys())
        
        # Find first incomplete category
        incomplete_cats = []
        for cat in all_categories:
            cat_questions = QUESTION_BANK[cat]["questions"]
            answered_in_cat = len(self.answers.get("responses", {}).get(cat, {}))
            if answered_in_cat < len(cat_questions):
                incomplete_cats.append((cat, answered_in_cat, len(cat_questions)))
        
        if not incomplete_cats:
            print("\n✓ All categories complete!")
            self.show_summary()
            return
        
        print(f"\n📊 Progress: {len(answered_categories)}/{len(all_categories)} categories started")
        print("\nIncomplete categories:")
        for i, (cat, done, total) in enumerate(incomplete_cats, 1):
            data = QUESTION_BANK[cat]
            print(f"  {i}. {data['name']} ({done}/{total} questions)")
        
        print(f"\nPress Enter to continue with '{QUESTION_BANK[incomplete_cats[0][0]]['name']}'")
        print("Or type a number to jump to that category")
        
        choice = input("> ").strip()
        
        if choice:
            try:
                idx = int(choice) - 1
                cat_to_continue = incomplete_cats[idx][0]
            except:
                cat_to_continue = incomplete_cats[0][0]
        else:
            cat_to_continue = incomplete_cats[0][0]
        
        # Continue from this category onwards
        start_idx = all_categories.index(cat_to_continue)
        for cat in all_categories[start_idx:]:
            self.ask_category_questions(cat)
        
        self.auto_save()
        self.show_summary()
    
    def show_intro(self):
        """Show introduction"""
        print("\n" + "="*70)
        print("           DEEP ENGRAM BUILDER")
        print("     Creating Your Digital Personality Clone")
        print("="*70)
        print("""
This questionnaire will create a comprehensive psychological profile 
that enables an AI to authentically replicate your:

  • Thinking patterns
  • Communication style  
  • Emotional reactions
  • Values and beliefs
  • Decision-making process
  • Unique personality quirks

BE HONEST. There are no right answers. Skip anything you don't 
want to answer. The more authentic you are, the better the clone.
""")
    
    def run_quick_session(self):
        """Run a shortened version with key questions"""
        key_categories = [
            "openness", "conscientiousness", "extraversion", 
            "agreeableness", "neuroticism", "communication",
            "thinking_style", "quirks"
        ]
        
        for cat in key_categories:
            if cat in QUESTION_BANK:
                # Ask first 10 questions from each category
                self.ask_category_questions(cat, limit=10)
    
    def run_full_session(self):
        """Run all questions"""
        for category in QUESTION_BANK:
            self.ask_category_questions(category)
    
    def run_section_session(self):
        """Let user pick sections"""
        print("\nAvailable sections:")
        categories = list(QUESTION_BANK.keys())
        for i, cat in enumerate(categories, 1):
            data = QUESTION_BANK[cat]
            print(f"  {i}. {data['name']} ({len(data['questions'])} questions)")
        
        print("\nEnter section numbers separated by commas (e.g., 1,3,5)")
        print("Or 'all' for everything")
        
        choice = input("Your choice: ").strip()
        
        if choice.lower() == "all":
            selected = categories
        else:
            try:
                indices = [int(x.strip())-1 for x in choice.split(",")]
                selected = [categories[i] for i in indices if 0 <= i < len(categories)]
            except:
                selected = categories[:3]
        
        for cat in selected:
            self.ask_category_questions(cat)
    
    def ask_category_questions(self, category: str, limit: int = None):
        """Ask questions from a category"""
        if category not in QUESTION_BANK:
            return
        
        data = QUESTION_BANK[category]
        questions = data["questions"]
        if limit:
            questions = questions[:limit]
        
        # Get already answered questions in this category
        already_answered = self.answers.get("responses", {}).get(category, {})
        remaining_questions = [q for q in questions if q["id"] not in already_answered]
        
        if not remaining_questions:
            print(f"\n✓ {data['name']} - Already complete!")
            return
        
        print(f"\n{'='*60}")
        print(f" {data['name'].upper()}")
        print(f" {data['description']}")
        print(f"{'='*60}")
        
        if already_answered:
            print(f"(Resuming - {len(already_answered)}/{len(questions)} already done)")
        
        print(f"({len(remaining_questions)} questions - type 'skip' to skip, 'quit' to save & exit)\n")
        
        if category not in self.answers.get("responses", {}):
            self.answers.setdefault("responses", {})[category] = {}
        
        start_num = len(already_answered) + 1
        for i, q in enumerate(remaining_questions, start_num):
            answer = self.ask_question(q, i, len(questions))
            
            if answer == "QUIT":
                self.auto_save()
                print(f"\n💾 Progress saved! ({i-1}/{len(questions)} in this category)")
                raise KeyboardInterrupt
            
            if answer != "SKIP":
                self.answers["responses"][category][q["id"]] = answer
        
        # Auto-save after completing each category
        self.auto_save()
        print(f"\n💾 Category saved! ({len(self.answers['responses'][category])}/{len(questions)} answered)")
    
    def ask_question(self, question: dict, num: int, total: int) -> str:
        """Ask a single question and get answer"""
        q_type = question.get("type", "text")
        q_text = question["text"]
        
        print(f"\n[{num}/{total}] {q_text}")
        
        # Show options for choice questions
        if q_type == "choice" and "options" in question:
            for i, opt in enumerate(question["options"], 1):
                print(f"   {i}. {opt}")
        elif q_type == "scale":
            print("   (1-10 scale: 1=not at all, 10=very much)")
        elif q_type == "frequency":
            print("   (never / rarely / sometimes / often / always)")
        elif q_type == "yesno":
            print("   (yes / no)")
        
        answer = input("> ").strip()
        
        if answer.lower() == "skip":
            return "SKIP"
        if answer.lower() == "quit":
            return "QUIT"
        
        # Validate and process answer
        if q_type == "scale":
            try:
                return int(answer)
            except:
                return answer
        elif q_type == "number":
            try:
                return float(answer)
            except:
                return answer
        elif q_type == "choice" and "options" in question:
            try:
                idx = int(answer) - 1
                return question["options"][idx]
            except:
                return answer
        elif q_type == "yesno":
            return answer.lower() in ["yes", "y", "true", "1"]
        
        return answer
    
    def show_summary(self):
        """Show summary of completed questionnaire"""
        total_questions = sum(len(d["questions"]) for d in QUESTION_BANK.values())
        answered = sum(len(v) for v in self.answers.get("responses", {}).values())
        
        print(f"\n{'='*60}")
        print(" ENGRAM SESSION SUMMARY")
        print(f"{'='*60}")
        print(f" Questions answered: {answered}/{total_questions}")
        print(f" Categories covered: {len(self.answers.get('responses', {}))}/{len(QUESTION_BANK)}")
        if self.session_file:
            print(f" Saved to: {self.session_file}")
        print(f"\n Run again anytime to continue where you left off!")
        print(" Load it into Abby's brain_clone to activate!")
        print(f"{'='*60}\n")


# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == "__main__":
    print("Counting questions...")
    total = count_all_questions()
    
    print(f"\n🧠 Deep Engram Builder - {total} questions ready")
    input("Press Enter to start the questionnaire...")
    
    try:
        builder = DeepEngramBuilder()
        builder.run()
    except KeyboardInterrupt:
        print("\n\nSession saved. Run again to continue!")
