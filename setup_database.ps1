# Aqua-Sentinel Database Setup Script
# Automated installation of PostgreSQL and MinIO

Write-Host "🌊 AQUA-SENTINEL DATABASE SETUP" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "⚠️  This script needs administrator privileges" -ForegroundColor Yellow
    Write-Host "Right-click and select 'Run as Administrator'" -ForegroundColor Yellow
    pause
    exit
}

# Configuration
$POSTGRES_VERSION = "15"
$POSTGRES_PASSWORD = "drdo123456"
$MINIO_PATH = "C:\minio"
$MINIO_DATA = "$MINIO_PATH\data"

Write-Host "`n📦 STEP 1: Installing Chocolatey (Package Manager)..." -ForegroundColor Green

# Install Chocolatey if not present
if (!(Get-Command choco -ErrorAction SilentlyContinue)) {
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    Write-Host "✅ Chocolatey installed" -ForegroundColor Green
} else {
    Write-Host "✅ Chocolatey already installed" -ForegroundColor Green
}

Write-Host "`n📦 STEP 2: Installing PostgreSQL..." -ForegroundColor Green

# Install PostgreSQL
if (!(Get-Command psql -ErrorAction SilentlyContinue)) {
    choco install postgresql15 -y --params "/Password:$POSTGRES_PASSWORD"
    
    # Add to PATH
    $env:Path += ";C:\Program Files\PostgreSQL\$POSTGRES_VERSION\bin"
    [System.Environment]::SetEnvironmentVariable("Path", $env:Path, [System.EnvironmentVariableTarget]::Machine)
    
    Write-Host "✅ PostgreSQL installed" -ForegroundColor Green
    Write-Host "   Default password: $POSTGRES_PASSWORD" -ForegroundColor Yellow
} else {
    Write-Host "✅ PostgreSQL already installed" -ForegroundColor Green
}

Write-Host "`n📦 STEP 3: Creating Database..." -ForegroundColor Green

Start-Sleep -Seconds 5  # Wait for PostgreSQL to start

# Create database
$createDbScript = @"
CREATE DATABASE drdo_underwater;
CREATE USER admin WITH PASSWORD '$POSTGRES_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE drdo_underwater TO admin;
ALTER DATABASE drdo_underwater OWNER TO admin;
"@

$createDbScript | & "C:\Program Files\PostgreSQL\$POSTGRES_VERSION\bin\psql.exe" -U postgres 2>$null

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Database 'drdo_underwater' created" -ForegroundColor Green
} else {
    Write-Host "⚠️  Database might already exist or PostgreSQL service starting..." -ForegroundColor Yellow
}

Write-Host "`n📦 STEP 4: Installing MinIO..." -ForegroundColor Green

# Create MinIO directory
if (!(Test-Path $MINIO_PATH)) {
    New-Item -ItemType Directory -Path $MINIO_PATH -Force | Out-Null
    New-Item -ItemType Directory -Path $MINIO_DATA -Force | Out-Null
    Write-Host "✅ Created MinIO directories" -ForegroundColor Green
}

# Download MinIO
$minioExe = "$MINIO_PATH\minio.exe"
if (!(Test-Path $minioExe)) {
    Write-Host "   Downloading MinIO..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri "https://dl.min.io/server/minio/release/windows-amd64/minio.exe" -OutFile $minioExe
    Write-Host "✅ MinIO downloaded" -ForegroundColor Green
} else {
    Write-Host "✅ MinIO already downloaded" -ForegroundColor Green
}

Write-Host "`n⚙️  STEP 5: Setting Environment Variables..." -ForegroundColor Green

# Set environment variables
$envVars = @{
    "POSTGRES_HOST" = "localhost"
    "POSTGRES_PORT" = "5432"
    "POSTGRES_DB" = "drdo_underwater"
    "POSTGRES_USER" = "admin"
    "POSTGRES_PASSWORD" = "$POSTGRES_PASSWORD"
    "MINIO_ENDPOINT" = "localhost:9000"
    "MINIO_ACCESS_KEY" = "admin"
    "MINIO_SECRET_KEY" = "$POSTGRES_PASSWORD"
}

foreach ($key in $envVars.Keys) {
    [System.Environment]::SetEnvironmentVariable($key, $envVars[$key], [System.EnvironmentVariableTarget]::User)
    Write-Host "   Set $key" -ForegroundColor Gray
}

Write-Host "✅ Environment variables configured" -ForegroundColor Green

Write-Host "`n🚀 STEP 6: Creating Startup Scripts..." -ForegroundColor Green

# Create MinIO startup script
$minioStartScript = @"
# Start MinIO Server for Aqua-Sentinel
`$env:MINIO_ROOT_USER = "admin"
`$env:MINIO_ROOT_PASSWORD = "$POSTGRES_PASSWORD"

Write-Host "🪣 Starting MinIO Server..." -ForegroundColor Cyan
Write-Host "Console: http://localhost:9001" -ForegroundColor Yellow
Write-Host "API: http://localhost:9000" -ForegroundColor Yellow
Write-Host "Login: admin / $POSTGRES_PASSWORD" -ForegroundColor Yellow
Write-Host ""

Set-Location "$MINIO_PATH"
.\minio.exe server .\data --console-address ":9001"
"@

$minioStartScript | Out-File -FilePath "$MINIO_PATH\start_minio.ps1" -Encoding UTF8

# Create all-in-one startup script
$startAllScript = @"
# Start All Services for Aqua-Sentinel

Write-Host "🌊 STARTING AQUA-SENTINEL SERVICES" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

# Start PostgreSQL
Write-Host "`n📊 Starting PostgreSQL..." -ForegroundColor Green
net start postgresql-x64-$POSTGRES_VERSION
Start-Sleep -Seconds 2

# Start MinIO in background
Write-Host "`n🪣 Starting MinIO..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-File", "$MINIO_PATH\start_minio.ps1"
Start-Sleep -Seconds 3

# Start Aqua-Sentinel
Write-Host "`n🚀 Starting Aqua-Sentinel Web Application..." -ForegroundColor Green
Set-Location "C:\Users\shewa\OneDrive\Desktop\Neurobots\Aqua-Sentinel\webapp"
Write-Host "Application will start at: http://localhost:5000" -ForegroundColor Yellow
Write-Host ""

python app.py
"@

$startAllScript | Out-File -FilePath "C:\Users\shewa\OneDrive\Desktop\Neurobots\Aqua-Sentinel\start_all_services.ps1" -Encoding UTF8

Write-Host "✅ Startup scripts created" -ForegroundColor Green

Write-Host "`n✅ SETUP COMPLETE!" -ForegroundColor Green -BackgroundColor Black
Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "📝 NEXT STEPS:" -ForegroundColor Yellow
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Close this window" -ForegroundColor White
Write-Host "2. Open NEW PowerShell (to load environment variables)" -ForegroundColor White
Write-Host "3. Run: .\start_all_services.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "Or start services individually:" -ForegroundColor Gray
Write-Host "  - PostgreSQL: " -NoNewline -ForegroundColor Gray
Write-Host "net start postgresql-x64-$POSTGRES_VERSION" -ForegroundColor Yellow
Write-Host "  - MinIO: " -NoNewline -ForegroundColor Gray
Write-Host ".\minio\start_minio.ps1" -ForegroundColor Yellow
Write-Host "  - Aqua-Sentinel: " -NoNewline -ForegroundColor Gray
Write-Host "python app.py" -ForegroundColor Yellow
Write-Host ""
Write-Host "🌐 Access Points:" -ForegroundColor Cyan
Write-Host "  - Aqua-Sentinel: http://localhost:5000" -ForegroundColor White
Write-Host "  - MinIO Console: http://localhost:9001" -ForegroundColor White
Write-Host "  - PostgreSQL: localhost:5432" -ForegroundColor White
Write-Host ""
Write-Host "🔐 Credentials:" -ForegroundColor Cyan
Write-Host "  - Username: admin" -ForegroundColor White
Write-Host "  - Password: $POSTGRES_PASSWORD" -ForegroundColor White
Write-Host ""

pause
