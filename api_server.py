"""
Web API Server for Abby Unleashed
Enables mobile and remote access to the AI system
With user presence awareness - knows who she's talking to!
"""
import json
import logging
import os
import subprocess
import sys
from typing import Dict, Any, Optional, List
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
from datetime import datetime
import threading
from collections import deque
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

from cli import AbbyUnleashed
from presence.user_tracker import get_user_tracker, UserTracker
from skills_display import get_skills_manager
from plan_routes import plan_routes as plans_bp

logger = logging.getLogger(__name__)

# ============ LOG BUFFER FOR GUI ============
class LogBuffer(logging.Handler):
    """Captures logs in a buffer for GUI display"""
    def __init__(self, maxlen=500):
        super().__init__()
        self.buffer = deque(maxlen=maxlen)
        self.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s', datefmt='%H:%M:%S'))
    
    def emit(self, record):
        try:
            msg = self.format(record)
            self.buffer.append({
                'time': datetime.now().isoformat(),
                'level': record.levelname,
                'message': msg
            })
        except:
            pass
    
    def get_logs(self, count=100):
        return list(self.buffer)[-count:]
    
    def clear(self):
        self.buffer.clear()

# Global log buffer
log_buffer = LogBuffer()
logging.getLogger().addHandler(log_buffer)

# ============ NGROK MANAGER ============
class NgrokManager:
    """Manages ngrok tunnel lifecycle"""
    def __init__(self):
        self.process = None
        self.public_url = None
        self.is_running = False
        self._lock = threading.Lock()
    
    def find_ngrok_path(self) -> Optional[str]:
        """Find ngrok executable"""
        # Try common locations
        paths = [
            "ngrok",  # In PATH
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\ngrok\ngrok.exe"),
            r"C:\ngrok\ngrok.exe",
        ]
        
        for path in paths:
            try:
                expanded = os.path.expandvars(path)
                if os.path.exists(expanded):
                    return expanded
                # Try running it
                result = subprocess.run([path, "version"], capture_output=True, timeout=5)
                if result.returncode == 0:
                    return path
            except:
                continue
        
        # Search in WinGet packages
        try:
            winget_path = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages")
            for root, dirs, files in os.walk(winget_path):
                if "ngrok.exe" in files:
                    return os.path.join(root, "ngrok.exe")
        except:
            pass
        
        return None
    
    def start(self, port: int = 8080) -> Dict[str, Any]:
        """Start ngrok tunnel"""
        with self._lock:
            if self.is_running:
                return {'success': True, 'url': self.public_url, 'message': 'Already running'}
            
            ngrok_path = self.find_ngrok_path()
            if not ngrok_path:
                return {'success': False, 'error': 'ngrok not found. Install with: winget install ngrok.ngrok'}
            
            try:
                # Start ngrok
                self.process = subprocess.Popen(
                    [ngrok_path, "http", str(port)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )
                
                # Wait for tunnel to establish and get URL
                import time
                import requests
                for _ in range(30):  # Try for 15 seconds
                    time.sleep(0.5)
                    try:
                        resp = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=2)
                        tunnels = resp.json().get('tunnels', [])
                        for tunnel in tunnels:
                            if tunnel.get('proto') == 'https':
                                self.public_url = tunnel.get('public_url')
                                self.is_running = True
                                logger.info(f"🌐 Ngrok tunnel active: {self.public_url}")
                                return {'success': True, 'url': self.public_url}
                    except:
                        continue
                
                return {'success': False, 'error': 'Timeout waiting for ngrok tunnel'}
                
            except Exception as e:
                logger.error(f"Ngrok start error: {e}")
                return {'success': False, 'error': str(e)}
    
    def stop(self) -> Dict[str, Any]:
        """Stop ngrok tunnel"""
        with self._lock:
            if not self.is_running:
                return {'success': True, 'message': 'Not running'}
            
            try:
                if self.process:
                    self.process.terminate()
                    self.process.wait(timeout=5)
                    self.process = None
                
                self.public_url = None
                self.is_running = False
                logger.info("🌐 Ngrok tunnel stopped")
                return {'success': True}
            except Exception as e:
                logger.error(f"Ngrok stop error: {e}")
                return {'success': False, 'error': str(e)}
    
    def status(self) -> Dict[str, Any]:
        """Get ngrok status"""
        return {
            'running': self.is_running,
            'url': self.public_url
        }

# Global ngrok manager
ngrok_manager = NgrokManager()

# Mobile detection patterns
MOBILE_USER_AGENTS = [
    'Android', 'webOS', 'iPhone', 'iPad', 'iPod', 
    'BlackBerry', 'IEMobile', 'Opera Mini', 'Mobile', 'mobile'
]

def is_mobile_request() -> bool:
    """Check if request is from a mobile device"""
    user_agent = request.headers.get('User-Agent', '')
    return any(pattern in user_agent for pattern in MOBILE_USER_AGENTS)

def auto_start_ngrok_for_mobile():
    """Auto-start ngrok if mobile device detected and not using HTTPS"""
    if not is_mobile_request():
        return None
    
    # Check if already on ngrok or HTTPS
    host = request.host.lower()
    if 'ngrok' in host or request.is_secure:
        return None
    
    # Mobile on local network without HTTPS - start ngrok
    if not ngrok_manager.is_running:
        logger.info("📱 Mobile device detected - auto-starting ngrok for HTTPS...")
        result = ngrok_manager.start(8080)
        if result.get('success'):
            logger.info(f"📱 Ngrok auto-started: {result.get('url')}")
    
    return ngrok_manager.public_url

# Initialize Flask app
app = Flask(__name__, static_folder='web', static_url_path='')

# Enable CORS with restrictions for local network security (plus ngrok)
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:*",
            "http://127.0.0.1:*",
            "http://192.168.*.*:*",
            "http://10.*.*.*:*",
            "https://localhost:*",
            "https://127.0.0.1:*",
            "https://192.168.*.*:*",
            "https://10.*.*.*:*",
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
            "http://172.31.*.*:*",
            "https://172.16.*.*:*",
            "https://172.17.*.*:*",
            "https://172.18.*.*:*",
            "https://172.19.*.*:*",
            "https://172.20.*.*:*",
            "https://172.21.*.*:*",
            "https://172.22.*.*:*",
            "https://172.23.*.*:*",
            "https://172.24.*.*:*",
            "https://172.25.*.*:*",
            "https://172.26.*.*:*",
            "https://172.27.*.*:*",
            "https://172.28.*.*:*",
            "https://172.29.*.*:*",
            "https://172.30.*.*:*",
            "https://172.31.*.*:*",
            "https://*.ngrok-free.app",  # Ngrok tunnels
            "https://*.ngrok.io"
        ],
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type"]
    }
})

# Register Plan Manager API Blueprint
app.register_blueprint(plans_bp)

# Global Abby instance
abby: Optional[AbbyUnleashed] = None
abby_lock = threading.Lock()

# Global user tracker instance
user_tracker: Optional[UserTracker] = None


def get_user_tracker_instance() -> UserTracker:
    """Get or initialize UserTracker instance (thread-safe)"""
    global user_tracker
    with abby_lock:
        if user_tracker is None:
            user_tracker = get_user_tracker()
        return user_tracker


def get_abby():
    """Get or initialize Abby instance (thread-safe)"""
    global abby
    with abby_lock:
        if abby is None:
            abby = AbbyUnleashed(verbose=False)
        return abby


@app.route('/')
def index():
    """Serve mobile web interface - auto-starts ngrok for mobile devices"""
    ngrok_url = auto_start_ngrok_for_mobile()
    
    # If mobile and ngrok is now running, we could redirect
    # But better to let the client decide via JS
    return send_from_directory('web', 'index.html')


@app.route('/plans')
def plan_manager():
    """Serve Plan Manager GUI"""
    return send_from_directory('static', 'plan_manager.html')


@app.route('/api/mobile-redirect', methods=['GET'])
def mobile_redirect():
    """Check if mobile should redirect to ngrok URL"""
    ngrok_url = auto_start_ngrok_for_mobile()
    
    if ngrok_url and is_mobile_request() and not request.is_secure:
        return jsonify({
            'should_redirect': True,
            'ngrok_url': ngrok_url,
            'reason': 'Mobile device needs HTTPS for camera/mic access'
        })
    
    return jsonify({
        'should_redirect': False,
        'is_mobile': is_mobile_request(),
        'is_secure': request.is_secure
    })


@app.route('/cert.pem')
def download_cert():
    """Download SSL certificate for mobile installation"""
    try:
        return send_from_directory('ssl', 'cert.pem', 
                                   mimetype='application/x-pem-file',
                                   as_attachment=True,
                                   download_name='abby-unleashed-cert.pem')
    except:
        return "Certificate not found. Start server with --https first.", 404


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint - auto-starts ngrok for mobile"""
    try:
        # Auto-start ngrok for mobile devices
        ngrok_url = auto_start_ngrok_for_mobile()
        
        abby_instance = get_abby()
        ollama_healthy = abby_instance.ollama_client.health_check()
        
        response_data = {
            'status': 'healthy' if ollama_healthy else 'degraded',
            'ollama': 'connected' if ollama_healthy else 'disconnected',
            'timestamp': datetime.now().isoformat(),
            'ngrok': ngrok_manager.status(),
            'is_mobile': is_mobile_request()
        }
        
        # Suggest redirect for mobile on HTTP
        if ngrok_url and is_mobile_request() and not request.is_secure:
            response_data['suggest_redirect'] = ngrok_url
        
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


# ============== SKILLS & CHARACTER SHEET API ==============

@app.route('/api/skills', methods=['GET'])
def get_skills():
    """Get Abby's skills for RPG character sheet display"""
    try:
        skills_manager = get_skills_manager()
        return jsonify(skills_manager.get_all_skills())
    except Exception as e:
        logger.error(f"Skills fetch failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/skills/category/<category>', methods=['GET'])
def get_skills_by_category(category):
    """Get skills for a specific category"""
    try:
        skills_manager = get_skills_manager()
        all_skills = skills_manager.get_all_skills()
        if category in all_skills['categories']:
            return jsonify(all_skills['categories'][category])
        return jsonify({'error': f'Category {category} not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============== SERVER LOGS API ==============

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Get recent server logs"""
    try:
        return jsonify({
            'logs': log_buffer.get_logs(),
            'count': len(log_buffer.buffer)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs/clear', methods=['POST'])
def clear_logs():
    """Clear the log buffer"""
    try:
        log_buffer.clear()
        return jsonify({'success': True, 'message': 'Logs cleared'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============== AGENT ACTIVITY API ==============

# Global agent activity tracker
agent_activity = {
    'active': False,
    'current_task': None,
    'agents': [],
    'started_at': None
}

def update_agent_activity(active: bool, task_info: dict = None, agents: list = None):
    """Update the global agent activity state"""
    global agent_activity
    agent_activity['active'] = active
    agent_activity['current_task'] = task_info
    agent_activity['agents'] = agents or []
    if active:
        agent_activity['started_at'] = datetime.now().isoformat()

@app.route('/api/agent-activity', methods=['GET'])
def get_agent_activity():
    """Get current agent activity for the GUI preview"""
    try:
        return jsonify(agent_activity)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/agent-activity', methods=['POST'])
def set_agent_activity():
    """Update agent activity (called by task executor)"""
    try:
        data = request.get_json()
        update_agent_activity(
            active=data.get('active', False),
            task_info=data.get('current_task'),
            agents=data.get('agents', [])
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============== NGROK TUNNEL API ==============

@app.route('/api/ngrok/status', methods=['GET'])
def ngrok_status():
    """Get ngrok tunnel status"""
    try:
        status = ngrok_manager.status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ngrok/start', methods=['POST'])
def ngrok_start():
    """Start ngrok tunnel"""
    try:
        data = request.get_json() or {}
        port = data.get('port', 8080)
        
        result = ngrok_manager.start(port)
        if result.get('success'):
            logger.info(f"Ngrok tunnel started: {result.get('url')}")
            return jsonify(result)
        else:
            return jsonify(result), 500
    except Exception as e:
        logger.error(f"Failed to start ngrok: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ngrok/stop', methods=['POST'])
def ngrok_stop():
    """Stop ngrok tunnel"""
    try:
        result = ngrok_manager.stop()
        if result.get('success'):
            logger.info("Ngrok tunnel stopped")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Failed to stop ngrok: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============== PRESENCE & IDENTITY APIs ==============
# Track who's connected and customize Abby's responses

@app.route('/api/presence/session', methods=['POST'])
def create_or_get_session():
    """
    Create or retrieve a session for the connected user.
    Call this when the web app first loads.
    
    Returns session_id and available users for identification.
    """
    try:
        tracker = get_user_tracker_instance()
        
        # Get connection info
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        # Check if client already has a session
        data = request.get_json() or {}
        existing_session_id = data.get('session_id')
        
        # Get or create session
        session = tracker.get_or_create_session(
            session_id=existing_session_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return jsonify({
            'session_id': session.session_id,
            'user_id': session.user_id,
            'display_name': session.display_name,
            'device': session.device_info,
            'available_users': tracker.list_available_users(),
            'greeting': tracker.get_greeting(session.session_id) if session.user_id != 'unknown' else None,
            'is_identified': session.user_id != 'unknown'
        })
    
    except Exception as e:
        logger.error(f"Session creation error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/presence/identify', methods=['POST'])
def identify_user():
    """
    Identify who is using this session.
    
    POST body:
        session_id: The current session ID
        user_id: The user to identify as (e.g., 'organic_abby', 'boyfriend')
    """
    try:
        data = request.get_json()
        
        if not data or 'session_id' not in data or 'user_id' not in data:
            return jsonify({'error': 'session_id and user_id required'}), 400
        
        tracker = get_user_tracker_instance()
        result = tracker.identify_user(data['session_id'], data['user_id'])
        
        if result.get('success'):
            logger.info(f"User identified: {result['display_name']} ({result['user_id']})")
            return jsonify(result)
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"User identification error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/presence/users', methods=['GET'])
def list_available_users():
    """List available user profiles that can be selected"""
    try:
        tracker = get_user_tracker_instance()
        return jsonify({
            'users': tracker.list_available_users()
        })
    
    except Exception as e:
        logger.error(f"List users error: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== FACE RECOGNITION ====================

@app.route('/api/face/status', methods=['GET'])
def face_recognition_status():
    """Check if face recognition is available and configured"""
    try:
        from presence.face_recognition import get_face_recognizer
        recognizer = get_face_recognizer()
        
        return jsonify({
            'available': recognizer.is_available,
            'known_users': len(recognizer.known_faces),
            'users': recognizer.get_known_users()
        })
    except Exception as e:
        logger.error(f"Face status error: {e}")
        return jsonify({'available': False, 'error': str(e)})


@app.route('/api/face/detect', methods=['POST'])
def detect_faces():
    """
    Detect and recognize faces in an image.
    
    POST body:
        image: Base64 encoded image
        
    Returns:
        faces_detected: Number of faces found
        faces: List of face info with recognition results
    """
    try:
        from presence.face_recognition import get_face_recognizer
        recognizer = get_face_recognizer()
        
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'error': 'Image required'}), 400
        
        result = recognizer.process_image(data['image'])
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Face detect error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/face/learn', methods=['POST'])
def learn_face():
    """
    Learn a new face for a user.
    
    POST body:
        user_id: Unique identifier (e.g., 'organic_abby', 'boyfriend')
        name: Display name
        image: Base64 encoded image with the face
        
    Returns:
        success: Whether learning succeeded
        total_samples: Number of face samples for this user
    """
    try:
        from presence.face_recognition import get_face_recognizer
        recognizer = get_face_recognizer()
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Data required'}), 400
        
        user_id = data.get('user_id')
        name = data.get('name')
        image = data.get('image')
        
        if not all([user_id, name, image]):
            return jsonify({'error': 'user_id, name, and image are required'}), 400
        
        result = recognizer.learn_face(user_id, name, image)
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Face learn error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/face/identify', methods=['POST'])
def identify_face():
    """
    Identify who is in front of the camera and update their session.
    Combines face detection with presence tracking.
    
    POST body:
        image: Base64 encoded image
        session_id: Optional session to update
        
    Returns:
        recognized: Whether a known face was found
        user_id: ID of recognized user (if any)
        session_updated: Whether the session was updated
    """
    try:
        from presence.face_recognition import get_face_recognizer
        recognizer = get_face_recognizer()
        
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'error': 'Image required'}), 400
        
        # Detect faces
        result = recognizer.process_image(data['image'])
        
        if result.get('error'):
            return jsonify(result)
        
        # Look for a recognized face
        recognized_user = None
        for face in result.get('faces', []):
            if face.get('recognized') and face.get('confidence', 0) >= 0.5:
                recognized_user = face
                break
        
        response = {
            'faces_detected': result.get('faces_detected', 0),
            'recognized': recognized_user is not None
        }
        
        if recognized_user:
            response['user_id'] = recognized_user['user_id']
            response['name'] = recognized_user['name']
            response['confidence'] = recognized_user['confidence']
            
            # Update session if provided
            session_id = data.get('session_id')
            if session_id:
                tracker = get_user_tracker_instance()
                tracker.identify_user(session_id, recognized_user['user_id'])
                response['session_updated'] = True
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Face identify error: {e}")
        return jsonify({'error': str(e)}), 500


# ===== Visual Awareness Endpoints (LOCAL processing only) =====

@app.route('/api/vision/status', methods=['GET'])
def vision_status():
    """
    Get current visual awareness status.
    Shows what Abby currently "sees".
    """
    try:
        from presence.visual_awareness import get_visual_awareness
        vision = get_visual_awareness()
        return jsonify(vision.get_status())
    except Exception as e:
        logger.error(f"Vision status error: {e}")
        return jsonify({'error': str(e), 'available': False})


@app.route('/api/vision/analyze', methods=['POST'])
def vision_analyze():
    """
    Analyze a camera frame for faces, expressions, and scene context.
    ALL processing is LOCAL - no external APIs.
    
    POST body:
        image: Base64 encoded image (with or without data: prefix)
        
    Returns:
        faces_detected: Number of faces found
        faces: Array of face info with identity, expression, position
        people_present: Names of recognized people
        scene: Basic scene info (lighting, etc)
    """
    try:
        from presence.visual_awareness import get_visual_awareness
        vision = get_visual_awareness()
        
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'error': 'Image required'}), 400
        
        result = vision.analyze_frame(data['image'])
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Vision analyze error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/vision/context', methods=['GET'])
def vision_context():
    """
    Get natural language description of what Abby sees.
    Used to inject visual awareness into conversations.
    
    Returns:
        context: String describing what Abby sees
        faces_visible: Number of faces currently visible
    """
    try:
        from presence.visual_awareness import get_visual_awareness
        vision = get_visual_awareness()
        
        return jsonify({
            'context': vision.get_visual_context(),
            'faces_visible': len(vision.current_faces),
            'people_present': [f['name'] for f in vision.current_faces],
            'last_analysis': vision.last_analysis
        })
    
    except Exception as e:
        logger.error(f"Vision context error: {e}")
        return jsonify({'error': str(e), 'context': ''})


@app.route('/api/presence/active', methods=['GET'])
def list_active_sessions():
    """List all active sessions (for admin/debug)"""
    try:
        tracker = get_user_tracker_instance()
        return jsonify({
            'sessions': tracker.list_active_sessions()
        })
    
    except Exception as e:
        logger.error(f"List sessions error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/presence/context', methods=['POST'])
def get_user_context():
    """
    Get the full context for a session.
    Useful for debugging or showing user info.
    """
    try:
        data = request.get_json() or {}
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'error': 'session_id required'}), 400
        
        tracker = get_user_tracker_instance()
        context = tracker.get_user_context(session_id)
        
        return jsonify(context)
    
    except Exception as e:
        logger.error(f"Get context error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/task', methods=['POST'])
def execute_task():
    """Execute a task with user presence and visual awareness"""
    try:
        data = request.get_json()
        
        if not data or 'task' not in data:
            return jsonify({'error': 'Task description required'}), 400
        
        task = data['task']
        context = data.get('context', {})
        use_orchestrator = data.get('use_orchestrator', True)
        session_id = data.get('session_id')
        visual_context = data.get('visual_context', '')  # From camera/vision system
        
        # Inject user presence context if we have a session
        if session_id:
            tracker = get_user_tracker_instance()
            user_context = tracker.get_user_context(session_id)
            context['user_presence'] = user_context
            context['user_prompt_addition'] = tracker.get_system_prompt_addition(session_id)
        
        # Add visual context if provided (LOCAL processing)
        if visual_context:
            existing_prompt = context.get('user_prompt_addition', '')
            context['user_prompt_addition'] = f"{existing_prompt}\n\n{visual_context}" if existing_prompt else visual_context
            logger.info(f"Task visual context: {visual_context[:100]}...")
        
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


# ============ STREAMING CONVERSATION API ============

def get_streaming_conversation_instance():
    """Get the streaming conversation instance with Abby attached"""
    try:
        from streaming_conversation import get_streaming_conversation
        sc = get_streaming_conversation()
        sc.abby = get_abby()
        return sc
    except Exception as e:
        logger.error(f"Could not get streaming conversation: {e}")
        return None


@app.route('/api/stream/chat', methods=['POST'])
def stream_chat():
    """
    Stream a conversation response using Server-Sent Events.
    
    Request body:
        - message: The user's message
        - session_id: Optional session ID for user context
        - visual_context: Optional visual context from camera
    
    Returns:
        SSE stream with events:
        - thinking: Abby's thought process
        - text: Response text (can be partial)
        - step: Progress on multi-step tasks
        - action: Actions being performed
        - done: Response complete
        - error: Something went wrong
    """
    # IMPORTANT: Extract request data BEFORE the generator function
    # Flask request context is not available inside generators after first yield
    data = request.get_json() or {}
    message = data.get('message', '')
    session_id = data.get('session_id')
    visual_context = data.get('visual_context', '')
    
    # Build context while still in request context
    context = {}
    if session_id:
        tracker = get_user_tracker_instance()
        context['user_presence'] = tracker.get_user_context(session_id)
        context['user_prompt_addition'] = tracker.get_system_prompt_addition(session_id)
    
    if visual_context:
        existing = context.get('user_prompt_addition', '')
        context['user_prompt_addition'] = f"{existing}\n\n{visual_context}" if existing else visual_context
    
    def generate_stream():
        try:
            if not message:
                yield f"data: {json.dumps({'type': 'error', 'content': 'No message provided'})}\n\n"
                return
            
            # Get streaming conversation
            sc = get_streaming_conversation_instance()
            if not sc:
                yield f"data: {json.dumps({'type': 'error', 'content': 'Streaming not available'})}\n\n"
                return
            
            # Stream the response
            for event in sc.stream_response(message, context):
                yield event.to_sse()
            
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
    
    return Response(
        generate_stream(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'  # Disable nginx buffering
        }
    )


@app.route('/api/stream/status', methods=['GET'])
def stream_status():
    """Get current streaming conversation status"""
    try:
        sc = get_streaming_conversation_instance()
        if not sc:
            return jsonify({'error': 'Streaming not available'}), 500
        
        return jsonify(sc.get_status())
    
    except Exception as e:
        logger.error(f"Stream status error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/stream/interrupt', methods=['POST'])
def stream_interrupt():
    """
    Interrupt the current streaming response.
    
    Request body:
        - redirect: Optional new message to redirect to
    """
    try:
        sc = get_streaming_conversation_instance()
        if not sc:
            return jsonify({'error': 'Streaming not available'}), 500
        
        data = request.get_json() or {}
        redirect_message = data.get('redirect')
        
        success = sc.interrupt(redirect_message)
        
        return jsonify({
            'success': success,
            'message': 'Interrupt requested' if success else 'Nothing to interrupt'
        })
    
    except Exception as e:
        logger.error(f"Interrupt error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/stream/user-speaking', methods=['POST'])
def stream_user_speaking():
    """
    Notify that user started speaking (for natural interrupts).
    Called by the UI when VAD or speech recognition detects user voice.
    """
    try:
        sc = get_streaming_conversation_instance()
        if not sc:
            return jsonify({'error': 'Streaming not available'}), 500
        
        interrupted = sc.on_user_started_speaking()
        
        return jsonify({
            'interrupted': interrupted,
            'state': sc.state.value
        })
    
    except Exception as e:
        logger.error(f"User speaking notification error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/stream/clear', methods=['POST'])
def stream_clear():
    """Clear streaming conversation history"""
    try:
        sc = get_streaming_conversation_instance()
        if not sc:
            return jsonify({'error': 'Streaming not available'}), 500
        
        sc.clear_history()
        return jsonify({'success': True})
    
    except Exception as e:
        logger.error(f"Clear error: {e}")
        return jsonify({'error': str(e)}), 500


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


@app.route('/api/current_model', methods=['GET'])
def get_current_model():
    """Get the current conversation model being used"""
    try:
        # Get the conversation model from environment
        conversation_model = os.getenv("DEFAULT_MODEL", "mistral:latest")
        
        # Note: qwen3-coder is only used for actual coding tasks
        # Conversation/personality uses the smaller, faster mistral model
        return jsonify({
            'conversation_model': conversation_model,
            'coding_model': 'qwen3-coder:30b',
            'description': 'Conversations use mistral for personality. Coding tasks use qwen3-coder.'
        })
    
    except Exception as e:
        logger.error(f"Current model error: {e}")
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
    Process a task with parallel output and user presence awareness.
    
    POST body:
        task: User's task/question
        conversation_id: Optional conversation ID
        session_id: Optional session ID for user presence
        output_mode: Optional override (display, voice, both, summary)
        speak: Whether to return voice audio (default: based on mode)
    
    Returns:
        display: Full text for display
        voice_text: Text that will be spoken (if any)
        voice_audio: Base64 audio (if speak=true)
        user_context: Current user identity info
    """
    try:
        data = request.get_json()
        
        if not data or 'task' not in data:
            return jsonify({'error': 'Task required'}), 400
        
        task = data['task']
        conversation_id = data.get('conversation_id', 'default')
        session_id = data.get('session_id')
        output_mode = data.get('output_mode')
        speak = data.get('speak', True)
        
        # Get user presence context
        user_context = None
        user_prompt_addition = ""
        if session_id:
            tracker = get_user_tracker_instance()
            user_context = tracker.get_user_context(session_id)
            user_prompt_addition = tracker.get_system_prompt_addition(session_id)
        
        # Get enhanced server
        server = get_enhanced_server()
        
        # Inject user context into the server's personality if available
        if user_prompt_addition:
            # Store original and add user context temporarily
            # This affects how Abby responds
            server._user_context = user_prompt_addition
        
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
                server.process_task(task, conversation_id, user_context=user_context)
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
        
        # Add user context to response if available
        if user_context:
            response['user_context'] = {
                'user_id': user_context.get('user_id'),
                'display_name': user_context.get('display_name'),
                'relationship': user_context.get('relationship')
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
        import traceback
        logger.error(f"Enhanced task error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
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
    Now with user presence awareness and visual context!
    
    Request:
        {
            "transcript": "user's speech transcript",
            "speak": true,  // whether to synthesize voice
            "session_id": "optional session for presence",
            "visual_context": "[Visual context: I can see John...]"  // from camera
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
            "processing_time": 1.23,
            "user_context": {...}  // if session provided
        }
    """
    try:
        data = request.get_json()
        
        if 'transcript' not in data:
            return jsonify({'error': 'transcript required'}), 400
        
        transcript = data['transcript'].strip()
        speak = data.get('speak', True)
        session_id = data.get('session_id')
        visual_context = data.get('visual_context', '')  # From camera/vision system
        
        if not transcript:
            return jsonify({'error': 'Empty transcript'}), 400
        
        # Get user presence context if session provided
        user_context = None
        user_prompt_addition = ""
        if session_id:
            tracker = get_user_tracker_instance()
            user_context = tracker.get_user_context(session_id)
            user_prompt_addition = tracker.get_system_prompt_addition(session_id)
        
        # Add visual context to prompt addition if provided (LOCAL processing)
        if visual_context:
            visual_note = f"\n\n{visual_context}"
            user_prompt_addition = user_prompt_addition + visual_note if user_prompt_addition else visual_note
            logger.info(f"Visual context injected: {visual_context[:100]}...")
        
        rtc = get_realtime_conversation()
        if not rtc:
            return jsonify({'error': 'Realtime conversation not available'}), 500
        
        # Process synchronously (async wrapper)
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                rtc.process_transcript(transcript, user_context=user_context, user_prompt_addition=user_prompt_addition)
            )
        finally:
            loop.close()
        
        # Remove voice_audio if not requested
        if not speak and 'voice_audio' in result:
            del result['voice_audio']
        
        # Add user context to response if available
        if user_context:
            result['user_context'] = {
                'user_id': user_context.get('user_id'),
                'display_name': user_context.get('display_name'),
                'relationship': user_context.get('relationship')
            }
        
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


def start_server(host: str = '0.0.0.0', port: int = 8080, debug: bool = False, https: bool = False):
    """
    Start the web API server using Waitress (production WSGI server)
    
    Args:
        host: Host to bind to (0.0.0.0 for all interfaces)
        port: Port to bind to
        debug: Enable debug mode (uses Flask dev server if True)
        https: Enable HTTPS with self-signed certificate
    """
    protocol = "https" if https else "http"
    logger.info(f"Starting Abby Unleashed API server on {protocol}://{host}:{port}")
    logger.info(f"Access from your phone: {protocol}://<your-pc-ip>:{port}")
    logger.info(f"To find your PC IP: Linux/Mac: ifconfig | Windows: ipconfig")
    
    if https:
        logger.info("🔐 HTTPS enabled - mobile camera will work!")
        logger.info("⚠️  Accept the self-signed certificate warning in your browser")
    
    # Initialize Abby
    get_abby()
    
    # Initialize local speech recognition (Vosk)
    try:
        from local_speech import register_speech_routes, get_speech_recognizer
        register_speech_routes(app)
        recognizer = get_speech_recognizer()
        if recognizer.is_available:
            logger.info("🎤 Local speech recognition enabled (Vosk)")
        else:
            logger.warning("Local speech recognition not available - model may be missing")
    except Exception as e:
        logger.warning(f"Could not initialize local speech: {e}")
    
    # Initialize enhanced server (starts background workers)
    try:
        get_enhanced_server()
        logger.info("Enhanced server features enabled")
    except Exception as e:
        logger.warning(f"Enhanced server features not available: {e}")
    
    # Use Waitress production server (much better for streaming and threading)
    # Fall back to Flask dev server only if debug=True
    if debug:
        logger.warning("⚠️ Debug mode: Using Flask development server (not for production)")
        if https:
            cert_file = "ssl/cert.pem"
            key_file = "ssl/key.pem"
            if not os.path.exists(cert_file) or not os.path.exists(key_file):
                logger.info("Generating SSL certificates...")
                from generate_ssl_cert import generate_ssl_cert
                cert_file, key_file = generate_ssl_cert()
            app.run(host=host, port=port, debug=debug, threaded=True, ssl_context=(cert_file, key_file))
        else:
            app.run(host=host, port=port, debug=debug, threaded=True)
    else:
        # Production mode: Use Waitress WSGI server
        try:
            from waitress import serve
            logger.info("🚀 Using Waitress production WSGI server")
            logger.info(f"Server ready at http://{host}:{port}")
            
            if https:
                # For HTTPS with Waitress, we need to use a reverse proxy or wrapper
                # For now, fall back to Flask's SSL support with threaded mode
                logger.warning("HTTPS with Waitress requires reverse proxy - using Flask SSL")
                cert_file = "ssl/cert.pem"
                key_file = "ssl/key.pem"
                if not os.path.exists(cert_file) or not os.path.exists(key_file):
                    logger.info("Generating SSL certificates...")
                    from generate_ssl_cert import generate_ssl_cert
                    cert_file, key_file = generate_ssl_cert()
                app.run(host=host, port=port, debug=False, threaded=True, ssl_context=(cert_file, key_file))
            else:
                # Waitress handles threading properly - great for streaming responses
                serve(app, host=host, port=port, threads=8, connection_limit=100,
                      channel_timeout=120, recv_bytes=65536,
                      url_scheme='http')
        except ImportError:
            logger.warning("Waitress not installed - falling back to Flask dev server")
            logger.warning("Install with: pip install waitress")
            app.run(host=host, port=port, debug=False, threaded=True)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Abby Unleashed Web API Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--https', action='store_true', help='Enable HTTPS for mobile camera support')
    parser.add_argument('--no-browser', action='store_true', help='Do not auto-launch Abby Browser')
    
    args = parser.parse_args()
    
    # Auto-launch Abby Browser unless disabled
    if not args.no_browser:
        import subprocess
        import threading
        import time
        
        def launch_browser():
            """Launch Abby Browser after a short delay to let server start"""
            time.sleep(2)  # Wait for server to be ready
            browser_path = os.path.join(os.path.dirname(__file__), 'abby_browser.py')
            if os.path.exists(browser_path):
                protocol = 'https' if args.https else 'http'
                url = f"{protocol}://localhost:{args.port}"
                logger.info(f"🚀 Launching Abby Browser -> {url}")
                try:
                    # Use pythonw to avoid extra console window, fall back to python
                    python_exe = sys.executable
                    pythonw = python_exe.replace('python.exe', 'pythonw.exe')
                    if os.path.exists(pythonw):
                        subprocess.Popen([pythonw, browser_path, url], 
                                       creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                    else:
                        subprocess.Popen([python_exe, browser_path, url],
                                       creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                except Exception as e:
                    logger.warning(f"Could not launch Abby Browser: {e}")
            else:
                logger.warning("Abby Browser not found - open http://localhost:8080 manually")
        
        # Start browser launch in background thread
        threading.Thread(target=launch_browser, daemon=True).start()
    
    start_server(host=args.host, port=args.port, debug=args.debug, https=args.https)


