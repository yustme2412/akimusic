# Subir AkiMusic a GitHub — Script Automático
# Ejecuta este script en PowerShell para subir el proyecto a GitHub

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   AkiMusic — Subir a GitHub                   " -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que git esté instalado
if (!(Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Git no está instalado." -ForegroundColor Red
    Write-Host "Descárgalo en: https://git-scm.com/download/win" -ForegroundColor Yellow
    Read-Host "Presiona Enter para salir"
    exit 1
}

# Pedir URL del repositorio
Write-Host "Pasos previos en GitHub.com:" -ForegroundColor Green
Write-Host "  1. Ve a https://github.com/new" -ForegroundColor White
Write-Host "  2. Nombra tu repositorio (ej: akimusic)" -ForegroundColor White
Write-Host "  3. Haz clic en 'Create repository'" -ForegroundColor White
Write-Host "  4. Copia la URL que te muestra (ej: https://github.com/tuusuario/akimusic.git)" -ForegroundColor White
Write-Host ""
$repoUrl = Read-Host "Pega aquí la URL de tu repositorio de GitHub"

if (!$repoUrl -or !$repoUrl.StartsWith("https://")) {
    Write-Host "URL no válida." -ForegroundColor Red
    exit 1
}

# Inicializar git si no existe
if (!(Test-Path ".git")) {
    git init
    Write-Host "Git inicializado." -ForegroundColor Green
}

# Añadir todos los archivos
git add .
git commit -m "Primer commit: AkiMusic sin keys de Spotify" 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "AVISO: Configurando identidad de Git..." -ForegroundColor Yellow
    $nombre = Read-Host "Tu nombre para git (ej: Tu Nombre)"
    $email = Read-Host "Tu email para git"
    git config user.name "$nombre"
    git config user.email "$email"
    git add .
    git commit -m "Primer commit: AkiMusic sin keys de Spotify"
}

# Conectar y subir
git remote remove origin 2>$null
git remote add origin $repoUrl
git branch -M main
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Green
    Write-Host "   Código subido exitosamente!                  " -ForegroundColor Green
    Write-Host "   GitHub Actions compilará el APK en ~20 min  " -ForegroundColor Green
    Write-Host "================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Próximos pasos:" -ForegroundColor Cyan
    Write-Host "  1. Ve a tu repositorio en GitHub" -ForegroundColor White
    Write-Host "  2. Haz clic en la pestaña 'Actions'" -ForegroundColor White
    Write-Host "  3. Espera a que termine el workflow 'Build AkiMusic APK'" -ForegroundColor White
    Write-Host "  4. Descarga el APK real de AkiMusic desde 'Artifacts'" -ForegroundColor White
} else {
    Write-Host "Error al subir. Puede ser que necesites autenticarte." -ForegroundColor Red
    Write-Host "Asegúrate de estar logueado en GitHub CLI o usa un token personal." -ForegroundColor Yellow
}

Write-Host ""
Read-Host "Presiona Enter para salir"
