"""Audio Battle Phase 1-3 prototype.

Phase 1: Keyboard input
Phase 2: Sound effect playback
Phase 3: Left/right stereo audio cues
"""

from __future__ import annotations

import math
import struct
import sys
from dataclasses import dataclass

import pygame

from audio_core import stereo_gains

SAMPLE_RATE = 44_100


class Narrator:
    def __init__(self) -> None:
        self._engine = None
        try:
            import pyttsx3  # type: ignore

            self._engine = pyttsx3.init()
        except Exception:
            self._engine = None

    def say(self, text: str) -> None:
        print(text)
        if self._engine is None:
            return
        self._engine.say(text)
        self._engine.runAndWait()


@dataclass(frozen=True)
class ToneDef:
    frequency: float
    duration_ms: int
    volume: float


def make_tone(tone: ToneDef, pan: float) -> pygame.mixer.Sound:
    left_gain, right_gain = stereo_gains(pan)
    frames = int((tone.duration_ms / 1000.0) * SAMPLE_RATE)
    samples = bytearray()

    for i in range(frames):
        t = i / SAMPLE_RATE
        base = math.sin(2.0 * math.pi * tone.frequency * t)
        amp = int(32767 * tone.volume * base)
        left = int(amp * left_gain)
        right = int(amp * right_gain)
        samples.extend(struct.pack("<hh", left, right))

    return pygame.mixer.Sound(buffer=bytes(samples))


class AudioBattlePhase13:
    def __init__(self) -> None:
        pygame.init()
        pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2)
        self.screen = pygame.display.set_mode((640, 240))
        pygame.display.set_caption("Audio Battle - Phase 1-3")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 28)
        self.narrator = Narrator()

        self.enemy_tone = ToneDef(660.0, 220, 0.45)
        self.dodge_tone = ToneDef(420.0, 160, 0.45)
        self.attack_tone = ToneDef(300.0, 180, 0.5)

    def announce_start(self) -> None:
        self.narrator.say("Audio Battleへようこそ。")
        self.narrator.say("Enterキーでゲーム開始。Escキーで終了。")

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
        pan = -1.0 if direction == "left" else 1.0
        cue = make_tone(self.enemy_tone, pan)
        cue.play()
        self.narrator.say(f"敵の気配: {direction}")

    def play_dodge(self, direction: str) -> None:
        pan = -1.0 if direction == "left" else 1.0
        sfx = make_tone(self.dodge_tone, pan)
        sfx.play()
        self.narrator.say(f"回避: {direction}")

    def play_attack(self) -> None:
        make_tone(self.attack_tone, 0.0).play()
        self.narrator.say("攻撃")

    def run(self) -> None:
        self.announce_start()
        running = True
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

        pygame.quit()


def main() -> int:
    app = AudioBattlePhase13()
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
