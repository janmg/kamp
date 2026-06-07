# Installation Guide

## 1. Configure MariaDB

```sql
CREATE DATABASE zomerkamp CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'zomerkamp_user'@'10.0.0.%' IDENTIFIED BY 'change_me';
GRANT ALL PRIVILEGES ON zomerkamp.* TO 'zomerkamp_user'@'localhost';
FLUSH PRIVILEGES;
```

If you are running everything locally, you can also create the user on `localhost` instead of `10.0.0.%`.

## 2. Create environment settings

Create a `.env` file in this folder:

```env
DB_USER=zomerkamp_user
DB_PASSWORD=change_me
DB_HOST=localhost
DB_PORT=3306
DB_NAME=zomerkamp
```

## 3. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 4. Initialize the database

```bash
python -c "from models import init_db; init_db()"
```

```sql
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE change_logs;
TRUNCATE TABLE unavailabilities;
TRUNCATE TABLE availability;
TRUNCATE TABLE assignments;
TRUNCATE TABLE participants;
TRUNCATE TABLE tasks;
SET FOREIGN_KEY_CHECKS = 1;
```

You can also initialize the tables from the web interface on the Import page.

## 5. Load data

### Web upload flow

Start the web server:

```bash
python web/app.py
```

Then open `http://127.0.0.1:5001/import` and:

1. Initialize the database tables if needed.
2. Upload `tasks.csv` and/or your survey export CSV (for example `Zomerkamp Survey NTC Finland 2026 (Antwoorden) - Formulierreacties.csv`).
3. Continue to `/admin` to manage assignments and download CSV exports.

## 6. Run the scheduler

You can also do this from the web interface at `http://127.0.0.1:5001/admin`.

```bash
python tools/app2_schedule.py schedule
```

To preserve existing assignments and only fill gaps:

```bash
python tools/app2_schedule.py schedule --keep-existing
```

## 7. Useful commands

```bash
python tools/app2_schedule.py show
python tools/app2_schedule.py export --output ./exports
python tools/app3_admin.py list-people
python tools/app3_admin.py list-tasks --day 2
python tools/app3_admin.py set-unavailable --person "Alice" --day 2 --reason "Unavailable"
python tools/app3_admin.py set-lead --task 5 --person "Grace"
python tools/app3_admin.py remove-assignment --task 5 --person "Bob"
python web/app.py
```

## 8. Web interface

Start the Flask application:

```bash
python web/app.py
```

Available pages:

- `/`: dashboard and links to all app areas
- `/import`: upload tasks and participants CSV files
- `/admin`: manage unavailability, leads, assignments, and download CSV files
- `/admin`: manage unavailability, leads, and assignments
- `/leaderboard`: participant ranking by points
- `/schedule`: per-participant schedule view
- `/master`: full task overview by day

## 9. Code layout

The application is now split into reusable layers:

- `tools/app2_schedule.py`, `tools/app3_admin.py`: CLI entry points
- `web/app.py`: Flask entry point
- `web/routes/`: web routes grouped by feature
- `web/services/`: shared business logic used by both web and CLI flows
- `models.py`, `roster_logic.py`: database models and scheduling helpers