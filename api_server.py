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


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500


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
