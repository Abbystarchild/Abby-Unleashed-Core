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
