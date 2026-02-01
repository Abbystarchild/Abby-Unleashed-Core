"""
Face Recognition Module for Abby Unleashed
Allows Abby to see and recognize users via webcam

Uses face_recognition library (dlib-based) for:
- Face detection
- Face encoding (128-dimensional embeddings)
- Face matching against known users
"""
import os
import json
import logging
import base64
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import face recognition libraries
try:
    import face_recognition
    import cv2
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    logger.warning("face_recognition or cv2 not installed. Camera features disabled.")
    logger.warning("Install with: pip install face_recognition opencv-python")


class FaceRecognizer:
    """
    Recognizes faces and matches them to known users.
    Integrates with the user presence system.
    """
    
    def __init__(self, data_dir: str = None):
        """
        Initialize the face recognizer.
        
        Args:
            data_dir: Directory to store face encodings and photos
        """
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = Path(__file__).parent.parent / "data" / "faces"
        
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.encodings_file = self.data_dir / "face_encodings.json"
        
        # Known faces: {user_id: [list of 128-dim encodings]}
        self.known_faces: Dict[str, List[List[float]]] = {}
        self.known_names: Dict[str, str] = {}  # user_id -> display name
        
        # Recognition settings
        self.tolerance = 0.6  # Lower = more strict matching
        self.min_confidence = 0.5
        
        # Load existing encodings
        self._load_encodings()
        
        logger.info(f"FaceRecognizer initialized with {len(self.known_faces)} known users")
    
    @property
    def is_available(self) -> bool:
        """Check if face recognition is available"""
        return FACE_RECOGNITION_AVAILABLE
    
    def _load_encodings(self):
        """Load saved face encodings from disk"""
        if self.encodings_file.exists():
            try:
                with open(self.encodings_file, 'r') as f:
                    data = json.load(f)
                    self.known_faces = data.get('encodings', {})
                    self.known_names = data.get('names', {})
                logger.info(f"Loaded {len(self.known_faces)} face profiles")
            except Exception as e:
                logger.error(f"Error loading face encodings: {e}")
    
    def _save_encodings(self):
        """Save face encodings to disk"""
        try:
            with open(self.encodings_file, 'w') as f:
                json.dump({
                    'encodings': self.known_faces,
                    'names': self.known_names,
                    'updated': datetime.now().isoformat()
                }, f)
            logger.info("Face encodings saved")
        except Exception as e:
            logger.error(f"Error saving face encodings: {e}")
    
    def process_image(self, image_data: str) -> Dict[str, Any]:
        """
        Process a base64 image and detect/recognize faces.
        
        Args:
            image_data: Base64 encoded image (with or without data URI prefix)
            
        Returns:
            Dict with detected faces and recognition results
        """
        if not FACE_RECOGNITION_AVAILABLE:
            return {
                'error': 'Face recognition not available',
                'help': 'Install with: pip install face_recognition opencv-python'
            }
        
        try:
            # Decode base64 image
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                return {'error': 'Could not decode image'}
            
            # Convert BGR to RGB (face_recognition uses RGB)
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Find faces
            face_locations = face_recognition.face_locations(rgb_image)
            face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
            
            if not face_locations:
                return {
                    'faces_detected': 0,
                    'message': 'No faces detected in image'
                }
            
            # Process each detected face
            results = []
            for i, (face_loc, face_enc) in enumerate(zip(face_locations, face_encodings)):
                top, right, bottom, left = face_loc
                
                # Try to match against known faces
                match = self._find_match(face_enc)
                
                results.append({
                    'index': i,
                    'location': {
                        'top': top,
                        'right': right,
                        'bottom': bottom,
                        'left': left
                    },
                    'recognized': match is not None,
                    'user_id': match['user_id'] if match else None,
                    'name': match['name'] if match else 'Unknown',
                    'confidence': match['confidence'] if match else 0
                })
            
            return {
                'faces_detected': len(face_locations),
                'faces': results,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return {'error': str(e)}
    
    def _find_match(self, face_encoding: np.ndarray) -> Optional[Dict]:
        """
        Find a match for a face encoding in known faces.
        
        Returns:
            Dict with user_id, name, confidence if match found, else None
        """
        if not self.known_faces:
            return None
        
        best_match = None
        best_distance = float('inf')
        
        for user_id, encodings in self.known_faces.items():
            # Compare against all encodings for this user
            for known_enc in encodings:
                distance = face_recognition.face_distance([known_enc], face_encoding)[0]
                
                if distance < best_distance and distance < self.tolerance:
                    best_distance = distance
                    confidence = 1 - distance  # Convert distance to confidence
                    
                    if confidence >= self.min_confidence:
                        best_match = {
                            'user_id': user_id,
                            'name': self.known_names.get(user_id, user_id),
                            'confidence': round(confidence, 3),
                            'distance': round(distance, 3)
                        }
        
        return best_match
    
    def learn_face(self, user_id: str, name: str, image_data: str) -> Dict[str, Any]:
        """
        Learn a new face for a user.
        
        Args:
            user_id: Unique user identifier
            name: Display name for the user
            image_data: Base64 encoded image containing the face
            
        Returns:
            Dict with success status and info
        """
        if not FACE_RECOGNITION_AVAILABLE:
            return {
                'error': 'Face recognition not available',
                'help': 'Install with: pip install face_recognition opencv-python'
            }
        
        try:
            # Decode image
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                return {'error': 'Could not decode image'}
            
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Find faces
            face_locations = face_recognition.face_locations(rgb_image)
            
            if not face_locations:
                return {
                    'success': False,
                    'error': 'No face detected in image',
                    'help': 'Make sure your face is clearly visible and well-lit'
                }
            
            if len(face_locations) > 1:
                return {
                    'success': False,
                    'error': f'Multiple faces detected ({len(face_locations)})',
                    'help': 'Please use an image with only one face'
                }
            
            # Get face encoding
            face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
            face_encoding = face_encodings[0].tolist()
            
            # Add to known faces
            if user_id not in self.known_faces:
                self.known_faces[user_id] = []
            
            self.known_faces[user_id].append(face_encoding)
            self.known_names[user_id] = name
            
            # Save photo for reference
            photo_path = self.data_dir / f"{user_id}_{len(self.known_faces[user_id])}.jpg"
            cv2.imwrite(str(photo_path), image)
            
            # Save encodings
            self._save_encodings()
            
            return {
                'success': True,
                'user_id': user_id,
                'name': name,
                'total_samples': len(self.known_faces[user_id]),
                'message': f"Learned face for {name}! Total samples: {len(self.known_faces[user_id])}"
            }
            
        except Exception as e:
            logger.error(f"Error learning face: {e}")
            return {'error': str(e)}
    
    def get_known_users(self) -> List[Dict]:
        """Get list of users with learned faces"""
        return [
            {
                'user_id': uid,
                'name': self.known_names.get(uid, uid),
                'samples': len(encodings)
            }
            for uid, encodings in self.known_faces.items()
        ]
    
    def remove_user(self, user_id: str) -> Dict:
        """Remove a user's face data"""
        if user_id in self.known_faces:
            del self.known_faces[user_id]
            if user_id in self.known_names:
                del self.known_names[user_id]
            self._save_encodings()
            return {'success': True, 'message': f'Removed face data for {user_id}'}
        return {'success': False, 'error': 'User not found'}


# Singleton instance
_face_recognizer: Optional[FaceRecognizer] = None


def get_face_recognizer() -> FaceRecognizer:
    """Get the face recognizer instance"""
    global _face_recognizer
    if _face_recognizer is None:
        _face_recognizer = FaceRecognizer()
    return _face_recognizer
