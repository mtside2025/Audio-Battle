import struct
import unittest
from unittest.mock import MagicMock

from audio_battle import AudioBattlePhase13, ToneDef, synthesize_tone_bytes
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

    def test_synthesize_tone_bytes_frame_size(self):
        tone = ToneDef(frequency=440.0, duration_ms=100, volume=0.5)
        data = synthesize_tone_bytes(tone, pan=0.0, sample_rate=1000)
        expected_frames = int((tone.duration_ms / 1000.0) * 1000)
        self.assertEqual(len(data), expected_frames * 4)  # 16-bit stereo

    def test_synthesize_tone_bytes_pan_balance(self):
        tone = ToneDef(frequency=440.0, duration_ms=120, volume=0.5)
        left_data = synthesize_tone_bytes(tone, pan=-1.0, sample_rate=4000)
        right_data = synthesize_tone_bytes(tone, pan=1.0, sample_rate=4000)
        center_data = synthesize_tone_bytes(tone, pan=0.0, sample_rate=4000)

        def channel_energy(raw: bytes) -> tuple[int, int]:
            left_total = 0
            right_total = 0
            for i in range(0, len(raw), 4):
                left, right = struct.unpack("<hh", raw[i : i + 4])
                left_total += abs(left)
                right_total += abs(right)
            return left_total, right_total

        ll, lr = channel_energy(left_data)
        rl, rr = channel_energy(right_data)
        cl, cr = channel_energy(center_data)

        self.assertGreater(ll, lr)
        self.assertGreater(rr, rl)
        self.assertAlmostEqual(cl / cr, 1.0, places=2)

    def test_synthesize_tone_volume_scaling(self):
        silent = ToneDef(frequency=440.0, duration_ms=100, volume=0.0)
        quiet = ToneDef(frequency=440.0, duration_ms=100, volume=0.2)
        loud = ToneDef(frequency=440.0, duration_ms=100, volume=0.8)

        silent_data = synthesize_tone_bytes(silent, pan=0.0, sample_rate=4000)
        quiet_data = synthesize_tone_bytes(quiet, pan=0.0, sample_rate=4000)
        loud_data = synthesize_tone_bytes(loud, pan=0.0, sample_rate=4000)

        def total_energy(raw: bytes) -> int:
            total = 0
            for i in range(0, len(raw), 4):
                left, right = struct.unpack("<hh", raw[i : i + 4])
                total += abs(left) + abs(right)
            return total

        self.assertEqual(total_energy(silent_data), 0)
        self.assertGreater(total_energy(loud_data), total_energy(quiet_data))

    def test_synthesize_tone_bytes_rejects_non_positive_sample_rate(self):
        tone = ToneDef(frequency=440.0, duration_ms=100, volume=0.5)
        with self.assertRaises(ValueError):
            synthesize_tone_bytes(tone, pan=0.0, sample_rate=0)

    def test_announce_start_speaks_controls(self):
        app = AudioBattlePhase13.__new__(AudioBattlePhase13)
        app.speak = MagicMock()
        app.voice_enabled = True
        app.announce_start()
        calls = [c.args[0] for c in app.speak.call_args_list]
        self.assertTrue(any("Audio Battleへようこそ" in c for c in calls))
        self.assertTrue(any("左右矢印" in c and "AとD" in c and "Jで攻撃" in c for c in calls))


if __name__ == "__main__":
    unittest.main()
