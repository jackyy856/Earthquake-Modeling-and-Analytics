# Earthquake-Modeling-and-Analytics
IEE 305 Term Project to build a decision support information system that helps engineers solve problems with data-driven insights using USGS earthquake systems

## Backend (FastAPI + SQLModel + SQLite)

From `project-root/`:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# build + load data (creates project-root/database/earthquakes.db)
python fetch_data.py --reset --start 2024-01-01 --end 2024-12-31 --min-mag 2.5 --limit 1000

# run API
uvicorn main:app --reload --host 127.0.0.1 --port 8000
