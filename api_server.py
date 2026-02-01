"""
Web API Server for Abby Unleashed
Enables mobile and remote access to the AI system
"""
import logging
import os
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
import threading
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

from cli import AbbyUnleashed

logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder='web', static_url_path='')

# Enable CORS with restrictions for local network security
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:*",
            "http://127.0.0.1:*",
            "http://192.168.*.*:*",
            "http://10.*.*.*:*",
            "http://172.16.*.*:*",  # Common private network ranges
            "http://172.17.*.*:*",
            "http://172.18.*.*:*",
            "http://172.19.*.*:*",
            "http://172.20.*.*:*",
            "http://172.21.*.*:*",
            "http://172.22.*.*:*",
            "http://172.23.*.*:*",
            "http://172.24.*.*:*",
            "http://172.25.*.*:*",
            "http://172.26.*.*:*",
            "http://172.27.*.*:*",
            "http://172.28.*.*:*",
            "http://172.29.*.*:*",
            "http://172.30.*.*:*",
            "http://172.31.*.*:*"
        ],
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type"]
    }
})

# Global Abby instance
abby: Optional[AbbyUnleashed] = None
abby_lock = threading.Lock()


def get_abby():
    """Get or initialize Abby instance (thread-safe)"""
    global abby
    with abby_lock:
        if abby is None:
            abby = AbbyUnleashed(verbose=False)
        return abby


@app.route('/')
def index():
    """Serve mobile web interface"""
    return send_from_directory('web', 'index.html')


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        abby_instance = get_abby()
        ollama_healthy = abby_instance.ollama_client.health_check()
        
        return jsonify({
            'status': 'healthy' if ollama_healthy else 'degraded',
            'ollama': 'connected' if ollama_healthy else 'disconnected',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/task', methods=['POST'])
def execute_task():
    """Execute a task"""
    try:
        data = request.get_json()
        
        if not data or 'task' not in data:
            return jsonify({'error': 'Task description required'}), 400
        
        task = data['task']
        context = data.get('context', {})
        use_orchestrator = data.get('use_orchestrator', True)
        
        # Execute task
        abby_instance = get_abby()
        result = abby_instance.execute_task(task, context, use_orchestrator)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Task execution error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get system statistics"""
    try:
        abby_instance = get_abby()
        stats = abby_instance.get_stats()
        
        return jsonify(stats)
    
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/progress', methods=['GET'])
def get_progress():
    """Get orchestrator progress"""
    try:
        abby_instance = get_abby()
        progress = abby_instance.get_orchestrator_progress()
        
        return jsonify(progress)
    
    except Exception as e:
        logger.error(f"Progress error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/models', methods=['GET'])
def list_models():
    """List available Ollama models"""
    try:
        abby_instance = get_abby()
        models = abby_instance.ollama_client.list_models()
        
        return jsonify(models)
    
    except Exception as e:
        logger.error(f"Models list error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/conversation/history', methods=['GET'])
def get_conversation_history():
    """Get conversation history"""
    try:
        limit = request.args.get('limit', 10, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        abby_instance = get_abby()
        
        # Access long-term memory if available
        if hasattr(abby_instance, 'long_term_memory'):
            conversations = abby_instance.long_term_memory.get_conversations(limit, offset)
            return jsonify({'conversations': conversations})
        else:
            return jsonify({'conversations': []})
    
    except Exception as e:
        logger.error(f"Conversation history error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/personality', methods=['GET'])
def get_personality():
    """Get current personality configuration"""
    try:
        abby_instance = get_abby()
        personality = abby_instance.brain_clone.get_personality()
        
        return jsonify(personality)
    
    except Exception as e:
        logger.error(f"Personality error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/engram/questionnaire', methods=['GET'])
def get_engram_questionnaire():
    """Get the questionnaire for creating a personality engram"""
    try:
        abby_instance = get_abby()
        questionnaire = abby_instance.brain_clone.create_engram_questionnaire()
        
        return jsonify({
            'questionnaire': questionnaire,
            'instructions': 'Answer these questions to create an accurate digital clone of your personality.'
        })
    
    except Exception as e:
        logger.error(f"Engram questionnaire error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/engram/create', methods=['POST'])
def create_engram():
    """Create a new personality engram from questionnaire responses"""
    try:
        from personality.engram_builder import EngramBuilder, Engram, OceanTraits, CommunicationStyle, ValueSystem, DecisionMakingStyle, KnowledgeBase
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Engram data required'}), 400
        
        # Build engram from responses
        builder = EngramBuilder()
        engram = builder.start_new_engram(data.get('name', 'User'))
        
        # Process OCEAN traits if provided
        if 'ocean' in data:
            ocean_data = data['ocean']
            engram.ocean_traits = OceanTraits(
                openness=ocean_data.get('openness', 50),
                conscientiousness=ocean_data.get('conscientiousness', 50),
                extraversion=ocean_data.get('extraversion', 50),
                agreeableness=ocean_data.get('agreeableness', 50),
                neuroticism=ocean_data.get('neuroticism', 50),
                honesty_humility=ocean_data.get('honesty_humility', 50)
            )
        
        # Process communication style if provided
        if 'communication' in data:
            comm_data = data['communication']
            engram.communication_style = CommunicationStyle(
                formality=comm_data.get('formality', 50),
                verbosity=comm_data.get('verbosity', 50),
                directness=comm_data.get('directness', 50),
                humor_level=comm_data.get('humor_level', 50),
                humor_style=comm_data.get('humor_style', 'witty'),
                favorite_expressions=comm_data.get('favorite_expressions', [])
            )
        
        # Process values if provided
        if 'values' in data:
            values_data = data['values']
            engram.value_system = ValueSystem(
                core_values=values_data.get('core_values', []),
                deal_breakers=values_data.get('deal_breakers', []),
                motivators=values_data.get('motivators', []),
                risk_tolerance=values_data.get('risk_tolerance', 50)
            )
        
        # Process knowledge if provided
        if 'knowledge' in data:
            kb_data = data['knowledge']
            engram.knowledge_base = KnowledgeBase(
                expertise_areas=kb_data.get('expertise_areas', []),
                interests=kb_data.get('interests', []),
                background_facts=kb_data.get('background_facts', []),
                pet_peeves=kb_data.get('pet_peeves', [])
            )
        
        # Save engram
        abby_instance = get_abby()
        saved_path = abby_instance.brain_clone.save_engram(engram)
        
        # Generate system prompt
        system_prompt = builder.generate_system_prompt(engram)
        
        return jsonify({
            'status': 'success',
            'message': f'Engram created for {engram.subject_name}',
            'saved_to': saved_path,
            'system_prompt_preview': system_prompt[:500] + '...' if len(system_prompt) > 500 else system_prompt
        })
    
    except Exception as e:
        logger.error(f"Engram creation error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/engram/analyze-writing', methods=['POST'])
def analyze_writing():
    """Analyze a writing sample to extract personality patterns"""
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': 'Text sample required'}), 400
        
        abby_instance = get_abby()
        patterns = abby_instance.brain_clone.analyze_writing(data['text'])
        
        return jsonify({
            'status': 'success',
            'patterns': patterns
        })
    
    except Exception as e:
        logger.error(f"Writing analysis error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/personas', methods=['GET'])
def list_personas():
    """List available personas"""
    try:
        abby_instance = get_abby()
        personas = abby_instance.persona_library.list_personas()
        
        return jsonify({'personas': personas})
    
    except Exception as e:
        logger.error(f"Personas list error: {e}")
        return jsonify({'error': str(e)}), 500


# ============== AGENT RESEARCH APIs ==============
# Allow agents to acquire and demonstrate expertise

@app.route('/api/agent/research', methods=['POST'])
def agent_research():
    """Have an agent research a topic to acquire expertise"""
    try:
        from agents.research_toolkit import get_research_toolkit
        
        data = request.get_json()
        
        if not data or 'topic' not in data:
            return jsonify({'error': 'Topic required'}), 400
        
        topic = data['topic']
        depth = data.get('depth', 'standard')  # quick, standard, deep
        
        toolkit = get_research_toolkit()
        knowledge = toolkit.research_topic(topic, depth)
        
        return jsonify({
            'status': 'success',
            'topic': knowledge.topic,
            'sources_count': len(knowledge.sources),
            'key_facts': knowledge.key_facts,
            'summary': knowledge.summary,
            'sources': [{'source': s.source, 'url': s.url} for s in knowledge.sources]
        })
    
    except Exception as e:
        logger.error(f"Agent research error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/agent/create-expert', methods=['POST'])
def create_expert_agent():
    """Create an expert agent that researches its domain"""
    try:
        from agents.agent_dna import AgentDNA
        from agents.base_agent import Agent
        
        data = request.get_json()
        
        if not data or 'role' not in data or 'domain' not in data:
            return jsonify({'error': 'Role and domain required'}), 400
        
        # Create DNA for the expert
        dna = AgentDNA(
            role=data['role'],
            domain=data['domain'],
            seniority=data.get('seniority', 'Senior'),
            industry_knowledge=data.get('knowledge', [data['domain']]),
            methodologies=data.get('methodologies', ['Best Practices']),
            constraints={'quality': 'high', 'accuracy': 'verified'},
            output_format={'style': 'professional', 'citations': 'when_relevant'}
        )
        
        # Create agent - this will trigger expertise acquisition
        agent = Agent(dna=dna)
        
        # Return what the agent learned
        knowledge_summary = {}
        for topic, k in agent.acquired_knowledge.items():
            knowledge_summary[topic] = {
                'facts_learned': len(k.key_facts),
                'sources_consulted': len(k.sources),
                'sample_facts': k.key_facts[:3]
            }
        
        return jsonify({
            'status': 'success',
            'agent': {
                'role': dna.role,
                'domain': dna.domain,
                'seniority': dna.seniority
            },
            'expertise_acquired': knowledge_summary,
            'message': f"Expert {dna.role} created and has researched {len(agent.acquired_knowledge)} topics"
        })
    
    except Exception as e:
        logger.error(f"Create expert error: {e}")
        return jsonify({'error': str(e)}), 500


# ============== FILE ACCESS APIs ==============
# These allow Abby to read and help with your code

# Define allowed workspace paths for security
ALLOWED_WORKSPACES = [
    os.path.abspath(os.path.dirname(__file__)),  # This project
    os.path.expanduser("~/Dev"),  # Common dev folder
    os.path.expanduser("~/Projects"),
    "C:\\Dev",  # Windows dev folders
    "D:\\Dev",
]


def is_path_allowed(filepath: str) -> bool:
    """Check if filepath is within allowed workspaces"""
    abs_path = os.path.abspath(filepath)
    return any(abs_path.startswith(os.path.abspath(ws)) for ws in ALLOWED_WORKSPACES)


@app.route('/api/files/read', methods=['POST'])
def read_file():
    """Read a file from the workspace"""
    try:
        data = request.get_json()
        
        if not data or 'path' not in data:
            return jsonify({'error': 'File path required'}), 400
        
        filepath = data['path']
        
        # Security check
        if not is_path_allowed(filepath):
            return jsonify({'error': 'Access denied: path outside allowed workspaces'}), 403
        
        if not os.path.exists(filepath):
            return jsonify({'error': f'File not found: {filepath}'}), 404
        
        if not os.path.isfile(filepath):
            return jsonify({'error': 'Path is not a file'}), 400
        
        # Read file with size limit (1MB)
        if os.path.getsize(filepath) > 1024 * 1024:
            return jsonify({'error': 'File too large (max 1MB)'}), 400
        
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        return jsonify({
            'status': 'success',
            'path': filepath,
            'content': content,
            'size': len(content)
        })
    
    except Exception as e:
        logger.error(f"File read error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/files/write', methods=['POST'])
def write_file():
    """Write content to a file in the workspace"""
    try:
        data = request.get_json()
        
        if not data or 'path' not in data or 'content' not in data:
            return jsonify({'error': 'File path and content required'}), 400
        
        filepath = data['path']
        content = data['content']
        
        # Security check
        if not is_path_allowed(filepath):
            return jsonify({'error': 'Access denied: path outside allowed workspaces'}), 403
        
        # Create directory if needed
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Backup existing file
        if os.path.exists(filepath):
            backup_path = filepath + '.bak'
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                with open(backup_path, 'w', encoding='utf-8') as bf:
                    bf.write(f.read())
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return jsonify({
            'status': 'success',
            'path': filepath,
            'bytes_written': len(content)
        })
    
    except Exception as e:
        logger.error(f"File write error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/files/list', methods=['POST'])
def list_files():
    """List files in a directory"""
    try:
        data = request.get_json() or {}
        dirpath = data.get('path', os.path.dirname(__file__))
        
        # Security check
        if not is_path_allowed(dirpath):
            return jsonify({'error': 'Access denied: path outside allowed workspaces'}), 403
        
        if not os.path.exists(dirpath):
            return jsonify({'error': f'Directory not found: {dirpath}'}), 404
        
        if not os.path.isdir(dirpath):
            return jsonify({'error': 'Path is not a directory'}), 400
        
        items = []
        for name in os.listdir(dirpath):
            full_path = os.path.join(dirpath, name)
            items.append({
                'name': name,
                'path': full_path,
                'type': 'directory' if os.path.isdir(full_path) else 'file',
                'size': os.path.getsize(full_path) if os.path.isfile(full_path) else None
            })
        
        return jsonify({
            'status': 'success',
            'path': dirpath,
            'items': sorted(items, key=lambda x: (x['type'] != 'directory', x['name']))
        })
    
    except Exception as e:
        logger.error(f"File list error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/files/search', methods=['POST'])
def search_files():
    """Search for files by name pattern"""
    try:
        import glob
        
        data = request.get_json()
        
        if not data or 'pattern' not in data:
            return jsonify({'error': 'Search pattern required'}), 400
        
        basepath = data.get('path', os.path.dirname(__file__))
        pattern = data['pattern']
        
        # Security check
        if not is_path_allowed(basepath):
            return jsonify({'error': 'Access denied: path outside allowed workspaces'}), 403
        
        # Search for files
        search_pattern = os.path.join(basepath, '**', pattern)
        matches = glob.glob(search_pattern, recursive=True)
        
        # Limit results
        matches = matches[:100]
        
        return jsonify({
            'status': 'success',
            'pattern': pattern,
            'matches': matches,
            'count': len(matches)
        })
    
    except Exception as e:
        logger.error(f"File search error: {e}")
        return jsonify({'error': str(e)}), 500


# ============== CODE ASSISTANT APIs ==============

@app.route('/api/code/analyze', methods=['POST'])
def analyze_code():
    """Analyze code and provide suggestions"""
    try:
        data = request.get_json()
        
        if not data or 'code' not in data:
            return jsonify({'error': 'Code content required'}), 400
        
        code = data['code']
        language = data.get('language', 'python')
        task = data.get('task', 'review')  # review, explain, improve, debug
        
        abby_instance = get_abby()
        
        # Build specialized prompt for code analysis
        prompts = {
            'review': f"Review this {language} code and provide feedback on quality, potential bugs, and best practices:\n\n```{language}\n{code}\n```",
            'explain': f"Explain what this {language} code does, step by step:\n\n```{language}\n{code}\n```",
            'improve': f"Suggest improvements for this {language} code to make it more efficient, readable, or maintainable:\n\n```{language}\n{code}\n```",
            'debug': f"Find potential bugs or issues in this {language} code and explain how to fix them:\n\n```{language}\n{code}\n```"
        }
        
        prompt = prompts.get(task, prompts['review'])
        result = abby_instance.execute_task(prompt)
        
        return jsonify({
            'status': 'success',
            'task': task,
            'language': language,
            'analysis': result.get('output', 'No analysis available')
        })
    
    except Exception as e:
        logger.error(f"Code analysis error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/code/generate', methods=['POST'])
def generate_code():
    """Generate code based on a description"""
    try:
        data = request.get_json()
        
        if not data or 'description' not in data:
            return jsonify({'error': 'Code description required'}), 400
        
        description = data['description']
        language = data.get('language', 'python')
        context = data.get('context', '')  # Optional existing code for context
        
        abby_instance = get_abby()
        
        prompt = f"Write {language} code that: {description}"
        if context:
            prompt += f"\n\nHere's some existing code for context:\n```{language}\n{context}\n```"
        prompt += f"\n\nProvide clean, well-commented {language} code."
        
        result = abby_instance.execute_task(prompt)
        
        return jsonify({
            'status': 'success',
            'language': language,
            'code': result.get('output', 'No code generated')
        })
    
    except Exception as e:
        logger.error(f"Code generation error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/engram/start', methods=['POST'])
def start_engram_conversation():
    """Start an interactive engram creation session"""
    try:
        abby_instance = get_abby()
        
        # Get the questionnaire
        questionnaire = abby_instance.brain_clone.create_engram_questionnaire()
        
        # Create a conversational intro
        intro = """Hey! I'd love to help you create your engram - a digital snapshot of your personality that'll help me understand and respond more like you would.

This involves a few things:
1. **Personality Questions** - About 30 questions covering how you think, communicate, and make decisions
2. **Writing Samples** - Some text you've written (emails, messages, etc.) so I can learn your style
3. **Your Values & Interests** - What matters to you and what you know a lot about

Would you like to:
- **Start the questionnaire** - I'll ask you one question at a time
- **Upload writing samples** - Share some text and I'll analyze your style
- **Do both** - The most accurate engram!

Just tell me how you'd like to proceed! 🧠✨"""
        
        return jsonify({
            'status': 'success',
            'message': intro,
            'questionnaire_sections': list(questionnaire.keys()),
            'total_questions': sum(len(qs) for qs in questionnaire.values())
        })
    
    except Exception as e:
        logger.error(f"Engram start error: {e}")
        return jsonify({'error': str(e)}), 500


# ============== INTERNET RESEARCH APIs ==============
# Allow Abby to search the web and fetch information

@app.route('/api/research/search', methods=['POST'])
def web_search():
    """Search the web using DuckDuckGo (no API key needed)"""
    try:
        import urllib.request
        import urllib.parse
        import json as json_lib
        import re
        
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({'error': 'Search query required'}), 400
        
        query = data['query']
        num_results = data.get('num_results', 5)
        
        # Use DuckDuckGo instant answer API
        encoded_query = urllib.parse.quote(query)
        url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'AbbyUnleashed/1.0'})
        
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json_lib.loads(response.read().decode('utf-8'))
        
        # Extract useful information
        search_results = {
            'query': query,
            'abstract': result.get('Abstract', ''),
            'abstract_source': result.get('AbstractSource', ''),
            'abstract_url': result.get('AbstractURL', ''),
            'answer': result.get('Answer', ''),
            'definition': result.get('Definition', ''),
            'related_topics': []
        }
        
        # Get related topics
        for topic in result.get('RelatedTopics', [])[:num_results]:
            if isinstance(topic, dict) and 'Text' in topic:
                search_results['related_topics'].append({
                    'text': topic.get('Text', ''),
                    'url': topic.get('FirstURL', '')
                })
        
        return jsonify({
            'status': 'success',
            'results': search_results
        })
    
    except Exception as e:
        logger.error(f"Web search error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/research/fetch', methods=['POST'])
def fetch_webpage():
    """Fetch and extract text content from a webpage"""
    try:
        import urllib.request
        import re
        from html.parser import HTMLParser
        
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({'error': 'URL required'}), 400
        
        url = data['url']
        
        # Security: only allow http/https
        if not url.startswith(('http://', 'https://')):
            return jsonify({'error': 'Invalid URL scheme'}), 400
        
        # Simple HTML text extractor
        class TextExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.text = []
                self.skip_tags = {'script', 'style', 'nav', 'footer', 'header'}
                self.current_tag = None
                
            def handle_starttag(self, tag, attrs):
                self.current_tag = tag
                
            def handle_endtag(self, tag):
                self.current_tag = None
                
            def handle_data(self, data):
                if self.current_tag not in self.skip_tags:
                    text = data.strip()
                    if text:
                        self.text.append(text)
        
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8', errors='replace')
        
        # Extract text
        extractor = TextExtractor()
        extractor.feed(html)
        
        # Join and clean text
        text = ' '.join(extractor.text)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Limit length
        max_length = data.get('max_length', 10000)
        if len(text) > max_length:
            text = text[:max_length] + '...'
        
        return jsonify({
            'status': 'success',
            'url': url,
            'content': text,
            'length': len(text)
        })
    
    except Exception as e:
        logger.error(f"Webpage fetch error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/research/ask', methods=['POST'])
def research_and_answer():
    """Search the web and have Abby answer based on findings"""
    try:
        import urllib.request
        import urllib.parse
        import json as json_lib
        
        data = request.get_json()
        
        if not data or 'question' not in data:
            return jsonify({'error': 'Question required'}), 400
        
        question = data['question']
        
        # First, search for relevant information
        encoded_query = urllib.parse.quote(question)
        url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'AbbyUnleashed/1.0'})
        
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                search_result = json_lib.loads(response.read().decode('utf-8'))
        except:
            search_result = {}
        
        # Build context from search
        context_parts = []
        if search_result.get('Abstract'):
            context_parts.append(f"From {search_result.get('AbstractSource', 'web')}: {search_result['Abstract']}")
        if search_result.get('Answer'):
            context_parts.append(f"Quick answer: {search_result['Answer']}")
        for topic in search_result.get('RelatedTopics', [])[:3]:
            if isinstance(topic, dict) and 'Text' in topic:
                context_parts.append(topic['Text'])
        
        research_context = '\n'.join(context_parts) if context_parts else "No specific information found."
        
        # Have Abby answer with the research context
        abby_instance = get_abby()
        
        enhanced_question = f"""The user asked: {question}

Here's what I found from searching online:
{research_context}

Please answer the user's question using this information. If the search didn't find relevant info, use your general knowledge but mention you couldn't find specific current information."""
        
        result = abby_instance.execute_task(enhanced_question)
        
        return jsonify({
            'status': 'success',
            'question': question,
            'research_found': bool(context_parts),
            'answer': result.get('output', 'I could not find an answer.')
        })
    
    except Exception as e:
        logger.error(f"Research error: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== ELEVENLABS TTS ====================

@app.route('/api/tts/synthesize', methods=['POST'])
def synthesize_speech():
    """
    Convert text to speech using ElevenLabs
    
    POST body:
        text: Text to synthesize
        settings: Optional voice settings (stability, similarity_boost, style)
    
    Returns:
        Audio file (audio/mpeg) or JSON error
    """
    try:
        from speech_interface.elevenlabs_tts import get_tts
        from flask import Response
        
        tts = get_tts()
        
        if not tts.is_configured:
            return jsonify({
                'error': 'ElevenLabs not configured',
                'help': 'Set ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID in .env'
            }), 503
        
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'Text required'}), 400
        
        text = data['text']
        settings = data.get('settings', {})
        
        # Synthesize audio (get bytes, not numpy array)
        audio_data = tts.synthesize_bytes(text, settings=settings)
        
        if audio_data:
            return Response(
                audio_data,
                mimetype='audio/mpeg',
                headers={
                    'Content-Disposition': 'inline',
                    'Cache-Control': 'public, max-age=3600'
                }
            )
        else:
            return jsonify({'error': 'Synthesis failed'}), 500
    
    except Exception as e:
        logger.error(f"TTS error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/tts/stream', methods=['POST'])
def stream_speech():
    """
    Stream text-to-speech audio (for long text)
    
    Returns streaming audio response
    """
    try:
        from speech_interface.elevenlabs_tts import get_tts
        from flask import Response
        
        tts = get_tts()
        
        if not tts.is_configured:
            return jsonify({
                'error': 'ElevenLabs not configured'
            }), 503
        
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'Text required'}), 400
        
        text = data['text']
        settings = data.get('settings', {})
        
        def generate():
            for chunk in tts.synthesize_stream(text, settings=settings):
                yield chunk
        
        return Response(
            generate(),
            mimetype='audio/mpeg',
            headers={
                'Transfer-Encoding': 'chunked',
                'Cache-Control': 'no-cache'
            }
        )
    
    except Exception as e:
        logger.error(f"TTS stream error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/tts/voices', methods=['GET'])
def list_voices():
    """List available ElevenLabs voices"""
    try:
        from speech_interface.elevenlabs_tts import get_tts
        
        tts = get_tts()
        
        if not tts.is_configured:
            return jsonify({
                'configured': False,
                'voices': [],
                'help': 'Set ELEVENLABS_API_KEY in .env'
            })
        
        voices_data = tts.get_voices()
        return jsonify({
            'configured': True,
            'current_voice': tts.voice_id,
            'voices': voices_data.get('voices', [])
        })
    
    except Exception as e:
        logger.error(f"Voices list error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/tts/status', methods=['GET'])
def tts_status():
    """Get ElevenLabs TTS status and usage"""
    try:
        from speech_interface.elevenlabs_tts import get_tts
        
        tts = get_tts()
        
        if not tts.is_configured:
            return jsonify({
                'configured': False,
                'api_key_set': bool(tts.api_key),
                'voice_id_set': bool(tts.voice_id),
                'help': 'Add ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID to .env'
            })
        
        user_info = tts.get_user_info()
        subscription = user_info.get('subscription', {})
        
        return jsonify({
            'configured': True,
            'voice_id': tts.voice_id,
            'model': tts.model_id,
            'characters_used': subscription.get('character_count', 0),
            'characters_limit': subscription.get('character_limit', 0),
            'tier': subscription.get('tier', 'unknown')
        })
    
    except Exception as e:
        logger.error(f"TTS status error: {e}")
        return jsonify({'error': str(e)}), 500


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500


# ==================== ENHANCED SERVER FEATURES ====================

# Enhanced server instance
_enhanced_server = None


def get_enhanced_server():
    """Get or create the enhanced server"""
    global _enhanced_server
    if _enhanced_server is None:
        from enhanced_server import get_enhanced_server as create_server
        _enhanced_server = create_server()
        _enhanced_server.start()
    return _enhanced_server


@app.route('/api/enhanced/status', methods=['GET'])
def enhanced_status():
    """Get enhanced server status"""
    try:
        server = get_enhanced_server()
        return jsonify(server.get_status())
    except Exception as e:
        logger.error(f"Enhanced status error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/enhanced/output-mode', methods=['GET', 'POST'])
def output_mode():
    """Get or set output mode"""
    try:
        server = get_enhanced_server()
        
        if request.method == 'GET':
            return jsonify({
                'mode': server.output_router.voice_mode.value,
                'available_modes': ['display', 'voice', 'both', 'summary']
            })
        
        data = request.get_json()
        mode = data.get('mode')
        
        if not mode:
            return jsonify({'error': 'Mode required'}), 400
        
        if server.set_output_mode(mode):
            return jsonify({
                'success': True,
                'mode': mode,
                'message': f'Output mode set to: {mode}'
            })
        else:
            return jsonify({
                'error': f'Invalid mode: {mode}',
                'available_modes': ['display', 'voice', 'both', 'summary']
            }), 400
    
    except Exception as e:
        logger.error(f"Output mode error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/enhanced/task', methods=['POST'])
def enhanced_task():
    """
    Process a task with parallel output.
    
    POST body:
        task: User's task/question
        conversation_id: Optional conversation ID
        output_mode: Optional override (display, voice, both, summary)
        speak: Whether to return voice audio (default: based on mode)
    
    Returns:
        display: Full text for display
        voice_text: Text that will be spoken (if any)
        voice_audio: Base64 audio (if speak=true)
    """
    try:
        data = request.get_json()
        
        if not data or 'task' not in data:
            return jsonify({'error': 'Task required'}), 400
        
        task = data['task']
        conversation_id = data.get('conversation_id', 'default')
        output_mode = data.get('output_mode')
        speak = data.get('speak', True)
        
        # Get enhanced server
        server = get_enhanced_server()
        
        # Set mode if specified
        if output_mode:
            from enhanced_server import OutputMode
            try:
                server.output_router.set_mode(OutputMode(output_mode))
            except ValueError:
                pass
        
        # Process task
        import asyncio
        
        # Run async in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                server.process_task(task, conversation_id)
            )
        finally:
            loop.close()
        
        response = {
            'task_id': result['task_id'],
            'display': result['display'],
            'voice_text': result['voice'],
            'voice_mode': result['voice_mode'],
            'status': result['result'].get('status', 'completed')
        }
        
        # Synthesize voice if requested
        if speak and result['voice']:
            try:
                from speech_interface.elevenlabs_tts import get_tts
                import base64
                
                tts = get_tts()
                if tts.is_configured:
                    audio_bytes = tts.synthesize_bytes(result['voice'])
                    if audio_bytes:
                        response['voice_audio'] = base64.b64encode(audio_bytes).decode('utf-8')
                        response['voice_format'] = 'mp3'
            except Exception as e:
                logger.warning(f"Voice synthesis error: {e}")
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Enhanced task error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/enhanced/reload', methods=['POST'])
def trigger_reload():
    """Manually trigger a hot reload"""
    try:
        server = get_enhanced_server()
        server._on_reload()
        return jsonify({
            'success': True,
            'message': 'Reload triggered'
        })
    except Exception as e:
        logger.error(f"Reload error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/enhanced/refresh-knowledge', methods=['POST'])
def refresh_knowledge():
    """Manually trigger knowledge refresh"""
    try:
        server = get_enhanced_server()
        server.background_learner.trigger_refresh()
        return jsonify({
            'success': True,
            'message': 'Knowledge refresh triggered',
            'last_refresh': server.background_learner.last_refresh.isoformat() if server.background_learner.last_refresh else None
        })
    except Exception as e:
        logger.error(f"Refresh error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/capabilities', methods=['GET'])
def get_capabilities():
    """
    Get Abby's full capabilities - what she and her agents can do.
    """
    capabilities = {
        "abby_core": {
            "description": "Abby Unleashed - Your AI assistant with a unique personality",
            "abilities": [
                "Natural conversation with personality",
                "Task execution (not just talking)",
                "Multi-agent orchestration",
                "Voice interaction (your cloned voice via ElevenLabs)",
                "Real-time web research",
                "Code generation and execution"
            ]
        },
        "action_execution": {
            "description": "Abby can actually DO things, not just describe them",
            "abilities": [
                "Create files and directories",
                "Edit existing files",
                "Run shell commands",
                "Execute Python code",
                "Run tests",
                "Git operations (commit, push, etc.)",
                "Research topics online"
            ]
        },
        "agent_system": {
            "description": "Dynamic agent creation with 5-element DNA",
            "dna_elements": [
                "Role - What the agent does",
                "Domain - Area of expertise",
                "Seniority - Level of experience",
                "Communication Style - How they interact",
                "Specializations - Specific skills"
            ],
            "features": [
                "Auto-create agents for new domains",
                "Save and reuse personas",
                "Agents research their domain to gain real expertise",
                "Sub-agents for complex tasks"
            ]
        },
        "knowledge_bases": {
            "description": "14 comprehensive knowledge bases for coding expertise",
            "domains": [
                "Coding foundations (AI vibe coding awareness)",
                "Python mastery",
                "JavaScript/TypeScript",
                "Kotlin",
                "Docker/containers",
                "Database (SQL/NoSQL)",
                "API design (REST)",
                "Git version control",
                "Testing patterns",
                "Security (OWASP)",
                "Performance optimization",
                "DevOps/CI-CD",
                "Error handling",
                "General programming (SOLID, Clean Code)"
            ]
        },
        "research_toolkit": {
            "description": "Agents can research to acquire real knowledge",
            "abilities": [
                "Web search and scraping",
                "Documentation fetching",
                "Build knowledge from multiple sources",
                "Save research for future use"
            ]
        },
        "voice_interface": {
            "description": "Voice interaction with your cloned voice",
            "features": [
                "Speech-to-text via browser/PersonaPlex",
                "Text-to-speech via ElevenLabs",
                "Wake word detection",
                "Voice activity detection"
            ]
        },
        "enhanced_server": {
            "description": "Advanced server features for continuous operation",
            "features": [
                "Hot reload (update code without restart)",
                "Background learning (periodic knowledge refresh)",
                "Parallel processing (display + voice)",
                "Smart output routing (save API costs)",
                "WebSocket real-time updates"
            ],
            "output_modes": {
                "display": "Show everything on screen, no voice",
                "voice": "Speak everything, minimal display",
                "both": "Display and speak full response",
                "summary": "Display full, speak condensed summary (saves ElevenLabs)"
            }
        }
    }
    
    return jsonify(capabilities)


# ============ REALTIME CONVERSATION API ============

def get_realtime_conversation():
    """Get realtime conversation instance."""
    try:
        from realtime_conversation import get_realtime_conversation as get_rtc
        rtc = get_rtc()
        rtc.abby = get_abby()
        return rtc
    except Exception as e:
        logger.error(f"Could not get realtime conversation: {e}")
        return None


@app.route('/api/realtime/status', methods=['GET'])
def realtime_status():
    """Get realtime conversation status."""
    try:
        rtc = get_realtime_conversation()
        if not rtc:
            return jsonify({'error': 'Realtime conversation not available'}), 500
        
        return jsonify({
            'state': rtc.state.value,
            'hot_mic_enabled': rtc.hot_mic_enabled,
            'auto_resume': rtc.auto_resume_listening,
            'history_length': len(rtc.conversation_history),
            'turn_count': rtc.turn_counter
        })
    except Exception as e:
        logger.error(f"Realtime status error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/realtime/settings', methods=['POST'])
def realtime_settings():
    """Update realtime conversation settings."""
    try:
        data = request.get_json()
        rtc = get_realtime_conversation()
        if not rtc:
            return jsonify({'error': 'Realtime conversation not available'}), 500
        
        if 'hot_mic_enabled' in data:
            rtc.hot_mic_enabled = bool(data['hot_mic_enabled'])
        if 'auto_resume' in data:
            rtc.auto_resume_listening = bool(data['auto_resume'])
        if 'silence_duration' in data:
            rtc.vad.silence_duration = float(data['silence_duration'])
        if 'energy_threshold' in data:
            rtc.vad.energy_threshold = float(data['energy_threshold'])
        
        return jsonify({
            'status': 'updated',
            'hot_mic_enabled': rtc.hot_mic_enabled,
            'auto_resume': rtc.auto_resume_listening,
            'silence_duration': rtc.vad.silence_duration,
            'energy_threshold': rtc.vad.energy_threshold
        })
    except Exception as e:
        logger.error(f"Realtime settings error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/realtime/conversation', methods=['POST'])
def realtime_conversation():
    """
    Process a conversation turn with rich display + voice summary.
    
    Request:
        {
            "transcript": "user's speech transcript",
            "speak": true  // whether to synthesize voice
        }
    
    Response:
        {
            "turn_id": "turn_1_...",
            "transcript": "user's input",
            "display_content": [
                {"type": "markdown", "content": "full response..."},
                {"type": "code", "content": "...", "language": "python"},
                {"type": "image", "content": "url", "alt_text": "..."}
            ],
            "voice_text": "summary for speech",
            "voice_audio": "base64 mp3 audio",
            "full_text": "complete unabridged response",
            "processing_time": 1.23
        }
    """
    try:
        data = request.get_json()
        
        if 'transcript' not in data:
            return jsonify({'error': 'transcript required'}), 400
        
        transcript = data['transcript'].strip()
        speak = data.get('speak', True)
        
        if not transcript:
            return jsonify({'error': 'Empty transcript'}), 400
        
        rtc = get_realtime_conversation()
        if not rtc:
            return jsonify({'error': 'Realtime conversation not available'}), 500
        
        # Process synchronously (async wrapper)
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(rtc.process_transcript(transcript))
        finally:
            loop.close()
        
        # Remove voice_audio if not requested
        if not speak and 'voice_audio' in result:
            del result['voice_audio']
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Realtime conversation error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/realtime/history', methods=['GET'])
def realtime_history():
    """Get conversation history."""
    try:
        rtc = get_realtime_conversation()
        if not rtc:
            return jsonify({'error': 'Realtime conversation not available'}), 500
        
        return jsonify({
            'history': rtc.get_conversation_history(),
            'turn_count': rtc.turn_counter
        })
    except Exception as e:
        logger.error(f"History error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/realtime/history', methods=['DELETE'])
def clear_realtime_history():
    """Clear conversation history."""
    try:
        rtc = get_realtime_conversation()
        if not rtc:
            return jsonify({'error': 'Realtime conversation not available'}), 500
        
        rtc.clear_history()
        return jsonify({'status': 'cleared'})
    except Exception as e:
        logger.error(f"Clear history error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/realtime/speaking-complete', methods=['POST'])
def speaking_complete():
    """Notify that TTS playback finished (for auto-resume)."""
    try:
        rtc = get_realtime_conversation()
        if not rtc:
            return jsonify({'error': 'Realtime conversation not available'}), 500
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(rtc.on_speaking_complete())
        finally:
            loop.close()
        
        return jsonify({
            'status': 'ok',
            'new_state': rtc.state.value,
            'listening': rtc.state.value == 'listening'
        })
    except Exception as e:
        logger.error(f"Speaking complete error: {e}")
        return jsonify({'error': str(e)}), 500


def start_server(host: str = '0.0.0.0', port: int = 8080, debug: bool = False):
    """
    Start the web API server
    
    Args:
        host: Host to bind to (0.0.0.0 for all interfaces)
        port: Port to bind to
        debug: Enable debug mode
    """
    logger.info(f"Starting Abby Unleashed API server on {host}:{port}")
    logger.info(f"Access from your phone: http://<your-pc-ip>:{port}")
    logger.info(f"To find your PC IP: Linux/Mac: ifconfig | Windows: ipconfig")
    
    # Initialize Abby
    get_abby()
    
    # Initialize enhanced server (starts background workers)
    try:
        get_enhanced_server()
        logger.info("Enhanced server features enabled")
    except Exception as e:
        logger.warning(f"Enhanced server features not available: {e}")
    
    # Start Flask server
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Abby Unleashed Web API Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    start_server(host=args.host, port=args.port, debug=args.debug)

