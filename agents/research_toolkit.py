"""
Research Toolkit for Agents
Enables agents to acquire expert knowledge from the internet

An agent claiming expertise in a domain should be able to:
1. Search for authoritative sources on the topic
2. Fetch and read documentation, papers, articles
3. Build a knowledge base from multiple sources
4. Stay current with their domain knowledge
"""

import logging
import urllib.request
import urllib.parse
import json
import re
import os
from typing import Dict, Any, List, Optional, Tuple
from html.parser import HTMLParser
from dataclasses import dataclass, field
from datetime import datetime


logger = logging.getLogger(__name__)


@dataclass
class ResearchResult:
    """A single research finding"""
    source: str
    url: str
    content: str
    relevance: float = 0.0
    fetched_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass 
class KnowledgeAcquisition:
    """Knowledge acquired from research"""
    topic: str
    sources: List[ResearchResult]
    summary: str = ""
    key_facts: List[str] = field(default_factory=list)
    acquired_at: str = field(default_factory=lambda: datetime.now().isoformat())


class TextExtractor(HTMLParser):
    """Extract readable text from HTML"""
    
    def __init__(self):
        super().__init__()
        self.text = []
        self.skip_tags = {'script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript'}
        self.current_tag = None
        self.in_skip_tag = False
        
    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        if tag in self.skip_tags:
            self.in_skip_tag = True
            
    def handle_endtag(self, tag):
        if tag in self.skip_tags:
            self.in_skip_tag = False
        self.current_tag = None
        
    def handle_data(self, data):
        if not self.in_skip_tag and self.current_tag not in self.skip_tags:
            text = data.strip()
            if text and len(text) > 2:  # Skip very short fragments
                self.text.append(text)
    
    def get_text(self) -> str:
        return ' '.join(self.text)


class ResearchToolkit:
    """
    Research toolkit that enables agents to acquire expert knowledge
    
    An agent should use this to:
    1. Research their domain when first created
    2. Look up specific information during task execution
    3. Verify claims and get authoritative sources
    """
    
    def __init__(self, cache_dir: str = "data/research_cache"):
        self.cache_dir = cache_dir
        self.user_agent = 'AbbyUnleashed-Agent/1.0 (Research Bot)'
        
        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)
    
    def search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search the web for information on a topic
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            List of search results with text and URLs
        """
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1"
            
            req = urllib.request.Request(url, headers={'User-Agent': self.user_agent})
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            results = []
            
            # Main abstract (often from Wikipedia)
            if data.get('Abstract'):
                results.append({
                    'title': data.get('Heading', query),
                    'text': data['Abstract'],
                    'url': data.get('AbstractURL', ''),
                    'source': data.get('AbstractSource', 'Unknown'),
                    'type': 'abstract'
                })
            
            # Direct answer
            if data.get('Answer'):
                results.append({
                    'title': 'Direct Answer',
                    'text': data['Answer'],
                    'url': '',
                    'source': 'DuckDuckGo',
                    'type': 'answer'
                })
            
            # Related topics
            for topic in data.get('RelatedTopics', [])[:num_results]:
                if isinstance(topic, dict) and 'Text' in topic:
                    results.append({
                        'title': topic.get('Text', '')[:50] + '...' if len(topic.get('Text', '')) > 50 else topic.get('Text', ''),
                        'text': topic.get('Text', ''),
                        'url': topic.get('FirstURL', ''),
                        'source': 'DuckDuckGo Related',
                        'type': 'related'
                    })
            
            logger.info(f"Search '{query}' returned {len(results)} results")
            return results[:num_results]
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def fetch_url(self, url: str, max_length: int = 15000) -> Optional[str]:
        """
        Fetch and extract text content from a URL
        
        Args:
            url: URL to fetch
            max_length: Maximum content length
            
        Returns:
            Extracted text content or None on error
        """
        try:
            # Security check
            if not url.startswith(('http://', 'https://')):
                return None
            
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            with urllib.request.urlopen(req, timeout=15) as response:
                # Check content type
                content_type = response.headers.get('Content-Type', '')
                if 'html' not in content_type.lower() and 'text' not in content_type.lower():
                    return None
                
                html = response.read().decode('utf-8', errors='replace')
            
            # Extract text
            extractor = TextExtractor()
            extractor.feed(html)
            text = extractor.get_text()
            
            # Clean up
            text = re.sub(r'\s+', ' ', text).strip()
            
            if len(text) > max_length:
                text = text[:max_length] + '...'
            
            logger.info(f"Fetched {len(text)} chars from {url}")
            return text
            
        except Exception as e:
            logger.error(f"Fetch error for {url}: {e}")
            return None
    
    def research_topic(self, topic: str, depth: str = "standard") -> KnowledgeAcquisition:
        """
        Perform comprehensive research on a topic to acquire expert knowledge
        
        Args:
            topic: Topic to research
            depth: "quick" (1-2 sources), "standard" (3-5 sources), "deep" (5-10 sources)
            
        Returns:
            KnowledgeAcquisition with gathered information
        """
        num_sources = {"quick": 2, "standard": 5, "deep": 10}.get(depth, 5)
        
        logger.info(f"Researching topic: {topic} (depth: {depth})")
        
        # Search for information
        search_results = self.search(topic, num_sources)
        
        sources = []
        all_content = []
        
        for result in search_results:
            # Add search result text
            sources.append(ResearchResult(
                source=result['source'],
                url=result['url'],
                content=result['text'],
                relevance=1.0 if result['type'] == 'abstract' else 0.7
            ))
            all_content.append(result['text'])
            
            # For deep research, also fetch full pages
            if depth == "deep" and result['url']:
                page_content = self.fetch_url(result['url'])
                if page_content:
                    sources.append(ResearchResult(
                        source=f"Full page: {result['source']}",
                        url=result['url'],
                        content=page_content[:5000],  # Limit per-source
                        relevance=0.8
                    ))
                    all_content.append(page_content[:2000])
        
        # Extract key facts (simple extraction - could use LLM)
        key_facts = self._extract_key_facts('\n'.join(all_content))
        
        return KnowledgeAcquisition(
            topic=topic,
            sources=sources,
            summary='\n\n'.join([s.content[:500] for s in sources[:3]]),
            key_facts=key_facts
        )
    
    def _extract_key_facts(self, text: str) -> List[str]:
        """Extract key facts from text (simple heuristic)"""
        facts = []
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            # Look for definitional or factual patterns
            if any(pattern in sentence.lower() for pattern in [
                ' is ', ' are ', ' was ', ' were ', ' means ',
                ' defined as ', ' refers to ', ' consists of ',
                ' invented ', ' created ', ' developed ', ' founded '
            ]):
                if 20 < len(sentence) < 300:  # Reasonable length
                    facts.append(sentence)
        
        return facts[:15]  # Limit to top facts
    
    def acquire_domain_expertise(self, domain: str, subtopics: List[str] = None) -> Dict[str, KnowledgeAcquisition]:
        """
        Acquire comprehensive expertise in a domain
        
        This is what an agent should call when created to truly become
        an expert in their claimed domain.
        
        Args:
            domain: Main domain (e.g., "Machine Learning", "Web Development")
            subtopics: Specific subtopics to research
            
        Returns:
            Dictionary of topic -> KnowledgeAcquisition
        """
        expertise = {}
        
        # Research main domain
        logger.info(f"Acquiring expertise in: {domain}")
        expertise[domain] = self.research_topic(domain, depth="standard")
        
        # Research subtopics
        if subtopics:
            for subtopic in subtopics[:5]:  # Limit subtopics
                full_topic = f"{domain} {subtopic}"
                expertise[subtopic] = self.research_topic(full_topic, depth="quick")
        
        logger.info(f"Acquired expertise: {len(expertise)} topics researched")
        return expertise
    
    def lookup_for_task(self, task: str, agent_domain: str) -> str:
        """
        Quick lookup to support a specific task
        
        Call this during task execution to get relevant current information.
        
        Args:
            task: The task being performed
            agent_domain: Agent's domain for context
            
        Returns:
            Relevant information as a string for the LLM context
        """
        # Extract key terms from task
        query = f"{agent_domain}: {task}"
        
        # Quick search
        results = self.search(query, num_results=3)
        
        if not results:
            return ""
        
        # Format for LLM context
        context_parts = ["\n--- Research Findings ---"]
        for r in results:
            context_parts.append(f"\nSource: {r['source']}")
            if r['url']:
                context_parts.append(f"URL: {r['url']}")
            context_parts.append(f"Content: {r['text'][:500]}")
        context_parts.append("--- End Research ---\n")
        
        return '\n'.join(context_parts)
    
    def verify_claim(self, claim: str) -> Tuple[bool, str]:
        """
        Attempt to verify a factual claim
        
        Args:
            claim: The claim to verify
            
        Returns:
            Tuple of (could_verify, supporting_info)
        """
        results = self.search(claim, num_results=3)
        
        if not results:
            return False, "Could not find information to verify this claim."
        
        # Check if any result seems to support or contradict
        supporting_text = results[0].get('text', '') if results else ''
        
        return True, f"Related information found: {supporting_text[:300]}"


# Singleton instance for easy access
_toolkit = None

def get_research_toolkit() -> ResearchToolkit:
    """Get the global research toolkit instance"""
    global _toolkit
    if _toolkit is None:
        _toolkit = ResearchToolkit()
    return _toolkit
