"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the one way anything in the game makes a sound.

play fires a short effect on its own channel, so any number of them
overlap: two zombies and the player swinging at once are three swings.

The music functions drive the single music stream: only one track plays
at a time, and queue_music lines up the next one to start the moment the
current one ends, with no gap. Loading or stopping a track discards
whatever was queued behind it.

A name with no file behind it, or a machine with no audio device, plays
nothing instead of raising.
"""

from typing import Optional

import pygame

import settings


def play(name: Optional[str]) -> None:
    sound = settings.SOUNDS.get(name) if name else None

    if sound is not None:
        sound.play()


def play_music(name: str, loops: int = -1) -> None:
    """ loops=-1 repeats forever, loops=0 plays the track once. """
    path = settings.MUSIC.get(name)

    if path is None:
        return

    pygame.mixer.music.load(str(path))
    pygame.mixer.music.play(loops)


def queue_music(name: str, loops: int = -1) -> None:
    path = settings.MUSIC.get(name)

    if path is not None:
        pygame.mixer.music.queue(str(path), loops=loops)


def stop_music() -> None:
    if settings.AUDIO_ENABLED:
        pygame.mixer.music.stop()


def music_playing() -> bool:
    return settings.AUDIO_ENABLED and pygame.mixer.music.get_busy()
