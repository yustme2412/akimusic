# AkiMusic APK Builder - Lanzador automático
# Ejecutar en PowerShell

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   AkiMusic APK Builder - Iniciando Compilación " -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Directorio actual
$currentDir = $PSScriptRoot
# Convertir a ruta WSL
$wslPath = $currentDir -replace '\\', '/' -replace '([A-Za-z]):', '/mnt/$1'
$wslPath = $wslPath.ToLower().Substring(0, 7) + $wslPath.Substring(7)
$buildScript = "$wslPath/build.sh"

Write-Host "Directorio del proyecto: $currentDir" -ForegroundColor Gray
Write-Host "Ruta en WSL: $wslPath" -ForegroundColor Gray
Write-Host ""

# Verificar si WSL está disponible
$wslCheck = wsl.exe --status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "AVISO: WSL no tiene una distribución configurada aún." -ForegroundColor Yellow
    Write-Host "Para compilar con WSL en Windows:" -ForegroundColor Cyan
    Write-Host "1. Abre una terminal como Administrador y ejecuta: wsl --install -d Ubuntu" -ForegroundColor White
    Write-Host "2. Una vez instalado Ubuntu, vuelve a ejecutar este script." -ForegroundColor White
    Write-Host ""
    Write-Host "TIP: ¡También puedes usar el flujo de GitHub Actions incluido (.github/workflows/build_apk.yml)!" -ForegroundColor Green
    Write-Host ""
    Read-Host "Presiona Enter para salir"
    exit 0
}

Write-Host "Ejecutando compilacion en WSL..." -ForegroundColor Yellow
wsl.exe bash -c "cd '$wslPath' && chmod +x build.sh && bash build.sh"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Green
    Write-Host "   APK compilado correctamente!                " -ForegroundColor Green
    Write-Host "   Revisa la carpeta 'bin/' o tu Escritorio    " -ForegroundColor Green
    Write-Host "================================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Hubo un error durante la compilación en WSL." -ForegroundColor Red
}

Write-Host ""
Read-Host "Presiona Enter para salir"
