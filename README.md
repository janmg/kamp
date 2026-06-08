# Zomerkamp Task Roster

Zomerkamp is a volunteer scheduling system for a 4-day event. It stores participants, tasks, assignments, and exceptions in MariaDB via SQLAlchemy, and exposes the workflow both through CLI entry points and a modular Flask web app.

The main flows from the old scripts now also exist inside the web server:

- CSV import through `/import`
- scheduling and export operations through `/admin`
- admin overrides and assignment management through `/admin`

## Prompts
I want a task roster application in python for a 4 day event, which takes fairness, availability and preference into account. Store the data in an mariadb database

A python flask application, based on the url shows a list of people ordered by points earned by doing the tasks. Another url should show a table of all people in alphabetical order with a list of tasks with timeslot and a third url should show one master sheet with all activities ordered by time and assigned people. This last one should show all data.

The application should import two XLSX files, one with tasks listed with a task name, begin time and end time and the amount of points to be earned and the amount of people required. The other XLSX files should be a list of participants with name, email address, phonenumber and blocks of time (morning, afternoon, evening) where people are available to help and a multiple choice preference for an activity like "serving snacks", "serving food", "cleaning after food", "cleaning toilets", "organize afternoon games". include a free text remarks field.

The application should schedule based on fairness and availability. Make it possible to export the tables as csv. Nominate one person to be the lead for a task. Once the schedule is calculated.

For admins, to select a person, who is unavailable for a task or for a day or for all days. Select the backup for each task, award this person points for the fairness and based on fairness select a new backup based on fairness.

## Project Structure

```text
zomerkamp/
|- config.py                    # Database credentials and event constants
|- models.py                    # SQLAlchemy ORM models and DB helpers
|- roster_logic.py              # Candidate ranking and scheduling helpers
|- requirements.txt
|
|- web/
|  |- __init__.py               # Flask app factory
|  |- app.py                    # Flask startup entry point
|  |- routes/
|  |  |- dashboard.py           # Read-only dashboard pages
|  |  |- imports.py             # Upload/import web flow
|  |  |- admin.py              # Admin management + export web flow
|  |  |- admin.py               # Admin management web flow
|  |
|  |- services/
|  |  |- import_service.py      # Shared import logic
|  |  |- schedule_service.py    # Shared scheduling/export logic
|  |  |- admin_service.py       # Shared admin logic
|  |
|  |- templates/                # Flask HTML templates
|  |- static/                   # Static assets
|
|- sample_tasks.csv             # Example tasks CSV
|- Zomerkamp-Formulierreacties.csv
|- INSTALLATION.md              # Setup and run instructions
```

## Quick Start

### 1. Install and configure

Follow [INSTALLATION.md](INSTALLATION.md) for the full MariaDB and environment setup.

### 2. Create tables

Optionally use the CLI tools or the web-based import to initialize the database.

### 3. Start the web app

```bash
python web/app.py
```

Open `http://127.0.0.1:5001`.

### 4. Load data

Go to `/import` and upload `sample_tasks.csv` and `Formulierreacties.csv`.

### 5. Generate a schedule

Use `/admin` in the browser or run:

## Web Interface

The web app is now the main operational surface.

| URL | Description |
|---|---|
| `/` | Dashboard with navigation and summary metrics |
| `/import` | Initialize DB tables and upload tasks/participants CSV files |
| `/admin` | Manage unavailability, leads, assignments, and download exports |
| `/admin` | Manage unavailability, leads, and assignments |
| `/leaderboard` | Participants ranked by points earned |
| `/schedule` | Per-participant schedule view |
| `/master` | Master sheet across all days and tasks |

## XLS Formats

### `participants.xls` (Google Survey)

Key mappings:

- `Naam Ouder` -> participant `name`
- `E-mail Ouder` -> participant `email`
- `Telefoonnummer Ouder` -> participant `phone`
- `Mijn beschikbaarheid als hulpouder is: [...]` -> mapped to corresponding 07:00-21:00 slots.
- child-related fields (e.g. `child_first`, `child_last`, `child_diet`, `has_car`)


### `tasks.xls`

| Column | Description |
|---|---|
| `task_name` | Name of the task |
| `day` | Day number (1-4) |
| `begin_time` | Start time (`HH:MM` or `HH:MM:SS`) |
| `end_time` | End time (`HH:MM` or `HH:MM:SS`) |
| `points` | Points earned for doing this task |
| `people_required` | Number of volunteers needed |

The system derives the time block (one of the six slots between 07:00 and 21:00) automatically from the task midpoint.

## Scheduling Rules

1. Tasks are processed in day/time order.
2. Eligible candidates must be available for the task's day and time block.
3. Unavailability rules are respected for all-days, per-day, and per-task exclusions.
4. Candidates are ranked by fairness first: lowest projected total points wins.
5. The first active assignee becomes `lead`; remaining required people become `helper`.
7. When someone becomes unavailable, replacements are calculated on the fly from eligible candidates.

8. Divide the workload evenly on the participants
8. Spread the load evenly for each participant

## Export Output

The export flow writes three timestamped CSV files:

- `schedule_<ts>.csv`: one row per assignment
- `points_<ts>.csv`: leaderboard by total points
- `per_person_<ts>.csv`: assignments grouped by participant

## Data Model Overview

### Participant

- `id`, `name`, `email`, `phone`
- `day1_0700_0730` ... `day4_1800_2100`
- `excluded_all_days`

### Assignment

- `id`
- `task_id`
- `participant_id`
- `role`
- `points_awarded`

### Task

- `id`, `name`, `day`
- `begin_time`, `end_time`
- `points`, `people_required`
- `time_block`

### Unavailability

- `participant_id`
- `task_id` (nullable, specific task)
- `day` (nullable, whole day)
- `all_days` (boolean)

## Roles

- `lead`: first person assigned, earns points
- `helper`: additional required people, earn points

## Architecture Notes

- `web/services/` contains the shared business logic used by both web routes and CLI scripts.
- `web/routes/` keeps Flask routes grouped by feature instead of putting all views in one file.
- The CLI remains useful for scripting, while the browser now supports the same operational workflows.

## Requirements
- Leiders op de eerste dag moeten ervaring hebben van vorig jaar OF instructie krijgen.
- Nieuwe ‘leiders’ moeten de activiteit al een keer eerder gedaan hebben als helper
- Avond activiteiten indien mogelijk ouders van oudere kinderen (geen noodzaak in de tent te blijven)
- Aantal activiteiten ongeveer gelijk verdeeld onder de vrijwilligers (max 8 activiteiten over 4 dagen) 
- Sommige mensen hebben beperkingen (e.g. Matthijs Serdijn doet liever zittend werk)
- Voor sommige activiteiten is een rijbewijs / auto nodig (Boodschappen doen)
- Voor kantine supervisie is het mooi om ouders te gebruiken wiens kind in de betreffende klas zit.
- Als geen persoon gevonden wordt die beide vakken waarin een activiteit valt ingevuldt heeft, neem een persoon die één van de twee vakken ingevuld heeft.
- Goeie variatie in de wc schoonmaak, niet tof als één persoon dat 4x op z’n bord krijgt ;) 
- Cross-checken in welke groep een ouder een kind heeft, zodat die niet voor een activiteit ingeplanned wordt terwijl zijn of haar kind diploma uitreiking heeft.
- We moeten taken als ‘groot' of ‘klein' labellen. Het was de afgelopen jaren onoverkomelijk mensen binnen een tijdsvak voor twee kleinere activiteiten in te plannen (maar twee grotere kan niet).

## TODO
x remove req, points, assigned
beschrijving in een tooltip 
kleine taken grote taken, niet twee grote taken achter elkaar moeten doen
tijd indicatie, zodat je ongeveer weet hoe lang het duurt

naschoolse activiteiten, leider van te voren kunnen informen
wie er verder in zijn task zitten, met contact details
signal, whatsapps, sms
in the lead maak het clickable

hide points
list of tasks

url, qr code
als de tasks klaar zijn, uit het mastersheet verwijderen.
alleen de een na laatste in grijs laten zien
switch to full schedule

diploma uitreiking ... op basis van survey, welke klassen hebben overlap... 2 uur uitrijking ...
taken die gedaan moeten worden tijdens uitreiking (30 minuten) ... gedaan tijdens niet klas gerelateerde ouders.

inzet voor mensen vroeg weg... 
filmvertoning op einde met popcorn
zodat ouders ook kunnen.

bonte avond, disco, playback... 
stukjes op einde... 

samen eindvoorstelling als bovenbouw, per klas uitreiking.

## INITD
cp /usr/src/zomerkamp/zomerkamp.initd /etc/init.d/zomerkamp
chmod +x /etc/init.d/zomerkamp
rc-update add zomerkamp default
rc-service zomerkamp start

## NGINX 
server {
    listen 80;
    server_name zomerkamp.janmg.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    http2 on;
    server_name zomerkamp.janmg.com;
    ssl_certificate     /etc/letsencrypt/live/zomerkamp.janmg.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/zomerkamp.janmg.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
    }
}

## DATABASE TRUNCATE
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE assignments;
TRUNCATE availability;
TRUNCATE participants;
SET FOREIGN_KEY_CHECKS = 1;

# Reserved Assignments Implementation

## Purpose
Prevent scheduler from changing assignments made from task import Column E (leader names). These are "reserved" leadership positions that should remain locked in during scheduling.

## Changes Made

### 1. models.py - Assignment Model
- Added `is_reserved = Column(Boolean, default=False)` field
- Marks assignments that should not be reassigned by scheduler

### 2. import_service.py - Task Import
- When parsing Column E leader names and creating assignments, set `is_reserved=True`
- Also skips numeric values in Column E (they represent count of leaders needed, not names)

### 3. schedule_service.py - Scheduler
- **clear_assignments()**: Only clears non-reserved assignments (`Assignment.is_reserved == False`)
- **run_schedule_stream() & run_schedule()**: 
  - Separates `active_assignments` (non-reserved, can be scheduled) from `reserved_assignments` (locked in)
  - Calculates `open_slots = people_required - active_assignments - reserved_assignments`
  - Excludes reserved participants from exclusion sets when finding candidates
  - Checks for reserved leads when determining if lead slot is filled

## Workflow
1. Import tasks with Column E leader names
   - Arthur assigned as lead to "Koken" task, marked `is_reserved=True`
2. Run scheduler
   - Existing reserved assignments preserved
   - **Reserved assignments LOCK the task** - no additional people scheduled
   - Only tasks WITHOUT reserved assignments get additional scheduling
3. Result: Arthur is the ONLY person on "Koken" (reserved assignment locks it)

## Key Behavior Change
- **Reserved assignments lock tasks**: If a task has ANY reserved assignments (e.g., Arthur for Koken), the scheduler will NOT add other participants to fill remaining slots
- This ensures tasks reserved for specific people are handled exactly as intended
- Example: Koken requires 2 people, Arthur is reserved → Scheduler assigns ONLY Arthur, no one else

## Root Cause of Import Failures (FIXED)
**Issue**: Karen/Wouter were still assigned to Koken even though Arthur was in Column E
**Root cause**: Non-reserved assignments from previous imports weren't being deleted before creating Arthur's reserved assignment in the initial code version
**Solution implemented**: 
1. Task import now deletes ALL non-reserved assignments when processing Column E
2. Only then creates reserved assignments for listed leaders
3. Scheduler skips scheduling additional people if reserved assignments exist

## Critical Code Points
- **import_service.py** lines ~1000-1040: Delete non-reserved assignments BEFORE creating reserved ones from Column E
- **schedule_service.py** line ~78: Check "if reserved_assignments:" to lock task
- **Assignment model**: is_reserved column (default False) marks locked assignments


## Helper Preselection Feature (REVISED)
**Purpose**: Allow helpers to be preselected during task import, similar to leaders

**Implementation**:
- Column F (Medewerkers) contains helper information instead of just a number
- Format: "Name1, Name2, 2" means assign Name1 & Name2 as helpers, then select 2 more randomly
- Backward compatible: pure numeric values only set people_required, don't assign helpers
- **Only explicitly named helpers are marked is_reserved=True** (locked in)
- Randomly selected helpers are marked is_reserved=False (scheduler can rebalance them)
- Named helpers matched using fuzzy matching (60%+ similarity threshold)
- Additional helpers randomly selected from available participants with matching time slot availability

**Key Behavior Changes**:
- If Column F is purely numeric (e.g., "2"): only sets people_required, scheduler fills slots
- If Column F has names (e.g., "Alice, Bob"): those people are reserved as helpers
- If Column F has names + number (e.g., "Alice, Bob, 2"): Alice & Bob reserved, plus 2 random non-reserved helpers
- **Reserved assignments LOCK THE PERSON IN**: Arthur with 12 points reserved won't get additional assignments during scheduling
- **Non-reserved helpers can be rebalanced**: Random helpers selected during import can be reassigned by scheduler

**Changes Made**:
1. Fixed import_tasks_from_excel() to only assign helpers when Column F explicitly contains names
2. Marked only named helpers as is_reserved=True, random selections as is_reserved=False
3. Only assign random helpers if there are explicit named helpers (don't auto-fill pure numeric values)
4. Consolidated imports (random, fuzz) at top of file

## Fixes Applied (May 26, 2026)

### Issue 1: Cook over-assigned
**Problem**: Cook was assigned to tasks beyond his 12-point cooking roles (Tasks 17, 46, 75)
**Root Cause**: Helper preselection was marking ALL helpers as is_reserved=True, locking them and preventing scheduler from reassigning
**Solution**:
- Only explicitly NAMED helpers are marked is_reserved=True
- Randomly selected helpers are marked is_reserved=False so scheduler can rebalance
- Pure numeric Column F values now only set people_required, don't assign helpers
**Result**: Arthur stays at 12 points, others get assigned instead

### Issue 2: Zero-point participants on schedule
**Problem**: Schedule displayed participants with no assigned tasks (0 points)
**Solution**: Filter added to dashboard.py schedule() route to skip participants with total_points == 0
**File**: [web/routes/dashboard.py](web/routes/dashboard.py#L62-L76)

### Issue 3: double-assigned to overlapping times
**Problem**: vrijwilliger assigned to tasks 106 & 107 both at 13:45-14:15 on Day 4
**Root Cause**: Random helper selection during import created overlapping assignments
**Solution**:
- Fixed helper preselection logic (issue #1) prevents random duplicate assignments
- Scheduler already has overlap detection via participant_has_conflict() in roster_logic.py
- Both tasks re-imported, cleared bad assignments
**Result**: No more overlapping assignments for same participant in same time block

### Evaluation

1. Downtime, due to IPv4 change+over
Could buffer more in client, reduce data reliance
Download assets
Use cloud api? REST API
2. Use kamp.ntc.fi with cname to server
3. Add more useful links, schedules
4. Send messages over twillio, personlized links, personalized calendar invites?
5. Integrate with screens
6. Edit tasks and times, names
7. Helemaal in het nederlands
8. Logische links
9. Telefoonnummers niet delen
10. Reimplement in GO?
11. Remove Truncate Database after events have started.
12. NTC Logins for admins.
13. Fix achternaam kind v.s. ouders
14. Twee ouders, twee helpers?
15. Maak lijst met wie er nu beschikbaar is
16. Normalize capitalization, take belgium caps into account
17. Tables op telefoon passend krijgen.
18. Ho, ik kan dan niet knopje
19. Marktplaats, wie kan dit van me overnemen?
20. 1x persoon kunnen wisselen.
21. personen kunnen toevoegen aan taak en als vrijwilliger
22. directe feedback kunnen toepassen.
