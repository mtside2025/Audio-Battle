# Audio Battle

Phase 1–3 prototype for an audio-first PC game:

- **Phase 1:** keyboard input (`Enter`, `A`, `D`, `H`, and `Escape`)
- **Phase 2:** generated sound effects, so no audio assets are required
- **Phase 3:** stereo direction cues, with the louder channel indicating left or right

## Requirements

- Python 3.10 or newer
- A stereo output device (headphones are recommended)

## Setup and launch

From the repository directory:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python audio_battle.py
```

Press **Enter** at the menu to start. During the demo, listen for a tone that
is louder on the left or right, then press **A** for left or **D** for right.
Press **H** to hear the controls again and **Escape** to quit.

The window only provides optional visual context; the menu, controls, cues,
and feedback are usable without looking at the screen. Text-to-speech,
combat, HP, and stage progression are intentionally deferred to later phases.