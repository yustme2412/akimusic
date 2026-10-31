"""
AkiMusic - downloader.py
Motor de descarga universal y sin necesidad de API keys de Spotify.
Soporta:
  1. Canciones, álbumes y playlists de Spotify (extracción directa sin API keys).
  2. Enlaces directos de YouTube, YouTube Music, SoundCloud y URLs genéricas.
  3. Integración nativa con yt-dlp en Python (compatible con Android y Desktop).
"""

import os
import re
import json
import urllib.request
from pathlib import Path
from typing import Optional, List, Dict, Tuple

# Detectar plataforma y definir carpeta de descargas
def get_download_dir() -> Path:
    # Si estamos en Android
    if "ANDROID_ARGUMENT" in os.environ or os.path.exists("/sdcard"):
        # Intentar carpeta pública Music/AkiMusic
        base = Path("/sdcard/Music/AkiMusic")
        try:
            base.mkdir(parents=True, exist_ok=True)
            return base
        except Exception:
            pass
    # Desktop (Windows / Linux / macOS)
    path = Path.home() / "Music" / "AkiMusic"
    path.mkdir(parents=True, exist_ok=True)
    return path

DOWNLOAD_DIR = get_download_dir()
CONFIG_FILE = Path(__file__).parent / "config.json"

# Headers estándar para peticiones web
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
}

# ─── CONFIG ──────────────────────────────────────────────
def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_config(data: dict):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass

def has_credentials() -> bool:
    # Ya NO son obligatorias las credenciales
    return True


# ─── EXTRACTOR SPOTIFY SIN API KEYS ──────────────────────
def _extract_spotify_id_and_type(url: str) -> Tuple[Optional[str], Optional[str]]:
    """Extrae el tipo (track/album/playlist) y el ID de una URL de Spotify."""
    patterns = [
        r"open\.spotify\.com/(track|album|playlist)/([A-Za-z0-9]+)",
        r"spotify:(track|album|playlist):([A-Za-z0-9]+)",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1), m.group(2)
    return None, None


def _get_spotify_metadata_no_keys(res_type: str, res_id: str) -> List[Dict]:
    """
    Obtiene los datos de canciones de Spotify sin requerir credenciales ni tokens de desarrollador.
    Usa el endpoint público embed de Spotify.
    """
    embed_url = f"https://open.spotify.com/embed/{res_type}/{res_id}"
    req = urllib.request.Request(embed_url, headers=DEFAULT_HEADERS)
    
    html = urllib.request.urlopen(req, timeout=12).read().decode("utf-8", "ignore")
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html)
    if not m:
        # Fallback a oEmbed
        return _get_spotify_oembed(res_type, res_id)

    data = json.loads(m.group(1))
    entity = data.get("props", {}).get("pageProps", {}).get("state", {}).get("data", {}).get("entity", {})

    cover = ""
    images = entity.get("visualIdentity", {}).get("image", [])
    if images:
        cover = images[-1].get("url", "")

    tracks = []
    if res_type == "track":
        title = entity.get("title") or entity.get("name") or "Canción desconocida"
        artists = ", ".join(a.get("name", "") for a in entity.get("artists", [])) or "Artista desconocido"
        tracks.append({
            "title": title,
            "artist": artists,
            "album": entity.get("album", {}).get("name", ""),
            "cover": cover,
        })
    else:
        # Álbum o Playlist
        collection_name = entity.get("title") or entity.get("name") or ""
        track_list = entity.get("trackList", [])
        for t in track_list:
            tracks.append({
                "title": t.get("title", ""),
                "artist": t.get("subtitle", "Artista desconocido"),
                "album": collection_name,
                "cover": cover,
            })

    return tracks


def _get_spotify_oembed(res_type: str, res_id: str) -> List[Dict]:
    """Fallback secundario usando oEmbed de Spotify."""
    try:
        url = f"https://open.spotify.com/oembed?url=https://open.spotify.com/{res_type}/{res_id}"
        req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
        data = json.loads(urllib.request.urlopen(req, timeout=10).read().decode("utf-8"))
        title = data.get("title", "Canción")
        cover = data.get("thumbnail_url", "")
        return [{
            "title": title,
            "artist": "",
            "album": "",
            "cover": cover
        }]
    except Exception:
        return []


# ─── MOTOR DE DESCARGA (yt-dlp directo) ─────────────────
def _download_via_ytdlp(query_or_url: str, output_title: Optional[str], progress_cb) -> bool:
    """
    Descarga audio usando la librería yt-dlp en Python de forma directa.
    """
    import yt_dlp

    download_dir = get_download_dir()
    if output_title:
        safe_title = re.sub(r'[\\/*?:"<>|]', "", output_title).strip()
        outtmpl = str(download_dir / f"{safe_title}.%(ext)s")
    else:
        outtmpl = str(download_dir / "%(title)s.%(ext)s")

    def ytdlp_hook(d):
        status = d.get("status")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            if total > 0:
                pct = int((downloaded / total) * 100)
            else:
                pct = 50
            name = output_title or d.get("filename", "")
            progress_cb("Descargando audio", min(pct, 98), Path(name).stem)
        elif status == "finished":
            name = output_title or d.get("filename", "")
            progress_cb("Procesando audio...", 99, Path(name).stem)

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": outtmpl,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [ytdlp_hook],
        "ignoreerrors": True,
    }

    # Si ffmpeg existe, podemos convertir a mp3
    try:
        import subprocess
        ffmpeg_check = subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if ffmpeg_check.returncode == 0:
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]
    except Exception:
        pass

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ret = ydl.download([query_or_url])
            return ret == 0
    except Exception as e:
        print(f"[downloader] Error yt-dlp: {e}")
        return False


def _tag_file_with_metadata(title: str, artist: str, album: str, cover_url: Optional[str]):
    """Intenta escribir tags ID3 y carátula si mutagen está disponible."""
    try:
        from mutagen.easyid3 import EasyID3
        from mutagen.id3 import ID3, APIC
        from mutagen.mp3 import MP3

        download_dir = get_download_dir()
        # Buscar el archivo más recientemente modificado
        audio_files = sorted(
            [p for p in download_dir.iterdir() if p.suffix.lower() in [".mp3", ".m4a", ".opus", ".webm", ".ogg"]],
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        if not audio_files:
            return
        latest = audio_files[0]

        if latest.suffix.lower() == ".mp3":
            try:
                audio = EasyID3(str(latest))
            except Exception:
                audio = EasyID3()
            if title:
                audio["title"] = [title]
            if artist:
                audio["artist"] = [artist]
            if album:
                audio["album"] = [album]
            audio.save(str(latest))

            if cover_url:
                try:
                    req = urllib.request.Request(cover_url, headers=DEFAULT_HEADERS)
                    img_data = urllib.request.urlopen(req, timeout=8).read()
                    id3 = ID3(str(latest))
                    id3.add(APIC(
                        encoding=3,
                        mime="image/jpeg",
                        type=3,
                        desc="Cover",
                        data=img_data
                    ))
                    id3.save(str(latest))
                except Exception:
                    pass
    except Exception:
        pass


# ─── FUNCIÓN PRINCIPAL DE DESCARGA ────────────────────────
def download(url: str, progress_cb, done_cb):
    """
    Descarga canciones a partir de cualquier enlace (Spotify, YouTube, SoundCloud, etc.)
    sin requerir credenciales de usuario.
    """
    url = url.strip()
    if not url:
        done_cb(False, "El enlace está vacío.")
        return

    # 1. Comprobar si es un enlace de Spotify
    sp_type, sp_id = _extract_spotify_id_and_type(url)

    if sp_type and sp_id:
        progress_cb("Obteniendo información de Spotify...", 5, "")
        try:
            tracks = _get_spotify_metadata_no_keys(sp_type, sp_id)
        except Exception as e:
            tracks = []

        if not tracks:
            done_cb(False, "No se pudo leer la información de Spotify. Comprueba el enlace o tu conexión.")
            return

        total = len(tracks)
        progress_cb(f"Preparando {total} canción(es)...", 10, "")
        downloaded = 0
        failed = 0

        for i, track in enumerate(tracks):
            song_name = f"{track['artist']} - {track['title']}"
            base_pct = 10 + int((i / total) * 85)

            def make_cb(bp):
                def cb(status, pct, name):
                    final_pct = bp + int(pct * 0.85 / total)
                    progress_cb(status, min(final_pct, 98), song_name)
                return cb

            progress_cb("Buscando audio", base_pct, song_name)
            search_query = f"ytsearch1:{track['artist']} - {track['title']} audio"
            ok = _download_via_ytdlp(search_query, song_name, make_cb(base_pct))
            if ok:
                downloaded += 1
                _tag_file_with_metadata(track["title"], track["artist"], track["album"], track.get("cover"))
            else:
                failed += 1

        if downloaded > 0:
            msg = f"{downloaded} canción(es) descargada(s) correctamente."
            if failed > 0:
                msg += f" ({failed} no pudieron descargarse)"
            done_cb(True, msg)
        else:
            done_cb(False, "No se pudo descargar ninguna canción. Revisa tu conexión.")

    else:
        # 2. Es un enlace directo de YouTube u otra plataforma
        progress_cb("Analizando enlace directo...", 10, "")
        try:
            ok = _download_via_ytdlp(url, None, progress_cb)
            if ok:
                done_cb(True, "Audio descargado correctamente.")
            else:
                done_cb(False, "No se pudo descargar el enlace directo.")
        except Exception as e:
            done_cb(False, f"Error: {e}")
