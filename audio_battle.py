"""Audio Battle Phase 1-3 prototype.

The prototype demonstrates keyboard input, generated sound effects, and
stereo direction cues without requiring any external audio assets.
"""

from __future__ import annotations

import math
import random
import sys
from array import array

import pygame


WIDTH = 900
HEIGHT = 520
SAMPLE_RATE = 44_100
CUE_INTERVAL_MS = 2_500
CUE_DURATION_MS = 420


def make_tone(frequency: float, duration_ms: int, left: float, right: float) -> pygame.mixer.Sound:
    """Create a short stereo sine tone with independent channel volumes."""
    sample_count = int(SAMPLE_RATE * duration_ms / 1_000)
    samples = array("h")
    amplitude = 0.38 * 32_767

    for index in range(sample_count):
        envelope = min(1.0, index / (SAMPLE_RATE * 0.02))
        envelope *= min(1.0, (sample_count - index) / (SAMPLE_RATE * 0.04))
        value = math.sin(2 * math.pi * frequency * index / SAMPLE_RATE)
        samples.append(int(value * amplitude * envelope * left))
        samples.append(int(value * amplitude * envelope * right))

    return pygame.mixer.Sound(buffer=samples.tobytes())


def play_center(sound: pygame.mixer.Sound) -> None:
    sound.set_volume(1.0)
    sound.play()


def draw_text(screen: pygame.Surface, font: pygame.font.Font, message: str, y: int) -> None:
    screen.blit(font.render(message, True, (235, 235, 245)), (54, y))


def run() -> None:
    pygame.mixer.pre_init(SAMPLE_RATE, -16, 2, 512)
    pygame.init()
    if pygame.mixer.get_init() is None:
        raise RuntimeError("Audio could not be initialized. Check the system audio device.")

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Audio Battle - Phase 1-3 Prototype")
    font = pygame.font.Font(None, 34)
    title_font = pygame.font.Font(None, 56)
    clock = pygame.time.Clock()

    left_tone = make_tone(440, CUE_DURATION_MS, 1.0, 0.12)
    right_tone = make_tone(440, CUE_DURATION_MS, 0.12, 1.0)
    center_tone = make_tone(660, 180, 0.8, 0.8)
    success_tone = make_tone(880, 180, 0.8, 0.8)
    error_tone = make_tone(180, 260, 0.8, 0.8)

    state = "menu"
    running = True
    direction = ""
    last_cue_at = 0
    feedback = "Press Enter to start. Press Escape to quit."
    feedback_until = 0

    while running:
        now = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif state == "menu" and event.key == pygame.K_RETURN:
                    state = "battle"
                    feedback = "Battle started. Listen for the direction cue."
                    feedback_until = now + 2_000
                    last_cue_at = now - CUE_INTERVAL_MS + 700
                    play_center(center_tone)
                elif state == "battle" and event.key in (pygame.K_a, pygame.K_d):
                    pressed = "left" if event.key == pygame.K_a else "right"
                    if pressed == direction:
                        feedback = "Correct direction."
                        play_center(success_tone)
                    else:
                        feedback = "Try matching the louder side."
                        play_center(error_tone)
                    feedback_until = now + 1_200
                elif state == "battle" and event.key == pygame.K_h:
                    feedback = "A is left. D is right. Listen for the next cue."
                    feedback_until = now + 2_000

        if state == "battle" and now - last_cue_at >= CUE_INTERVAL_MS:
            direction = random.choice(("left", "right"))
            if direction == "left":
                left_tone.play()
            else:
                right_tone.play()
            last_cue_at = now

        screen.fill((18, 20, 30))
        if state == "menu":
            draw_text(screen, title_font, "Audio Battle", 55)
            draw_text(screen, font, "Phase 1-3: keyboard input and stereo audio", 130)
            draw_text(screen, font, "Press Enter to start", 225)
            draw_text(screen, font, "Press Escape to quit", 275)
            draw_text(screen, font, "The game can be played without looking at this window.", 375)
        else:
            draw_text(screen, title_font, "Listen and react", 55)
            draw_text(screen, font, "A = left       D = right       H = repeat controls", 145)
            draw_text(screen, font, "A directional tone will be louder on the enemy's side.", 205)
            if now < feedback_until:
                draw_text(screen, font, feedback, 315)
            else:
                draw_text(screen, font, "Waiting for the next audio cue...", 315)
            draw_text(screen, font, "Escape = quit", 425)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        pygame.quit()
        sys.exit(0)
