# Quick Database Setup for Aqua-Sentinel
# Run this as Administrator

Write-Host "🌊 Quick Database Setup" -ForegroundColor Cyan

$choice = Read-Host @"

Choose setup option:
1. Full Automated Setup (Installs PostgreSQL + MinIO)
2. Docker Setup (Easiest - requires Docker Desktop)
3. Skip Database (Use file-based storage)

Enter choice (1-3)
"@

switch ($choice) {
    "1" {
        Write-Host "`n🚀 Starting full automated setup..." -ForegroundColor Green
        Write-Host "This will install PostgreSQL and MinIO" -ForegroundColor Yellow
        Write-Host ""
        $confirm = Read-Host "Continue? (Y/N)"
        if ($confirm -eq "Y" -or $confirm -eq "y") {
            .\setup_database.ps1
        }
    }
    
    "2" {
        Write-Host "`n🐳 Docker Setup Selected" -ForegroundColor Green
        Write-Host ""
        Write-Host "Requirements:" -ForegroundColor Yellow
        Write-Host "  - Docker Desktop installed" -ForegroundColor White
        Write-Host "  - Docker Desktop running" -ForegroundColor White
        Write-Host ""
        
        $hasDocker = Get-Command docker -ErrorAction SilentlyContinue
        if ($hasDocker) {
            Write-Host "✅ Docker found!" -ForegroundColor Green
            Write-Host "`nCreating docker-compose.yml..." -ForegroundColor Cyan
            
            $dockerCompose = @"
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: aqua-sentinel-db
    environment:
      POSTGRES_DB: drdo_underwater
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: drdo123456
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  minio:
    image: minio/minio
    container_name: aqua-sentinel-minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: admin
      MINIO_ROOT_PASSWORD: drdo123456
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
    restart: unless-stopped

volumes:
  postgres_data:
  minio_data:
"@
            
            $dockerCompose | Out-File -FilePath "docker-compose.yml" -Encoding UTF8
            
            Write-Host "✅ Created docker-compose.yml" -ForegroundColor Green
            Write-Host "`nStarting services..." -ForegroundColor Cyan
            
            docker-compose up -d
            
            Write-Host ""
            Write-Host "✅ Services Started!" -ForegroundColor Green
            Write-Host ""
            Write-Host "Access:" -ForegroundColor Yellow
            Write-Host "  - PostgreSQL: localhost:5432" -ForegroundColor White
            Write-Host "  - MinIO Console: http://localhost:9001" -ForegroundColor White
            Write-Host "  - Credentials: admin / drdo123456" -ForegroundColor White
            Write-Host ""
            Write-Host "Now run: python app.py" -ForegroundColor Cyan
        } else {
            Write-Host "❌ Docker not found!" -ForegroundColor Red
            Write-Host "Install Docker Desktop from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
        }
    }
    
    "3" {
        Write-Host "`n✅ File-Based Mode Selected" -ForegroundColor Green
        Write-Host ""
        Write-Host "The system will work without database using local files." -ForegroundColor White
        Write-Host "All features are available, just without persistent storage." -ForegroundColor White
        Write-Host ""
        Write-Host "Starting Aqua-Sentinel..." -ForegroundColor Cyan
        Set-Location "C:\Users\shewa\OneDrive\Desktop\Neurobots\Aqua-Sentinel\webapp"
        python app.py
    }
    
    default {
        Write-Host "Invalid choice. Please run again." -ForegroundColor Red
    }
}
