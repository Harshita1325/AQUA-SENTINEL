"""
Quick test script to verify database setup
Run this after starting Docker containers
"""

import sys
import time

def test_docker():
    """Test if Docker is installed and running"""
    import subprocess
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ Docker is installed:", result.stdout.strip())
            return True
        else:
            print("❌ Docker command failed")
            return False
    except FileNotFoundError:
        print("❌ Docker is not installed")
        print("   Please install Docker Desktop from: https://www.docker.com/products/docker-desktop")
        return False
    except Exception as e:
        print(f"❌ Error checking Docker: {e}")
        return False


def test_postgres():
    """Test PostgreSQL connection"""
    try:
        import psycopg2
        print("\n🔍 Testing PostgreSQL connection...")
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='drdo_underwater',
            user='admin',
            password='drdo123456',
            connect_timeout=5
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ PostgreSQL connected successfully!")
        print(f"   Version: {version[:50]}...")
        cursor.close()
        conn.close()
        return True
    except ImportError:
        print("❌ psycopg2 not installed")
        print("   Run: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Make sure Docker Desktop is running")
        print("   2. Run: docker-compose up -d")
        print("   3. Check containers: docker-compose ps")
        return False


def test_minio():
    """Test MinIO connection"""
    try:
        from minio import Minio
        print("\n🔍 Testing MinIO connection...")
        client = Minio(
            'localhost:9000',
            access_key='admin',
            secret_key='drdo123456',
            secure=False
        )
        # Test by listing buckets
        buckets = client.list_buckets()
        print(f"✅ MinIO connected successfully!")
        print(f"   Found {len(buckets)} bucket(s)")
        return True
    except ImportError:
        print("❌ minio package not installed")
        print("   Run: pip install minio")
        return False
    except Exception as e:
        print(f"❌ MinIO connection failed: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Make sure Docker containers are running")
        print("   2. Check: docker-compose ps")
        print("   3. View logs: docker-compose logs minio")
        return False


def test_database_config():
    """Test database configuration module"""
    try:
        print("\n🔍 Testing database configuration...")
        from database_config import SecureImageDatabase
        
        db = SecureImageDatabase()
        stats = db.get_statistics()
        
        print("✅ Database configuration loaded successfully!")
        print(f"\n📊 Current Statistics:")
        print(f"   Total Images: {stats['total_images']}")
        print(f"   Total Size: {stats['total_size_gb']:.2f} GB")
        print(f"   Activity (24h): {stats['activity_24h']}")
        
        db.close()
        return True
    except ImportError as e:
        print(f"❌ Missing module: {e}")
        print("   Run: pip install psycopg2-binary minio cryptography")
        return False
    except Exception as e:
        print(f"❌ Database config failed: {e}")
        return False


def check_docker_containers():
    """Check if Docker containers are running"""
    import subprocess
    try:
        print("\n🔍 Checking Docker containers...")
        result = subprocess.run(['docker-compose', 'ps'], 
                              capture_output=True, text=True, timeout=10,
                              cwd='../database-setup')
        
        if 'Up' in result.stdout:
            print("✅ Docker containers are running")
            print(result.stdout)
            return True
        else:
            print("❌ Docker containers are not running")
            print("\n💡 Start containers with:")
            print("   cd database-setup")
            print("   docker-compose up -d")
            return False
    except FileNotFoundError:
        print("❌ docker-compose not found or database-setup folder missing")
        return False
    except Exception as e:
        print(f"❌ Error checking containers: {e}")
        return False


def main():
    """Run all tests"""
    print("="*60)
    print("🧪 DRDO Database Setup - Connection Test")
    print("="*60)
    
    results = []
    
    # Test 1: Docker
    results.append(("Docker Installation", test_docker()))
    time.sleep(1)
    
    # Test 2: PostgreSQL
    results.append(("PostgreSQL Connection", test_postgres()))
    time.sleep(1)
    
    # Test 3: MinIO
    results.append(("MinIO Connection", test_minio()))
    time.sleep(1)
    
    # Test 4: Database Config
    results.append(("Database Configuration", test_database_config()))
    
    # Summary
    print("\n" + "="*60)
    print("📋 Test Summary")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("="*60)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 SUCCESS! Your database is fully operational!")
        print("\n📱 Access Web Interfaces:")
        print("   MinIO Console: http://localhost:9001")
        print("   PgAdmin: http://localhost:5050")
        print("\n🔐 Login Credentials:")
        print("   Username: admin")
        print("   Password: drdo123456")
    else:
        print("\n⚠️ Some tests failed. Please check the troubleshooting steps above.")
        print("\n📚 For detailed setup instructions, see:")
        print("   installation/EASY_DATABASE_SETUP.md")
    
    print("="*60)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
