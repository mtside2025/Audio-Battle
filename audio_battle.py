"""Audio Battle Phase 1-3 prototype.

Phase 1: Keyboard input
Phase 2: Sound effect playback
Phase 3: Left/right stereo audio cues
"""

from __future__ import annotations

import math
import struct
import threading
import time
from collections import deque
from dataclasses import dataclass

import pygame

from audio_core import stereo_gains

SAMPLE_RATE = 44_100


class Narrator:
    def __init__(self) -> None:
        self._engine = None
        self._queue: deque[str] = deque()
        self._lock = threading.Lock()
        self._running = True
        try:
            import pyttsx3  # type: ignore

            self._engine = pyttsx3.init()
        except Exception:
            self._engine = None
        self._thread = threading.Thread(target=self._speak_loop, daemon=True)
        self._thread.start()

    def say(self, text: str) -> None:
        print(text)
        if self._engine is None:
            return
        with self._lock:
            self._queue.append(text)

    def _speak_loop(self) -> None:
        while self._running:
            message = None
            with self._lock:
                if self._queue:
                    message = self._queue.popleft()
            if message is None:
                time.sleep(0.02)
                continue
            try:
                self._engine.say(message)
                self._engine.runAndWait()
            except Exception:
                self._running = False

    def stop(self) -> None:
        self._running = False
        if self._thread.is_alive():
            self._thread.join(timeout=1.0)


@dataclass(frozen=True)
class ToneDef:
    frequency: float
    duration_ms: int
    volume: float


def make_tone(tone: ToneDef, pan: float) -> pygame.mixer.Sound:
    """Create a pygame Sound from a synthesized 16-bit stereo PCM tone."""
    return pygame.mixer.Sound(buffer=synthesize_tone_bytes(tone, pan))


def synthesize_tone_bytes(tone: ToneDef, pan: float, sample_rate: int = SAMPLE_RATE) -> bytes:
    """Return little-endian signed 16-bit stereo PCM bytes for the given tone.

    `pan` is expected in [-1.0, 1.0] and is clamped by stereo_gains.
    `tone.volume` is expected in [0.0, 1.0].
    """
    left_gain, right_gain = stereo_gains(pan)
    frames = int((tone.duration_ms / 1000.0) * sample_rate)
    samples = bytearray(frames * 4)

    for i in range(frames):
        t = i / sample_rate
        base = math.sin(2.0 * math.pi * tone.frequency * t)
        amp = int(32767 * tone.volume * base)
        left = max(-32768, min(32767, int(amp * left_gain)))
        right = max(-32768, min(32767, int(amp * right_gain)))
        struct.pack_into("<hh", samples, i * 4, left, right)

    return bytes(samples)


class AudioBattlePhase13:
    def __init__(self) -> None:
        self._init_pygame()
        current_mixer = pygame.mixer.get_init()
        needs_mixer_init = not bool(current_mixer)
        if current_mixer and (current_mixer[0] != SAMPLE_RATE or current_mixer[2] != 2):
            pygame.mixer.quit()
            needs_mixer_init = True
        try:
            if needs_mixer_init or not pygame.mixer.get_init():
                pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2)
        except pygame.error as exc:
            pygame.quit()
            raise RuntimeError("Audio device initialization failed.") from exc
        self.screen = pygame.display.set_mode((640, 240))
        pygame.display.set_caption("Audio Battle - Phase 1-3")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 28)
        self.narrator = Narrator()

        self.enemy_tone = ToneDef(660.0, 220, 0.45)
        self.dodge_tone = ToneDef(420.0, 160, 0.45)
        self.attack_tone = ToneDef(300.0, 180, 0.5)
        self.enemy_sounds = {
            "left": make_tone(self.enemy_tone, -1.0),
            "right": make_tone(self.enemy_tone, 1.0),
        }
        self.dodge_sounds = {
            "left": make_tone(self.dodge_tone, -1.0),
            "right": make_tone(self.dodge_tone, 1.0),
        }
        self.attack_sound = make_tone(self.attack_tone, 0.0)

    @staticmethod
    def _init_pygame() -> None:
        pygame.mixer.pre_init(frequency=SAMPLE_RATE, size=-16, channels=2)
        pygame.init()
        if not pygame.display.get_init():
            pygame.display.init()
        if not pygame.font.get_init():
            pygame.font.init()
        if not pygame.display.get_init() or not pygame.font.get_init():
            pygame.quit()
            raise RuntimeError("Display or font initialization failed.")

    def announce_start(self) -> None:
        self.narrator.say("Audio Battleへようこそ。")
        self.narrator.say(
            "Enterでゲーム開始。左右矢印で敵方向音。AとDで回避。Jで攻撃。Hで説明。Escで終了。"
        )

    def draw_text(self) -> None:
        lines = [
            "Audio Battle Phase 1-3 Prototype",
            "Enter: Start announcement",
            "Left/Right: Enemy cue (stereo)",
            "A/D: Dodge SFX (left/right)",
            "J: Attack SFX (center)",
            "H: Read controls",
            "Esc or Q: Quit",
        ]
        self.screen.fill((10, 10, 15))
        y = 20
        for line in lines:
            txt = self.font.render(line, True, (230, 230, 230))
            self.screen.blit(txt, (20, y))
            y += 28
        pygame.display.flip()

    def play_enemy_cue(self, direction: str) -> None:
        self.enemy_sounds[direction].play()
        direction_ja = "左" if direction == "left" else "右"
        self.narrator.say(f"敵の気配: {direction_ja}")

    def play_dodge(self, direction: str) -> None:
        self.dodge_sounds[direction].play()
        direction_ja = "左" if direction == "left" else "右"
        self.narrator.say(f"回避: {direction_ja}")

    def play_attack(self) -> None:
        self.attack_sound.play()
        self.narrator.say("攻撃")

    def run(self) -> None:
        self.announce_start()
        running = True
        try:
            while running:
                self.draw_text()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key in (pygame.K_ESCAPE, pygame.K_q):
                            running = False
                        elif event.key == pygame.K_RETURN:
                            self.narrator.say("ゲーム開始")
                        elif event.key == pygame.K_LEFT:
                            self.play_enemy_cue("left")
                        elif event.key == pygame.K_RIGHT:
                            self.play_enemy_cue("right")
                        elif event.key == pygame.K_a:
                            self.play_dodge("left")
                        elif event.key == pygame.K_d:
                            self.play_dodge("right")
                        elif event.key == pygame.K_j:
                            self.play_attack()
                        elif event.key == pygame.K_h:
                            self.narrator.say(
                                "操作説明。左矢印と右矢印で敵方向音。AとDで回避。Jで攻撃。"
                            )
                self.clock.tick(60)
        finally:
            self.narrator.stop()
            pygame.quit()


def main() -> int:
    app = AudioBattlePhase13()
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
