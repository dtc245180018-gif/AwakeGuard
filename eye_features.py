"""The shared eye preprocessing and feature pipeline (training and webcam)."""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageOps

WIDTH = 48
HEIGHT = 32


def to_gray_image(image: Image.Image | np.ndarray) -> np.ndarray:
    """Normalize an eye crop into the same 32x48 grayscale representation."""
    if isinstance(image, np.ndarray):
        if image.ndim == 3:
            # App crops BGR images; convert without a mandatory cv2 import.
            array = image.astype(np.float32)
            image = Image.fromarray(np.uint8(np.clip(
                array[:, :, 0] * 0.114 + array[:, :, 1] * 0.587 +
                array[:, :, 2] * 0.299, 0, 255
            )), "L")
        else:
            image = Image.fromarray(np.asarray(image, dtype=np.uint8), "L")
    img = ImageOps.autocontrast(image.convert("L"), cutoff=1)
    img = ImageOps.fit(img, (WIDTH, HEIGHT), method=Image.Resampling.BILINEAR)
    return np.asarray(img, dtype=np.float32) / 255.0


def hog_feature(image: Image.Image | np.ndarray) -> np.ndarray:
    """Tiny HOG descriptor with local 2x2 block normalization.

    Implemented in NumPy to keep inference independent of scikit-image.
    """
    pixels = to_gray_image(image)
    dy, dx = np.gradient(pixels)
    magnitude = np.hypot(dx, dy)
    angle = (np.arctan2(dy, dx) % np.pi) / np.pi * 9.0
    bins = np.floor(angle).astype(np.int32) % 9
    fractions = angle - np.floor(angle)
    hist = np.zeros((4, 6, 9), dtype=np.float32)
    for cy in range(4):
        for cx in range(6):
            y0, x0 = cy * 8, cx * 8
            mag = magnitude[y0:y0 + 8, x0:x0 + 8]
            b = bins[y0:y0 + 8, x0:x0 + 8]
            frac = fractions[y0:y0 + 8, x0:x0 + 8]
            hist[cy, cx] = (
                np.bincount(b.ravel(), weights=(mag * (1 - frac)).ravel(), minlength=9)
                + np.bincount(((b + 1) % 9).ravel(), weights=(mag * frac).ravel(), minlength=9)
            )
    blocks = []
    for cy in range(3):
        for cx in range(5):
            block = hist[cy:cy + 2, cx:cx + 2].ravel()
            blocks.append(block / np.sqrt(np.dot(block, block) + 1e-5))
    return np.concatenate(blocks).astype(np.float32)


# MediaPipe Face Landmarker 468-point topology: corner, upper1, upper2,
# opposite corner, lower2, lower1.
EYE_LANDMARKS = ((33, 160, 158, 133, 153, 144),
                 (362, 385, 387, 263, 373, 380))


def eye_aspect_ratio(landmarks, width: int, height: int, indices) -> float:
    pts = np.array([(landmarks[i].x * width, landmarks[i].y * height)
                    for i in indices], dtype=np.float32)
    horizontal = max(float(np.linalg.norm(pts[0] - pts[3])), 1e-6)
    return float((np.linalg.norm(pts[1] - pts[5]) +
                  np.linalg.norm(pts[2] - pts[4])) / (2 * horizontal))


def extract_eye_crop(frame: np.ndarray, landmarks, indices) -> np.ndarray | None:
    """Extract an aligned crop around the visible eye; do not crop by eyelid height."""
    import cv2

    height, width = frame.shape[:2]
    a = np.array([landmarks[indices[0]].x * width,
                  landmarks[indices[0]].y * height], dtype=np.float32)
    b = np.array([landmarks[indices[3]].x * width,
                  landmarks[indices[3]].y * height], dtype=np.float32)
    eye_width = float(np.linalg.norm(b - a))
    if eye_width < 12.0:
        return None
    center = (a + b) / 2
    angle = np.degrees(np.arctan2(b[1] - a[1], b[0] - a[0]))
    rotation = cv2.getRotationMatrix2D(tuple(center), angle, 1.0)
    rotated = cv2.warpAffine(frame, rotation, (width, height),
                             flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
    # Fixed proportions ensure a closed eye doesn't produce a zero-height crop.
    crop_w, crop_h = eye_width * 1.5, eye_width * 0.90
    x0, x1 = int(center[0] - crop_w / 2), int(center[0] + crop_w / 2)
    y0, y1 = int(center[1] - crop_h / 2), int(center[1] + crop_h / 2)
    x0, x1 = max(0, x0), min(width, x1)
    y0, y1 = max(0, y0), min(height, y1)
    if x1 - x0 < 12 or y1 - y0 < 8:
        return None
    return rotated[y0:y1, x0:x1].copy()
