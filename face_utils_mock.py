# Mock face_utils for deployment without face recognition libraries
def get_face_encoding_from_base64(photo_data_url):
    """Mock function - returns dummy encoding for deployment"""
    return [0.1] * 128  # Standard face encoding length

def compare_encodings(current_encoding, stored_encoding, tolerance=0.6):
    """Mock function - always returns True for deployment"""
    return True, 0.3  # Always match with low distance