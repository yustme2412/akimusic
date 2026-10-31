[app]

# ─── Info de la app ─────────────────────────────────────
title = AkiMusic
package.name = akimusic
package.domain = com.akimusic
version = 1.0.0

# ─── Código fuente ───────────────────────────────────────
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
source.main = main.py

# ─── Dependencias Python ─────────────────────────────────
requirements = python3,kivy==2.3.0,pillow,mutagen,requests,certifi,charset-normalizer,urllib3,yt-dlp

# ─── Permisos Android ────────────────────────────────────
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,READ_MEDIA_AUDIO,READ_MEDIA_IMAGES
android.request_legacy_external_storage = True

# ─── Android SDK ─────────────────────────────────────────
android.api = 33
android.minapi = 24
android.ndk = 25b
android.sdk = 33
android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a

# ─── Configuración de la app ─────────────────────────────
orientation = portrait
fullscreen = 0

# ─── Icono y splash ──────────────────────────────────────
# icon.filename = %(source.dir)s/assets/icon.png
# presplash.filename = %(source.dir)s/assets/splash.png

# ─── Android extras ──────────────────────────────────────
android.enable_androidx = True

# ─── Log level ───────────────────────────────────────────
log_level = 2

[buildozer]
# Directorio de build (en Linux/WSL)
build_dir = ./.buildozer
bin_dir = ./bin
warn_on_root = 1
