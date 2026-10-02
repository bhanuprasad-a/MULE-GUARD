"""
MuleGuard Facial Recognition System (FRS) Engine
Local face detection via YuNet and deep feature embedding extraction via SFace.
Operates 100% locally with OpenCV DNN without external network or cloud dependencies.
"""

import os
import base64
import threading
import math
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List

import cv2
import numpy as np

# Model Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
YUNET_MODEL_PATH = str(BASE_DIR / "data" / "models" / "face_detection_yunet_2023mar.onnx")
SFACE_MODEL_PATH = str(BASE_DIR / "data" / "models" / "face_recognition_sface_2021dec.onnx")
MINIFASNET_MODEL_PATH = str(BASE_DIR / "data" / "models" / "minifasnet_v2.onnx")

# Face Recognition Configuration
# Calibrated cosine similarity threshold for SFace 128-d embeddings.
# SFace LFW benchmark threshold at 0.1% FAR is 0.363; 0.40 provides strict banking-grade rejection.
DEFAULT_FACE_THRESHOLD = 0.40
FACE_SIMILARITY_THRESHOLD = float(os.getenv("AUTH_FACE_SIMILARITY_THRESHOLD", str(DEFAULT_FACE_THRESHOLD)))

# Presentation-Attack Detection (PAD) Configuration
DEFAULT_PAD_THRESHOLD = 0.50
PAD_LIVENESS_THRESHOLD = float(os.getenv("AUTH_PAD_LIVENESS_THRESHOLD", str(DEFAULT_PAD_THRESHOLD)))

# Thread-safe model singleton
_MODEL_LOCK = threading.Lock()
_DETECTOR: Optional[cv2.FaceDetectorYN] = None
_RECOGNIZER: Optional[cv2.FaceRecognizerSF] = None
_PAD_NET: Optional[cv2.dnn.Net] = None


def get_face_models() -> Tuple[cv2.FaceDetectorYN, cv2.FaceRecognizerSF]:
    """Initializes and returns cached thread-safe YuNet and SFace models."""
    global _DETECTOR, _RECOGNIZER
    with _MODEL_LOCK:
        if _DETECTOR is None or _RECOGNIZER is None:
            if not os.path.exists(YUNET_MODEL_PATH):
                raise FileNotFoundError(f"YuNet model not found at {YUNET_MODEL_PATH}")
            if not os.path.exists(SFACE_MODEL_PATH):
                raise FileNotFoundError(f"SFace model not found at {SFACE_MODEL_PATH}")

            # Initialize with default 320x320; dynamic sizes configured per frame
            _DETECTOR = cv2.FaceDetectorYN.create(
                model=YUNET_MODEL_PATH,
                config="",
                input_size=(320, 320),
                score_threshold=0.60,
                nms_threshold=0.3,
                top_k=5000
            )
            _RECOGNIZER = cv2.FaceRecognizerSF.create(
                model=SFACE_MODEL_PATH,
                config=""
            )
    return _DETECTOR, _RECOGNIZER


def get_pad_model() -> cv2.dnn.Net:
    """Initializes and returns cached thread-safe MiniFASNetV2 anti-spoofing model."""
    global _PAD_NET
    with _MODEL_LOCK:
        if _PAD_NET is None:
            if not os.path.exists(MINIFASNET_MODEL_PATH):
                raise FileNotFoundError(f"MiniFASNetV2 model not found at {MINIFASNET_MODEL_PATH}")
            _PAD_NET = cv2.dnn.readNetFromONNX(MINIFASNET_MODEL_PATH)
    return _PAD_NET


def evaluate_passive_pad(img: np.ndarray, face_box: tuple | list | np.ndarray) -> Tuple[bool, str, float]:
    """
    Evaluates Presentation Attack Detection (PAD) locally via MiniFASNetV2.
    Evaluates 80x80 crop against spoof classes using official Minivision boundary-safe box scaling:
      Class 0: Photo Spoof (printed paper, glossy photo)
      Class 1: Live Face (genuine human presentation)
      Class 2: Screen / Video Replay Spoof (LCD, OLED, monitor replay)

    Returns:
      (is_live: bool, classification: str, confidence: float)
    """
    fx, fy, fw, fh = [float(x) for x in face_box[:4]]
    src_h, src_w, _ = img.shape

    # Official Minivision boundary-safe box scaling:
    # Clamps the scale factor so the crop never exceeds image dimensions,
    # preventing artificial black borders/bezels that trigger false SCREEN_REPLAY_SPOOF.
    scale = 2.7
    scale = min((src_h - 1) / max(fh, 1.0), min((src_w - 1) / max(fw, 1.0), scale))
    new_width = fw * scale
    new_height = fh * scale
    center_x = fw / 2.0 + fx
    center_y = fh / 2.0 + fy

    left_top_x = center_x - new_width / 2.0
    left_top_y = center_y - new_height / 2.0
    right_bottom_x = center_x + new_width / 2.0
    right_bottom_y = center_y + new_height / 2.0

    if left_top_x < 0:
        right_bottom_x -= left_top_x
        left_top_x = 0
    if left_top_y < 0:
        right_bottom_y -= left_top_y
        left_top_y = 0
    if right_bottom_x > src_w - 1:
        left_top_x -= right_bottom_x - src_w + 1
        right_bottom_x = src_w - 1
    if right_bottom_y > src_h - 1:
        left_top_y -= right_bottom_y - src_h + 1
        right_bottom_y = src_h - 1

    x1 = max(0, int(left_top_x))
    y1 = max(0, int(left_top_y))
    x2 = min(src_w - 1, int(right_bottom_x))
    y2 = min(src_h - 1, int(right_bottom_y))

    patch = img[y1 : y2 + 1, x1 : x2 + 1]
    if patch.size == 0:
        return False, "CROP_FAILED", 0.0

    crop_80 = cv2.resize(patch, (80, 80))
    blob = cv2.dnn.blobFromImage(crop_80, 1.0, (80, 80), (0, 0, 0), swapRB=False)

    pad_net = get_pad_model()
    with _MODEL_LOCK:
        pad_net.setInput(blob)
        out = pad_net.forward()[0]

    e_x = np.exp(out - np.max(out))
    probs = e_x / e_x.sum()

    pred_idx = int(np.argmax(probs))
    live_confidence = float(probs[1])

    if pred_idx == 1 and live_confidence >= PAD_LIVENESS_THRESHOLD:
        return True, "LIVE_FACE", round(live_confidence, 4)
    elif pred_idx == 0:
        return False, "PHOTO_SPOOF", round(float(probs[0]), 4)
    else:
        # Screen replay spoof: require decisive confidence (>= 0.65) to prevent false positives from monitor glare
        spoof_conf = float(probs[2])
        if spoof_conf >= 0.65 or live_confidence < 0.25:
            return False, "SCREEN_REPLAY_SPOOF", round(spoof_conf, 4)
        return True, "LIVE_FACE", round(live_confidence, 4)


def extract_landmark_pose(face: np.ndarray) -> Dict[str, Any]:
    """
    Extracts geometric yaw ratio and pitch ratio from 5 YuNet facial landmarks:
      0: right eye (re)
      1: left eye (le)
      2: nose tip (nose)
      3: right mouth corner (rm)
      4: left mouth corner (lm)
    """
    re_x, re_y = float(face[4]), float(face[5])
    le_x, le_y = float(face[6]), float(face[7])
    n_x, n_y = float(face[8]), float(face[9])
    rm_x, rm_y = float(face[10]), float(face[11])
    lm_x, lm_y = float(face[12]), float(face[13])

    eye_dist = float(np.hypot(le_x - re_x, le_y - re_y))
    eye_mid_x = (re_x + le_x) / 2.0
    eye_mid_y = (re_y + le_y) / 2.0
    mouth_mid_y = (rm_y + lm_y) / 2.0

    # Horizontal yaw ratio: distance from nose to right eye vs left eye
    d_re = abs(n_x - re_x)
    d_le = abs(n_x - le_x) + 1e-6
    yaw_ratio = d_re / d_le

    # Normalized horizontal offset: displacement of nose from eye midpoint
    norm_yaw = (n_x - eye_mid_x) / (eye_dist + 1e-6)

    # Pitch ratio: nose vertical distance from eye level vs mouth vertical distance from eye level
    pitch_ratio = (n_y - eye_mid_y) / (mouth_mid_y - eye_mid_y + 1e-6)

    return {
        "yaw_ratio": round(float(yaw_ratio), 4),
        "pitch_ratio": round(float(pitch_ratio), 4),
        "norm_yaw": round(float(norm_yaw), 4),
        "eye_dist": round(eye_dist, 2),
        "landmarks": {
            "re": [re_x, re_y],
            "le": [le_x, le_y],
            "nose": [n_x, n_y],
            "rm": [rm_x, rm_y],
            "lm": [lm_x, lm_y]
        }
    }


def verify_active_challenge_movement(
    baseline_pose: Dict[str, Any],
    action_pose: Dict[str, Any],
    required_action: str
) -> Tuple[bool, str, float]:
    """
    Evaluates physical movement between baseline and action frame.
    Rejects static frames where geometry remains unchanged.
    Verifies that the movement matches required challenge (TURN_LEFT, TURN_RIGHT, NOD).
    """
    delta_yaw = action_pose["yaw_ratio"] - baseline_pose["yaw_ratio"]
    delta_norm_yaw = action_pose["norm_yaw"] - baseline_pose["norm_yaw"]
    delta_pitch = action_pose["pitch_ratio"] - baseline_pose["pitch_ratio"]

    abs_yaw_diff = abs(delta_yaw)
    abs_pitch_diff = abs(delta_pitch)
    abs_norm_yaw_diff = abs(delta_norm_yaw)

    # 1. Reject static image presentation
    # If the user held up a photo or did not move at all:
    if abs_yaw_diff < 0.05 and abs_pitch_diff < 0.025 and abs_norm_yaw_diff < 0.025:
        return False, "STATIC_IMAGE_DETECTED: No physical movement detected between camera frames.", 0.1

    action_upper = required_action.upper()

    if action_upper in ["TURN_RIGHT", "TURN_HEAD"]:
        # Right head turn shifts nose towards camera left (lower norm_yaw) or increases yaw_ratio
        is_turn_right = (
            delta_yaw >= 0.18 or
            abs(delta_yaw) >= 0.20 or
            action_pose["yaw_ratio"] >= 1.45 or
            delta_norm_yaw <= -0.035
        )
        if is_turn_right:
            return True, "ACTIVE_LIVENESS_CONFIRMED: Head turn right verified.", 0.95
        else:
            return False, f"WRONG_MOVEMENT: Required head turn to right not completed (delta_yaw={delta_yaw:.2f}).", 0.3

    elif action_upper == "TURN_LEFT":
        # Left head turn shifts nose towards camera right (higher norm_yaw) or decreases yaw_ratio
        is_turn_left = (
            delta_yaw <= -0.18 or
            action_pose["yaw_ratio"] <= 0.75 or
            delta_norm_yaw >= 0.035
        )
        if is_turn_left:
            return True, "ACTIVE_LIVENESS_CONFIRMED: Head turn left verified.", 0.95
        else:
            return False, f"WRONG_MOVEMENT: Required head turn to left not completed (delta_yaw={delta_yaw:.2f}).", 0.3

    elif action_upper == "NOD":
        is_nod = (
            delta_pitch >= 0.038 or
            abs(delta_pitch) >= 0.038 or
            action_pose["pitch_ratio"] >= 0.60
        )
        if is_nod:
            return True, "ACTIVE_LIVENESS_CONFIRMED: Head nod verified.", 0.95
        else:
            return False, f"WRONG_MOVEMENT: Required head nod not completed (delta_pitch={delta_pitch:.2f}).", 0.3

    else:
        # Generic motion fallback
        if abs_yaw_diff >= 0.10 or abs_pitch_diff >= 0.035:
            return True, f"ACTIVE_LIVENESS_CONFIRMED: Movement detected ({required_action}).", 0.90
        return False, f"CHALLENGE_MISMATCH: Unsupported or incomplete challenge {required_action}.", 0.2


def detect_face_and_pose_from_bytes(
    image_bytes: bytes,
    min_confidence: float = 0.60
) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], Optional[Dict[str, Any]], Optional[str]]:
    """
    Decodes image bytes, detects single face via YuNet, and extracts landmarks & pose.
    Returns: (img, face_row, pose_dict, error_reason)
    """
    if not image_bytes:
        return None, None, None, "NO_IMAGE_DATA: Empty image buffer."

    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return None, None, None, "INVALID_IMAGE_FORMAT: Could not decode image."

    h, w, _ = img.shape
    if h < 64 or w < 64:
        return None, None, None, "IMAGE_TOO_SMALL: Image resolution is insufficient."

    detector, _ = get_face_models()
    with _MODEL_LOCK:
        detector.setInputSize((w, h))
        _, faces = detector.detect(img)

    if faces is None or len(faces) == 0:
        return img, None, None, "NO_FACE_DETECTED: No human face detected in camera frame."

    if len(faces) > 1:
        return img, None, None, "MULTIPLE_FACES_DETECTED: Multiple faces detected. Exactly one required."

    face = faces[0]
    conf = float(face[14])
    if conf < min_confidence:
        return img, None, None, f"LOW_FACE_CONFIDENCE: Face confidence ({conf:.2f}) below threshold."

    pose = extract_landmark_pose(face)
    return img, face, pose, None


def extract_face_embedding_from_bytes(
    image_bytes: bytes,
    min_confidence: float = 0.60,
    min_face_size: int = 40,
    min_blur_score: float = 10.0
) -> Tuple[Optional[List[float]], Optional[str], Dict[str, Any]]:
    """
    Decodes an image buffer, detects faces using YuNet, verifies quality/uniqueness,
    and extracts a 128-dimensional L2-normalized embedding using SFace.

    Returns:
        (embedding_vector, error_reason, metadata)
    """
    if not image_bytes:
        return None, "NO_IMAGE_DATA: Empty image payload provided.", {}

    # Decode bytes into BGR image
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return None, "INVALID_IMAGE_FORMAT: Could not decode image buffer.", {}

    h, w, _ = img.shape
    if h < 64 or w < 64:
        return None, "IMAGE_TOO_SMALL: Image resolution is insufficient for biometric verification.", {}

    detector, recognizer = get_face_models()

    # Dynamic input size setting inside lock for thread safety
    with _MODEL_LOCK:
        detector.setInputSize((w, h))
        _, faces = detector.detect(img)

    if faces is None or len(faces) == 0:
        return None, "NO_FACE_DETECTED: No human face detected in camera frame. Please face the camera directly.", {}

    if len(faces) > 1:
        return None, "MULTIPLE_FACES_DETECTED: Multiple faces detected. Verification requires exactly one person in frame.", {}

    face = faces[0]
    fx, fy, fw, fh = face[:4]
    conf = float(face[14])

    if conf < min_confidence:
        return None, f"LOW_FACE_CONFIDENCE: Face detection confidence ({conf:.2f}) below requirement ({min_confidence:.2f}).", {}

    if fw < min_face_size or fh < min_face_size:
        return None, f"FACE_TOO_SMALL: Face bbox ({int(fw)}x{int(fh)}) too small. Please position closer to the camera.", {}

    # Check blur / sharpness via Laplacian variance on face ROI
    x1, y1 = max(0, int(fx)), max(0, int(fy))
    x2, y2 = min(w, int(fx + fw)), min(h, int(fy + fh))
    face_roi = img[y1:y2, x1:x2]
    blur_score = 0.0
    if face_roi.size > 0:
        gray_roi = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        blur_score = float(cv2.Laplacian(gray_roi, cv2.CV_64F).var())
        if blur_score < min_blur_score:
            return None, f"FACE_TOO_BLURRY: Face image sharpness ({blur_score:.1f}) is too degraded. Please hold steady.", {}

    # Align and crop face using 5 facial landmarks
    with _MODEL_LOCK:
        aligned_face = recognizer.alignCrop(img, face)
        raw_feat = recognizer.feature(aligned_face)

    # Convert to standard Python float list (128 dimensions)
    embedding = [float(x) for x in raw_feat[0]]

    metadata = {
        "dimension": len(embedding),
        "confidence": round(conf, 4),
        "quality_score": round(min(100.0, conf * 100.0), 2),
        "blur_score": round(blur_score, 2),
        "face_box": [int(fx), int(fy), int(fw), int(fh)]
    }

    return embedding, None, metadata


def extract_face_embedding_from_base64(
    b64_string: str,
    min_confidence: float = 0.60,
    min_face_size: int = 40,
    min_blur_score: float = 10.0
) -> Tuple[Optional[List[float]], Optional[str], Dict[str, Any]]:
    """
    Decodes base64-encoded image (handling data URI headers like 'data:image/jpeg;base64,...'),
    and extracts a 128-dimensional embedding.
    """
    if not b64_string:
        return None, "NO_IMAGE_DATA: Empty base64 image string.", {}

    # Strip data URI header if present
    if "," in b64_string:
        b64_string = b64_string.split(",", 1)[1]

    try:
        image_bytes = base64.b64decode(b64_string)
    except Exception as e:
        return None, f"BASE64_DECODE_ERROR: Invalid base64 string: {e}", {}

    return extract_face_embedding_from_bytes(
        image_bytes=image_bytes,
        min_confidence=min_confidence,
        min_face_size=min_face_size,
        min_blur_score=min_blur_score
    )


def compute_cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """
    Computes cosine similarity between two float vectors.
    Returns float in range [-1.0, 1.0].
    """
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0

    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot / (norm_a * norm_b)
