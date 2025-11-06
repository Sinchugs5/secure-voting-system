# face_utils.py
import io
import base64
from PIL import Image
import face_recognition
import numpy as np
try:
    from fer import FER
    emotion_detector = FER(mtcnn=True)
except ImportError:
    emotion_detector = None
    print("FER not installed. Emotion detection disabled.")


def _b64_to_image_array(b64_string):
    # Accepts either 'data:image/png;base64,...' or raw base64
    if ',' in b64_string:
        _, b64data = b64_string.split(',', 1)
    else:
        b64data = b64_string
    img_bytes = base64.b64decode(b64data)
    img = face_recognition.load_image_file(io.BytesIO(img_bytes))
    return img


def get_face_encoding_from_base64(b64_string):
    img = _b64_to_image_array(b64_string)
    encodings = face_recognition.face_encodings(img)
    if len(encodings) == 0:
        raise ValueError('No face found in the image')
    if len(encodings) > 1:
        raise ValueError('Multiple faces detected. Please ensure only one person is in the photo.')
    return encodings[0].tolist()  # return as plain list (for JSON storage)


def compare_encodings(known_encoding, candidate_encoding, tolerance=0.4):
    # known_encoding and candidate_encoding are Python lists
    ke = np.array(known_encoding)
    ce = np.array(candidate_encoding)
    result = face_recognition.compare_faces([ke], ce, tolerance=tolerance)
    distance = face_recognition.face_distance([ke], ce)[0]
    return result[0], float(distance)

def detect_emotion_security(b64_string):
    """Detect emotions to identify potential coercion or duress"""
    if not emotion_detector:
        return True, "Emotion detection not available"
    
    try:
        img = _b64_to_image_array(b64_string)
        emotions = emotion_detector.detect_emotions(img)
        
        if not emotions:
            return True, "No face detected for emotion analysis"
        
        # Get dominant emotion
        emotion_scores = emotions[0]['emotions']
        dominant_emotion = max(emotion_scores, key=emotion_scores.get)
        confidence = emotion_scores[dominant_emotion]
        
        # Security flags for concerning emotions
        concerning_emotions = ['fear', 'sad', 'angry']
        stress_threshold = 0.6
        
        if dominant_emotion in concerning_emotions and confidence > stress_threshold:
            return False, f"Security alert: {dominant_emotion} detected ({confidence:.1%}). Please ensure you are voting freely."
        
        # Check for very low happiness/neutral (potential duress)
        if emotion_scores.get('happy', 0) < 0.1 and emotion_scores.get('neutral', 0) < 0.3:
            return False, "Security alert: Emotional distress detected. Please ensure you are voting without pressure."
        
        return True, f"Emotion check passed: {dominant_emotion} ({confidence:.1%})"
        
    except Exception as e:
        print(f"Emotion detection error: {e}")
        return True, "Emotion detection failed, proceeding with vote"
