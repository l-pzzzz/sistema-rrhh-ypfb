# Levanta la demo del sistema en Windows (PowerShell 5.1 o superior).
# Uso, desde la carpeta del repositorio:
#   powershell -ExecutionPolicy Bypass -File .\scripts\levantar_demo.ps1
# Requisitos: Git y Docker Desktop abierto. No necesita Python.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

function Nuevo-Secreto([int]$bytes = 36) {
    $b = New-Object byte[] $bytes
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b)
    return [Convert]::ToBase64String($b).Replace('+', '-').Replace('/', '_').TrimEnd('=')
}

# 1. .env con secretos propios (solo si no existe; nunca se sube al repositorio)
if (-not (Test-Path .env)) {
    $lineas = Get-Content .env.example -Encoding UTF8
    $lineas = $lineas -replace '^SECRET_KEY=$', ("SECRET_KEY=" + (Nuevo-Secreto 50))
    $lineas = $lineas -replace '^DB_PASSWORD=$', ("DB_PASSWORD=" + (Nuevo-Secreto))
    $lineas = $lineas -replace '^DB_ROOT_PASSWORD=$', ("DB_ROOT_PASSWORD=" + (Nuevo-Secreto))
    $lineas = $lineas -replace '^REDIS_PASSWORD=$', ("REDIS_PASSWORD=" + (Nuevo-Secreto))
    # UTF-8 sin BOM: Docker Compose no admite el BOM al inicio del archivo.
    [System.IO.File]::WriteAllLines((Join-Path (Get-Location) ".env"), $lineas, (New-Object System.Text.UTF8Encoding $false))
    Write-Host ".env creado con secretos aleatorios."
} else {
    Write-Host ".env ya existe: se usa el actual."
}

# 2. Docker Desktop debe estar corriendo
docker info *> $null
if ($LASTEXITCODE -ne 0) { throw "Docker Desktop no está abierto. Ábralo, espere a que diga 'Running' y vuelva a ejecutar el script." }

# 3. Levantar MySQL, Redis, web, Celery y nginx
docker compose -p rrhh-demo up -d --build
if ($LASTEXITCODE -ne 0) { throw "No se pudo levantar el sistema con Docker Compose." }

# 4. Esperar las migraciones (la primera vez tardan alrededor de un minuto)
for ($i = 1; $i -le 30; $i++) {
    docker compose -p rrhh-demo exec -T web python manage.py migrate --noinput *> $null
    if ($LASTEXITCODE -eq 0) { break }
    Write-Host "Esperando a que la base de datos esté lista ($i/30)..."
    Start-Sleep -Seconds 5
}
if ($LASTEXITCODE -ne 0) { throw "Las migraciones no terminaron. Revise: docker compose -p rrhh-demo logs web" }

# 5. Datos de demostración: las contraseñas se muestran UNA sola vez
Write-Host ""
Write-Host "=== Copie las contraseñas que aparecen a continuación: no se vuelven a mostrar ===" -ForegroundColor Yellow
docker compose -p rrhh-demo exec -T web python manage.py cargar_datos_demo

# 6. Abrir el navegador
Start-Process "https://localhost:8443"
Write-Host ""
Write-Host "Listo: https://localhost:8443 (acepte la advertencia del certificado autofirmado)."
Write-Host "Para apagar y borrar la demo: docker compose -p rrhh-demo down -v"
