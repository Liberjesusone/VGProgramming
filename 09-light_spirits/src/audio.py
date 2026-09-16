"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains play: the one way anything in the game makes a sound.
A missing name plays nothing, so an attack can ask for its cue before the
sound file for it exists.
"""

from typing import Optional

import settings


def play(name: Optional[str]) -> None:
    sound = settings.SOUNDS.get(name) if name else None

    if sound is not None:
        sound.play()
