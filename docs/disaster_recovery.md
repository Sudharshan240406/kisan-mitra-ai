# Disaster Recovery Guide

This guide documents the procedures for backing up and restoring database and configuration files on the **Kisan Mitra AI** platform.

---

## Backup Strategy

*   **Frequency**: Automated daily snapshot at 02:00 AM UTC.
*   **Retention**: Keep daily backups for 30 days, weekly backups for 12 weeks, and monthly backups for 1 year.
*   **Target Content**:
    *   PostgreSQL relational schema and tables.
    *   `.env` deployment configuration parameters.

---

## Executing Backup Manually

Run the portable Python backup utility from the root directory:
```bash
python scripts/backup.py
```
This utility:
1. Connects to PostgreSQL using database parameters in environment variables.
2. Generates an SQL snapshot file.
3. Packages the SQL snapshot and active `.env` file into a timestamped compressed archive in `backups/` directory.

---

## Executing Recovery / Restoration

To restore your systems from a backup archive:

1. Stop application containers to prevent active database writing:
   ```bash
   docker compose stop backend frontend proxy
   ```

2. Run the restore utility with the target archive path:
   ```bash
   python scripts/restore.py backups/backup_YYYYMMDD_HHMMSS.zip
   ```

3. Follow the interactive prompts:
   * Confirm copying the environment profile.
   * Confirm dropping the existing target database and restoring the snapshot.

4. Start the application containers again:
   ```bash
   docker compose start backend frontend proxy
   ```

5. Verify the health status of all services:
   ```bash
   curl -f http://localhost/api/v1/health/readiness
   ```

---

## Disaster Scenarios & Mitigation

### Scenario A: Corruption of the Database
*   **Sign**: Application throws database connection errors, or readiness check returns `database: unhealthy`.
*   **Mitigation**: Run `restore.py` using the last verified daily backup.

### Scenario B: Storage Drive Exhaustion
*   **Sign**: Logs stop writing, Postgres goes offline, disk usage hits 100%.
*   **Mitigation**: Scale the disk volume size, prune old Docker logs (`docker system prune -a --volumes`), and ensure log rotation limits are active in Nginx and Python loggers.
