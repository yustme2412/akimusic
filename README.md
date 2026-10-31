# 🎵 AkiMusic — Reproductor y Descargador Offline (Android APK)

App para Android y Desktop para **descargar, organizar y escuchar música y playlists sin conexión a internet** a partir de cualquier enlace (Spotify, YouTube, SoundCloud, etc.).  
Diseño **blanco y negro** minimalista.

✨ **100% Libre y sin keys**: Ya **no requiere** crear apps en Spotify Developers ni ingresar Client ID ni Client Secret.

---

## 🚀 Novedades y Características

- **Sin API Keys**: Extrae directamente los metadatos de canciones, álbumes y playlists de Spotify mediante su motor integrado sin credenciales de usuario.
- **Enlaces Universales**: Acepta URLs de canciones, álbumes y playlists de Spotify, además de enlaces directos de YouTube, YouTube Music y SoundCloud.
- **Modo Offline Completo**: Guarda los archivos en el almacenamiento local (`Music/AkiMusic`) con carátulas y metadatos para reproducirlos sin conexión.
- **Reproductor Integrado**: Control de reproducción (play/pause, anterior, siguiente, barra de progreso y cola de reproducción).
- **Biblioteca Automática**: Escaneo y organización de archivos de audio (`.mp3`, `.m4a`, `.opus`, `.webm`, `.ogg`, `.flac`, `.wav`).

---

## 📁 Estructura del Proyecto

| Archivo / Carpeta | Descripción |
|---|---|
| `main.py` | Aplicación visual (Kivy) con diseño monocromático |
| `downloader.py` | Motor de descarga sin keys de Spotify (Spotify Embed + `yt-dlp`) |
| `library.py` | Gestor de la biblioteca local de música offline y metadatos |
| `player.py` | Reproductor de audio con soporte para Android y Desktop |
| `buildozer.spec` | Configuración para compilar el APK con Buildozer / Python-for-Android |
| `Compilar_AkiMusic.ps1` | Lanzador automático para compilar en Windows mediante WSL |
| `build.sh` | Script automatizado para compilar en Linux / WSL |
| `.github/workflows/build_apk.yml` | Compilación automática del APK en la nube con GitHub Actions |
| `android_app/` | Proyecto Android nativo (Gradle / Compose) listo para compilar |

---

## 🏗️ Cómo Generar el APK

Tienes 3 alternativas según tu preferencia:

### Opción 1 — En la nube con GitHub Actions (Recomendada / Sin configurar nada localmente)
1. Sube este repositorio a tu cuenta de GitHub.
2. Ve a la pestaña **Actions** en tu repositorio de GitHub.
3. El flujo **Build AkiMusic APK** compilará automáticamente el APK en los servidores de GitHub.
4. Descarga el archivo `AkiMusic-APK` listo para instalar en tu teléfono Android.

---

### Opción 2 — Compilar en Windows con WSL
1. Si no tienes WSL instalado, abre PowerShell como Administrador y ejecuta:
   ```powershell
   wsl --install -d Ubuntu
   ```
2. Ejecuta el script incluido:
   ```powershell
   .\Compilar_AkiMusic.ps1
   ```
   O directamente desde tu terminal WSL:
   ```bash
   bash build.sh
   ```
3. El APK compilado se guardará en la carpeta `bin/`.

---

### Opción 3 — Proyecto Android con Gradle / Android Studio
En la carpeta `android_app/`:
```bash
cd android_app
.\gradlew.bat assembleDebug
```
El APK se genera en `android_app/app/build/outputs/apk/debug/app-debug.apk`.

---

## 📱 Instalación en Android

1. Pasa el archivo `.apk` a tu teléfono móvil (por USB, Drive, Telegram, etc.).
2. En tu teléfono: **Ajustes** → **Seguridad** → **Instalar aplicaciones desconocidas** → Permitir.
3. Abre el archivo `.apk` desde el gestor de archivos de tu teléfono y pulsa **Instalar**.
4. ¡Listo! Abre **AkiMusic**, pega cualquier link y descarga tus canciones favoritas para escucharlas sin internet.

---

## 🧪 Probar en Windows (Desktop Preview)

Para probar la interfaz y las descargas directamente en tu computadora:

```powershell
python -m pip install -r requirements.txt
python main.py
```
