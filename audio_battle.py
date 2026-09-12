"""Audio Battle, phases 1-6.

The visual display is only a debugging aid.  All important combat events also
produce a directional sound or an announcement, so the game can be played
with a keyboard and headphones alone.
"""

from __future__ import annotations

import math
import random
import struct
import threading
import time
from collections import deque
from dataclasses import dataclass
from enum import Enum

import pygame

from audio_core import stereo_gains

SAMPLE_RATE = 44_100
REACTION_TIME = 1.0
PERFECT_DODGE_WINDOW = 0.20
ENEMY_ATTACK_INTERVAL = (1.5, 3.0)
RECOVERY_TIME = 2.0
PLAYER_MAX_HP = 100
ENEMY_MAX_HP = 100
NORMAL_ATTACK_DAMAGE = 10
HEAVY_ATTACK_DAMAGE = 25
ENEMY_ATTACK_DAMAGE = 20
HEAVY_ATTACK_COOLDOWN = 2.0


class GameState(Enum):
    MENU = "MENU"
    PLAYING = "PLAYING"
    WARNING = "WARNING"
    ATTACKING = "ATTACKING"
    ENEMY_RECOVERY = "ENEMY_RECOVERY"
    VICTORY = "VICTORY"
    GAME_OVER = "GAME_OVER"


class EnemyState(Enum):
    IDLE = "IDLE"
    WARNING = "WARNING"
    ATTACKING = "ATTACKING"
    RECOVERY = "RECOVERY"
    DEAD = "DEAD"


@dataclass
class Player:
    hp: int = PLAYER_MAX_HP

    def take_damage(self, amount: int) -> int:
        self.hp = max(0, self.hp - amount)
        return self.hp

    def reset(self) -> None:
        self.hp = PLAYER_MAX_HP


@dataclass
class Enemy:
    hp: int = ENEMY_MAX_HP
    state: EnemyState = EnemyState.IDLE
    direction: str | None = None
    state_started: float = 0.0
    next_attack: float = 0.0

    def take_damage(self, amount: int) -> int:
        self.hp = max(0, self.hp - amount)
        if self.hp == 0:
            self.state = EnemyState.DEAD
        return self.hp

    def reset(self, now: float) -> None:
        self.hp = ENEMY_MAX_HP
        self.state = EnemyState.IDLE
        self.direction = None
        self.state_started = now
        self.next_attack = now + random.uniform(*ENEMY_ATTACK_INTERVAL)


class Narrator:
    def __init__(self) -> None:
        self._engine = None
        self._queue: deque[str] = deque()
        self._lock = threading.Lock()
        self._running = True
        self._thread: threading.Thread | None = None
        try:
            import pyttsx3  # type: ignore

            self._engine = pyttsx3.init()
        except Exception:
            self._engine = None
        self.available = self._engine is not None
        if self._engine is not None:
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
            with self._lock:
                message = self._queue.popleft() if self._queue else None
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
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=1.0)


@dataclass(frozen=True)
class ToneDef:
    frequency: float
    duration_ms: int
    volume: float


def synthesize_tone_bytes(
    tone: ToneDef, pan: float, sample_rate: int = SAMPLE_RATE
) -> bytes:
    if sample_rate <= 0:
        raise ValueError("sample_rate must be positive.")
    left_gain, right_gain = stereo_gains(pan)
    frames = int((tone.duration_ms / 1000.0) * sample_rate)
    samples = bytearray(frames * 4)
    for i in range(frames):
        base = math.sin(2.0 * math.pi * tone.frequency * i / sample_rate)
        amp = int(32767 * tone.volume * base)
        struct.pack_into(
            "<hh",
            samples,
            i * 4,
            max(-32768, min(32767, int(amp * left_gain))),
            max(-32768, min(32767, int(amp * right_gain))),
        )
    return bytes(samples)


def make_tone(tone: ToneDef, pan: float) -> pygame.mixer.Sound:
    return pygame.mixer.Sound(buffer=synthesize_tone_bytes(tone, pan))


class AudioBattlePhase13:
    """Compatibility name retained for the original Phase 1-3 entry point."""

    def __init__(self) -> None:
        self._init_pygame()
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2)
        self.screen = pygame.display.set_mode((700, 360))
        pygame.display.set_caption("Audio Battle - Phase 4-6")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 26)
        self.narrator = Narrator()
        self.voice_enabled = self.narrator.available
        self.player = Player()
        self.enemy = Enemy()
        self.state = GameState.MENU
        self.attack_action: str | None = None
        self.heavy_ready_at = 0.0
        self._build_sounds()

    @staticmethod
    def _init_pygame() -> None:
        pygame.mixer.pre_init(frequency=SAMPLE_RATE, size=-16, channels=2)
        pygame.init()
        if not pygame.display.get_init():
            pygame.display.init()
        if not pygame.font.get_init():
            pygame.font.init()

    def _build_sounds(self) -> None:
        tones = {
            "enemy": ToneDef(660, 220, 0.45),
            "dodge": ToneDef(420, 160, 0.45),
            "attack": ToneDef(300, 180, 0.5),
            "warning": ToneDef(220, 160, 0.55),
            "success": ToneDef(760, 140, 0.5),
            "damage": ToneDef(120, 220, 0.55),
            "low_hp": ToneDef(90, 400, 0.5),
        }
        self.sounds = {
            "enemy_left": make_tone(tones["enemy"], -1),
            "enemy_right": make_tone(tones["enemy"], 1),
            "warning_left": make_tone(tones["warning"], -1),
            "warning_right": make_tone(tones["warning"], 1),
            "dodge": make_tone(tones["dodge"], 0),
            "attack": make_tone(tones["attack"], 0),
            "success": make_tone(tones["success"], 0),
            "damage": make_tone(tones["damage"], 0),
            "low_hp": make_tone(tones["low_hp"], 0),
        }

    def speak(self, text: str, important: bool = False) -> None:
        if self.voice_enabled:
            self.narrator.say(text)
        else:
            print(f"[TTS unavailable] {text}")
            self.sounds["damage" if important else "success"].play()

    def announce_start(self) -> None:
        self.speak("Audio Battleへようこそ。", important=True)
        self.speak(
            "Enterでゲーム開始。左右矢印で敵方向音。AとDで回避。Jで攻撃。Hで説明。Escで終了。"
        )

    def announce_status(self) -> None:
        print(f"Your HP: {self.player.hp}; Enemy HP: {self.enemy.hp}")
        self.speak(f"Your HP: {self.player.hp}. Enemy HP: {self.enemy.hp}.")

    def _hp_damage(self, amount: int) -> None:
        self.player.take_damage(amount)
        self.sounds["damage"].play()
        if self.player.hp <= 20:
            self.sounds["low_hp"].play()
        if self.player.hp == 0:
            self.state = GameState.GAME_OVER
            self.speak("Game Over. Press Enter to restart. Press Escape to quit.", True)

    def _begin_attack(self, now: float) -> None:
        self.enemy.direction = random.choice(("left", "right"))
        self.enemy.state = EnemyState.WARNING
        self.enemy.state_started = now
        self.attack_action = None
        self.state = GameState.WARNING
        direction = self.enemy.direction
        self.sounds[f"warning_{direction}"].play()
        self.speak(f"Enemy warning {direction}.")

    def _resolve_attack(self) -> None:
        direction = self.enemy.direction
        if self.attack_action == "guard":
            self.speak("Guard!")
        elif self.attack_action == direction:
            remaining = REACTION_TIME - (time.monotonic() - self.enemy.state_started)
            if remaining <= PERFECT_DODGE_WINDOW:
                self.sounds["success"].play()
                self.speak("Perfect Dodge!")
            else:
                self.sounds["dodge"].play()
                self.speak("Dodge!")
        else:
            self._hp_damage(ENEMY_ATTACK_DAMAGE)
            self.speak("Hit!")

    def _update(self, now: float) -> None:
        if self.state != GameState.PLAYING and self.state not in (
            GameState.WARNING,
            GameState.ATTACKING,
            GameState.ENEMY_RECOVERY,
        ):
            return
        if self.enemy.state == EnemyState.IDLE and now >= self.enemy.next_attack:
            self._begin_attack(now)
        elif self.enemy.state == EnemyState.WARNING and now - self.enemy.state_started >= REACTION_TIME:
            self.enemy.state = EnemyState.ATTACKING
            self.enemy.state_started = now
            self.state = GameState.ATTACKING
            self.sounds[f"enemy_{self.enemy.direction}"].play()
            self.sounds["attack"].play()
            self.speak("Attack!")
            self._resolve_attack()
        elif self.enemy.state == EnemyState.ATTACKING and now - self.enemy.state_started >= 0.25:
            self.enemy.state = EnemyState.RECOVERY
            self.enemy.state_started = now
            self.state = GameState.ENEMY_RECOVERY
        elif self.enemy.state == EnemyState.RECOVERY and now - self.enemy.state_started >= RECOVERY_TIME:
            self.enemy.state = EnemyState.IDLE
            self.enemy.next_attack = now + random.uniform(*ENEMY_ATTACK_INTERVAL)
            self.state = GameState.PLAYING

    def _player_attack(self, heavy: bool, now: float) -> None:
        if self.enemy.state != EnemyState.RECOVERY or self.enemy.hp <= 0:
            self.speak("Enemy is not vulnerable.")
            return
        if heavy and now < self.heavy_ready_at:
            self.speak("Heavy attack cooling down.")
            return
        damage = HEAVY_ATTACK_DAMAGE if heavy else NORMAL_ATTACK_DAMAGE
        if heavy:
            self.heavy_ready_at = now + HEAVY_ATTACK_COOLDOWN
        self.enemy.take_damage(damage)
        self.sounds["attack"].play()
        self.speak(f"{'Heavy attack' if heavy else 'Attack'}.")
        if self.enemy.hp == 0:
            self.state = GameState.VICTORY
            self.speak("Enemy Defeated! Victory! Press Enter to play again.", True)

    def _handle_key(self, event: pygame.event.Event, now: float) -> bool:
        if event.key in (pygame.K_ESCAPE, pygame.K_q):
            return False
        if event.key == pygame.K_RETURN and self.state in (
            GameState.MENU,
            GameState.GAME_OVER,
            GameState.VICTORY,
        ):
            self.player.reset()
            self.enemy.reset(now)
            self.state = GameState.PLAYING
            self.speak("Game started.", True)
        elif event.key == pygame.K_h:
            self.announce_status()
        elif self.state in (GameState.WARNING, GameState.ATTACKING):
            if event.key == pygame.K_a:
                self.attack_action = "left"
            elif event.key == pygame.K_d:
                self.attack_action = "right"
            elif event.key == pygame.K_SPACE:
                self.attack_action = "guard"
        elif event.key == pygame.K_j:
            self._player_attack(False, now)
        elif event.key == pygame.K_k:
            self._player_attack(True, now)
        # Preserve the original Phase 1-3 directional demonstration.
        elif event.key == pygame.K_LEFT:
            self.sounds["enemy_left"].play()
        elif event.key == pygame.K_RIGHT:
            self.sounds["enemy_right"].play()
        return True

    def draw_text(self) -> None:
        def bar(value: int) -> str:
            return "█" * (value // 10) + "░" * (10 - value // 10)

        direction = self.enemy.direction or "-"
        lines = [
            "Audio Battle",
            f"Player HP: {bar(self.player.hp)} {self.player.hp}",
            f"Enemy HP:  {bar(self.enemy.hp)} {self.enemy.hp}",
            f"State: {self.state.value}  Enemy: {self.enemy.state.value}  Direction: {direction}",
            "A/D = Dodge   SPACE = Guard   J = Attack   K = Heavy Attack",
            "H = Status   ENTER = Start/Restart   ESC = Quit",
        ]
        self.screen.fill((10, 10, 15))
        for index, line in enumerate(lines):
            self.screen.blit(self.font.render(line, True, (230, 230, 230)), (20, 20 + index * 48))
        pygame.display.flip()

    def run(self) -> None:
        self.announce_start()
        running = True
        try:
            while running:
                now = time.monotonic()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        running = self._handle_key(event, now)
                self._update(now)
                self.draw_text()
                self.clock.tick(60)
        finally:
            self.narrator.stop()
            pygame.quit()


def main() -> int:
    AudioBattlePhase13().run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
