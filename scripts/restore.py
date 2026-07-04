#!/usr/bin/env python3
"""
Kisan Mitra AI - Portable Production Restore/Recovery Utility
Restores PostgreSQL database and configuration files from an archive.
"""

import os
import sys
import subprocess
import shutil
import tempfile
import zipfile
import tarfile

# Enforce script paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main():
    print("=" * 60)
    print("KISAN MITRA AI - PRODUCTION RESTORE RUNNER")
    print("=" * 60)
    
    if len(sys.argv) < 2:
        print("Usage: python restore.py <path_to_backup_archive>")
        print("Example: python restore.py backups/backup_20260630_120000.zip")
        print("=" * 60)
        sys.exit(1)
        
    backup_archive_path = sys.argv[1]
    if not os.path.exists(backup_archive_path):
        print(f"[-] Error: Backup archive does not exist at: {backup_archive_path}")
        sys.exit(1)

    print(f"[*] Verifying backup archive: {backup_archive_path}...")
    
    # 1. Initialize temporary workspace
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"[*] Extracting archive contents to temporary workspace: {temp_dir}...")
        try:
            if backup_archive_path.endswith(".zip"):
                with zipfile.ZipFile(backup_archive_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
            elif backup_archive_path.endswith(".tar.gz") or backup_archive_path.endswith(".tgz"):
                with tarfile.open(backup_archive_path, 'r:gz') as tar_ref:
                    tar_ref.extractall(temp_dir)
            else:
                # Try automated detection
                shutil.unpack_archive(backup_archive_path, temp_dir)
            print("[+] Archive extracted successfully.")
        except Exception as e:
            print(f"[-] Error: Failed to extract backup archive: {e}")
            sys.exit(1)

        # 2. Identify extracted files
        extracted_files = os.listdir(temp_dir)
        db_sql_file = None
        env_file = None
        
        for f in extracted_files:
            if f.endswith(".sql"):
                db_sql_file = os.path.join(temp_dir, f)
            elif f == "environment.env":
                env_file = os.path.join(temp_dir, f)
                
        # 3. Restore environment configurations
        if env_file:
            target_env = os.path.join(BASE_DIR, ".env")
            confirm = input(f"[?] Copy environment.env to {target_env}? (y/n): ").strip().lower()
            if confirm == 'y':
                try:
                    shutil.copy2(env_file, target_env)
                    print(f"[+] Restored environment file to: {target_env}")
                except Exception as e:
                    print(f"[-] Failed to restore environment file: {e}")
            else:
                print("[*] Skipped environment file restoration.")
        else:
            print("[*] No environment configuration file found in backup.")

        # 3.5 Restore local data files
        data_src_dir = os.path.join(temp_dir, "data")
        if os.path.exists(data_src_dir):
            target_data = os.path.join(BASE_DIR, "data")
            confirm = input(f"[?] Copy local data files directory to {target_data}? (y/n): ").strip().lower()
            if confirm == 'y':
                try:
                    if os.path.exists(target_data):
                        shutil.rmtree(target_data)
                    shutil.copytree(data_src_dir, target_data)
                    print(f"[+] Restored local data files to: {target_data}")
                except Exception as e:
                    print(f"[-] Failed to restore local data files: {e}")
            else:
                print("[*] Skipped local data files restoration.")
        else:
            print("[*] No local data files directory found in backup.")

        # 4. Restore PostgreSQL database
        if db_sql_file:
            db_host = os.getenv("DB_HOST", "localhost")
            db_port = os.getenv("DB_PORT", "5432")
            db_user = os.getenv("DB_USER", "postgres")
            db_pass = os.getenv("DB_PASSWORD", "postgres")
            db_name = os.getenv("DB_NAME", "kisan_mitra_db")
            
            confirm = input(f"[?] Restore database snapshot into postgres://{db_user}@{db_host}:{db_port}/{db_name}? (y/n): ").strip().lower()
            if confirm == 'y':
                print(f"[*] Initiating database restoration via psql...")
                env = os.environ.copy()
                if db_pass:
                    env["PGPASSWORD"] = db_pass
                    
                try:
                    # Clean/recreate database to avoid conflicts
                    drop_cmd = ["dropdb", "-h", db_host, "-p", db_port, "-U", db_user, "--if-exists", db_name]
                    create_cmd = ["createdb", "-h", db_host, "-p", db_port, "-U", db_user, db_name]
                    restore_cmd = ["psql", "-h", db_host, "-p", db_port, "-U", db_user, "-d", db_name, "-f", db_sql_file]
                    
                    print("[*] Dropping existing database if exists...")
                    subprocess.run(drop_cmd, env=env, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    
                    print("[*] Creating empty target database...")
                    subprocess.run(create_cmd, env=env, check=True, stdout=subprocess.DEVNULL)
                    
                    print("[*] Restoring database tables schema and data logs...")
                    subprocess.run(restore_cmd, env=env, check=True, capture_output=True, text=True)
                    print("[+] Database tables and values successfully restored.")
                except FileNotFoundError:
                    print("[-] Error: 'psql', 'createdb', or 'dropdb' executables were not found. Please install PostgreSQL client tools.")
                    print("[-] Skipping database restoration...")
                except subprocess.CalledProcessError as err:
                    print(f"[-] Error: Database restoration failed: {err.stderr}")
                    print("[-] Skipping database restoration...")
            else:
                print("[*] Skipped database restoration.")
        else:
            print("[*] No database backup snapshot found in archive.")
            
    print("=" * 60)
    print("[+] RESTORE RUN COMPLETED.")
    print("=" * 60)

if __name__ == "__main__":
    main()
