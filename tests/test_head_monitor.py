"""Synthetic, repeatable tests for head nods and occlusion alert logic."""

import unittest

import numpy as np

from head_monitor import DriverMonitor, head_pitch_degrees


def ready_monitor(**overrides):
    monitor = DriverMonitor(calibration_seconds=1.0, **overrides)
    last = None
    for i in range(13):
        last = monitor.update(i / 10, face_seen=True, pitch=3.0,
                              nose_y=0.45, face_height=0.30, eyes_closed=False)
    assert last.calibrated
    return monitor


def observe(monitor, now, *, pitch=3.0, nose_y=0.45, closed=False):
    return monitor.update(now, face_seen=True, pitch=pitch,
                          nose_y=nose_y, face_height=0.30, eyes_closed=closed)


class HeadPoseTests(unittest.TestCase):
    def test_pitch_matrix_known_downward_nod(self):
        for degrees in (0.0, 17.0, 35.0, -22.0):
            angle = np.radians(degrees)
            pose = np.eye(4)
            pose[:3, :3] = np.array([
                [1, 0, 0],
                [0, np.cos(angle), -np.sin(angle)],
                [0, np.sin(angle), np.cos(angle)],
            ]) * 1.17
            self.assertAlmostEqual(head_pitch_degrees(pose), degrees, places=5)

    def test_malformed_pose(self):
        self.assertIsNone(head_pitch_degrees(np.zeros((2, 2))))
        self.assertIsNone(head_pitch_degrees(np.full((4, 4), np.nan)))


class DriverMonitorTests(unittest.TestCase):
    def test_moderate_looking_down_with_open_eyes_never_beeps(self):
        monitor = ready_monitor()
        self.assertEqual(observe(monitor, 2.0, pitch=27.0).warnings, ())
        self.assertEqual(observe(monitor, 2.6, pitch=27.0).warnings, ())
        result = observe(monitor, 20.0, pitch=27.0)
        self.assertTrue(result.looking_down)
        self.assertFalse(result.should_beep)
        self.assertEqual(result.warnings, ())
        self.assertEqual(result.closed_seconds, 0)

    def test_severe_head_nod_triggers_even_with_open_eyes(self):
        monitor = ready_monitor()
        self.assertEqual(observe(monitor, 2.0, pitch=43.0).warnings, ())
        self.assertEqual(observe(monitor, 4.4, pitch=43.0).warnings, ())
        result = observe(monitor, 4.6, pitch=43.0)
        self.assertIn("HEAD NOD", result.warnings)
        self.assertTrue(result.should_beep)
        self.assertEqual(result.closed_seconds, 0)
        self.assertFalse(observe(monitor, 4.7, pitch=43.0).should_beep)
        self.assertEqual(observe(monitor, 4.8, pitch=3.0).warnings, ())

    def test_eyes_confirmed_policy_ignores_even_severe_open_eye_nod(self):
        monitor = ready_monitor(head_policy="eyes_confirmed")
        observe(monitor, 2.0, pitch=43.0)
        result = observe(monitor, 12.0, pitch=43.0)
        self.assertTrue(result.looking_down)
        self.assertFalse(result.should_beep)
        self.assertEqual(result.warnings, ())

        # Head + closed eyes still alarms under the strict policy.
        observe(monitor, 13.0, pitch=26.0, closed=True)
        result = observe(monitor, 14.1, pitch=26.0, closed=True)
        self.assertIn("HEAD NOD", result.warnings)

    def test_short_look_down_does_not_trigger(self):
        monitor = ready_monitor()
        observe(monitor, 2.0, pitch=25.0)
        observe(monitor, 2.5, pitch=25.0)
        result = observe(monitor, 2.6, pitch=3.0)
        self.assertEqual(result.warnings, ())
        self.assertEqual(result.head_seconds, 0)

    def test_posture_change_matches_reported_false_alarm_without_beep(self):
        """Open eyes, +2.7deg nod and +0.51 face drop must not beep."""
        monitor = ready_monitor()
        observe(monitor, 2.0, pitch=5.7, nose_y=0.603)
        result = observe(monitor, 20.0, pitch=5.7, nose_y=0.603)
        self.assertAlmostEqual(result.drop_ratio, 0.51)
        self.assertAlmostEqual(result.pitch_change, 2.7)
        self.assertTrue(result.posture_shift)
        self.assertEqual(result.head_seconds, 0)
        self.assertEqual(result.warnings, ())
        self.assertFalse(result.should_beep)

    def test_confirmed_head_drop_with_supporting_pitch(self):
        monitor = ready_monitor()
        first = observe(monitor, 2.0, pitch=12.0, nose_y=0.58, closed=True)
        self.assertFalse(first.posture_shift)
        self.assertEqual(first.warnings, ())
        result = observe(monitor, 3.1, pitch=12.0, nose_y=0.58, closed=True)
        self.assertIn("HEAD DROP", result.warnings)

    def test_deep_head_collapse_even_without_rotation(self):
        monitor = ready_monitor()
        first = observe(monitor, 2.0, pitch=3.0, nose_y=0.75)
        self.assertGreaterEqual(first.drop_ratio, 0.95)
        self.assertEqual(first.warnings, ())
        result = observe(monitor, 4.6, pitch=3.0, nose_y=0.75)
        self.assertIn("HEAD DROP", result.warnings)

    def test_moderate_head_nod_requires_closed_eyes(self):
        monitor = ready_monitor()
        observe(monitor, 2.0, pitch=27.0, closed=False)
        self.assertEqual(observe(monitor, 4.0, pitch=27.0, closed=False).warnings, ())
        self.assertEqual(observe(monitor, 4.1, pitch=27.0, closed=True).warnings, ())
        result = observe(monitor, 5.2, pitch=27.0, closed=True)
        self.assertIn("HEAD NOD", result.warnings)
        self.assertNotIn("EYES CLOSED", result.warnings)  # eye warning starts at 1.5s

    def test_unstable_startup_pose_does_not_become_baseline(self):
        monitor = DriverMonitor(calibration_seconds=1.0)
        for i in range(13):
            result = observe(monitor, i / 10, nose_y=0.45 if i < 6 else 0.61)
        self.assertFalse(result.calibrated)
        for i in range(13, 27):
            result = observe(monitor, i / 10, nose_y=0.61)
        self.assertTrue(result.calibrated)
        self.assertAlmostEqual(result.drop_ratio or 0, 0, places=6)

    def test_no_face_before_first_detection_is_not_an_alarm(self):
        monitor = DriverMonitor()
        result = monitor.update(15.0, face_seen=False)
        self.assertEqual(result.warnings, ())

    def test_sustained_face_loss_warns_after_prior_tracking(self):
        monitor = ready_monitor()
        monitor.update(1.3, face_seen=False)
        self.assertEqual(monitor.update(2.7, face_seen=False).warnings, ())
        result = monitor.update(2.9, face_seen=False)
        self.assertIn("FACE LOST", result.warnings)
        self.assertEqual(observe(monitor, 3.0).warnings, ())

    def test_eye_alert_operates_independent_of_pose(self):
        monitor = ready_monitor()
        self.assertEqual(observe(monitor, 2.0, closed=True).warnings, ())
        result = observe(monitor, 3.6, closed=True)
        self.assertIn("EYES CLOSED", result.warnings)
        self.assertEqual(observe(monitor, 3.7, closed=False).warnings, ())

    def test_manual_recalibration_changes_baseline(self):
        monitor = ready_monitor()
        monitor.recalibrate()
        self.assertFalse(monitor.calibrated)
        for i in range(14):
            result = observe(monitor, 3.0 + i / 10, pitch=20.0, nose_y=0.5)
        self.assertTrue(result.calibrated)
        result = observe(monitor, 4.5, pitch=20.0, nose_y=0.5)
        self.assertAlmostEqual(result.pitch_change, 0, places=5)
        self.assertAlmostEqual(result.drop_ratio, 0, places=5)


if __name__ == "__main__":
    unittest.main()
