import unittest

import numpy as np
from PIL import Image

from alerting import AlertState
from eye_features import hog_feature


class FeatureTests(unittest.TestCase):
    def test_shape_and_finiteness(self):
        feature = hog_feature(Image.fromarray(np.random.default_rng(7).integers(
            0, 256, (42, 65), dtype=np.uint8)))
        self.assertEqual(feature.shape, (540,))
        self.assertTrue(np.isfinite(feature).all())

    def test_dark_image(self):
        self.assertTrue(np.isfinite(hog_feature(np.zeros((32, 48), np.uint8))).all())


class AlertTests(unittest.TestCase):
    def test_continuous_closure_and_reset(self):
        alert = AlertState(trigger_seconds=1.5)
        self.assertEqual(alert.update(10.0, True), (0.0, False, False))
        self.assertEqual(alert.update(10.7, True)[1], False)
        self.assertEqual(alert.update(11.6, True)[1:], (True, True))
        self.assertEqual(alert.update(11.7, True)[2], False)
        self.assertEqual(alert.update(11.8, None), (0.0, False, False))
        self.assertEqual(alert.update(12.0, True)[1], False)


if __name__ == "__main__":
    unittest.main()
