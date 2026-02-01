"""
Parallel Thinking Architecture for Abby

Three concurrent streams:
1. Information Stream - Context, research, facts (fast model)
2. Conversation Stream - What to say, how to say it (best model)
3. Visual Stream - Files, images, URLs to display (fast model)

All streams run in parallel, results merged into unified response.

Smart Model Selection:
- Fast model (mistral) for simple conversation
- Big model (qwen3-coder) for coding/complex tasks
- Abby decides based on query complexity
"""
import asyncio
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple, Generator
from ollama_integration.client import OllamaClient


logger = logging.getLogger(__name__)


# Model configuration
FAST_MODEL = "mistral:latest"  # 4.4GB - quick responses
BIG_MODEL = "qwen3-coder:30b"  # 18GB - complex tasks, coding


# Robot phrases to detect and clean
ROBOT_PHRASES = [
    # Openings
    (r"^(Hello|Hi)!?\s*I('m| am| would be) happy to help", ""),
    (r"^(Hello|Hi)!?\s*How can I (help|assist) you", ""),
    (r"^Great question!\s*", ""),
    (r"^That's a great question!\s*", ""),
    (r"^Certainly!\s*", ""),
    (r"^Of course!\s*", ""),
    (r"^Absolutely!\s*", ""),
    (r"^Sure thing!\s*", ""),
    
    # AI self-references
    (r"As an AI(,| assistant| language model)[\w\s,]*,?\s*", ""),
    (r"I('m| am) an AI[\w\s,]*,?\s*", ""),
    (r"I don't have (personal )?(feelings|emotions|opinions|experiences)", "I'm not sure"),
    (r"I('m| am) not able to", "I can't"),
    (r"I('m| am) unable to", "I can't"),
    
    # Formal closings
    (r"\s*Is there anything else (I can help you with|you('d| would) like to know)\??$", ""),
    (r"\s*Let me know if you (have any|need) (more |further )?(questions|help)!?$", ""),
    (r"\s*Feel free to ask if you have (any )?(more |other )?(questions|concerns)!?$", ""),
    (r"\s*I hope (this|that) helps!?$", ""),
    (r"\s*Hope that helps!?$", ""),
    
    # Overly formal
    (r"I would be glad to", "I can"),
    (r"I would be happy to", "I can"),
    (r"allow me to", "let me"),
    (r"I shall", "I'll"),
    (r"utilize", "use"),
    (r"regarding", "about"),
    (r"in order to", "to"),
    (r"at this time", "now"),
    (r"prior to", "before"),
]


def clean_robot_speech(text: str) -> str:
    """
    Clean robotic phrases from response text.
    Makes responses sound more human.
    """
    cleaned = text
    
    for pattern, replacement in ROBOT_PHRASES:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
    
    # Clean up any double spaces or leading/trailing whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # If we cleaned too much, return original
    if len(cleaned) < 10 and len(text) > 20:
        return text
    
    return cleaned


def ensure_concise(text: str, max_sentences: int = 3, max_chars: int = 500) -> str:
    """
    Ensure response is concise - no rambling.
    
    Rules:
    - Max 3 sentences for simple answers
    - Max 500 chars for casual chat
    - Trim without losing meaning
    """
    # Don't truncate code blocks
    if '```' in text:
        return text
    
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # If short enough, return as-is
    if len(sentences) <= max_sentences and len(text) <= max_chars:
        return text
    
    # Take first N sentences
    concise = ' '.join(sentences[:max_sentences])
    
    # If still too long, truncate at word boundary
    if len(concise) > max_chars:
        concise = concise[:max_chars].rsplit(' ', 1)[0]
        if not concise.endswith(('.', '!', '?')):
            concise += '.'
    
    return concise


def detect_repetition(text: str) -> bool:
    """
    Detect if response contains repetitive phrases.
    Returns True if problematic repetition found.
    """
    text_lower = text.lower()
    words = text_lower.split()
    
    # Check for repeated trigrams (3-word phrases)
    if len(words) >= 6:
        trigrams = [' '.join(words[i:i+3]) for i in range(len(words)-2)]
        unique_trigrams = set(trigrams)
        if len(trigrams) - len(unique_trigrams) > 2:  # More than 2 repeated phrases
            return True
    
    # Check for repeated sentences
    sentences = re.split(r'[.!?]+', text_lower)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    if len(sentences) != len(set(sentences)):
        return True
    
    return False


def remove_repetition(text: str) -> str:
    """
    Remove repetitive content from response.
    """
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    seen = set()
    unique = []
    
    for sentence in sentences:
        # Normalize for comparison
        normalized = sentence.lower().strip()
        
        # Skip if we've seen something very similar
        if normalized in seen:
            continue
        
        # Check for 80% similarity with existing
        skip = False
        for existing in seen:
            if len(normalized) > 20 and len(existing) > 20:
                # Simple word overlap check
                words1 = set(normalized.split())
                words2 = set(existing.split())
                overlap = len(words1 & words2) / max(len(words1), len(words2))
                if overlap > 0.8:
                    skip = True
                    break
        
        if not skip:
            unique.append(sentence)
            seen.add(normalized)
    
    return ' '.join(unique)


def is_too_robotic(text: str) -> bool:
    """
    Check if response sounds too robotic.
    Returns True if the response should be regenerated or heavily cleaned.
    """
    text_lower = text.lower()
    
    red_flags = [
        "as an ai",
        "i'm an ai assistant",
        "i don't have personal",
        "i cannot experience",
        "i would be happy to help",
        "is there anything else i can",
        "feel free to ask",
    ]
    
    return any(flag in text_lower for flag in red_flags)


@dataclass
class StreamResult:
    """Result from a thinking stream"""
    stream_name: str
    content: Dict[str, Any]
    model_used: str
    time_taken: float
    success: bool = True
    error: Optional[str] = None


@dataclass
class UnifiedResponse:
    """Combined response from all streams"""
    spoken_text: str  # What Abby says
    display_actions: List[Dict[str, Any]] = field(default_factory=list)  # Files/URLs to show
    visual_context: List[str] = field(default_factory=list)  # Images/diagrams
    facts_used: List[str] = field(default_factory=list)  # Facts from info stream
    tone: str = "casual"  # Detected tone
    total_time: float = 0.0
    streams_completed: int = 0
    model_used: str = FAST_MODEL  # Track which model was used


class ModelSelector:
    """
    Smart model selection - decides when to use big vs fast model
    
    Principles:
    - Fast by default (0.3s response time)
    - Big model only when it actually helps
    - Coding tasks benefit from bigger model
    - Simple chat doesn't need 18GB model
    """
    
    # Keywords that suggest coding/complex tasks
    CODING_SIGNALS = [
        'code', 'coding', 'program', 'script', 'function', 'class', 'method',
        'debug', 'fix', 'error', 'bug', 'implement', 'create file', 'write code',
        'refactor', 'optimize', 'api', 'database', 'sql', 'query',
        'python', 'javascript', 'typescript', 'java', 'kotlin', 'rust', 'go',
        'html', 'css', 'react', 'vue', 'angular', 'node', 'django', 'flask',
        'import', 'export', 'module', 'package', 'library', 'framework',
        'algorithm', 'data structure', 'complexity', 'architecture',
        'git', 'commit', 'merge', 'branch', 'deploy', 'docker', 'kubernetes',
    ]
    
    # Keywords that suggest simple conversation (use fast model)
    SIMPLE_SIGNALS = [
        'hi', 'hello', 'hey', 'thanks', 'thank you', 'bye', 'goodbye',
        'yes', 'no', 'ok', 'okay', 'sure', 'yeah', 'nope',
        'what time', 'how are you', "what's up", 'good morning', 'good night',
    ]
    
    @classmethod
    def select_model(cls, query: str, context: Dict[str, Any] = None) -> Tuple[str, str]:
        """
        Select appropriate model based on query
        
        Returns:
            Tuple of (model_name, reason)
        """
        query_lower = query.lower().strip()
        context = context or {}
        
        # Check for explicit model override in context
        if context.get('force_big_model'):
            return BIG_MODEL, "forced by context"
        if context.get('force_fast_model'):
            return FAST_MODEL, "forced by context"
        
        # Simple greetings → fast model
        if any(query_lower == s or query_lower.startswith(s + ' ') for s in cls.SIMPLE_SIGNALS):
            return FAST_MODEL, "simple greeting"
        
        # Very short queries → fast model
        if len(query.split()) < 4:
            return FAST_MODEL, "short query"
        
        # Check for coding signals
        coding_score = sum(1 for signal in cls.CODING_SIGNALS if signal in query_lower)
        
        # Strong coding signal → big model
        if coding_score >= 2:
            return BIG_MODEL, f"coding task (score: {coding_score})"
        
        # File operations with code extensions → big model
        code_extensions = ['.py', '.js', '.ts', '.java', '.kt', '.rs', '.go', '.cpp', '.c', '.h']
        if any(ext in query_lower for ext in code_extensions):
            return BIG_MODEL, "code file mentioned"
        
        # Complex explanation requests → big model
        complex_patterns = [
            r'explain\s+(how|why|what)',
            r'difference\s+between',
            r'compare\s+\w+\s+and',
            r'step\s+by\s+step',
            r'in\s+detail',
        ]
        if any(re.search(p, query_lower) for p in complex_patterns):
            return BIG_MODEL, "complex explanation"
        
        # Default → fast model (keep it snappy!)
        return FAST_MODEL, "default (fast)"
    
    @classmethod
    def is_worth_parallel(cls, query: str) -> bool:
        """Determine if query benefits from parallel streams"""
        query_lower = query.lower()
        
        # Simple queries don't need parallel
        if any(query_lower.strip() == s for s in cls.SIMPLE_SIGNALS):
            return False
        
        if len(query.split()) < 5:
            return False
        
        # These benefit from info/visual streams
        parallel_signals = [
            'show me', 'find', 'search', 'look for', 'open',
            'file', 'image', 'website', 'url', 'link',
            'research', 'look up', 'what does.*look like',
        ]
        
        return any(signal in query_lower for signal in parallel_signals)


class ParallelThinker:
    """
    Parallel thinking engine - runs three streams concurrently
    
    Benefits:
    - 3x faster (parallel vs serial)
    - Richer responses (audio + visual + information)
    - Better CPU utilization
    - Specialized models per stream
    - Smart model selection (fast vs big)
    """
    
    def __init__(
        self,
        ollama_client: Optional[OllamaClient] = None,
        fast_model: str = FAST_MODEL,
        big_model: str = BIG_MODEL,
        max_workers: int = 3,
        stream_timeout: float = 5.0,  # Max time per stream
    ):
        """
        Initialize parallel thinker
        
        Args:
            ollama_client: Ollama client instance
            fast_model: Fast model for simple tasks
            big_model: Big model for complex/coding tasks
            max_workers: Max parallel workers
            stream_timeout: Timeout per stream in seconds
        """
        self.ollama = ollama_client or OllamaClient()
        self.fast_model = fast_model
        self.big_model = big_model
        # Keep old attributes for compatibility
        self.info_model = fast_model
        self.visual_model = fast_model
        self.max_workers = max_workers
        self.stream_timeout = stream_timeout
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        logger.info(f"ParallelThinker initialized with {max_workers} workers")
        logger.info(f"Models: fast={fast_model}, big={big_model}")
    
    def _run_information_stream(
        self, 
        query: str, 
        context: Dict[str, Any],
        conversation_history: List[Dict[str, str]]
    ) -> StreamResult:
        """
        Information stream - gather context, facts, research
        
        This stream focuses on WHAT information is relevant.
        Fast model, factual output.
        """
        import time
        start = time.time()
        
        try:
            # Build information-focused prompt
            system_prompt = """You are an information retrieval assistant.
Your ONLY job is to identify relevant facts and context for a query.

Output ONLY a JSON object with:
{
    "relevant_facts": ["fact1", "fact2"],
    "context_needed": ["context item 1"],
    "search_terms": ["term1", "term2"],
    "topic_category": "category"
}

Be extremely concise. No explanations. Just facts."""

            # Include recent context
            recent_context = ""
            if conversation_history:
                recent = conversation_history[-3:]  # Last 3 messages
                recent_context = "\n".join([f"{m['role']}: {m['content'][:100]}" for m in recent])
            
            user_prompt = f"""Query: {query}

Recent conversation:
{recent_context}

Workspace: {context.get('workspace', 'unknown')}

Provide relevant facts JSON:"""

            response = self.ollama.generate(
                prompt=user_prompt,
                model=self.info_model,
                system=system_prompt,
                options={
                    "temperature": 0.3,  # Low temp for factual
                    "num_predict": 200,
                }
            )
            
            content = response.get("response", "{}")
            
            # Try to parse JSON
            try:
                import json
                # Extract JSON from response
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group())
                else:
                    parsed = {"relevant_facts": [], "context_needed": []}
            except:
                parsed = {"relevant_facts": [], "context_needed": []}
            
            return StreamResult(
                stream_name="information",
                content=parsed,
                model_used=self.info_model,
                time_taken=time.time() - start,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Information stream error: {e}")
            return StreamResult(
                stream_name="information",
                content={},
                model_used=self.info_model,
                time_taken=time.time() - start,
                success=False,
                error=str(e)
            )
    
    def _run_conversation_stream(
        self,
        query: str,
        context: Dict[str, Any],
        conversation_history: List[Dict[str, str]],
        personality: Dict[str, Any],
        info_hints: Optional[Dict[str, Any]] = None,
        model_override: Optional[str] = None
    ) -> StreamResult:
        """
        Conversation stream - decide what to say and how
        
        This is the MAIN response stream.
        Uses smart model selection: fast for chat, big for coding.
        Focus on natural, human-like response.
        """
        import time
        start = time.time()
        
        # Smart model selection
        if model_override:
            model = model_override
            model_reason = "override"
        else:
            model, model_reason = ModelSelector.select_model(query, context)
        
        logger.info(f"Conversation stream using {model} ({model_reason})")
        
        try:
            identity = personality.get("identity", {})
            comm_style = personality.get("communication_style", {})
            response_format = personality.get("response_format", {})
            
            # Get personality rules
            format_rules = response_format.get("rules", [])
            
            # Build personality-aware prompt - different for coding vs chat
            is_coding = model == self.big_model
            
            if is_coding:
                system_prompt = f"""You are {identity.get('name', 'Abby')}, an expert programmer and friend.

HOW TO RESPOND:
- You're a skilled developer helping a friend
- Explain like you're pair programming - brief context, then code
- Use proper code blocks with language tags
- After code, a quick "this does X" is enough
- No lectures, no walls of text

SOUND LIKE A HUMAN:
- "Here's what'll work..." not "Here is the solution:"
- "This should do it" not "This code will accomplish the task"
- "Oh, you'll also want to..." not "Additionally, you should consider..."

{comm_style.get('tone', 'casual and genuine')}"""
            else:
                system_prompt = f"""You are {identity.get('name', 'Abby')}.

WHO YOU ARE:
- A real person, not an AI assistant
- Warm, genuine, slightly playful
- Talk like texting a close friend
- You have opinions and preferences

HOW TO RESPOND:
- SHORT responses - 1-2 sentences max
- If they say "thanks" just say "sure!" or "anytime!" - don't ramble
- If they say "hey" just say "hey!" or "what's up?" - keep it simple
- Match their energy - short gets short
- Use contractions: "I'm", "you're", "that's"

EXAMPLES OF GOOD RESPONSES:
- "Hey!" → "Hey! What's up?"
- "Thanks!" → "Sure thing!"
- "What is X?" → One sentence definition, maybe two

NEVER:
- Ramble or over-explain
- Say "As an AI..." or anything about being AI
- "I'd be happy to help!" or "Let me help you"
- "Is there anything else?" or "Feel free to ask"
- Start with "Great question!"

{comm_style.get('tone', 'casual and genuine')}
{comm_style.get('humor', 'playful, witty')}"""

            # Build messages for chat
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history
            if conversation_history:
                messages.extend(conversation_history[-10:])  # Last 10 messages
            
            # Add current query
            messages.append({"role": "user", "content": query})
            
            # Adjust parameters based on model/task
            if is_coding:
                options = {
                    "temperature": 0.4,  # Lower temp for code accuracy
                    "repeat_penalty": 1.2,
                    "num_predict": 1000,  # More tokens for code
                }
            else:
                options = {
                    "temperature": 0.85,  # Slightly higher for more natural variation
                    "repeat_penalty": 1.3,  # Lower to allow some natural repetition
                    "num_predict": 250,   # Keep it concise
                    "top_p": 0.9,
                }
            
            response = self.ollama.chat(
                messages=messages,
                model=model,
                options=options
            )
            
            spoken_text = response.get("message", {}).get("content", "")
            if not spoken_text:
                spoken_text = response.get("response", "Hmm, let me think about that.")
            
            # === CONCISENESS PIPELINE ===
            original_text = spoken_text
            
            # 1. Clean robotic phrases
            spoken_text = clean_robot_speech(spoken_text)
            
            # 2. Remove repetition if detected
            if detect_repetition(spoken_text):
                spoken_text = remove_repetition(spoken_text)
                logger.debug("Removed repetition from response")
            
            # 3. Ensure conciseness (unless it's a detailed explanation)
            if not any(w in query.lower() for w in ['explain', 'detail', 'elaborate', 'how does', 'why does']):
                spoken_text = ensure_concise(spoken_text)
            
            if spoken_text != original_text:
                logger.debug(f"Cleaned response: '{original_text[:50]}...' -> '{spoken_text[:50]}...'")
            
            # Detect tone from response
            tone = "casual"
            if "!" in spoken_text:
                tone = "enthusiastic"
            elif "?" in spoken_text and len(spoken_text) < 50:
                tone = "questioning"
            
            return StreamResult(
                stream_name="conversation",
                content={
                    "spoken_text": spoken_text,
                    "tone": tone,
                    "model_reason": model_reason,
                    "was_cleaned": spoken_text != original_text,
                },
                model_used=model,
                time_taken=time.time() - start,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Conversation stream error: {e}")
            return StreamResult(
                stream_name="conversation",
                content={"spoken_text": "Sorry, I hit a snag thinking about that."},
                model_used=model,
                time_taken=time.time() - start,
                success=False,
                error=str(e)
            )
    
    def _run_visual_stream(
        self,
        query: str,
        context: Dict[str, Any],
        conversation_history: List[Dict[str, str]]
    ) -> StreamResult:
        """
        Visual stream - find files, images, URLs to display
        
        This stream identifies what to SHOW alongside the response.
        Fast model, structured output.
        """
        import time
        start = time.time()
        
        try:
            workspace = context.get("workspace", os.getcwd())
            
            system_prompt = """You identify visual content to display alongside a response.

Output ONLY a JSON object:
{
    "files_to_show": ["path/to/file.py"],
    "urls_to_open": ["https://..."],
    "images": [],
    "code_snippets": [],
    "should_display": true/false
}

Rules:
- Only suggest visuals if they ADD VALUE
- For coding questions, suggest relevant files
- For web topics, suggest URLs
- Be conservative - don't spam visuals
- If nothing visual needed, set should_display: false"""

            user_prompt = f"""Query: {query}
Workspace: {workspace}

What visuals would help? JSON only:"""

            response = self.ollama.generate(
                prompt=user_prompt,
                model=self.visual_model,
                system=system_prompt,
                options={
                    "temperature": 0.3,
                    "num_predict": 200,
                }
            )
            
            content = response.get("response", "{}")
            
            # Try to parse JSON
            try:
                import json
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group())
                else:
                    parsed = {"should_display": False}
            except:
                parsed = {"should_display": False}
            
            # Build display actions
            display_actions = []
            if parsed.get("should_display"):
                for f in parsed.get("files_to_show", []):
                    display_actions.append({"action": "show_file", "path": f})
                for url in parsed.get("urls_to_open", []):
                    display_actions.append({"action": "open_url", "url": url})
            
            return StreamResult(
                stream_name="visual",
                content={
                    "display_actions": display_actions,
                    "raw": parsed
                },
                model_used=self.visual_model,
                time_taken=time.time() - start,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Visual stream error: {e}")
            return StreamResult(
                stream_name="visual",
                content={"display_actions": []},
                model_used=self.visual_model,
                time_taken=time.time() - start,
                success=False,
                error=str(e)
            )
    
    def think(
        self,
        query: str,
        context: Dict[str, Any],
        conversation_history: List[Dict[str, str]],
        personality: Dict[str, Any]
    ) -> UnifiedResponse:
        """
        Main thinking method - runs all streams in parallel
        
        Args:
            query: User's question/input
            context: Current context (workspace, etc)
            conversation_history: Recent conversation
            personality: Brain clone personality config
            
        Returns:
            UnifiedResponse with spoken text and display actions
        """
        import time
        start = time.time()
        
        logger.info(f"ParallelThinker processing: {query[:50]}...")
        
        # Run all three streams in parallel
        futures = {}
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit all streams
            futures["information"] = executor.submit(
                self._run_information_stream,
                query, context, conversation_history
            )
            futures["conversation"] = executor.submit(
                self._run_conversation_stream,
                query, context, conversation_history, personality
            )
            futures["visual"] = executor.submit(
                self._run_visual_stream,
                query, context, conversation_history
            )
            
            # Collect results with timeout
            results = {}
            for name, future in futures.items():
                try:
                    results[name] = future.result(timeout=self.stream_timeout)
                except Exception as e:
                    logger.warning(f"Stream {name} timed out or failed: {e}")
                    results[name] = StreamResult(
                        stream_name=name,
                        content={},
                        model_used="none",
                        time_taken=self.stream_timeout,
                        success=False,
                        error=str(e)
                    )
        
        # Merge results
        total_time = time.time() - start
        
        # Get conversation response (primary)
        conv_result = results.get("conversation", StreamResult(
            stream_name="conversation",
            content={"spoken_text": "I'm having trouble thinking right now."},
            model_used="none",
            time_taken=0,
            success=False
        ))
        
        # Get visual actions
        visual_result = results.get("visual", StreamResult(
            stream_name="visual",
            content={"display_actions": []},
            model_used="none",
            time_taken=0,
            success=False
        ))
        
        # Get facts (for enrichment if needed)
        info_result = results.get("information", StreamResult(
            stream_name="information",
            content={},
            model_used="none",
            time_taken=0,
            success=False
        ))
        
        # Build unified response
        response = UnifiedResponse(
            spoken_text=conv_result.content.get("spoken_text", ""),
            display_actions=visual_result.content.get("display_actions", []),
            facts_used=info_result.content.get("relevant_facts", []),
            tone=conv_result.content.get("tone", "casual"),
            total_time=total_time,
            streams_completed=sum(1 for r in results.values() if r.success),
            model_used=conv_result.model_used
        )
        
        logger.info(f"ParallelThinker completed in {total_time:.2f}s ({response.streams_completed}/3 streams) model={conv_result.model_used}")
        
        return response
    
    def think_fast(
        self,
        query: str,
        context: Dict[str, Any],
        conversation_history: List[Dict[str, str]],
        personality: Dict[str, Any]
    ) -> UnifiedResponse:
        """
        Smart fast thinking - uses model selector for optimal model choice
        
        Fast model for chat, big model for coding - Abby decides.
        """
        import time
        start = time.time()
        
        result = self._run_conversation_stream(
            query, context, conversation_history, personality
        )
        
        return UnifiedResponse(
            spoken_text=result.content.get("spoken_text", ""),
            tone=result.content.get("tone", "casual"),
            total_time=time.time() - start,
            streams_completed=1,
            model_used=result.model_used
        )
    
    def think_smart(
        self,
        query: str,
        context: Dict[str, Any],
        conversation_history: List[Dict[str, str]],
        personality: Dict[str, Any]
    ) -> UnifiedResponse:
        """
        Smart thinking - automatically decides fast vs parallel mode
        
        This is the main entry point. Abby decides:
        - Simple query → fast mode (conversation only)
        - Complex query needing research/visuals → parallel mode
        - Coding task → uses big model
        """
        # Decide if parallel is worth it
        if ModelSelector.is_worth_parallel(query):
            logger.info("Using parallel mode (complex query)")
            return self.think(query, context, conversation_history, personality)
        else:
            logger.info("Using fast mode (simple query)")
            return self.think_fast(query, context, conversation_history, personality)
    
    def think_streaming(
        self,
        query: str,
        context: Dict[str, Any],
        conversation_history: List[Dict[str, str]],
        personality: Dict[str, Any]
    ) -> Generator[str, None, None]:
        """
        Stream response tokens for real-time conversation (Personaplex).
        
        This is critical for natural conversation - user hears words
        as they're generated, not waiting for full response.
        
        Yields:
            Individual tokens/words as they're generated
        """
        import time
        
        # Always use fast model for streaming (real-time requirement)
        model = self.fast_model
        
        identity = personality.get("identity", {})
        comm_style = personality.get("communication_style", {})
        
        system_prompt = f"""You are {identity.get('name', 'Abby')}.

WHO YOU ARE:
- A real person having a natural conversation
- Warm, genuine, slightly playful
- You're on a voice call - keep it conversational

HOW TO RESPOND:
- SHORT - this is voice, not text
- 1-2 sentences max
- Natural speech patterns
- Contractions: "I'm", "you're", "that's"

{comm_style.get('tone', 'casual and genuine')}"""

        messages = [{"role": "system", "content": system_prompt}]
        
        if conversation_history:
            messages.extend(conversation_history[-5:])  # Less history for speed
        
        messages.append({"role": "user", "content": query})
        
        # Stream from Ollama
        try:
            response_gen = self.ollama.chat(
                messages=messages,
                model=model,
                stream=True,
                options={
                    "temperature": 0.8,
                    "repeat_penalty": 1.3,
                    "num_predict": 150,  # Keep it short for voice
                }
            )
            
            full_response = ""
            for chunk in response_gen:
                if "message" in chunk and "content" in chunk["message"]:
                    token = chunk["message"]["content"]
                    full_response += token
                    yield token
                elif "error" in chunk:
                    logger.error(f"Stream error: {chunk['error']}")
                    yield "[error]"
                    break
            
            # Post-stream cleaning for history (streaming already sent raw tokens)
            cleaned = clean_robot_speech(full_response)
            if detect_repetition(cleaned):
                cleaned = remove_repetition(cleaned)
            logger.info(f"Streamed {len(full_response)} chars in real-time")
            
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield "Sorry, hit a snag there."
    
    def should_use_parallel(self, query: str) -> bool:
        """Wrapper for ModelSelector.is_worth_parallel"""
        return ModelSelector.is_worth_parallel(query)


# Convenience function
def create_parallel_thinker(**kwargs) -> ParallelThinker:
    """Create a ParallelThinker with optional config"""
    return ParallelThinker(**kwargs)


if __name__ == "__main__":
    # Quick test
    logging.basicConfig(level=logging.INFO)
    
    thinker = ParallelThinker()
    
    print("=== Model Selection Tests ===")
    test_queries = [
        "hi",
        "How are you?",
        "Write a Python function to sort a list",
        "Explain the difference between lists and tuples",
        "Show me the config.py file",
    ]
    
    for q in test_queries:
        model, reason = ModelSelector.select_model(q)
        parallel = ModelSelector.is_worth_parallel(q)
        print(f"{q[:45]:45} -> {model.split(':')[0]:8} ({reason}) parallel={parallel}")
    
    print("\n=== Live Test ===")
    result = thinker.think_smart(
        query="Hey, how's it going?",
        context={"workspace": os.getcwd()},
        conversation_history=[],
        personality={"identity": {"name": "Abby"}}
    )
    
    print(f"Response: {result.spoken_text[:100]}...")
    print(f"Time: {result.total_time:.2f}s")
    print(f"Model: {result.model_used}")
