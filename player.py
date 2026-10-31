"""
AkiMusic - player.py
Reproductor de audio usando kivy.core.audio con fallback a pygame.
"""

import os
from pathlib import Path
from typing import Optional, Dict

# Intentar usar kivy audio (android compatible)
try:
    from kivy.core.audio import SoundLoader
    KIVY_AUDIO = True
except ImportError:
    KIVY_AUDIO = False

# Fallback: pygame
try:
    import pygame
    pygame.mixer.init()
    PYGAME_AUDIO = True
except ImportError:
    PYGAME_AUDIO = False


# ─── ESTADO INTERNO ──────────────────────────────────────
_current_sound = None
_current_info: Optional[Dict] = None
_playlist: list = []
_playlist_index: int = 0
_paused: bool = False


def play(path: str, info: Optional[dict] = None):
    """Reproduce un archivo de audio."""
    global _current_sound, _current_info, _paused

    # Parar lo que esté sonando
    stop()

    if not os.path.exists(path):
        print(f"[player] Archivo no encontrado: {path}")
        return

    _paused = False

    if KIVY_AUDIO:
        _current_sound = SoundLoader.load(path)
        if _current_sound:
            _current_sound.play()
        else:
            print(f"[player] kivy no pudo cargar: {path}")
    elif PYGAME_AUDIO:
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
        except Exception as e:
            print(f"[player] pygame error: {e}")
    else:
        print("[player] No hay backend de audio disponible.")

    # Metadata
    if info:
        _current_info = info
    else:
        _current_info = {
            'title': Path(path).stem,
            'artist': '',
            'path': path,
        }
        # Intentar leer desde biblioteca
        try:
            import library
            all_songs = library.get_songs()
            for s in all_songs:
                if s.get('path') == path:
                    _current_info = s
                    break
        except Exception:
            pass


def pause():
    """Pausa la reproducción."""
    global _paused
    if KIVY_AUDIO and _current_sound:
        _current_sound.stop()
        _paused = True
    elif PYGAME_AUDIO:
        pygame.mixer.music.pause()
        _paused = True


def resume():
    """Reanuda la reproducción pausada."""
    global _paused
    if KIVY_AUDIO and _current_sound:
        _current_sound.play()
        _paused = False
    elif PYGAME_AUDIO:
        pygame.mixer.music.unpause()
        _paused = False


def stop():
    """Detiene la reproducción."""
    global _current_sound, _paused
    _paused = False
    if KIVY_AUDIO and _current_sound:
        _current_sound.stop()
        _current_sound = None
    elif PYGAME_AUDIO:
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass


def is_playing() -> bool:
    """Retorna True si hay audio reproduciéndose."""
    if _paused:
        return False
    if KIVY_AUDIO and _current_sound:
        return _current_sound.state == 'play'
    if PYGAME_AUDIO:
        try:
            return pygame.mixer.music.get_busy()
        except Exception:
            return False
    return False


def current_info() -> Optional[Dict]:
    """Retorna metadatos de la canción actual."""
    return _current_info


def set_playlist(songs: list, start_index: int = 0):
    """Carga una lista de canciones para reproducción consecutiva."""
    global _playlist, _playlist_index
    _playlist = songs
    _playlist_index = start_index
    if songs:
        play(songs[start_index].get('path', ''), songs[start_index])


def next_song():
    """Avanza a la siguiente canción en la playlist."""
    global _playlist_index
    if _playlist and _playlist_index < len(_playlist) - 1:
        _playlist_index += 1
        s = _playlist[_playlist_index]
        play(s.get('path', ''), s)


def prev():
    """Retrocede a la canción anterior."""
    global _playlist_index
    if _playlist and _playlist_index > 0:
        _playlist_index -= 1
        s = _playlist[_playlist_index]
        play(s.get('path', ''), s)


def get_position() -> float:
    """Retorna la posición actual en segundos."""
    if KIVY_AUDIO and _current_sound:
        return _current_sound.get_pos()
    if PYGAME_AUDIO:
        try:
            return pygame.mixer.music.get_pos() / 1000.0
        except Exception:
            return 0.0
    return 0.0
