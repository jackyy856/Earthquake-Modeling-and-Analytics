from fastapi import APIRouter, Depends
from sqlmodel import Session
from backend.database import get_session
from backend import queries

router = APIRouter()

# ---------------- Q1 ----------------
@router.get("/q1")
def run_q1(min_mag: float, days: int, session: Session = Depends(get_session)):
    return queries.q1_recent_large_quakes(session, min_mag, days)

# ---------------- Q2 ----------------
@router.get("/q2")
def run_q2(session: Session = Depends(get_session)):
    return queries.q2_quakes_with_regions(session)

# ---------------- Q3 ----------------
@router.get("/q3")
def run_q3(session: Session = Depends(get_session)):
    return queries.q3_region_avg(session)

# ---------------- Q4 ----------------
@router.get("/q4")
def run_q4(session: Session = Depends(get_session)):
    return queries.q4_frequent_big_quakes(session)

# ---------------- Q5 ----------------
@router.get("/q5")
def run_q5(session: Session = Depends(get_session)):
    return queries.q5_above_avg(session)

# ---------------- Q6 ----------------
@router.get("/q6")
def run_q6(session: Session = Depends(get_session)):
    return queries.q6_top10(session)

# ---------------- Q7 ----------------
@router.get("/q7")
def run_q7(session: Session = Depends(get_session)):
    return queries.q7_station_activity(session)

# ---------------- Q8 ----------------
@router.get("/q8")
def run_q8(session: Session = Depends(get_session)):
    return queries.q8_shallow_percent(session)

# ---------------- Q9 ----------------
@router.get("/q9")
def run_q9(session: Session = Depends(get_session)):
    return queries.q9_strongest(session)

# ---------------- Q10 ----------------
@router.get("/q10")
def run_q10(region: str, min_mag: float, start: int, end: int, session: Session = Depends(get_session)):
    return queries.q10_region_filter(session, region, min_mag, start, end)
