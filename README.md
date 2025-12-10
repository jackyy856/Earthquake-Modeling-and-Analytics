# Earthquake Analytics – IEE 305 Final Project

## Overview
This project is a decision-support information system built for Industrial Engineering applications.
It uses USGS Earthquake API data to help engineers analyze seismic activity for risk assessment,
infrastructure planning, and emergency resource planning.

The system includes:
- A fully populated SQLite database (3 entities, 3 tables)
- 10 analytical SQL queries demonstrating all required SQL concepts
- A FastAPI backend exposing /q1 through /q10 API endpoints
- A simple HTML/JavaScript frontend interface for running queries
- Complete documentation, ER diagram, schema, and screenshots included in the final report

---

## Project Structure
project-root/
│
├── backend/
│   ├── main.py               # FastAPI app (includes CORS)
│   ├── api.py                # API routes for q1–q10
│   ├── queries.py            # SQL queries
│   ├── models.py             # SQLModel/Pydantic models
│   ├── database.py           # DB utilities + create_db_and_tables()
│   ├── fetch_data.py         # Used to populate database
│   └── requirements.txt      # Python dependencies
│
├── frontend/
│   └── index.html            # Query Tester UI
│
├── database/
│   ├── schema.sql            # Database schema
│   └── earthquakes.db        # Populated SQLite database
│
├── docs/
│   ├── er_diagram.png
│   ├── relational_schema.png
│   └── screenshots/
│       ├── q1_output.png
│       ├── q2_output.png
│       └── (etc…)
│
└── README.md                 # This file
---

## Setup and Usage Instructions

### 1. Navigate to project folder
cd “C:\Users\kenne\IEE305Final\Earthquake-Modeling-and-Analytics”
cd project-root
### 2. Allow PowerShell script execution (Windows requirement)
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
### 3. Activate virtual environment
..venv\Scripts\activate
### 4. Install dependencies
pip install -r backend/requirements.txt
### 5. Start FastAPI backend (port 8000)
uvicorn backend.main:app –reload
### 6. Start frontend (port 5500)
Right-click `index.html` → **Open With Live Server**

The frontend will be available at:
http://127.0.0.1:5500/index.html
Backend runs at:
http://127.0.0.1:8000
---

## API Endpoints (Queries 1–10)

| Endpoint | Description |
|---------|-------------|
| `/q1` | Recent large earthquakes (min_mag, days) |
| `/q2` | Earthquakes joined with regions |
| `/q3` | Average magnitude & depth by region |
| `/q4` | Regions with high frequency of large quakes |
| `/q5` | Regions above average earthquake frequency |
| `/q6` | Top 10 most active regions |
| `/q7` | Station earthquake activity (1 year) |
| `/q8` | Percent shallow (<20km) earthquakes per region |
| `/q9` | Strongest quake per region |
| `/q10` | Regional filter (region, min_mag, start, end timestamps) |

---

## Frontend Usage
The Query Tester interface includes:
- Dropdown menu for Q1–Q10
- Input fields for parameters (only when needed)
- “Run Query” button
- Live JSON results displayed below the UI

Screenshots of results are included in `/docs/screenshots`.

---

## Notes
- SQLite DB contains 10+ records per table
- All SQL queries meet required IE concepts (JOIN, GROUP BY, HAVING, CTEs, LIMIT, filtering, parameterization)
- Backend includes CORS configuration so frontend + backend communicate correctly
- Exactly 3 entities and 3 tables with 3NF normalization

---

## Authors
**Kennedy**
**Yuki**
**Savannah**
**Jacky**

Arizona State University
IEE 305 – Information Systems Engineering
Fall 2025
