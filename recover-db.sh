# Stop Django
docker compose -f /path/to/project down
# Or just stop django service
docker compose -f /path/to/project stop django

# Drop and recreate DB
docker compose -f /path/to/project exec postgres dropdb -U debug yarima_mining
docker compose -f /path/to/project exec postgres createdb -U debug yarima_mining

# Restore
docker cp /home/ubuntu/backups/backup_20250405_1200.sql $(docker compose -f /path/to/project ps -q postgres):/tmp/backup.sql
docker compose -f /path/to/project exec postgres \
  psql -U debug -d yarima_mining -f /tmp/backup.sql

# Restart Django
docker compose -f /path/to/project up -d django