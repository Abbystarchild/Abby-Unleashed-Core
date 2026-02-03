"""
Context Window Manager for Abby

Handles bidirectional context windowing:
1. INBOUND (User → Abby): Large inputs get summarized + chunked
2. OUTBOUND (Abby → User): Long responses generated in coherent sections

Key Features:
- Automatic context size detection and management
- Summary generation with expandable sections
- Parallel pre-fetching of upcoming context
- Response planning for long-form output
- Maintains coherence across chunked processing

Architecture:
┌─────────────────────────────────────────────────────────────┐
│                    Context Window Manager                    │
├─────────────────────────────────────────────────────────────┤
│  INBOUND FLOW                  OUTBOUND FLOW                │
│  ┌─────────┐                   ┌─────────────┐              │
│  │ Large   │──► Summarize      │ Response    │◄── Plan      │
│  │ Input   │    + Chunk        │ Plan        │    Sections  │
│  └─────────┘       │           └─────────────┘              │
│       │            ▼                  │                     │
│       │      ┌──────────┐            ▼                     │
│       │      │ Summary  │      ┌──────────┐                │
│       │      │ + Chunks │      │ Generate │                │
│       │      └──────────┘      │ Sections │                │
│       │            │           └──────────┘                │
│       ▼            ▼                  │                     │
│  ┌──────────────────────┐            ▼                     │
│  │   Pre-fetch Queue    │◄───────────────                  │
│  │  (Background Load)   │     Parallel expansion           │
│  └──────────────────────┘                                  │
└─────────────────────────────────────────────────────────────┘
"""

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Generator, Callable
from enum import Enum
import re
import json

logger = logging.getLogger(__name__)


# Default context limits (conservative for most models)
DEFAULT_INPUT_TOKEN_LIMIT = 4000  # When to start chunking input
DEFAULT_OUTPUT_TOKEN_LIMIT = 2000  # Max tokens per response section
CHARS_PER_TOKEN = 4  # Rough estimate


class ChunkType(Enum):
    """Types of content chunks"""
    SUMMARY = "summary"        # Compressed overview
    FULL = "full"              # Complete original content
    SECTION = "section"        # Logical section of content
    CODE = "code"              # Code block (don't summarize)
    REFERENCE = "reference"    # Reference to expand later


@dataclass
class ContentChunk:
    """A chunk of content with metadata"""
    id: str
    content: str
    chunk_type: ChunkType
    token_estimate: int
    original_length: int = 0
    section_title: str = ""
    can_expand: bool = False
    expanded_content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResponsePlan:
    """Plan for generating a long response"""
    sections: List[Dict[str, str]]  # [{title, description, key_points}]
    total_sections: int
    current_section: int = 0
    generated_content: List[str] = field(default_factory=list)
    context_so_far: str = ""  # Summary of what's been generated


@dataclass
class ContextWindow:
    """Current context window state"""
    summary: str                        # High-level summary always in context
    active_chunks: List[ContentChunk]   # Currently active detailed chunks
    pending_chunks: List[ContentChunk]  # Chunks waiting to be processed
    prefetch_queue: List[str]           # Chunk IDs to prefetch
    total_tokens: int = 0
    max_tokens: int = DEFAULT_INPUT_TOKEN_LIMIT


class ContextWindowManager:
    """
    Manages context windowing for both input processing and output generation.
    
    For large inputs:
    - Creates a summary that's always in context
    - Breaks content into logical chunks
    - Pre-fetches upcoming chunks in background
    - Expands sections on-demand
    
    For long outputs:
    - Plans response structure
    - Generates sections with coherent transitions
    - Maintains context of what's been said
    - Allows continuation without losing thread
    """
    
    def __init__(
        self,
        ollama_client=None,
        summarizer_model: str = "mistral:latest",
        max_input_tokens: int = DEFAULT_INPUT_TOKEN_LIMIT,
        max_output_tokens: int = DEFAULT_OUTPUT_TOKEN_LIMIT,
        prefetch_workers: int = 2
    ):
        """
        Initialize the context window manager.
        
        Args:
            ollama_client: Ollama client for summarization
            summarizer_model: Model to use for summarization (fast model)
            max_input_tokens: Max tokens for input context window
            max_output_tokens: Max tokens per output section
            prefetch_workers: Number of parallel prefetch workers
        """
        self.ollama = ollama_client
        self.summarizer_model = summarizer_model
        self.max_input_tokens = max_input_tokens
        self.max_output_tokens = max_output_tokens
        
        # Thread pool for background prefetching
        self.prefetch_executor = ThreadPoolExecutor(max_workers=prefetch_workers)
        self.prefetch_cache: Dict[str, ContentChunk] = {}
        self.prefetch_futures: Dict[str, Future] = {}
        
        # Current state
        self.current_window: Optional[ContextWindow] = None
        self.current_response_plan: Optional[ResponsePlan] = None
        
        logger.info(f"ContextWindowManager initialized (input={max_input_tokens}, output={max_output_tokens})")
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count from text"""
        return len(text) // CHARS_PER_TOKEN
    
    def needs_windowing(self, content: str) -> bool:
        """Check if content needs windowing (too large for single context)"""
        return self.estimate_tokens(content) > self.max_input_tokens
    
    def needs_long_response(self, query: str, context: Dict[str, Any]) -> bool:
        """
        Detect if this query needs a long-form response.
        
        Returns True if:
        - User asks for detailed explanation
        - Task is complex with multiple parts
        - User explicitly asks for comprehensive answer
        """
        long_indicators = [
            'explain in detail', 'comprehensive', 'step by step',
            'walk me through', 'full explanation', 'everything about',
            'complete guide', 'thorough', 'in depth', 'elaborate',
            'tell me all about', 'describe fully'
        ]
        
        query_lower = query.lower()
        
        # Check for explicit long-form requests
        if any(ind in query_lower for ind in long_indicators):
            return True
        
        # Check for multi-part questions
        question_words = ['what', 'how', 'why', 'when', 'where', 'which']
        question_count = sum(1 for w in question_words if w in query_lower)
        if question_count >= 3:
            return True
        
        # Check for "and also" / "as well as" patterns
        if ' and also ' in query_lower or ' as well as ' in query_lower:
            return True
        
        return False
    
    # ==================== INBOUND: User → Abby ====================
    
    def process_large_input(self, content: str, preserve_code: bool = True) -> ContextWindow:
        """
        Process large input content into manageable chunks.
        
        Creates:
        1. A summary (always in context)
        2. Logical sections (loaded on demand)
        3. Code blocks preserved intact
        
        Args:
            content: The large input content
            preserve_code: Whether to keep code blocks intact (not summarized)
            
        Returns:
            ContextWindow with summary and chunks
        """
        logger.info(f"Processing large input: {len(content)} chars, ~{self.estimate_tokens(content)} tokens")
        
        # Extract code blocks first (preserve them)
        code_blocks = []
        if preserve_code:
            code_pattern = r'```[\w]*\n(.*?)```'
            for i, match in enumerate(re.finditer(code_pattern, content, re.DOTALL)):
                code_blocks.append(ContentChunk(
                    id=f"code_{i}",
                    content=match.group(0),
                    chunk_type=ChunkType.CODE,
                    token_estimate=self.estimate_tokens(match.group(0)),
                    original_length=len(match.group(0)),
                    section_title=f"Code Block {i+1}"
                ))
        
        # Remove code blocks for text processing
        text_content = re.sub(r'```[\w]*\n.*?```', '[CODE_BLOCK]', content, flags=re.DOTALL)
        
        # Split into logical sections
        sections = self._split_into_sections(text_content)
        
        # Generate overall summary
        summary = self._generate_summary(content)
        
        # Create chunks for each section
        chunks = []
        for i, section in enumerate(sections):
            chunk = ContentChunk(
                id=f"section_{i}",
                content=section['content'],
                chunk_type=ChunkType.SECTION,
                token_estimate=self.estimate_tokens(section['content']),
                original_length=len(section['content']),
                section_title=section.get('title', f'Section {i+1}'),
                can_expand=True
            )
            chunks.append(chunk)
        
        # Add code blocks
        chunks.extend(code_blocks)
        
        # Create context window
        self.current_window = ContextWindow(
            summary=summary,
            active_chunks=[],
            pending_chunks=chunks,
            prefetch_queue=[c.id for c in chunks[:3]],  # Prefetch first 3
            total_tokens=self.estimate_tokens(summary),
            max_tokens=self.max_input_tokens
        )
        
        # Start prefetching
        self._start_prefetch()
        
        return self.current_window
    
    def _split_into_sections(self, content: str) -> List[Dict[str, str]]:
        """Split content into logical sections"""
        sections = []
        
        # Try to split by headers first
        header_pattern = r'^(#{1,3})\s+(.+)$'
        lines = content.split('\n')
        current_section = {'title': 'Introduction', 'content': ''}
        
        for line in lines:
            header_match = re.match(header_pattern, line)
            if header_match:
                # Save current section if it has content
                if current_section['content'].strip():
                    sections.append(current_section)
                # Start new section
                current_section = {
                    'title': header_match.group(2),
                    'content': ''
                }
            else:
                current_section['content'] += line + '\n'
        
        # Add final section
        if current_section['content'].strip():
            sections.append(current_section)
        
        # If no headers found, split by paragraphs
        if len(sections) <= 1:
            paragraphs = content.split('\n\n')
            sections = []
            for i, para in enumerate(paragraphs):
                if para.strip():
                    sections.append({
                        'title': f'Part {i+1}',
                        'content': para
                    })
        
        # Merge small sections, split large ones
        return self._balance_sections(sections)
    
    def _balance_sections(self, sections: List[Dict], target_tokens: int = 500) -> List[Dict]:
        """Balance section sizes - merge small, split large"""
        balanced = []
        current = None
        
        for section in sections:
            tokens = self.estimate_tokens(section['content'])
            
            if tokens > target_tokens * 2:
                # Section too large, split it
                if current:
                    balanced.append(current)
                    current = None
                
                # Split by sentences
                sentences = re.split(r'(?<=[.!?])\s+', section['content'])
                chunk_content = ''
                chunk_num = 1
                
                for sentence in sentences:
                    if self.estimate_tokens(chunk_content + sentence) > target_tokens:
                        if chunk_content:
                            balanced.append({
                                'title': f"{section['title']} (Part {chunk_num})",
                                'content': chunk_content
                            })
                            chunk_num += 1
                        chunk_content = sentence
                    else:
                        chunk_content += ' ' + sentence if chunk_content else sentence
                
                if chunk_content:
                    balanced.append({
                        'title': f"{section['title']} (Part {chunk_num})",
                        'content': chunk_content
                    })
                    
            elif tokens < target_tokens // 2 and current:
                # Section too small, merge with current
                current['content'] += '\n\n' + section['content']
                current['title'] = current['title'].split(' & ')[0] + ' & ' + section['title']
            else:
                if current:
                    balanced.append(current)
                current = section
        
        if current:
            balanced.append(current)
        
        return balanced
    
    def _generate_summary(self, content: str, max_length: int = 500) -> str:
        """Generate a summary of the content using the fast model"""
        if not self.ollama:
            # Fallback: simple truncation with ellipsis
            if len(content) > max_length:
                return content[:max_length] + "... [truncated]"
            return content
        
        try:
            prompt = f"""Summarize this content in 2-3 paragraphs. Focus on:
1. Main topic/purpose
2. Key points and structure
3. Important details to remember

Content:
{content[:8000]}  # Limit input

Summary:"""
            
            response = self.ollama.generate(
                prompt=prompt,
                model=self.summarizer_model,
                options={"temperature": 0.3, "num_predict": 300}
            )
            
            if "error" in response:
                logger.warning(f"Summary generation failed: {response['error']}")
                return content[:max_length] + "... [truncated]"
            
            return response.get("response", content[:max_length])
            
        except Exception as e:
            logger.error(f"Summary generation error: {e}")
            return content[:max_length] + "... [truncated]"
    
    def get_active_context(self) -> str:
        """Get the current active context (summary + active chunks)"""
        if not self.current_window:
            return ""
        
        parts = [f"=== CONTEXT SUMMARY ===\n{self.current_window.summary}"]
        
        for chunk in self.current_window.active_chunks:
            parts.append(f"\n=== {chunk.section_title} ===\n{chunk.content}")
        
        return "\n".join(parts)
    
    def activate_chunk(self, chunk_id: str) -> Optional[ContentChunk]:
        """Activate a chunk (move from pending to active)"""
        if not self.current_window:
            return None
        
        # Check prefetch cache first
        if chunk_id in self.prefetch_cache:
            chunk = self.prefetch_cache.pop(chunk_id)
        else:
            # Find in pending
            chunk = None
            for i, c in enumerate(self.current_window.pending_chunks):
                if c.id == chunk_id:
                    chunk = self.current_window.pending_chunks.pop(i)
                    break
        
        if chunk:
            # Check if we need to deactivate old chunks to fit
            while (self.current_window.total_tokens + chunk.token_estimate > 
                   self.current_window.max_tokens and 
                   self.current_window.active_chunks):
                old_chunk = self.current_window.active_chunks.pop(0)
                self.current_window.total_tokens -= old_chunk.token_estimate
                # Move back to pending (in case needed again)
                self.current_window.pending_chunks.insert(0, old_chunk)
            
            self.current_window.active_chunks.append(chunk)
            self.current_window.total_tokens += chunk.token_estimate
            
            # Update prefetch queue
            self._update_prefetch_queue()
            
        return chunk
    
    def _start_prefetch(self):
        """Start prefetching chunks in background"""
        if not self.current_window:
            return
        
        for chunk_id in self.current_window.prefetch_queue:
            if chunk_id not in self.prefetch_cache and chunk_id not in self.prefetch_futures:
                # Find the chunk
                for chunk in self.current_window.pending_chunks:
                    if chunk.id == chunk_id:
                        # Submit prefetch task
                        future = self.prefetch_executor.submit(self._prefetch_chunk, chunk)
                        self.prefetch_futures[chunk_id] = future
                        break
    
    def _prefetch_chunk(self, chunk: ContentChunk) -> ContentChunk:
        """Prefetch a chunk (load into cache)"""
        # For now, just cache the chunk as-is
        # In the future, could expand references or enrich content
        logger.debug(f"Prefetched chunk: {chunk.id}")
        self.prefetch_cache[chunk.id] = chunk
        return chunk
    
    def _update_prefetch_queue(self):
        """Update the prefetch queue based on current position"""
        if not self.current_window:
            return
        
        # Get IDs of next few pending chunks
        pending_ids = [c.id for c in self.current_window.pending_chunks[:5]]
        
        # Remove already cached or active
        active_ids = {c.id for c in self.current_window.active_chunks}
        cached_ids = set(self.prefetch_cache.keys())
        
        self.current_window.prefetch_queue = [
            cid for cid in pending_ids 
            if cid not in active_ids and cid not in cached_ids
        ]
        
        # Start prefetching new items
        self._start_prefetch()
    
    # ==================== OUTBOUND: Abby → User ====================
    
    def plan_long_response(
        self,
        query: str,
        context: Dict[str, Any],
        personality: Dict[str, Any]
    ) -> ResponsePlan:
        """
        Plan a long-form response by breaking it into sections.
        
        Args:
            query: User's query
            context: Task context
            personality: Abby's personality settings
            
        Returns:
            ResponsePlan with sections to generate
        """
        logger.info(f"Planning long response for: {query[:50]}...")
        
        if not self.ollama:
            # Fallback: single section
            return ResponsePlan(
                sections=[{"title": "Response", "description": query, "key_points": []}],
                total_sections=1
            )
        
        try:
            plan_prompt = f"""You need to give a comprehensive response to this query.
Break it into 3-5 logical sections.

Query: {query}

Output a JSON object with sections:
{{
    "sections": [
        {{"title": "Section Title", "description": "What to cover", "key_points": ["point1", "point2"]}}
    ]
}}

Plan:"""
            
            response = self.ollama.generate(
                prompt=plan_prompt,
                model=self.summarizer_model,
                options={"temperature": 0.4, "num_predict": 500}
            )
            
            if "error" in response:
                raise RuntimeError(response["error"])
            
            # Parse JSON from response - handle common escaping issues
            text = response.get("response", "")
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            
            if json_match:
                json_str = json_match.group()
                # Fix common JSON issues from LLM output
                json_str = self._fix_json_string(json_str)
                try:
                    plan_data = json.loads(json_str)
                    sections = plan_data.get("sections", [])
                except json.JSONDecodeError:
                    # If still fails, use smart fallback
                    logger.warning("JSON parse failed, using smart task decomposition")
                    sections = self._smart_decompose_task(query)
            else:
                # Fallback: generate simple sections based on query
                sections = self._smart_decompose_task(query)
            
            self.current_response_plan = ResponsePlan(
                sections=sections,
                total_sections=len(sections)
            )
            
            logger.info(f"Planned {len(sections)} sections for response")
            return self.current_response_plan
            
        except Exception as e:
            logger.error(f"Response planning error: {e}")
            # Fallback
            sections = self._generate_fallback_sections(query)
            self.current_response_plan = ResponsePlan(
                sections=sections,
                total_sections=len(sections)
            )
            return self.current_response_plan
    
    def _generate_fallback_sections(self, query: str) -> List[Dict]:
        """Generate simple fallback sections"""
        return [
            {"title": "Overview", "description": f"Introduction to: {query[:50]}", "key_points": []},
            {"title": "Details", "description": "Main explanation", "key_points": []},
            {"title": "Summary", "description": "Key takeaways", "key_points": []}
        ]
    
    def _fix_json_string(self, json_str: str) -> str:
        """Fix common JSON issues from LLM output"""
        # Fix invalid escape sequences
        # Replace single backslashes that aren't part of valid escapes
        valid_escapes = ['\\n', '\\r', '\\t', '\\\\', '\\"', "\\'", '\\b', '\\f']
        
        # First, normalize line endings
        json_str = json_str.replace('\r\n', '\\n').replace('\r', '\\n')
        
        # Fix unescaped backslashes (common in file paths)
        result = []
        i = 0
        while i < len(json_str):
            if json_str[i] == '\\':
                # Check if it's a valid escape
                if i + 1 < len(json_str):
                    two_char = json_str[i:i+2]
                    if two_char in valid_escapes or json_str[i+1] == 'u':
                        result.append(json_str[i])
                    else:
                        # Invalid escape - double the backslash
                        result.append('\\\\')
                        i += 1
                        continue
                else:
                    result.append('\\\\')
            else:
                result.append(json_str[i])
            i += 1
        
        return ''.join(result)
    
    def _smart_decompose_task(self, query: str) -> List[Dict]:
        """
        Intelligently decompose a complex task into manageable sections.
        
        This is the key to Abby handling overwhelming requests - she breaks
        them down into logical chunks she can tackle one at a time.
        """
        sections = []
        query_lower = query.lower()
        
        # Detect task patterns and create appropriate sections
        
        # 1. Check for explicit numbered steps
        numbered_pattern = r'(?:^|\n)\s*(?:\d+[\.\):]|step\s+\d+)'
        if re.search(numbered_pattern, query_lower):
            # Extract numbered items
            items = re.split(r'(?:^|\n)\s*(?:\d+[\.\):]|step\s+\d+)\s*', query)
            items = [item.strip() for item in items if item.strip()]
            for i, item in enumerate(items[:10]):  # Max 10 sections
                sections.append({
                    "title": f"Step {i+1}",
                    "description": item[:200],
                    "key_points": []
                })
        
        # 2. Check for feature/component lists
        elif any(word in query_lower for word in ['feature', 'component', 'page', 'screen', 'section']):
            # Try to extract features
            feature_patterns = [
                r'(?:^|\n)\s*[-•*]\s*(.+)',  # Bullet points
                r'(?:^|\n)\s*(\w+\s+page)',   # "X page"
                r'(?:^|\n)\s*(\w+\s+screen)', # "X screen"
            ]
            features = []
            for pattern in feature_patterns:
                features.extend(re.findall(pattern, query, re.IGNORECASE))
            
            if features:
                # Analysis first
                sections.append({
                    "title": "Analysis & Planning",
                    "description": "Analyze existing codebase and plan approach",
                    "key_points": ["Review current code", "Identify dependencies", "Create task list"]
                })
                for feature in features[:8]:  # Max 8 features
                    sections.append({
                        "title": f"{feature.strip().title()}",
                        "description": f"Implement {feature.strip()}",
                        "key_points": []
                    })
                sections.append({
                    "title": "Integration & Testing",
                    "description": "Wire everything together and test",
                    "key_points": ["Connect components", "Test flows", "Fix issues"]
                })
        
        # 3. Check for app/project development
        elif any(word in query_lower for word in ['app', 'application', 'project', 'build', 'create', 'develop']):
            sections = [
                {"title": "Project Analysis", "description": "Analyze requirements and existing code", "key_points": ["Review specs", "Check existing files", "Identify gaps"]},
                {"title": "Architecture Design", "description": "Design system architecture and data flow", "key_points": ["Component structure", "Data models", "API design"]},
                {"title": "Core Implementation", "description": "Build core functionality", "key_points": ["Main features", "Business logic", "Data handling"]},
                {"title": "UI/UX Implementation", "description": "Build user interface", "key_points": ["Screens", "Navigation", "Styling"]},
                {"title": "Integration", "description": "Connect all components", "key_points": ["Wire up features", "Test flows", "Debug"]},
                {"title": "Polish & Testing", "description": "Final polish and testing", "key_points": ["Edge cases", "Performance", "User experience"]},
            ]
        
        # 4. Default: break by sentence groups
        else:
            sentences = re.split(r'[.!?]+', query)
            sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
            
            # Group sentences into sections (3-4 sentences each)
            chunk_size = max(1, len(sentences) // 4)
            for i in range(0, len(sentences), chunk_size):
                chunk = sentences[i:i+chunk_size]
                if chunk:
                    sections.append({
                        "title": f"Part {len(sections)+1}",
                        "description": '. '.join(chunk)[:200],
                        "key_points": []
                    })
        
        # Ensure we have at least one section
        if not sections:
            sections = self._generate_fallback_sections(query)
        
        return sections
    
    def generate_next_section(
        self,
        model: str,
        personality: Dict[str, Any],
        additional_context: str = ""
    ) -> Generator[str, None, None]:
        """
        Generate the next section of a long response.
        
        Yields tokens as they're generated for streaming.
        
        Args:
            model: Model to use for generation
            personality: Personality settings
            additional_context: Any extra context to include
            
        Yields:
            Response tokens
        """
        if not self.current_response_plan:
            yield "No response plan active."
            return
        
        plan = self.current_response_plan
        
        if plan.current_section >= plan.total_sections:
            yield "\n\n✅ Response complete."
            return
        
        section = plan.sections[plan.current_section]
        
        # Build context-aware prompt
        identity = personality.get("identity", {})
        context_so_far = plan.context_so_far or "This is the beginning of the response."
        
        section_prompt = f"""You are {identity.get('name', 'Abby')} giving a detailed response.

You're on section {plan.current_section + 1} of {plan.total_sections}.

WHAT YOU'VE COVERED SO FAR:
{context_so_far}

CURRENT SECTION: {section['title']}
WHAT TO COVER: {section['description']}
KEY POINTS: {', '.join(section.get('key_points', ['cover the topic thoroughly']))}

{additional_context}

Write this section naturally, as if continuing a conversation. 
Start with a brief transition from the previous section (unless this is section 1).
Be informative but conversational.

Section {plan.current_section + 1}:"""

        try:
            if not self.ollama:
                yield f"\n\n## {section['title']}\n\n{section['description']}"
                return
            
            # Generate with streaming
            response_gen = self.ollama.chat(
                messages=[
                    {"role": "system", "content": f"You are {identity.get('name', 'Abby')}, giving a detailed but conversational explanation."},
                    {"role": "user", "content": section_prompt}
                ],
                model=model,
                stream=True,
                options={
                    "temperature": 0.7,
                    "num_predict": self.max_output_tokens
                }
            )
            
            section_content = ""
            
            # Yield section header
            yield f"\n\n## {section['title']}\n\n"
            
            for chunk in response_gen:
                if "message" in chunk and "content" in chunk["message"]:
                    token = chunk["message"]["content"]
                    section_content += token
                    yield token
                elif "error" in chunk:
                    logger.error(f"Section generation error: {chunk['error']}")
                    yield f"\n[Error generating section: {chunk['error']}]"
                    break
            
            # Update plan state
            plan.generated_content.append(section_content)
            plan.current_section += 1
            
            # Update context summary for next section
            plan.context_so_far = self._summarize_generated(plan.generated_content)
            
        except Exception as e:
            logger.error(f"Section generation error: {e}")
            yield f"\n[Error: {e}]"
    
    def _summarize_generated(self, sections: List[str]) -> str:
        """Summarize what's been generated so far"""
        all_content = "\n".join(sections)
        
        if len(all_content) < 500:
            return all_content
        
        if not self.ollama:
            return all_content[:500] + "..."
        
        try:
            response = self.ollama.generate(
                prompt=f"Summarize the key points covered so far in 2-3 sentences:\n\n{all_content}",
                model=self.summarizer_model,
                options={"temperature": 0.3, "num_predict": 150}
            )
            return response.get("response", all_content[:500])
        except:
            return all_content[:500] + "..."
    
    def get_response_progress(self) -> Dict[str, Any]:
        """Get current response generation progress"""
        if not self.current_response_plan:
            return {"active": False}
        
        plan = self.current_response_plan
        return {
            "active": True,
            "current_section": plan.current_section,
            "total_sections": plan.total_sections,
            "sections": [s["title"] for s in plan.sections],
            "progress_percent": (plan.current_section / plan.total_sections) * 100
        }
    
    def continue_response(self) -> bool:
        """Check if there are more sections to generate"""
        if not self.current_response_plan:
            return False
        return self.current_response_plan.current_section < self.current_response_plan.total_sections
    
    def reset_response_plan(self):
        """Reset the current response plan"""
        self.current_response_plan = None
    
    # ==================== Utility ====================
    
    def cleanup(self):
        """Clean up resources"""
        self.prefetch_executor.shutdown(wait=False)
        self.prefetch_cache.clear()
        self.current_window = None
        self.current_response_plan = None


# Singleton instance
_context_manager: Optional[ContextWindowManager] = None


def get_context_manager(ollama_client=None) -> ContextWindowManager:
    """Get or create the context manager singleton"""
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextWindowManager(ollama_client=ollama_client)
    return _context_manager


# Test code
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    # Test inbound (large input)
    manager = ContextWindowManager()
    
    test_content = """
# Introduction
This is a test document with multiple sections.

## Section 1: Background
Lorem ipsum dolor sit amet, consectetur adipiscing elit. 
Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

## Section 2: Details
More detailed information here. This section covers the specifics.

```python
def example():
    return "This code should be preserved"
```

## Section 3: Conclusion
Final thoughts and summary.
""" * 10  # Make it large
    
    print("=== Testing Inbound (Large Input) ===")
    window = manager.process_large_input(test_content)
    print(f"Summary: {window.summary[:200]}...")
    print(f"Chunks: {len(window.pending_chunks)}")
    print(f"Tokens: {window.total_tokens}")
    
    print("\n=== Testing Outbound (Long Response Planning) ===")
    plan = manager.plan_long_response(
        "Explain how neural networks work, including backpropagation, activation functions, and training",
        {},
        {"identity": {"name": "Abby"}}
    )
    print(f"Sections planned: {plan.total_sections}")
    for s in plan.sections:
        print(f"  - {s['title']}: {s['description'][:50]}...")
