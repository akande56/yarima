# Project Commands

This file is a command reference for `yarima_mining`.

## 1) Docker Compose (Local)

### Start/stop/build
```powershell
docker compose -f docker-compose.local.yml build
docker compose -f docker-compose.local.yml up -d --remove-orphans
docker compose -f docker-compose.local.yml down
docker compose -f docker-compose.local.yml down -v
docker compose -f docker-compose.local.yml logs -f
```

### Run Django manage command (local)
```powershell
docker compose -f docker-compose.local.yml run --rm django python manage.py <command>
```

## 2) Docker Compose (Production)

### Build/start/stop
```powershell
docker compose -f docker-compose.production.yml build
docker compose -f docker-compose.production.yml up -d
docker compose -f docker-compose.production.yml down
docker compose -f docker-compose.production.yml logs -f
```

### Rebuild after code changes
```powershell
docker compose -f docker-compose.production.yml up -d --build
```

### Run Django manage command (production)
```powershell
docker compose -f docker-compose.production.yml run --build --rm django python manage.py <command>
```

## 3) `just` Shortcuts (uses `docker-compose.local.yml`)

```powershell
just
just build
just up
just down
just prune
just logs
just manage <manage.py args>
```

## 4) Core Django Commands

### Migrations
```powershell
docker compose -f docker-compose.production.yml run --build --rm django python manage.py makemigrations
docker compose -f docker-compose.production.yml run --build --rm django python manage.py migrate
```

### Superuser
```powershell
docker compose -f docker-compose.production.yml run --rm django python manage.py createsuperuser
```

### System checks
```powershell
docker compose -f docker-compose.production.yml run --build --rm django python manage.py check
```

### Tests
```powershell
docker compose -f docker-compose.production.yml run --build --rm django pytest
```

## 5) Project Management Commands (`core/management/commands`)

### 5.1 `export_monthly_data`
Export transactions or sales by month range as zipped Excel files.
```powershell
docker compose -f docker-compose.production.yml run --build --rm django python manage.py export_monthly_data --type transactions --start-month 2024-01 --end-month 2024-03
docker compose -f docker-compose.production.yml run --build --rm django python manage.py export_monthly_data --type sales --start-month 2024-01 --end-month 2024-12 --output ./exports
```

### 5.2 `monthly_maintenance`
Runs DB maintenance/statistics flow.
```powershell
docker compose -f docker-compose.production.yml run --build --rm django python manage.py monthly_maintenance
```

### 5.3 `clean_transaction_data`
Delete transaction/sales data (supports date range and dry-run).
```powershell
# Dry run
docker compose -f docker-compose.production.yml run --build --rm django python manage.py clean_transaction_data --type all --start-date 2026-01-01 --end-date 2026-03-31 --dry-run

# Delete only sales in date range
docker compose -f docker-compose.production.yml run --build --rm django python manage.py clean_transaction_data --type sales --start-date 2026-01-01 --end-date 2026-03-31 --yes

# Delete all transaction + sales data
docker compose -f docker-compose.production.yml run --build --rm django python manage.py clean_transaction_data --type all --yes

docker compose -f docker-compose.production.yml run --build --rm django python manage.py clean_transaction_data --type all --start-date 2026-01-01 --end-date 2026-03-31 --yes

```

### 5.4 `add_mineral_grades`
Adds predefined grades for Columbite/Monozite.
```powershell
docker compose -f docker-compose.production.yml run --build --rm django python manage.py add_mineral_grades --dry-run
docker compose -f docker-compose.production.yml run --build --rm django python manage.py add_mineral_grades
```

### 5.5 Legacy data-fix commands (use with caution)
These target `MineralTransaction` (legacy model path).
```powershell
docker compose -f docker-compose.production.yml run --build --rm django python manage.py fix_weight_unit --dry-run
docker compose -f docker-compose.production.yml run --build --rm django python manage.py fix_weight_unit --fix-all
docker compose -f docker-compose.production.yml run --build --rm django python manage.py fix_weight_unit --transaction-ids 1 2 3

docker compose -f docker-compose.production.yml run --build --rm django python manage.py fix_negotiated_prices --dry-run
docker compose -f docker-compose.production.yml run --build --rm django python manage.py fix_negotiated_prices --batch-size 200
```

## 6) Helper Scripts in Repo Root

### Database backup/recovery scripts
```powershell
./backup-db.sh
./recover-db.sh
```

### Env merge helper
```powershell
python merge_production_dotenvs_in_dotenv.py
```

## 7) Useful URLs (Production Compose Defaults)

```text
App:   http://127.0.0.1/
Admin: http://127.0.0.1/<DJANGO_ADMIN_URL from .envs/.production/.django>
```

## 8) Quick Day-to-Day Flow

```powershell
# 1) Rebuild and start
docker compose -f docker-compose.production.yml up -d --build

# 2) Run migrations
docker compose -f docker-compose.production.yml run --build --rm django python manage.py migrate

# 3) Check app config
docker compose -f docker-compose.production.yml run --build --rm django python manage.py check
```
