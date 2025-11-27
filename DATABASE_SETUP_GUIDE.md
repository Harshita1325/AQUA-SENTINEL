# 🗄️ DATABASE SETUP GUIDE - AQUA-SENTINEL

## Quick Setup (Recommended)

### Option 1: Automated Installation (Windows)

Run the PowerShell setup script:
```powershell
cd C:\Users\shewa\OneDrive\Desktop\Neurobots\Aqua-Sentinel
.\setup_database.ps1
```

### Option 2: Manual Installation

---

## 📦 INSTALL POSTGRESQL

### Windows Installation:

1. **Download PostgreSQL:**
   - Visit: https://www.postgresql.org/download/windows/
   - Download latest version (PostgreSQL 15 or 16)
   - Or use direct link: https://www.enterprisedb.com/downloads/postgres-postgresql-downloads

2. **Install:**
   ```
   - Run the installer
   - Set password: drdo123456 (or your choice)
   - Port: 5432 (default)
   - Locale: Default
   - Install components: PostgreSQL Server, pgAdmin 4, Command Line Tools
   ```

3. **Verify Installation:**
   ```powershell
   psql --version
   ```

---

## 🪣 INSTALL MINIO (S3-Compatible Storage)

### Windows Installation:

1. **Download MinIO:**
   ```powershell
   # Download MinIO server
   Invoke-WebRequest -Uri "https://dl.min.io/server/minio/release/windows-amd64/minio.exe" -OutFile "C:\minio\minio.exe"
   ```

2. **Create Data Directory:**
   ```powershell
   mkdir C:\minio\data
   ```

3. **Start MinIO Server:**
   ```powershell
   # Set credentials
   $env:MINIO_ROOT_USER = "admin"
   $env:MINIO_ROOT_PASSWORD = "drdo123456"
   
   # Start server
   C:\minio\minio.exe server C:\minio\data --console-address ":9001"
   ```

4. **Access MinIO Console:**
   - Open: http://localhost:9001
   - Login: admin / drdo123456

---

## ⚙️ CONFIGURE DATABASE

### 1. Create PostgreSQL Database:

```powershell
# Connect to PostgreSQL
psql -U postgres

# In psql prompt:
CREATE DATABASE drdo_underwater;
CREATE USER admin WITH PASSWORD 'drdo123456';
GRANT ALL PRIVILEGES ON DATABASE drdo_underwater TO admin;
\q
```

### 2. Set Environment Variables:

**Windows (PowerShell):**
```powershell
# PostgreSQL
[System.Environment]::SetEnvironmentVariable('POSTGRES_HOST', 'localhost', 'User')
[System.Environment]::SetEnvironmentVariable('POSTGRES_PORT', '5432', 'User')
[System.Environment]::SetEnvironmentVariable('POSTGRES_DB', 'drdo_underwater', 'User')
[System.Environment]::SetEnvironmentVariable('POSTGRES_USER', 'admin', 'User')
[System.Environment]::SetEnvironmentVariable('POSTGRES_PASSWORD', 'drdo123456', 'User')

# MinIO
[System.Environment]::SetEnvironmentVariable('MINIO_ENDPOINT', 'localhost:9000', 'User')
[System.Environment]::SetEnvironmentVariable('MINIO_ACCESS_KEY', 'admin', 'User')
[System.Environment]::SetEnvironmentVariable('MINIO_SECRET_KEY', 'drdo123456', 'User')
```

### 3. Or Use .env File:

Create `webapp/.env`:
```env
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=drdo_underwater
POSTGRES_USER=admin
POSTGRES_PASSWORD=drdo123456

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=drdo123456

# Security
ENCRYPTION_KEY=your-32-byte-encryption-key-here
SECRET_KEY=your-flask-secret-key-here
```

---

## 🚀 START SERVICES

### 1. Start PostgreSQL:
```powershell
# Windows (if not auto-started)
net start postgresql-x64-15  # or your version
```

### 2. Start MinIO:
```powershell
# Run in separate terminal
cd C:\minio
$env:MINIO_ROOT_USER = "admin"
$env:MINIO_ROOT_PASSWORD = "drdo123456"
.\minio.exe server .\data --console-address ":9001"
```

### 3. Start Aqua-Sentinel:
```powershell
cd C:\Users\shewa\OneDrive\Desktop\Neurobots\Aqua-Sentinel\webapp
python app.py
```

---

## ✅ VERIFY CONNECTION

### Check PostgreSQL:
```powershell
psql -U admin -d drdo_underwater -h localhost
```

### Check MinIO:
Open browser: http://localhost:9001

### Check Aqua-Sentinel:
Open browser: http://localhost:5000

---

## 🔧 TROUBLESHOOTING

### PostgreSQL Issues:

**Connection Refused:**
```powershell
# Check if service is running
Get-Service -Name postgresql*

# Start service
net start postgresql-x64-15
```

**Authentication Failed:**
```powershell
# Reset password
psql -U postgres
ALTER USER admin WITH PASSWORD 'drdo123456';
```

### MinIO Issues:

**Port Already in Use:**
```powershell
# Use different port
.\minio.exe server .\data --address ":9002" --console-address ":9003"

# Update .env:
MINIO_ENDPOINT=localhost:9002
```

**Access Denied:**
- Check credentials in environment variables
- Verify MINIO_ROOT_USER and MINIO_ROOT_PASSWORD

---

## 🎯 DOCKER SETUP (Alternative - Easiest!)

If you have Docker installed:

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: drdo_underwater
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: drdo123456
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: admin
      MINIO_ROOT_PASSWORD: drdo123456
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data

volumes:
  postgres_data:
  minio_data:
```

Run:
```powershell
docker-compose up -d
```

---

## 📊 DATABASE FEATURES

Once connected, you'll have:

✅ **Persistent Storage**: All images and results saved to database
✅ **User Management**: Multi-user support with roles
✅ **Audit Logs**: Track all operations
✅ **Search & Filter**: Query historical data
✅ **Backup & Recovery**: Automated backups
✅ **S3 Storage**: Scalable object storage with MinIO
✅ **Encryption**: Military-grade data protection

---

## 🔒 SECURITY NOTES

1. **Change Default Passwords** in production
2. **Enable SSL** for PostgreSQL and MinIO
3. **Use Strong Encryption Keys**
4. **Restrict Network Access** with firewall
5. **Regular Backups** of database
6. **Audit Logs** enabled by default

---

## 🆘 QUICK FIX: Skip Database (Temporary)

If you want to use the system WITHOUT database:

The system already works in **file-based mode**. Just ignore the warning:
```
⚠️ Database connection failed: connection to server at "localhost"
```

All features work using local file storage instead of database.

---

## 📞 SUPPORT

For issues:
1. Check logs in `webapp/logs/`
2. Verify services are running
3. Check firewall settings
4. Review environment variables

**Current Status**: System works WITHOUT database ✅
**Optional Setup**: Database adds advanced features 🚀
