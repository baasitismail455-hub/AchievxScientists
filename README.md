# AchievX Scientist

A research portfolio and project-workspace application built with Python (Flask), HTML, CSS, JavaScript and a relational database.

## What this application is designed to do

AchievX Scientist is **not a journal or publication platform**. It is a living portfolio of research projects.

- Public landing page with project cards, cover images, author portraits, discipline, collaboration type and status.
- An administrator can create, edit and manage projects.
- Each project has its own page containing the purpose, description, aims and an ongoing activity timeline.
- Project updates can be added over time, with multiple files attached to each entry.
- Supported uploads include PDF, CSV/TSV, Excel, Word, PowerPoint, text/JSON/ZIP, common images, audio and video.
- A simple account system supports project collaborators.
- The project owner can invite collaborators by email. A person can register with that email and accept the invitation.
- Public projects can be browsed without an account. Private projects are limited to the owner and collaborators.
- Profile photos and short biographies identify project contributors.

## Important first-account behaviour

The **first account registered on a fresh database automatically becomes the site administrator**. Register your own account first, before inviting other users. Subsequent accounts are standard accounts unless added as collaborators.

## Requirements

- Python 3.11 or 3.12 recommended.
- Windows, macOS or Linux.
- No external database is required for local development: SQLite is included with Python and is used automatically.
- PostgreSQL is supported and recommended for a multi-user production deployment.

## Windows setup

Open PowerShell in the extracted project folder.

```powershell
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
python run.py
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

Open `http://127.0.0.1:5000`, register your account, and start creating projects.

## Database choice

### Option A — SQLite (easiest local setup)

Leave `DATABASE_URL` commented out in `.env`. The application creates its database automatically at:

`instance/achievx_scientist.db`

This is a real relational database stored locally with the project. It requires no separate database server.

### Option B — PostgreSQL

Install PostgreSQL on the machine/server. Create a database named `achievx_scientist`, then set `DATABASE_URL` in `.env`:

```env
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/achievx_scientist
```

If your password contains URL-reserved characters, URL-encode them. Never commit `.env` or share database credentials.

## Upload storage

Uploaded files are stored on the application server in `instance/uploads/`. The database stores file metadata and the stored filename. Back up **both** the database and this uploads directory. If the site is deployed to an ephemeral filesystem, configure persistent disk storage before accepting important research files.

The current application upload limit defaults to 100 MB per request. Change `MAX_CONTENT_LENGTH_MB` in `.env` if needed, subject to your hosting provider's limits.

## Security and production checklist

This is a functional first release, not a security-audited production system. Before public deployment:

1. Set a strong random `SECRET_KEY` in `.env`.
2. Use PostgreSQL and a persistent backup strategy.
3. Serve over HTTPS.
4. Use a production WSGI server such as Gunicorn behind the host's web server.
5. Configure rate limiting, email delivery and account recovery.
6. Add malware scanning and stricter file-content validation for public uploads.
7. Set up persistent object/file storage and automated backups.
8. Add database migrations before making schema changes after real data has been entered.
9. Review privacy, consent and data-retention requirements before storing sensitive or human-subject research data.

The current invitation flow creates an in-app invitation record. It does not send email yet; the owner must communicate the invitation to the collaborator separately. Email delivery can be connected in a later release.

## Main routes

- `/` — public portfolio
- `/about` — platform overview
- `/register`, `/login`, `/logout` — accounts
- `/dashboard` — user workspace
- `/projects/new` — administrator project creation
- `/projects/<slug>` — project detail and activity timeline
- `/projects/<slug>/edit` — project settings
- `/profile` — profile details and avatar
- `/health` — health check

## Project structure

```text
AchievX_Scientist/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   ├── templates/
│   └── static/
├── instance/
│   └── uploads/
├── tests/
├── .env.example
├── requirements.txt
└── run.py
```

## Product direction

The platform is intentionally centred on **projects and their evolving work records**. It is not intended to turn every update into a formal publication. Each project can accumulate progress notes, datasets, documents, images, audio, video and other working materials as the research develops.
