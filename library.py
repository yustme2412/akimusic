"""
AkiMusic - library.py
Gestión de la biblioteca de música local offline.
Escanea la carpeta de descargas y extrae metadatos con mutagen o fallback.
Soporta: MP3, M4A, OPUS, WEBM, OGG, WAV, FLAC.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional

try:
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3, APIC
    from mutagen.easyid3 import EasyID3
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

import downloader

AUDIO_EXTS = {".mp3", ".m4a", ".opus", ".webm", ".ogg", ".flac", ".wav"}

# Cache de metadatos
_CACHE_FILE = downloader.get_download_dir() / ".akimusic_cache.json"
_cache: Dict[str, dict] = {}


def _load_cache():
    global _cache
    if _CACHE_FILE.exists():
        try:
            with open(_CACHE_FILE, 'r', encoding='utf-8') as f:
                _cache = json.load(f)
        except Exception:
            _cache = {}


def _save_cache():
    try:
        with open(_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(_cache, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _extract_metadata(audio_path: str) -> dict:
    """Extrae metadatos de un archivo de audio."""
    path_obj = Path(audio_path)
    stem_name = path_obj.stem
    artist_name = "Desconocido"
    title_name = stem_name

    # Intentar separar 'Artista - Título' si viene en el nombre de archivo
    if " - " in stem_name:
        parts = stem_name.split(" - ", 1)
        artist_name = parts[0].strip()
        title_name = parts[1].strip()

    info = {
        'path': audio_path,
        'title': title_name,
        'artist': artist_name,
        'album': '',
        'cover': None,
        'duration': 0,
    }

    # Verificar si hay una imagen con el mismo nombre
    for img_ext in [".jpg", ".png", ".webp", ".jpeg"]:
        potential_cover = path_obj.with_suffix(img_ext)
        if potential_cover.exists():
            info['cover'] = str(potential_cover)
            break

    if not MUTAGEN_AVAILABLE:
        return info

    try:
        if path_obj.suffix.lower() == ".mp3":
            try:
                audio = EasyID3(audio_path)
                info['title'] = str(audio.get('title', [title_name])[0])
                info['artist'] = str(audio.get('artist', [artist_name])[0])
                info['album'] = str(audio.get('album', [''])[0])
            except Exception:
                pass

            try:
                mp3 = MP3(audio_path)
                info['duration'] = int(mp3.info.length)
            except Exception:
                pass

            if not info['cover']:
                try:
                    full = ID3(audio_path)
                    for tag in full.values():
                        if isinstance(tag, APIC):
                            cover_path = str(path_obj.with_suffix('.jpg'))
                            if not os.path.exists(cover_path):
                                with open(cover_path, 'wb') as f:
                                    f.write(tag.data)
                            info['cover'] = cover_path
                            break
                except Exception:
                    pass
        else:
            # Para otros formatos (m4a, ogg, etc.)
            try:
                from mutagen import File
                audio = File(audio_path)
                if audio and audio.info:
                    info['duration'] = int(audio.info.length)
                if audio and audio.tags:
                    for k, v in audio.tags.items():
                        kl = k.lower()
                        if "title" in kl and v:
                            info['title'] = str(v[0])
                        elif "artist" in kl and v:
                            info['artist'] = str(v[0])
                        elif "album" in kl and v:
                            info['album'] = str(v[0])
            except Exception:
                pass

    except Exception as e:
        print(f"[library] Error leyendo metadatos de {audio_path}: {e}")

    return info


def get_songs(limit: Optional[int] = None) -> List[dict]:
    """
    Devuelve lista de canciones descargadas, ordenadas por fecha de modificación (más reciente primero).
    """
    _load_cache()
    download_dir = downloader.get_download_dir()
    audio_files = sorted(
        [p for p in download_dir.iterdir() if p.suffix.lower() in AUDIO_EXTS],
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    songs = []
    cache_updated = False

    for audio_path in audio_files:
        path_str = str(audio_path)
        mtime = audio_path.stat().st_mtime

        # Usar caché si el archivo no cambió
        if path_str in _cache and _cache[path_str].get('_mtime') == mtime:
            songs.append(_cache[path_str])
        else:
            meta = _extract_metadata(path_str)
            meta['_mtime'] = mtime
            _cache[path_str] = meta
            songs.append(meta)
            cache_updated = True

    if cache_updated:
        _save_cache()

    if limit:
        return songs[:limit]
    return songs


def delete_song(path: str) -> bool:
    """Elimina un archivo de música y sus datos asociados."""
    try:
        p = Path(path)
        if p.exists():
            p.unlink()
        # Eliminar portada si existe
        cover = p.with_suffix('.jpg')
        if cover.exists():
            cover.unlink()
        # Limpiar caché
        if path in _cache:
            del _cache[path]
            _save_cache()
        return True
    except Exception as e:
        print(f"[library] Error eliminando {path}: {e}")
        return False


def song_count() -> int:
    download_dir = downloader.get_download_dir()
    return len([p for p in download_dir.iterdir() if p.suffix.lower() in AUDIO_EXTS])
