"""
Visual Awareness Module for Abby Unleashed
Provides continuous visual perception using LOCAL processing only.

Uses:
- face_recognition (local) - Face detection & identification
- OpenCV (local) - Image processing & basic analysis
- Ollama (local) - Scene description when needed

NO external APIs except ElevenLabs for voice.
"""
import os
import json
import logging
import base64
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)

# Try imports
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False


class VisualAwareness:
    """
    Provides continuous visual awareness for Abby.
    All processing is done LOCALLY - no cloud APIs.
    """
    
    def __init__(self, data_dir: str = None):
        self.data_dir = Path(data_dir) if data_dir else Path(__file__).parent.parent / "data" / "vision"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Visual state
        self.is_watching = False
        self.current_frame = None
        self.last_analysis = None
        self.last_analysis_time = 0
        self.analysis_interval = 2.0  # Analyze every 2 seconds
        
        # Face tracking
        self.known_face_encodings = []
        self.known_face_names = []
        self.current_faces = []  # Currently visible faces
        self.face_history = deque(maxlen=30)  # Last 30 detections for smoothing
        
        # Callbacks
        self.on_person_entered: Optional[Callable] = None
        self.on_person_left: Optional[Callable] = None
        self.on_expression_change: Optional[Callable] = None
        
        # Load known faces from face_recognition module
        self._load_known_faces()
        
        logger.info(f"VisualAwareness initialized (local processing only)")
    
    @property
    def is_available(self) -> bool:
        return CV2_AVAILABLE and FACE_RECOGNITION_AVAILABLE
    
    def _load_known_faces(self):
        """Load known faces from the face recognition module"""
        try:
            from presence.face_recognition import get_face_recognizer
            recognizer = get_face_recognizer()
            
            for user_id, encodings in recognizer.known_faces.items():
                name = recognizer.known_names.get(user_id, user_id)
                for enc in encodings:
                    self.known_face_encodings.append(np.array(enc))
                    self.known_face_names.append(name)
            
            logger.info(f"Loaded {len(self.known_face_encodings)} known face encodings")
        except Exception as e:
            logger.warning(f"Could not load known faces: {e}")
    
    def analyze_frame(self, image_data: str) -> Dict[str, Any]:
        """
        Analyze a single frame for faces, expressions, and context.
        All processing is LOCAL.
        
        Args:
            image_data: Base64 encoded image
            
        Returns:
            Analysis results including faces, expressions, scene info
        """
        if not self.is_available:
            return {'error': 'Vision not available', 'available': False}
        
        try:
            # Decode image
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            nparr = np.frombuffer(image_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                return {'error': 'Could not decode image'}
            
            self.current_frame = frame
            
            # Convert to RGB for face_recognition
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Resize for faster processing (1/4 size)
            small_frame = cv2.resize(rgb_frame, (0, 0), fx=0.25, fy=0.25)
            
            # Detect faces
            face_locations = face_recognition.face_locations(small_frame)
            face_encodings = face_recognition.face_encodings(small_frame, face_locations)
            
            # Process each face
            faces = []
            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                # Scale back up
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
                
                # Try to identify
                name = "Unknown"
                confidence = 0
                
                if self.known_face_encodings:
                    distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                    if len(distances) > 0:
                        best_idx = np.argmin(distances)
                        if distances[best_idx] < 0.6:
                            name = self.known_face_names[best_idx]
                            confidence = 1 - distances[best_idx]
                
                # Analyze expression using landmarks
                face_landmarks = face_recognition.face_landmarks(rgb_frame, [(top, right, bottom, left)])
                expression = self._analyze_expression(face_landmarks[0] if face_landmarks else None)
                
                # Estimate head pose (basic)
                head_pose = self._estimate_head_pose(top, right, bottom, left, frame.shape)
                
                faces.append({
                    'name': name,
                    'confidence': round(confidence, 2),
                    'location': {'top': top, 'right': right, 'bottom': bottom, 'left': left},
                    'expression': expression,
                    'head_pose': head_pose,
                    'looking_at_camera': head_pose.get('facing_camera', False)
                })
            
            # Track face changes
            previous_names = {f['name'] for f in self.current_faces if f['name'] != 'Unknown'}
            current_names = {f['name'] for f in faces if f['name'] != 'Unknown'}
            
            # Detect entries/exits
            entered = current_names - previous_names
            left = previous_names - current_names
            
            self.current_faces = faces
            self.face_history.append(faces)
            
            # Build result
            result = {
                'timestamp': datetime.now().isoformat(),
                'faces_detected': len(faces),
                'faces': faces,
                'people_present': list(current_names) if current_names else ['Unknown'] if faces else [],
                'someone_looking': any(f.get('looking_at_camera') for f in faces),
                'scene': self._describe_scene(frame, faces)
            }
            
            if entered:
                result['entered'] = list(entered)
                if self.on_person_entered:
                    for name in entered:
                        self.on_person_entered(name)
            
            if left:
                result['left'] = list(left)
                if self.on_person_left:
                    for name in left:
                        self.on_person_left(name)
            
            self.last_analysis = result
            self.last_analysis_time = time.time()
            
            return result
            
        except Exception as e:
            logger.error(f"Frame analysis error: {e}")
            return {'error': str(e)}
    
    def _analyze_expression(self, landmarks: Optional[Dict]) -> Dict[str, Any]:
        """
        Analyze facial expression from landmarks (LOCAL processing).
        Basic detection of smile, eyes open/closed, eyebrows.
        """
        if not landmarks:
            return {'detected': False}
        
        try:
            expression = {'detected': True}
            
            # Analyze mouth for smile
            if 'top_lip' in landmarks and 'bottom_lip' in landmarks:
                top_lip = landmarks['top_lip']
                bottom_lip = landmarks['bottom_lip']
                
                # Mouth openness
                mouth_height = abs(top_lip[9][1] - bottom_lip[9][1])
                mouth_width = abs(top_lip[0][0] - top_lip[6][0])
                
                if mouth_width > 0:
                    mouth_ratio = mouth_height / mouth_width
                    expression['mouth_open'] = mouth_ratio > 0.3
                    
                    # Smile detection (corners up relative to center)
                    left_corner = top_lip[0][1]
                    right_corner = top_lip[6][1]
                    center = top_lip[3][1]
                    
                    smile_score = (center - (left_corner + right_corner) / 2) / mouth_width
                    expression['smiling'] = smile_score > 0.05
                    expression['smile_intensity'] = min(1.0, max(0, smile_score * 10))
            
            # Analyze eyes
            if 'left_eye' in landmarks and 'right_eye' in landmarks:
                left_eye = landmarks['left_eye']
                right_eye = landmarks['right_eye']
                
                # Eye openness
                left_height = abs(left_eye[1][1] - left_eye[5][1])
                right_height = abs(right_eye[1][1] - right_eye[5][1])
                
                avg_eye_height = (left_height + right_height) / 2
                expression['eyes_open'] = avg_eye_height > 3
                expression['possibly_tired'] = avg_eye_height < 5
            
            # Analyze eyebrows
            if 'left_eyebrow' in landmarks and 'right_eyebrow' in landmarks:
                left_brow = landmarks['left_eyebrow']
                right_brow = landmarks['right_eyebrow']
                
                # Brow position (raised or furrowed)
                if 'left_eye' in landmarks:
                    left_eye_top = min(p[1] for p in landmarks['left_eye'])
                    left_brow_bottom = max(p[1] for p in left_brow)
                    brow_distance = left_eye_top - left_brow_bottom
                    
                    expression['eyebrows_raised'] = brow_distance > 15
                    expression['possibly_surprised'] = brow_distance > 20
            
            # Overall mood estimate
            if expression.get('smiling') and expression.get('eyes_open'):
                expression['mood'] = 'happy'
            elif expression.get('possibly_tired'):
                expression['mood'] = 'tired'
            elif expression.get('possibly_surprised'):
                expression['mood'] = 'surprised'
            else:
                expression['mood'] = 'neutral'
            
            return expression
            
        except Exception as e:
            logger.debug(f"Expression analysis error: {e}")
            return {'detected': False, 'error': str(e)}
    
    def _estimate_head_pose(self, top: int, right: int, bottom: int, left: int, 
                           frame_shape: tuple) -> Dict[str, Any]:
        """Estimate head pose from face bounding box"""
        try:
            frame_height, frame_width = frame_shape[:2]
            
            face_center_x = (left + right) / 2
            face_center_y = (top + bottom) / 2
            face_width = right - left
            face_height = bottom - top
            
            # Position in frame
            x_offset = (face_center_x - frame_width / 2) / (frame_width / 2)
            y_offset = (face_center_y - frame_height / 2) / (frame_height / 2)
            
            # Face size relative to frame (closer = larger)
            face_size_ratio = face_width / frame_width
            
            return {
                'facing_camera': abs(x_offset) < 0.3 and abs(y_offset) < 0.3,
                'looking_left': x_offset < -0.2,
                'looking_right': x_offset > 0.2,
                'looking_up': y_offset < -0.2,
                'looking_down': y_offset > 0.2,
                'distance': 'close' if face_size_ratio > 0.3 else 'medium' if face_size_ratio > 0.15 else 'far',
                'position': {
                    'x': round(x_offset, 2),
                    'y': round(y_offset, 2)
                }
            }
        except Exception as e:
            return {'facing_camera': True}
    
    def _describe_scene(self, frame: np.ndarray, faces: List[Dict]) -> Dict[str, Any]:
        """Generate a basic scene description (LOCAL processing)"""
        try:
            height, width = frame.shape[:2]
            
            # Basic lighting analysis
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            brightness = np.mean(gray)
            
            if brightness < 50:
                lighting = 'dark'
            elif brightness < 100:
                lighting = 'dim'
            elif brightness < 180:
                lighting = 'normal'
            else:
                lighting = 'bright'
            
            # Contrast
            contrast = np.std(gray)
            
            return {
                'lighting': lighting,
                'brightness': round(brightness / 255, 2),
                'has_faces': len(faces) > 0,
                'face_count': len(faces),
                'frame_size': {'width': width, 'height': height}
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_visual_context(self) -> str:
        """
        Get a natural language description of what Abby currently sees.
        Used to inject into conversation context.
        """
        if not self.last_analysis:
            return ""
        
        analysis = self.last_analysis
        
        if analysis.get('faces_detected', 0) == 0:
            return "You can see through the camera but no one is currently visible."
        
        parts = []
        faces = analysis.get('faces', [])
        
        # Describe who's present
        names = [f['name'] for f in faces if f['name'] != 'Unknown']
        unknown_count = sum(1 for f in faces if f['name'] == 'Unknown')
        
        if names:
            if len(names) == 1:
                parts.append(f"You can see {names[0]} in front of the camera")
            else:
                parts.append(f"You can see {', '.join(names)} in front of the camera")
        
        if unknown_count:
            if names:
                parts.append(f"and {unknown_count} person{'s' if unknown_count > 1 else ''} you don't recognize")
            else:
                parts.append(f"You can see {unknown_count} person{'s' if unknown_count > 1 else ''} you don't recognize")
        
        # Describe expressions
        for face in faces:
            if face['name'] != 'Unknown' and face.get('expression', {}).get('detected'):
                expr = face['expression']
                mood = expr.get('mood', 'neutral')
                
                if mood == 'happy' or expr.get('smiling'):
                    parts.append(f"{face['name']} appears to be smiling")
                elif mood == 'tired':
                    parts.append(f"{face['name']} looks a bit tired")
                elif mood == 'surprised':
                    parts.append(f"{face['name']} looks surprised")
        
        # Describe attention
        looking = [f['name'] for f in faces if f.get('looking_at_camera') and f['name'] != 'Unknown']
        if looking:
            parts.append(f"{' and '.join(looking)} {'is' if len(looking) == 1 else 'are'} looking at you")
        
        # Lighting
        scene = analysis.get('scene', {})
        if scene.get('lighting') == 'dark':
            parts.append("The lighting is quite dark")
        elif scene.get('lighting') == 'dim':
            parts.append("The lighting is a bit dim")
        
        return ". ".join(parts) + "." if parts else ""
    
    def get_status(self) -> Dict[str, Any]:
        """Get current visual awareness status"""
        return {
            'available': self.is_available,
            'watching': self.is_watching,
            'faces_visible': len(self.current_faces),
            'people_present': [f['name'] for f in self.current_faces],
            'last_analysis_age': time.time() - self.last_analysis_time if self.last_analysis_time else None,
            'visual_context': self.get_visual_context()
        }


# Singleton
_visual_awareness: Optional[VisualAwareness] = None


def get_visual_awareness() -> VisualAwareness:
    """Get the visual awareness instance"""
    global _visual_awareness
    if _visual_awareness is None:
        _visual_awareness = VisualAwareness()
    return _visual_awareness
