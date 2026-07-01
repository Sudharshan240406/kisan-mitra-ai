#!/usr/bin/env python3
"""
Kisan Mitra AI - Portable Production Backup Utility
Generates timestamped PostgreSQL backups and logs system configurations.
"""

import os
import sys
import subprocess
import shutil
from datetime import datetime

# Enforce script paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKUPS_DIR = os.path.join(BASE_DIR, "backups")

# Add backend directory to sys.path to read application configs
sys.path.append(os.path.join(BASE_DIR, "backend"))

def main():
    print("=" * 60)
    print("KISAN MITRA AI - PRODUCTION BACKUP RUNNER")
    print("=" * 60)
    
    # 1. Initialize backup paths
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{timestamp}"
    target_backup_dir = os.path.join(BACKUPS_DIR, backup_name)
    os.makedirs(target_backup_dir, exist_ok=True)
    print(f"[*] Initialized backup workspace at: {target_backup_dir}")

    # 2. Extract database parameters from environment
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_user = os.getenv("DB_USER", "postgres")
    db_pass = os.getenv("DB_PASSWORD", "postgres")
    db_name = os.getenv("DB_NAME", "kisan_mitra_db")
    
    # 3. Create database snapshot
    db_dump_file = os.path.join(target_backup_dir, f"{db_name}.sql")
    print(f"[*] Starting PostgreSQL database snapshot for database: {db_name}...")
    
    env = os.environ.copy()
    if db_pass:
        env["PGPASSWORD"] = db_pass
        
    try:
        # Use pg_dump tool
        cmd = [
            "pg_dump",
            "-h", db_host,
            "-p", db_port,
            "-U", db_user,
            "-d", db_name,
            "-F", "p",  # Plain SQL script format
            "-f", db_dump_file
        ]
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
        print(f"[+] Database backup generated successfully: {db_dump_file}")
    except FileNotFoundError:
        print("[-] Error: 'pg_dump' executable was not found. Please install PostgreSQL client tools.")
        print("[-] Skipping database backup stage...")
    except subprocess.CalledProcessError as err:
        print(f"[-] Error: pg_dump execution failed: {err.stderr}")
        print("[-] Skipping database backup stage...")

    # 4. Backup active configuration environment profiles
    env_file = os.path.join(BASE_DIR, ".env")
    env_backup = os.path.join(target_backup_dir, "environment.env")
    if os.path.exists(env_file):
        try:
            shutil.copy2(env_file, env_backup)
            print(f"[+] Environment file configuration backed up to: {env_backup}")
        except Exception as e:
            print(f"[-] Failed to backup environment file: {e}")
    else:
        print("[*] No active '.env' file found at project root. Skipping config file backup...")

    # 5. Compress the backup directory into a tarball
    archive_format = "gztar" if sys.platform != "win32" else "zip"
    archive_extension = "tar.gz" if sys.platform != "win32" else "zip"
    archive_path = os.path.join(BACKUPS_DIR, backup_name)
    
    try:
        print(f"[*] Archiving snapshot directory using {archive_format} format...")
        shutil.make_archive(archive_path, archive_format, target_backup_dir)
        print(f"[+] COMPLETED: Production backup artifact generated: {archive_path}.{archive_extension}")
        
        # Cleanup temporary uncompressed folder
        shutil.rmtree(target_backup_dir)
    except Exception as e:
        print(f"[-] Failed to create compressed backup archive: {e}")
        
    print("=" * 60)

if __name__ == "__main__":
    main()
