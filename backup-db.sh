#!/bin/bash

# Exit on error
set -e

PROJECT_DIR="/home/ubuntu/yarima_mining"
BACKUP_DIR="/home/ubuntu/backups"
DATE=$(date +%Y%m%d_%H%M)
POSTGRES_CONTAINER=$(docker compose -f $PROJECT_DIR/docker-compose.production.yml ps -q postgres)

echo "📦 Creating database backup..."

# Run pg_dump inside container
docker compose -f $PROJECT_DIR/docker-compose.production.yml exec postgres \
  sh -c "PGPASSWORD=debug pg_dump -U debug -d yarima_mining -f /backups/backup.sql"

# Copy to host with timestamp
mkdir -p $BACKUP_DIR
docker cp "$POSTGRES_CONTAINER:/backups/backup.sql" "$BACKUP_DIR/backup_$DATE.sql"

echo "✅ Backup saved to $BACKUP_DIR/backup_$DATE.sql"