"""Vẽ chữ tiếng Việt có dấu lên khung hình OpenCV bằng Pillow.

cv2.putText không hỗ trợ đầy đủ Unicode, nên phải vẽ chữ bằng font TrueType.
Chỉ chuyển đổi ảnh sang Pillow một lần cho mỗi bảng điều khiển/khung hình.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


@lru_cache(maxsize=64)
def _font(size: int) -> ImageFont.FreeTypeFont:
    choices = (
        Path("C:/Windows/Fonts/segoeui.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    )
    for candidate in choices:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size)
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except OSError as exc:
        raise RuntimeError(
            "Không tìm thấy font hỗ trợ tiếng Việt. Hãy cài Segoe UI/Arial/DejaVu Sans."
        ) from exc


class VietnameseTextRenderer:
    def __init__(self) -> None:
        self._pending: dict[int, list[tuple[str, tuple[int, int], float,
                                             tuple[int, int, int], int]]] = {}

    def add(self, canvas: np.ndarray, text: str, pos: tuple[int, int],
            scale: float = 0.65, color: tuple[int, int, int] = (240, 245, 250),
            thickness: int = 2) -> None:
        self._pending.setdefault(id(canvas), []).append((text, pos, scale, color, thickness))

    def render(self, canvas: np.ndarray) -> np.ndarray:
        commands = self._pending.pop(id(canvas), ())
        if not commands:
            return canvas

        image = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
        painter = ImageDraw.Draw(image)
        for message, (x, y), scale, bgr, thickness in commands:
            size = max(11, round(29 * scale))
            font = _font(size)
            max_width = max(20, canvas.shape[1] - x - 7)
            # Tự thu nhỏ câu dài để không bị cắt bên phải bảng thông số.
            while (painter.textbbox((0, 0), message, font=font)[2] > max_width
                   and size > 11):
                size -= 1
                font = _font(size)
            painter.text((x, y), message, font=font, anchor="ls",
                         fill=(bgr[2], bgr[1], bgr[0]),
                         stroke_width=1 if thickness >= 3 else 0)
        return cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)
