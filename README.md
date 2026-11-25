# CampusCare — Smart Campus Complaint Management

A student-focused Flask + SQLite mini project for reporting campus infrastructure issues and an admin portal for tracking and updating complaint status.

## Features
- Complaint reporting for students, teaching staff and non-teaching staff
- Student USN validation for admission years 2023–2026; staff ID required for staff reporters
- Floor and specific-location selection, custom Other fields, complaint categories including Hostel
- Optional JPG/JPEG/PNG/WEBP photo upload (maximum 5 MB) with preview on the form
- High / Medium / Low priority labels and public complaint register with student USNs hidden
- Admin dashboard with floor-wise location overview, priority risk indicators and status updates (Pending / In Progress / Resolved)
- Responsive interface and SQLite database
- SQLite database; no MySQL installation required
- Render deployment configuration included

## Run on Windows
1. Install Python 3.10 or newer.
2. Open this folder in Command Prompt.
3. Run `py -m venv .venv`
4. Run `.venv\\Scripts\\activate`
5. Run `pip install -r requirements.txt`
6. Run `python app.py`
7. Open http://127.0.0.1:5000

## Admin demo login
- Username: `admin`
- Password: `CampusCare@123`

Change these using environment variables `ADMIN_USERNAME` and `ADMIN_PASSWORD` before a public deployment. Set a strong `SECRET_KEY` too. The demo default credentials are for classroom testing only.

## Deploy on Render
Create a new Web Service from this repository. Render can detect `render.yaml`; otherwise use build command `pip install -r requirements.txt` and start command `gunicorn app:app`. Add `ADMIN_PASSWORD` as a secret environment variable. The free service filesystem may reset, so SQLite demo records may not persist through restarts/redeploys. Do not enter real sensitive student information.

## Project details
Smart Campus Infrastructure Complaint and Maintenance Management Application — Group 12, CSE (AI & ML), A J Institute of Engineering and Technology.
