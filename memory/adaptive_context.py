"""
Adaptive Context Manager for Abby

Implements AGPF-style (Adaptive Gradient Prediction Filter) context loading:
- Only loads relevant context/memories based on query
- Estimates importance before loading (avoids memory bloat)
- Smart caching for frequently accessed context
- Gradual context expansion if initial context insufficient

Key Principle: Don't load everything - predict what's needed first.
"""
import logging
import re
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import deque
import time

logger = logging.getLogger(__name__)


@dataclass
class ContextChunk:
    """A piece of context that can be loaded"""
    id: str
    content: str
    source: str  # "conversation", "memory", "knowledge", "task"
    relevance_score: float = 0.0
    token_estimate: int = 0
    keywords: Set[str] = field(default_factory=set)
    last_accessed: float = 0.0
    access_count: int = 0


@dataclass
class ContextBudget:
    """Budget constraints for context loading"""
    max_tokens: int = 4000         # Max context tokens
    max_chunks: int = 10           # Max context chunks
    min_relevance: float = 0.3    # Minimum relevance to include
    conversation_priority: float = 1.5  # Boost for recent conversation


class AdaptiveContextManager:
    """
    Manages context loading with AGPF-style prediction.
    
    Instead of loading all context and trimming, we:
    1. Analyze the query to predict what context is needed
    2. Score available context chunks by relevance
    3. Load only high-relevance chunks within budget
    4. Expand if the model indicates it needs more context
    """
    
    def __init__(
        self,
        short_term_memory=None,
        long_term_memory=None,
        working_memory=None,
        budget: Optional[ContextBudget] = None
    ):
        self.short_term = short_term_memory
        self.long_term = long_term_memory
        self.working = working_memory
        self.budget = budget or ContextBudget()
        
        # Context cache (recently used chunks)
        self._cache: Dict[str, ContextChunk] = {}
        self._cache_hits = 0
        self._cache_misses = 0
        
        # Query pattern → context type mapping (learned over time)
        self._query_patterns: Dict[str, List[str]] = {
            "code|program|function|class|bug|error": ["knowledge", "task"],
            "remember|earlier|before|said|told": ["conversation"],
            "file|create|edit|delete": ["task", "working"],
            "search|find|look": ["knowledge"],
        }
        
        # Stats
        self._total_queries = 0
        self._avg_chunks_loaded = 0.0
        self._tokens_saved = 0
        
        logger.info("AdaptiveContextManager initialized")
    
    def get_context_for_query(
        self,
        query: str,
        force_sources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get relevant context for a query using AGPF prediction.
        
        Args:
            query: The user's query
            force_sources: Force include these sources (bypass prediction)
            
        Returns:
            Dict with selected context and metadata
        """
        self._total_queries += 1
        start_time = time.time()
        
        # 1. Extract query characteristics
        query_analysis = self._analyze_query(query)
        logger.debug(f"Query analysis: {query_analysis}")
        
        # 2. Predict which context sources are relevant
        predicted_sources = self._predict_sources(query_analysis)
        if force_sources:
            predicted_sources.update(force_sources)
        logger.debug(f"Predicted sources: {predicted_sources}")
        
        # 3. Gather candidate chunks from relevant sources
        candidates = self._gather_candidates(query_analysis, predicted_sources)
        logger.debug(f"Found {len(candidates)} candidate chunks")
        
        # 4. Score and rank candidates
        scored = self._score_candidates(candidates, query_analysis)
        
        # 5. Select chunks within budget
        selected = self._select_within_budget(scored)
        
        # 6. Build final context
        context = self._build_context(selected)
        
        elapsed = time.time() - start_time
        
        # Update stats
        self._avg_chunks_loaded = (
            (self._avg_chunks_loaded * (self._total_queries - 1) + len(selected))
            / self._total_queries
        )
        
        logger.info(
            f"Context loaded: {len(selected)} chunks, "
            f"~{context['token_estimate']} tokens, "
            f"{elapsed*1000:.1f}ms"
        )
        
        return context
    
    def _analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze query to extract characteristics for prediction"""
        query_lower = query.lower()
        words = set(re.findall(r'\b\w+\b', query_lower))
        
        # Detect query type
        is_question = '?' in query or any(
            query_lower.startswith(w) for w in ['what', 'how', 'why', 'when', 'where', 'who', 'can', 'could', 'would', 'is', 'are', 'do', 'does']
        )
        
        is_command = any(
            query_lower.startswith(w) for w in ['create', 'make', 'run', 'execute', 'delete', 'edit', 'update', 'fix', 'search', 'find']
        )
        
        references_past = any(w in words for w in ['earlier', 'before', 'said', 'told', 'remember', 'mentioned', 'previous', 'last'])
        
        is_followup = len(words) < 10 and any(w in words for w in ['it', 'that', 'this', 'those', 'them'])
        
        # Extract likely topics
        topics = words - {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 
                         'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                         'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
                         'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as',
                         'into', 'through', 'during', 'before', 'after', 'above', 'below',
                         'and', 'but', 'or', 'nor', 'so', 'yet', 'both', 'either', 'neither',
                         'not', 'only', 'own', 'same', 'than', 'too', 'very', 'just', 'also',
                         'i', 'me', 'my', 'you', 'your', 'we', 'our', 'they', 'their', 'it', 'its',
                         'what', 'how', 'why', 'when', 'where', 'who', 'which', 'that', 'this'}
        
        return {
            "query": query,
            "words": words,
            "topics": topics,
            "is_question": is_question,
            "is_command": is_command,
            "references_past": references_past,
            "is_followup": is_followup,
            "word_count": len(words)
        }
    
    def _predict_sources(self, analysis: Dict[str, Any]) -> Set[str]:
        """Predict which context sources are relevant"""
        sources = set()
        
        # Always include recent conversation for continuity
        sources.add("conversation_recent")
        
        # Followups need more conversation context
        if analysis["is_followup"]:
            sources.add("conversation_extended")
        
        # References to past need memory search
        if analysis["references_past"]:
            sources.add("conversation_search")
            sources.add("long_term")
        
        # Commands might need working memory (current tasks)
        if analysis["is_command"]:
            sources.add("working")
        
        # Check pattern matches
        query_lower = analysis["query"].lower()
        for pattern, pattern_sources in self._query_patterns.items():
            if re.search(pattern, query_lower):
                sources.update(pattern_sources)
        
        return sources
    
    def _gather_candidates(
        self,
        analysis: Dict[str, Any],
        sources: Set[str]
    ) -> List[ContextChunk]:
        """Gather candidate context chunks from relevant sources"""
        candidates = []
        
        # Recent conversation (always small, always relevant)
        if "conversation_recent" in sources and self.short_term:
            recent = self._get_recent_conversation(3)
            for i, turn in enumerate(recent):
                candidates.append(ContextChunk(
                    id=f"conv_recent_{i}",
                    content=f"{turn['role']}: {turn['content']}",
                    source="conversation",
                    relevance_score=0.9 - (i * 0.1),  # More recent = more relevant
                    token_estimate=len(turn['content'].split()) + 5,
                    keywords=set(re.findall(r'\b\w+\b', turn['content'].lower()))
                ))
        
        # Extended conversation
        if "conversation_extended" in sources and self.short_term:
            extended = self._get_recent_conversation(8)
            for i, turn in enumerate(extended[3:], start=3):  # Skip already added
                candidates.append(ContextChunk(
                    id=f"conv_ext_{i}",
                    content=f"{turn['role']}: {turn['content']}",
                    source="conversation",
                    relevance_score=0.6 - (i * 0.05),
                    token_estimate=len(turn['content'].split()) + 5,
                    keywords=set(re.findall(r'\b\w+\b', turn['content'].lower()))
                ))
        
        # Working memory (active tasks)
        if "working" in sources and self.working:
            active_tasks = self._get_active_tasks()
            for task_id, task in active_tasks.items():
                candidates.append(ContextChunk(
                    id=f"task_{task_id}",
                    content=f"Active task: {task.get('description', '')}",
                    source="working",
                    relevance_score=0.7,
                    token_estimate=len(task.get('description', '').split()) + 10,
                    keywords=set(re.findall(r'\b\w+\b', task.get('description', '').lower()))
                ))
        
        # Long-term memory search
        if "long_term" in sources and self.long_term and analysis["topics"]:
            query = ' '.join(analysis["topics"])
            memories = self._search_long_term(query, limit=5)
            for i, mem in enumerate(memories):
                candidates.append(ContextChunk(
                    id=f"memory_{i}",
                    content=mem.get("content", str(mem)),
                    source="memory",
                    relevance_score=0.5 - (i * 0.05),
                    token_estimate=len(str(mem).split()),
                    keywords=set(re.findall(r'\b\w+\b', str(mem).lower()))
                ))
        
        return candidates
    
    def _score_candidates(
        self,
        candidates: List[ContextChunk],
        analysis: Dict[str, Any]
    ) -> List[Tuple[float, ContextChunk]]:
        """Score candidates by relevance to query"""
        scored = []
        query_topics = analysis["topics"]
        
        for chunk in candidates:
            # Base relevance score
            score = chunk.relevance_score
            
            # Boost for keyword overlap
            if query_topics and chunk.keywords:
                overlap = len(query_topics & chunk.keywords)
                score += overlap * 0.1
            
            # Boost for conversation (continuity is important)
            if chunk.source == "conversation":
                score *= self.budget.conversation_priority
            
            # Penalty for very long chunks (efficiency)
            if chunk.token_estimate > 500:
                score *= 0.8
            
            # Boost for cached/frequently accessed
            if chunk.id in self._cache:
                cached = self._cache[chunk.id]
                score += min(cached.access_count * 0.05, 0.2)
                self._cache_hits += 1
            else:
                self._cache_misses += 1
            
            scored.append((score, chunk))
        
        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)
        
        return scored
    
    def _select_within_budget(
        self,
        scored: List[Tuple[float, ContextChunk]]
    ) -> List[ContextChunk]:
        """Select chunks within token and count budget"""
        selected = []
        total_tokens = 0
        
        for score, chunk in scored:
            # Check relevance threshold
            if score < self.budget.min_relevance:
                continue
            
            # Check token budget
            if total_tokens + chunk.token_estimate > self.budget.max_tokens:
                continue
            
            # Check chunk count
            if len(selected) >= self.budget.max_chunks:
                break
            
            selected.append(chunk)
            total_tokens += chunk.token_estimate
            
            # Update cache
            chunk.last_accessed = time.time()
            chunk.access_count += 1
            self._cache[chunk.id] = chunk
        
        return selected
    
    def _build_context(self, chunks: List[ContextChunk]) -> Dict[str, Any]:
        """Build final context from selected chunks"""
        # Group by source
        by_source: Dict[str, List[str]] = {}
        for chunk in chunks:
            if chunk.source not in by_source:
                by_source[chunk.source] = []
            by_source[chunk.source].append(chunk.content)
        
        # Build context string
        parts = []
        
        if "conversation" in by_source:
            parts.append("Recent conversation:\n" + "\n".join(by_source["conversation"]))
        
        if "working" in by_source:
            parts.append("Active tasks:\n" + "\n".join(by_source["working"]))
        
        if "memory" in by_source:
            parts.append("Relevant memories:\n" + "\n".join(by_source["memory"]))
        
        if "knowledge" in by_source:
            parts.append("Knowledge:\n" + "\n".join(by_source["knowledge"]))
        
        context_string = "\n\n".join(parts)
        token_estimate = sum(c.token_estimate for c in chunks)
        
        return {
            "context_string": context_string,
            "chunks": chunks,
            "sources_used": list(by_source.keys()),
            "token_estimate": token_estimate,
            "chunk_count": len(chunks)
        }
    
    def _get_recent_conversation(self, n: int) -> List[Dict[str, str]]:
        """Get recent conversation turns"""
        if not self.short_term:
            return []
        
        try:
            turns = self.short_term.get_recent_turns(n)
            return [{"role": t.role, "content": t.content} for t in turns]
        except Exception as e:
            logger.warning(f"Error getting conversation: {e}")
            return []
    
    def _get_active_tasks(self) -> Dict[str, Any]:
        """Get active tasks from working memory"""
        if not self.working:
            return {}
        
        try:
            return self.working.active_tasks
        except Exception as e:
            logger.warning(f"Error getting tasks: {e}")
            return {}
    
    def _search_long_term(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search long-term memory"""
        if not self.long_term:
            return []
        
        try:
            return self.long_term.search_conversations(query, limit)
        except Exception as e:
            logger.warning(f"Error searching memory: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get context manager statistics"""
        return {
            "total_queries": self._total_queries,
            "avg_chunks_per_query": round(self._avg_chunks_loaded, 2),
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "cache_hit_rate": self._cache_hits / max(1, self._cache_hits + self._cache_misses),
            "cache_size": len(self._cache),
            "budget": {
                "max_tokens": self.budget.max_tokens,
                "max_chunks": self.budget.max_chunks,
                "min_relevance": self.budget.min_relevance
            }
        }
    
    def clear_cache(self):
        """Clear the context cache"""
        self._cache.clear()
        logger.info("Context cache cleared")


# Convenience function
def create_adaptive_context_manager(
    short_term=None,
    long_term=None,
    working=None
) -> AdaptiveContextManager:
    """Create an adaptive context manager with optional memory systems"""
    return AdaptiveContextManager(
        short_term_memory=short_term,
        long_term_memory=long_term,
        working_memory=working
    )


if __name__ == "__main__":
    # Test the context manager
    logging.basicConfig(level=logging.INFO)
    
    manager = AdaptiveContextManager()
    
    print("\n=== Adaptive Context Manager Test ===\n")
    
    test_queries = [
        "What's up?",
        "Can you help me write a Python function?",
        "What did I say earlier about the project?",
        "Create a new file called test.py",
        "that thing we discussed",
    ]
    
    for query in test_queries:
        print(f"Query: '{query}'")
        analysis = manager._analyze_query(query)
        sources = manager._predict_sources(analysis)
        print(f"  → Predicted sources: {sources}")
        print(f"  → Is followup: {analysis['is_followup']}")
        print(f"  → References past: {analysis['references_past']}")
        print()
    
    print("=== Stats ===")
    print(manager.get_stats())
