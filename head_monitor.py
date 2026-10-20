"""Personalized, time-filtered driver attention cues from face geometry.

These are *risk indicators*, not a diagnosis of fatigue. A face disappearing
may simply mean the camera moved or the driver looked away.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


def head_pitch_degrees(transform: object) -> float | None:
    """Return head pitch from MediaPipe's 4x4 facial pose transform.

    Positive pitch corresponds to a downward nod in MediaPipe's camera frame.
    Reject malformed matrices rather than triggering an alarm from bad data.
    """
    try:
        transform = np.asarray(transform, dtype=np.float64)
        if transform.shape != (4, 4) or not np.isfinite(transform).all():
            return None
        rotation = transform[:3, :3]
        if np.linalg.norm(rotation) < 1e-5:
            return None
        # Face geometry matrices may include a uniform scale. SVD recovers
        # the nearest rotation even if tracking introduces minor distortion.
        u, _, vt = np.linalg.svd(rotation)
        rotation = u @ vt
        if np.linalg.det(rotation) < 0:
            return None
        return float(np.degrees(np.arctan2(rotation[2, 1], rotation[2, 2])))
    except (TypeError, ValueError, np.linalg.LinAlgError):
        return None


@dataclass(frozen=True)
class MonitorResult:
    calibrated: bool
    calibration_progress: float
    pitch_change: float | None
    drop_ratio: float | None
    posture_shift: bool
    looking_down: bool
    head_seconds: float
    head_limit: float
    closed_seconds: float
    missing_seconds: float
    warnings: tuple[str, ...]
    should_beep: bool

    @property
    def triggered(self) -> bool:
        return bool(self.warnings)


@dataclass
class DriverMonitor:
    """Alert for prolonged eyelid closure, head nod/drop, or missing face.

    Calibration is deliberately fixed after startup: continually adapting the
    baseline to a slumping driver would hide the movement we're detecting.
    Recalibrate manually when adjusting the seat/camera.
    """

    eye_seconds: float = 1.5
    head_seconds: float = 1.0
    pitch_threshold: float = 17.0
    drop_threshold: float = 0.33  # Fractions of the initial face height.
    drop_pitch_threshold: float = 8.0  # Mild nod corroborating a modest drop.
    deep_drop_threshold: float = 0.95  # Large collapse, even with visible open eyes.
    severe_pitch_threshold: float = 35.0
    severe_head_seconds: float = 2.5
    head_policy: str = "balanced"  # "eyes_confirmed" suppresses all open-eye head alarms.
    missing_threshold: float = 1.6
    calibration_seconds: float = 1.5
    cooldown_seconds: float = 3.0
    min_calibration_frames: int = 10

    baseline_pitch: float | None = None
    baseline_nose_y: float | None = None
    baseline_height: float | None = None
    _calibration_started: float | None = None
    _calibration_samples: list[tuple[float, float, float]] = field(default_factory=list)
    _eye_started: float | None = None
    _head_with_closed_eyes_started: float | None = None
    _severe_head_started: float | None = None
    _last_face: float | None = None
    _face_frames: int = 0
    _last_beep: float = -1e9

    @property
    def calibrated(self) -> bool:
        return self.baseline_pitch is not None

    def recalibrate(self) -> None:
        """Press C while sitting upright to set a fresh baseline."""
        self.baseline_pitch = None
        self.baseline_nose_y = None
        self.baseline_height = None
        self._calibration_started = None
        self._calibration_samples.clear()
        self._head_with_closed_eyes_started = None
        self._severe_head_started = None

    def update(
        self,
        now: float,
        *,
        face_seen: bool,
        pitch: float | None = None,
        nose_y: float | None = None,
        face_height: float | None = None,
        eyes_closed: bool | None = None,
    ) -> MonitorResult:
        # Only trust pose measurements while there is a detected face.
        good_pose = (face_seen and pitch is not None and nose_y is not None
                     and face_height is not None and np.isfinite((pitch, nose_y, face_height)).all()
                     and face_height > 0.03)

        if face_seen:
            self._face_frames += 1
            self._last_face = now
            missing = 0.0
        else:
            missing = max(0.0, now - self._last_face) if self._last_face is not None else 0.0

        if not self.calibrated:
            if good_pose:
                if self._calibration_started is None:
                    self._calibration_started = now
                self._calibration_samples.append((float(pitch), float(nose_y), float(face_height)))
                if (now - self._calibration_started >= self.calibration_seconds
                        and len(self._calibration_samples) >= self.min_calibration_frames):
                    samples = np.asarray(self._calibration_samples)
                    baseline = np.median(samples, axis=0)
                    pitch_spread = np.percentile(samples[:, 0], 90) - np.percentile(samples[:, 0], 10)
                    height_normalized_motion = ((np.percentile(samples[:, 1], 90) -
                                                 np.percentile(samples[:, 1], 10)) / baseline[2])
                    if pitch_spread > 7.0 or height_normalized_motion > 0.16:
                        # If the person was sitting down/moving during setup,
                        # restart instead of preserving a misleading baseline.
                        self._calibration_started = now
                        self._calibration_samples = [self._calibration_samples[-1]]
                    else:
                        self.baseline_pitch, self.baseline_nose_y, self.baseline_height = map(float, baseline)
                        self._calibration_samples.clear()
            elif missing > 0.5:
                # A broken calibration should not include two unrelated poses.
                self._calibration_started = None
                self._calibration_samples.clear()

        progress = (min(1.0, (now - self._calibration_started) / self.calibration_seconds)
                    if self._calibration_started is not None and not self.calibrated else
                    1.0 if self.calibrated else 0.0)

        if face_seen and eyes_closed is True:
            if self._eye_started is None:
                self._eye_started = now
            closed_duration = max(0.0, now - self._eye_started)
        else:
            self._eye_started = None
            closed_duration = 0.0

        pitch_change = None
        drop_ratio = None
        moderate_head_down = False
        severe_head_down = False
        posture_shift = False
        looking_down = False
        if good_pose and self.calibrated:
            pitch_change = float(pitch - self.baseline_pitch)
            drop_ratio = float((nose_y - self.baseline_nose_y) / self.baseline_height)
            moderate_head_down = (pitch_change >= self.pitch_threshold or
                                  (drop_ratio >= self.drop_threshold and
                                   pitch_change >= self.drop_pitch_threshold))
            severe_head_down = (pitch_change >= self.severe_pitch_threshold or
                                drop_ratio >= self.deep_drop_threshold)
            if self.head_policy == "eyes_confirmed" and eyes_closed is not True:
                severe_head_down = False
            posture_shift = (drop_ratio >= self.drop_threshold and
                             not moderate_head_down and not severe_head_down)
            looking_down = moderate_head_down and eyes_closed is False

        # A person can intentionally look down to read with wide-open eyes.
        # Moderate head tilt is *not* drowsiness evidence by itself. Require
        # eye closure too; only sustained, extreme slumps alert without it.
        corroborated = moderate_head_down and eyes_closed is True
        if corroborated:
            if self._head_with_closed_eyes_started is None:
                self._head_with_closed_eyes_started = now
            corroborated_duration = max(0.0, now - self._head_with_closed_eyes_started)
        else:
            self._head_with_closed_eyes_started = None
            corroborated_duration = 0.0

        if severe_head_down:
            if self._severe_head_started is None:
                self._severe_head_started = now
            severe_duration = max(0.0, now - self._severe_head_started)
        else:
            self._severe_head_started = None
            severe_duration = 0.0

        if corroborated:
            head_duration = corroborated_duration
            head_limit = self.head_seconds
        else:
            head_duration = severe_duration
            head_limit = self.severe_head_seconds

        warnings = []
        if closed_duration >= self.eye_seconds:
            warnings.append("EYES CLOSED")
        if (corroborated_duration >= self.head_seconds or
                severe_duration >= self.severe_head_seconds):
            warnings.append("HEAD NOD" if pitch_change >= self.pitch_threshold else "HEAD DROP")
        # Never report a missing face when the camera has not seen a driver.
        if self._face_frames >= self.min_calibration_frames and missing >= self.missing_threshold:
            warnings.append("FACE LOST")

        should_beep = bool(warnings) and now - self._last_beep >= self.cooldown_seconds
        if should_beep:
            self._last_beep = now
        return MonitorResult(self.calibrated, progress, pitch_change, drop_ratio,
                             posture_shift, looking_down, head_duration, head_limit,
                             closed_duration, missing,
                             tuple(warnings), should_beep)
