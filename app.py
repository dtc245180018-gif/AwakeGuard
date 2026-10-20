"""Trình diễn cảnh báo buồn ngủ qua webcam (giao diện tiếng Việt)."""

from __future__ import annotations

import argparse
import sys
import threading
import time
from pathlib import Path

import cv2
import joblib
import mediapipe as mp
import numpy as np

from eye_features import EYE_LANDMARKS, extract_eye_crop, eye_aspect_ratio, hog_feature
from head_monitor import DriverMonitor, head_pitch_degrees
from vi_text import VietnameseTextRenderer

ROOT = Path(__file__).resolve().parent
EYE_MODEL = ROOT / "models" / "eye_state_svm.joblib"
FACE_MODEL = ROOT / "models" / "face_landmarker.task"
TEXT_RENDERER = VietnameseTextRenderer()
REASON_NAMES = {
    "EYES CLOSED": "Nhắm mắt quá lâu",
    "HEAD NOD": "Gật/cúi đầu bất thường",
    "HEAD DROP": "Đầu gục xuống sâu",
    "FACE LOST": "Mất dấu khuôn mặt",
}
EYE_MODES = {"hybrid": "Kết hợp", "model": "AI", "geometry": "Hình học"}
HEAD_POLICIES = {"balanced": "Cân bằng", "eyes_confirmed": "Theo mắt"}


def sound_warning():
    if sys.platform == "win32":
        try:
            import winsound
            winsound.Beep(1100, 340)
            winsound.Beep(850, 340)
        except RuntimeError:
            print("\a", end="", flush=True)
    else:
        print("\a", end="", flush=True)


def draw_text(canvas, line, pos, scale=0.65, color=(240, 245, 250), thickness=2):
    TEXT_RENDERER.add(canvas, line, pos, scale, color, thickness)


def eye_prediction(model, crops):
    if len(crops) < 2 or any(c is None for c in crops):
        return None
    features = np.stack([hog_feature(c) for c in crops])
    probabilities = model.predict_proba(features)
    idx_closed = list(model.classes_).index(0)
    return float(np.mean(probabilities[:, idx_closed]))


def main():
    parser = argparse.ArgumentParser(description="Cảnh báo dấu hiệu ngủ gật bằng webcam (đồ án học tập)")
    parser.add_argument("--camera", type=int, default=0, help="Chỉ số camera (mặc định: 0)")
    parser.add_argument("--video", type=Path, help="Đọc video thay cho camera trực tiếp")
    parser.add_argument("--seconds", type=float, default=1.5,
                        help="Số giây nhắm mắt liên tục để cảnh báo")
    parser.add_argument("--head-degrees", type=float, default=17.0,
                        help="Góc cúi đầu so với tư thế thẳng (độ)")
    parser.add_argument("--head-seconds", type=float, default=1.0,
                        help="Thời gian cúi đầu khi mắt cũng được nhận diện là nhắm")
    parser.add_argument("--severe-head-degrees", type=float, default=35.0,
                        help="Góc gục đầu rất sâu, kể cả khi mắt còn mở")
    parser.add_argument("--severe-head-seconds", type=float, default=2.5,
                        help="Thời gian giữ tư thế gục sâu để báo động")
    parser.add_argument("--head-policy", choices=("balanced", "eyes_confirmed"),
                        default="balanced",
                        help="Chế độ 'eyes_confirmed' không báo riêng do đầu cúi khi mắt mở")
    parser.add_argument("--drop-ratio", type=float, default=0.33,
                        help="Mức đầu hạ xuống vừa phải so với chiều cao khuôn mặt")
    parser.add_argument("--drop-pitch-degrees", type=float, default=8.0,
                        help="Góc cúi đi kèm để xác nhận đầu hạ mức vừa")
    parser.add_argument("--deep-drop-ratio", type=float, default=0.95,
                        help="Mức đầu hạ rất sâu để tự xét cảnh báo")
    parser.add_argument("--missing-seconds", type=float, default=1.6,
                        help="Số giây mất dấu khuôn mặt để cảnh báo")
    parser.add_argument("--calibration-seconds", type=float, default=1.5,
                        help="Thời gian lấy tư thế ngồi thẳng lúc bắt đầu")
    parser.add_argument("--threshold", type=float, default=0.57,
                        help="Ngưỡng dự đoán mắt nhắm (từ 0 đến 1)")
    parser.add_argument("--mode", choices=("hybrid", "model", "geometry"), default="hybrid",
                        help="Kết hợp AI và EAR, chỉ AI hoặc chỉ EAR")
    parser.add_argument("--collect", choices=("open", "closed"),
                        help="Nhấn phím cách để lưu ảnh mắt theo nhãn mở/nhắm")
    parser.add_argument("--mute", action="store_true", help="Tắt âm thanh")
    parser.add_argument("--no-window", action="store_true", help="Xử lý mà không hiện cửa sổ")
    parser.add_argument("--max-frames", type=int, default=0,
                        help="Số khung hình tối đa (0 là không giới hạn)")
    args = parser.parse_args()
    if args.seconds <= 0 or not 0 < args.threshold < 1:
        parser.error("--seconds phải lớn hơn 0; --threshold phải nằm giữa 0 và 1")
    if (args.head_degrees <= 0 or args.head_seconds <= 0 or
            args.severe_head_degrees <= 0 or args.severe_head_seconds <= 0 or
            args.drop_ratio <= 0 or
            args.drop_pitch_degrees <= 0 or args.deep_drop_ratio <= 0 or
            args.missing_seconds <= 0 or args.calibration_seconds <= 0):
        parser.error("Các ngưỡng đầu, mất mặt và hiệu chỉnh phải lớn hơn 0")
    for path in (EYE_MODEL, FACE_MODEL):
        if not path.is_file():
            parser.error(f"Thiếu mô hình: {path}. Hãy xem README.md")

    model = joblib.load(EYE_MODEL)  # Trusted model shipped with this project only.
    options = mp.tasks.vision.FaceLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(FACE_MODEL)),
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_faces=1,
        min_face_detection_confidence=0.5,
        min_face_presence_confidence=0.5,
        min_tracking_confidence=0.5,
        output_facial_transformation_matrixes=True,
    )

    if args.video:
        camera = cv2.VideoCapture(str(args.video))
    elif sys.platform == "win32":
        camera = cv2.VideoCapture(args.camera, cv2.CAP_DSHOW)
        if not camera.isOpened():
            camera.release()
            camera = cv2.VideoCapture(args.camera)
    else:
        camera = cv2.VideoCapture(args.camera)
    if not camera.isOpened():
        parser.error("Không mở được camera/video. Kiểm tra quyền camera, chỉ số camera và đường dẫn.")
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 540)

    monitor = DriverMonitor(eye_seconds=args.seconds, head_seconds=args.head_seconds,
                            pitch_threshold=args.head_degrees,
                            severe_pitch_threshold=args.severe_head_degrees,
                            severe_head_seconds=args.severe_head_seconds,
                            head_policy=args.head_policy,
                            drop_threshold=args.drop_ratio,
                            drop_pitch_threshold=args.drop_pitch_degrees,
                            deep_drop_threshold=args.deep_drop_ratio,
                            missing_threshold=args.missing_seconds,
                            calibration_seconds=args.calibration_seconds)
    muted = args.mute
    score_threshold = args.threshold
    total_saved = 0
    start_time = time.monotonic()
    last_timestamp_ms = -1
    processed_frames = 0
    previous_warnings = ()
    print("Điều khiển: Q=thoát | M=tắt/bật tiếng | C=hiệu chỉnh | V=chế độ đầu | [ ]=ngưỡng mắt")
    print("Ngồi thẳng và nhìn vào camera để hiệu chỉnh. CHỈ THỬ KHI XE ĐÃ ĐỖ.")
    try:
        with mp.tasks.vision.FaceLandmarker.create_from_options(options) as face_detector:
            while True:
                ok, frame = camera.read()
                if not ok:
                    break
                frame = cv2.flip(frame, 1)
                height, width = frame.shape[:2]
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb))
                timestamp_ms = max(last_timestamp_ms + 1,
                                   int((time.monotonic() - start_time) * 1000))
                last_timestamp_ms = timestamp_ms
                result = face_detector.detect_for_video(mp_image, timestamp_ms)
                # For a prerecorded video, count closure using video time,
                # not how fast the computer decodes the file.
                if args.video:
                    now = camera.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                    if now <= 0:
                        fps = camera.get(cv2.CAP_PROP_FPS) or 25.0
                        now = (processed_frames + 1) / fps
                else:
                    now = time.monotonic()

                crops = []
                ear_value = None
                closed_probability = None
                combined_score = None
                face_seen = bool(result.face_landmarks)
                pitch = None
                nose_y = None
                face_height = None
                if face_seen:
                    landmarks = result.face_landmarks[0]
                    nose_y = float(landmarks[1].y)
                    face_height = abs(float(landmarks[152].y - landmarks[10].y))
                    if result.facial_transformation_matrixes:
                        pitch = head_pitch_degrees(result.facial_transformation_matrixes[0])
                    ears = [eye_aspect_ratio(landmarks, width, height, ids)
                            for ids in EYE_LANDMARKS]
                    ear_value = float(np.mean(ears))
                    crops = [extract_eye_crop(frame, landmarks, ids)
                             for ids in EYE_LANDMARKS]
                    closed_probability = eye_prediction(model, crops)
                    for ids in EYE_LANDMARKS:
                        for i in ids:
                            xy = (int(landmarks[i].x * width), int(landmarks[i].y * height))
                            cv2.circle(frame, xy, 2, (10, 220, 210), -1)

                closed = None
                if ear_value is not None:
                    # Geometry is an independent cue when the camera differs from
                    # the infrared images used to train the eye classifier.
                    geometric_closed = float(np.clip((0.28 - ear_value) / 0.13, 0, 1))
                    if args.mode == "geometry":
                        combined_score = geometric_closed
                    elif closed_probability is not None:
                        combined_score = (closed_probability if args.mode == "model" else
                                          .65 * closed_probability + .35 * geometric_closed)
                    if combined_score is not None:
                        closed = combined_score >= score_threshold
                detection = monitor.update(now, face_seen=face_seen, pitch=pitch,
                                           nose_y=nose_y, face_height=face_height,
                                           eyes_closed=closed)
                if detection.should_beep and not muted:
                    threading.Thread(target=sound_warning, daemon=True).start()

                # Single-window, webcam-first UI; doesn't record any video.
                # A webcam can be only 480px high; reserve enough room for the
                # instructions, otherwise footer labels overlap measurements.
                display_height = max(height, 600)
                sidebar = np.full((display_height, 300, 3), (29, 33, 42), dtype=np.uint8)
                draw_text(sidebar, "AWAKE GUARD - NGỦ GẬT", (17, 43), 0.85, (70, 230, 210))
                cv2.line(sidebar, (16, 60), (284, 60), (90, 94, 104), 1)
                status = ("CẢNH BÁO!" if detection.triggered else
                          "KHÔNG THẤY MẶT" if not face_seen else
                          "ĐANG HIỆU CHỈNH" if not detection.calibrated else
                          "ĐẦU CÚI SÂU" if detection.head_seconds > 0 else
                          "ĐỔI TƯ THẾ" if detection.posture_shift else
                          "ĐANG NHÌN XUỐNG" if detection.looking_down else
                          "CHƯA RÕ TRẠNG THÁI MẮT" if closed is None else
                          "MẮT ĐANG NHẮM" if closed else "BÌNH THƯỜNG")
                color = ((95, 95, 240) if detection.triggered else
                         (90, 210, 240) if closed or detection.head_seconds > 0 else
                         (75, 190, 255) if detection.posture_shift or detection.looking_down else
                         (130, 240, 150) if face_seen else (170, 170, 170))
                draw_text(sidebar, status, (17, 104), 0.85, color)
                if detection.warnings:
                    draw_text(sidebar, ", ".join(REASON_NAMES[x] for x in detection.warnings), (17, 132),
                              0.46, (100, 120, 255), 1)
                elif detection.posture_shift:
                    draw_text(sidebar, "Ngồi thẳng, nhấn C để hiệu chỉnh", (17, 132),
                              0.46, (75, 190, 255), 1)
                elif detection.looking_down:
                    draw_text(sidebar, "Mắt mở - không báo ngủ gật", (17, 132),
                              0.42, (75, 190, 255), 1)
                if closed_probability is not None:
                    draw_text(sidebar, f"AI dự đoán nhắm: {closed_probability:5.1%}", (17, 164), 0.57)
                else:
                    draw_text(sidebar, "AI dự đoán nhắm: --", (17, 164), 0.57)
                draw_text(sidebar, f"EAR (độ mở mắt): {ear_value:.3f}" if ear_value is not None
                          else "EAR (độ mở mắt): --", (17, 192), 0.57)
                draw_text(sidebar, f"Điểm kết hợp: {combined_score:.1%}" if combined_score is not None
                          else "Điểm kết hợp: --", (17, 220), 0.57)
                draw_text(sidebar, f"Mắt nhắm: {detection.closed_seconds:.1f} giây", (17, 249), 0.56)
                draw_text(sidebar, f"Góc cúi: {detection.pitch_change:+.1f}°"
                          if detection.pitch_change is not None else "Góc cúi: --", (17, 278), 0.56)
                draw_text(sidebar, f"Đầu hạ: {detection.drop_ratio:+.2f} lần mặt"
                          if detection.drop_ratio is not None else "Đầu hạ: --", (17, 306), 0.56)
                draw_text(sidebar, f"Tư thế đầu: {detection.head_seconds:.1f}/{detection.head_limit:.1f} giây",
                          (17, 334), 0.55)
                draw_text(sidebar, f"Mất mặt: {detection.missing_seconds:.1f} giây", (17, 362), 0.54)
                draw_text(sidebar, "Tư thế: ĐÃ HIỆU CHỈNH" if detection.calibrated else
                          f"Đang hiệu chỉnh: {detection.calibration_progress:.0%}",
                          (17, 390), 0.55, (100, 225, 160) if detection.calibrated
                          else (80, 220, 255))
                draw_text(sidebar, f"Ngưỡng mắt: {score_threshold:.2f} ({EYE_MODES[args.mode]})",
                          (17, 420), 0.46)
                draw_text(sidebar, f"Quy tắc đầu: {HEAD_POLICIES[monitor.head_policy]}",
                          (17, 448), 0.43, (120, 210, 230))
                draw_text(sidebar, "V: đổi quy tắc đầu", (17, 475), 0.46)
                draw_text(sidebar, "C: hiệu chỉnh khi ngồi thẳng", (17, display_height - 89), 0.48)
                draw_text(sidebar, "M: tiếng   [ ]: ngưỡng mắt", (17, display_height - 61), 0.47)
                draw_text(sidebar, "Q: thoát", (17, display_height - 36), 0.47)
                draw_text(sidebar, "CHỈ ĐỂ HỌC - KHÔNG DÙNG LÁI XE", (17, display_height - 11), 0.36,
                          (100, 155, 245), 1)
                if args.collect:
                    label = "MỞ" if args.collect == "open" else "NHẮM"
                    draw_text(frame, f"THU MẪU {label}: PHÍM CÁCH | đã lưu: {total_saved}",
                              (15, 62), 0.61, (110, 240, 240))
                if muted:
                    draw_text(frame, "ĐÃ TẮT TIẾNG", (15, 35), 0.7, (0, 200, 255))
                if face_seen and not detection.calibrated:
                    draw_text(frame, "NGỒI THẲNG, NHÌN PHÍA TRƯỚC ĐỂ HIỆU CHỈNH",
                              (20, height - 24), 0.66, (0, 210, 255), 2)
                if detection.triggered:
                    cv2.rectangle(frame, (4, 4), (width - 5, height - 5), (20, 20, 255), 8)
                    draw_text(frame, "CẢNH BÁO - HÃY DỪNG XE VÀ NGHỈ", (20, 105),
                              0.85, (0, 0, 255), 3)

                frame = TEXT_RENDERER.render(frame)
                sidebar = TEXT_RENDERER.render(sidebar)
                frame_display = (cv2.copyMakeBorder(frame, 0, display_height - height, 0, 0,
                                                   cv2.BORDER_CONSTANT, value=(29, 33, 42))
                                 if display_height > height else frame)
                output = np.concatenate((frame_display, sidebar), axis=1)
                processed_frames += 1
                if args.no_window:
                    key = -1
                    if processed_frames % 30 == 0 or detection.warnings != previous_warnings:
                        reasons = ", ".join(REASON_NAMES[x] for x in detection.warnings) or "Không"
                        print(f"Khung {processed_frames}: {status} | điểm mắt={combined_score} "
                              f"| góc cúi={detection.pitch_change} "
                              f"| đầu hạ={detection.drop_ratio} | cảnh báo={reasons}")
                    previous_warnings = detection.warnings
                else:
                    cv2.imshow("AwakeGuard - Cảnh báo dấu hiệu ngủ gật", output)
                    key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), 27):
                    break
                if key == ord("m"):
                    muted = not muted
                if key == ord("c"):
                    monitor.recalibrate()
                    print("Đang hiệu chỉnh lại: hãy ngồi thẳng và nhìn vào webcam.")
                if key == ord("v"):
                    monitor.head_policy = ("eyes_confirmed" if monitor.head_policy == "balanced"
                                           else "balanced")
                    print(f"Quy tắc đầu: {HEAD_POLICIES[monitor.head_policy]}. Chế độ Theo mắt có thể bỏ sót đầu gục khi mắt mở.")
                if key == ord("["):
                    score_threshold = max(0.20, round(score_threshold - 0.03, 2))
                if key == ord("]"):
                    score_threshold = min(0.90, round(score_threshold + 0.03, 2))
                if key == 32 and args.collect and len(crops) == 2 and all(c is not None for c in crops):
                    folder = ROOT / "data" / "custom" / args.collect
                    folder.mkdir(parents=True, exist_ok=True)
                    for crop in crops:
                        filename = folder / f"{int(time.time() * 1e6)}_{total_saved}.png"
                        cv2.imwrite(str(filename), crop)
                        total_saved += 1
                    print(f"Đã lưu {total_saved} ảnh mắt vào {folder}")
                if args.max_frames and processed_frames >= args.max_frames:
                    break
    finally:
        camera.release()
        if not args.no_window:
            cv2.destroyAllWindows()
    print(f"Đã xử lý {processed_frames} khung hình")


if __name__ == "__main__":
    main()
