import unittest

import numpy as np

from vi_text import VietnameseTextRenderer


class VietnameseTextTests(unittest.TestCase):
    def test_renders_accented_text(self):
        renderer = VietnameseTextRenderer()
        image = np.zeros((100, 350, 3), dtype=np.uint8)
        renderer.add(image, "CẢNH BÁO: MẮT NHẮM", (10, 45), 0.9)
        result = renderer.render(image)
        self.assertGreater(np.count_nonzero(result), 100)

    def test_long_label_stays_inside_sidebar(self):
        renderer = VietnameseTextRenderer()
        image = np.zeros((80, 300, 3), dtype=np.uint8)
        renderer.add(image, "NGỒI THẲNG, NHẤN C ĐỂ HIỆU CHỈNH LẠI", (17, 40), 0.9)
        result = renderer.render(image)
        self.assertGreater(np.count_nonzero(result[:, :290]), 50)
        self.assertEqual(result.shape, image.shape)


if __name__ == "__main__":
    unittest.main()
