#!/usr/bin/env bash
# =============================================================
#  AkiMusic — Script de compilación automática del APK
#  Ejecutar dentro de Linux/WSL
#  Uso: bash build.sh
# =============================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK_DIR="$HOME/akimusic_build"

echo -e "${CYAN}"
echo "╔═══════════════════════════════════════╗"
echo "║        AkiMusic APK Builder           ║"
echo "╚═══════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${YELLOW}[1/5] Preparando espacio de trabajo...${NC}"
mkdir -p "$WORK_DIR"
cp -r "$SCRIPT_DIR"/* "$WORK_DIR/" 2>/dev/null || true
cd "$WORK_DIR"
echo -e "${GREEN}✓ Archivos preparados en $WORK_DIR${NC}"

echo -e "${YELLOW}[2/5] Verificando dependencias del sistema...${NC}"
sudo apt-get update -qq
sudo apt-get install -y -qq \
    python3 python3-pip python3-venv \
    git zip unzip \
    openjdk-17-jdk \
    libffi-dev libssl-dev \
    build-essential autoconf libtool pkg-config \
    cmake ninja-build \
    ffmpeg wget curl lld

echo -e "${GREEN}✓ Dependencias del sistema listas${NC}"

echo -e "${YELLOW}[3/5] Configurando entorno virtual Python...${NC}"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip --quiet
pip install --quiet \
    "cython<3.0" \
    "buildozer>=1.5.0" \
    "kivy>=2.3.0" \
    yt-dlp \
    mutagen \
    Pillow \
    requests

echo -e "${GREEN}✓ Entorno Python listo${NC}"

echo -e "${YELLOW}[4/5] Iniciando compilación de Android APK con Buildozer...${NC}"
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

buildozer android debug 2>&1 | tee build.log

echo -e "${YELLOW}[5/5] Buscando APK generado...${NC}"
APK_FILE=$(find bin/ -name "*.apk" 2>/dev/null | head -1)

if [ -n "$APK_FILE" ]; then
    echo -e "${GREEN}"
    echo "╔═══════════════════════════════════════╗"
    echo "║         ¡APK COMPILADO! ✓             ║"
    echo "╚═══════════════════════════════════════╝"
    echo -e "${NC}"
    echo -e "${GREEN}APK listo: $WORK_DIR/$APK_FILE${NC}"
    
    # Copiar de vuelta a la carpeta del proyecto
    mkdir -p "$SCRIPT_DIR/bin"
    cp "$APK_FILE" "$SCRIPT_DIR/bin/"
    echo -e "${GREEN}✓ APK guardado en: $SCRIPT_DIR/bin/$(basename "$APK_FILE")${NC}"

    # Si hay escritorio Windows accesible
    WIN_DESKTOP="/mnt/c/Users/$USER/Desktop"
    if [ -d "$WIN_DESKTOP" ]; then
        cp "$APK_FILE" "$WIN_DESKTOP/AkiMusic.apk" && echo -e "${GREEN}✓ APK copiado al escritorio de Windows${NC}"
    fi
else
    echo -e "${RED}✗ No se encontró el APK. Revisa build.log.${NC}"
    exit 1
fi
