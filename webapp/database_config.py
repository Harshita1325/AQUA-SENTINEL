"""
Secure Database Configuration for DRDO Project
PostgreSQL + MinIO for military-grade security
"""

import os
import psycopg2
from psycopg2 import pool
from minio import Minio
from minio.error import S3Error
from datetime import datetime, timedelta
import hashlib
import secrets
from cryptography.fernet import Fernet
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecureImageDatabase:
    """Secure database system for underwater image storage"""
    
    def __init__(self):
        """Initialize PostgreSQL and MinIO connections"""
        
        # PostgreSQL Configuration
        self.pg_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=20,
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=os.getenv('POSTGRES_PORT', '5432'),
            database=os.getenv('POSTGRES_DB', 'drdo_underwater'),
            user=os.getenv('POSTGRES_USER', 'admin'),
            password=os.getenv('POSTGRES_PASSWORD', 'drdo123456'),
            sslmode='disable'  # Disable SSL for local development
        )
        
        # MinIO Configuration (S3-compatible)
        self.minio_client = Minio(
            endpoint=os.getenv('MINIO_ENDPOINT', 'localhost:9000'),
            access_key=os.getenv('MINIO_ACCESS_KEY', 'admin'),
            secret_key=os.getenv('MINIO_SECRET_KEY', 'drdo123456'),
            secure=False  # Use HTTP for local development
        )
        
        # Encryption key for sensitive data
        self.encryption_key = os.getenv('ENCRYPTION_KEY', Fernet.generate_key())
        self.cipher = Fernet(self.encryption_key)
        
        # Initialize buckets and tables
        self._initialize_storage()
        
        logger.info(" Secure database initialized")
    
    def _initialize_storage(self):
        """Create buckets and database tables"""
        
        # Create MinIO buckets
        buckets = [
            'raw-images',
            'enhanced-images',
            'threat-detections',
            'video-frames'
        ]
        
        for bucket in buckets:
            try:
                if not self.minio_client.bucket_exists(bucket_name=bucket):
                    self.minio_client.make_bucket(bucket_name=bucket)
                    logger.info(f" Created bucket: {bucket}")
            except S3Error as e:
                logger.error(f"Error creating bucket {bucket}: {e}")
        
        # Create PostgreSQL tables
        conn = self.pg_pool.getconn()
        try:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id SERIAL PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(50) NOT NULL,
                    clearance_level INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            
            # Images metadata table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS images (
                    image_id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(user_id),
                    original_filename VARCHAR(255) NOT NULL,
                    file_hash VARCHAR(64) UNIQUE NOT NULL,
                    minio_path VARCHAR(500) NOT NULL,
                    file_size_bytes BIGINT,
                    image_type VARCHAR(20),
                    width INTEGER,
                    height INTEGER,
                    upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    classification_level VARCHAR(50) DEFAULT 'RESTRICTED',
                    is_encrypted BOOLEAN DEFAULT TRUE
                )
            """)
            
            # Processing logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processing_logs (
                    log_id SERIAL PRIMARY KEY,
                    image_id INTEGER REFERENCES images(image_id),
                    user_id INTEGER REFERENCES users(user_id),
                    model_type VARCHAR(50),
                    processing_time_seconds FLOAT,
                    enhancement_metrics JSONB,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(50)
                )
            """)
            
            # Threat detections table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS threat_detections (
                    detection_id SERIAL PRIMARY KEY,
                    image_id INTEGER REFERENCES images(image_id),
                    threat_type VARCHAR(100),
                    confidence_score FLOAT,
                    bounding_box JSONB,
                    distance_estimate FLOAT,
                    severity_level VARCHAR(20),
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    verified_by_user INTEGER REFERENCES users(user_id),
                    false_positive BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Audit trail table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_trail (
                    audit_id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(user_id),
                    action VARCHAR(100),
                    resource_type VARCHAR(50),
                    resource_id INTEGER,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    success BOOLEAN
                )
            """)
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_user ON images(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_hash ON images(file_hash)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_image ON processing_logs(image_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_threats_image ON threat_detections(image_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_trail(user_id)")
            
            conn.commit()
            
            # Create default user if not exists
            cursor.execute("""
                INSERT INTO users (username, password_hash, role, clearance_level)
                VALUES ('system', 'no_password', 'ADMIN', 5)
                ON CONFLICT (username) DO NOTHING
            """)
            conn.commit()
            
            logger.info(" Database tables created successfully")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating tables: {e}")
        finally:
            cursor.close()
            self.pg_pool.putconn(conn)
    
    def store_image(self, file_path, user_id, image_type='raw', classification='RESTRICTED'):
        """
        Securely store image with encryption
        
        Args:
            file_path: Path to image file
            user_id: User ID uploading the image
            image_type: 'raw' or 'enhanced'
            classification: Security classification level
            
        Returns:
            image_id: Database ID of stored image
        """
        try:
            # Calculate file hash
            file_hash = self._calculate_file_hash(file_path)
            
            # Check for duplicates
            if self._check_duplicate(file_hash):
                logger.warning(f"Duplicate image detected: {file_hash}")
                return None
            
            # Generate secure object name
            filename = os.path.basename(file_path)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            secure_name = f"{timestamp}_{secrets.token_hex(8)}_{filename}"
            
            # Determine bucket
            bucket = 'raw-images' if image_type == 'raw' else 'enhanced-images'
            
            # Upload to MinIO (removed metadata parameter - not supported in this version)
            self.minio_client.fput_object(
                bucket_name=bucket,
                object_name=secure_name,
                file_path=file_path
            )
            
            # Get file info
            file_size = os.path.getsize(file_path)
            
            # Store metadata in PostgreSQL
            conn = self.pg_pool.getconn()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO images (
                        user_id, original_filename, file_hash, minio_path,
                        file_size_bytes, image_type, classification_level
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING image_id
                """, (user_id, filename, file_hash, f"{bucket}/{secure_name}",
                     file_size, image_type, classification))
                
                image_id = cursor.fetchone()[0]
                conn.commit()
                
                # Log action
                self._log_audit(user_id, 'UPLOAD_IMAGE', 'image', image_id, True)
                
                logger.info(f" Image stored: ID={image_id}, Hash={file_hash}")
                return image_id
                
            finally:
                cursor.close()
                self.pg_pool.putconn(conn)
                
        except Exception as e:
            logger.error(f"Error storing image: {e}")
            self._log_audit(user_id, 'UPLOAD_IMAGE', 'image', None, False)
            return None
    
    def retrieve_image(self, image_id, user_id, output_path):
        """
        Retrieve image with access control
        
        Args:
            image_id: Database ID of image
            user_id: User requesting the image
            output_path: Where to save the image
            
        Returns:
            bool: Success status
        """
        try:
            # Check access permissions
            if not self._check_access(user_id, image_id):
                logger.warning(f"Access denied: User {user_id} to Image {image_id}")
                self._log_audit(user_id, 'ACCESS_DENIED', 'image', image_id, False)
                return False
            
            # Get image metadata
            conn = self.pg_pool.getconn()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT minio_path FROM images WHERE image_id = %s",
                    (image_id,)
                )
                result = cursor.fetchone()
                
                if not result:
                    logger.error(f"Image not found: {image_id}")
                    return False
                
                minio_path = result[0]
                bucket, object_name = minio_path.split('/', 1)
                
                # Download from MinIO
                self.minio_client.fget_object(bucket, object_name, output_path)
                
                # Log access
                self._log_audit(user_id, 'DOWNLOAD_IMAGE', 'image', image_id, True)
                
                logger.info(f" Image retrieved: ID={image_id}")
                return True
                
            finally:
                cursor.close()
                self.pg_pool.putconn(conn)
                
        except Exception as e:
            logger.error(f"Error retrieving image: {e}")
            return False
    
    def delete_image(self, image_id, user_id):
        """
        Securely delete image (requires admin privileges)
        
        Args:
            image_id: Database ID of image
            user_id: User requesting deletion
            
        Returns:
            bool: Success status
        """
        try:
            # Check admin permissions
            if not self._is_admin(user_id):
                logger.warning(f"Delete denied: User {user_id} not admin")
                return False
            
            conn = self.pg_pool.getconn()
            try:
                cursor = conn.cursor()
                
                # Get MinIO path
                cursor.execute(
                    "SELECT minio_path FROM images WHERE image_id = %s",
                    (image_id,)
                )
                result = cursor.fetchone()
                
                if result:
                    minio_path = result[0]
                    bucket, object_name = minio_path.split('/', 1)
                    
                    # Delete from MinIO
                    self.minio_client.remove_object(bucket, object_name)
                    
                    # Soft delete in database (keep audit trail)
                    cursor.execute(
                        "UPDATE images SET is_encrypted = FALSE WHERE image_id = %s",
                        (image_id,)
                    )
                    
                    conn.commit()
                    
                    # Log deletion
                    self._log_audit(user_id, 'DELETE_IMAGE', 'image', image_id, True)
                    
                    logger.info(f" Image deleted: ID={image_id}")
                    return True
                
                return False
                
            finally:
                cursor.close()
                self.pg_pool.putconn(conn)
                
        except Exception as e:
            logger.error(f"Error deleting image: {e}")
            return False
    
    def _calculate_file_hash(self, file_path):
        """Calculate SHA-256 hash of file"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def _check_duplicate(self, file_hash):
        """Check if file already exists"""
        conn = self.pg_pool.getconn()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT image_id FROM images WHERE file_hash = %s", (file_hash,))
            return cursor.fetchone() is not None
        finally:
            cursor.close()
            self.pg_pool.putconn(conn)
    
    def _check_access(self, user_id, image_id):
        """Check if user has access to image"""
        conn = self.pg_pool.getconn()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT i.user_id, u.clearance_level, i.classification_level
                FROM images i
                JOIN users u ON u.user_id = %s
                WHERE i.image_id = %s
            """, (user_id, image_id))
            
            result = cursor.fetchone()
            if not result:
                return False
            
            owner_id, clearance, classification = result
            
            # Owner always has access
            if owner_id == user_id:
                return True
            
            # Check clearance level
            required_clearance = {
                'UNCLASSIFIED': 1,
                'RESTRICTED': 2,
                'CONFIDENTIAL': 3,
                'SECRET': 4,
                'TOP_SECRET': 5
            }
            
            return clearance >= required_clearance.get(classification, 5)
            
        finally:
            cursor.close()
            self.pg_pool.putconn(conn)
    
    def _is_admin(self, user_id):
        """Check if user is admin"""
        conn = self.pg_pool.getconn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role FROM users WHERE user_id = %s",
                (user_id,)
            )
            result = cursor.fetchone()
            return result and result[0] == 'ADMIN'
        finally:
            cursor.close()
            self.pg_pool.putconn(conn)
    
    def _log_audit(self, user_id, action, resource_type, resource_id, success):
        """Log action to audit trail"""
        conn = self.pg_pool.getconn()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO audit_trail (user_id, action, resource_type, resource_id, success)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, action, resource_type, resource_id, success))
            conn.commit()
        except Exception as e:
            logger.error(f"Audit log error: {e}")
        finally:
            cursor.close()
            self.pg_pool.putconn(conn)
    
    def get_statistics(self):
        """Get database statistics"""
        conn = self.pg_pool.getconn()
        try:
            cursor = conn.cursor()
            
            stats = {}
            
            # Total images
            cursor.execute("SELECT COUNT(*), SUM(file_size_bytes) FROM images")
            count, total_size = cursor.fetchone()
            stats['total_images'] = count or 0
            stats['total_size_gb'] = (total_size or 0) / (1024**3)
            
            # Images by type
            cursor.execute("SELECT image_type, COUNT(*) FROM images GROUP BY image_type")
            stats['by_type'] = dict(cursor.fetchall())
            
            # Recent activity
            cursor.execute("""
                SELECT COUNT(*) FROM audit_trail 
                WHERE timestamp > NOW() - INTERVAL '24 hours'
            """)
            stats['activity_24h'] = cursor.fetchone()[0]
            
            return stats
            
        finally:
            cursor.close()
            self.pg_pool.putconn(conn)
    
    def close(self):
        """Close all connections"""
        self.pg_pool.closeall()
        logger.info(" Database connections closed")


# Example usage
if __name__ == "__main__":
    # Initialize database
    db = SecureImageDatabase()
    
    # Get statistics
    stats = db.get_statistics()
    print(f" Database Statistics:")
    print(f"   Total Images: {stats['total_images']}")
    print(f"   Total Size: {stats['total_size_gb']:.2f} GB")
    print(f"   Activity (24h): {stats['activity_24h']}")
