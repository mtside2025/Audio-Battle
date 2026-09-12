import unittest

from audio_core import clamp_pan, stereo_gains


class TestAudioCore(unittest.TestCase):
    def test_clamp_pan(self):
        self.assertEqual(clamp_pan(-2.0), -1.0)
        self.assertEqual(clamp_pan(2.0), 1.0)
        self.assertEqual(clamp_pan(0.2), 0.2)

    def test_stereo_gains_extremes_and_center(self):
        left_l, left_r = stereo_gains(-1.0)
        center_l, center_r = stereo_gains(0.0)
        right_l, right_r = stereo_gains(1.0)
        clamped_low_l, clamped_low_r = stereo_gains(-2.0)
        clamped_high_l, clamped_high_r = stereo_gains(2.0)

        self.assertGreater(left_l, left_r)
        self.assertAlmostEqual(center_l, center_r, places=5)
        self.assertGreater(right_r, right_l)
        self.assertAlmostEqual(left_l, clamped_low_l, places=5)
        self.assertAlmostEqual(left_r, clamped_low_r, places=5)
        self.assertAlmostEqual(right_l, clamped_high_l, places=5)
        self.assertAlmostEqual(right_r, clamped_high_r, places=5)


if __name__ == "__main__":
    unittest.main()
