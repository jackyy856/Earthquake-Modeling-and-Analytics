#FastAPI application
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

from database import init_db, get_session
from models import Region, Station, Earthquake
from sql_queries import QUERIES, run_query

app = FastAPI(title="Earthquake Modeling & Analytics API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev-friendly; tighten if you want
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


# ---------------- Regions ----------------

@app.get("/regions", response_model=List[Region])
def list_regions(session: Session = Depends(get_session)) -> List[Region]:
    return session.exec(select(Region).order_by(Region.state_abbr)).all()


@app.get("/regions/{region_id}", response_model=Region)
def get_region(region_id: int, session: Session = Depends(get_session)) -> Region:
    r = session.get(Region, region_id)
    if not r:
        raise HTTPException(status_code=404, detail="Region not found")
    return r


# ---------------- Stations ----------------

@app.get("/stations", response_model=List[Station])
def list_stations(
    region_id: Optional[int] = None,
    limit: int = Query(200, ge=1, le=5000),
    session: Session = Depends(get_session),
) -> List[Station]:
    q = select(Station)
    if region_id is not None:
        q = q.where(Station.region_id == region_id)
    q = q.order_by(Station.network_code, Station.station_code).limit(limit)
    return session.exec(q).all()


@app.get("/stations/{station_id}", response_model=Station)
def get_station(station_id: int, session: Session = Depends(get_session)) -> Station:
    s = session.get(Station, station_id)
    if not s:
        raise HTTPException(status_code=404, detail="Station not found")
    return s


# ---------------- Earthquakes ----------------

@app.get("/earthquakes", response_model=List[Earthquake])
def list_earthquakes(
    region_id: Optional[int] = None,
    station_id: Optional[int] = None,
    start: Optional[str] = None,   # ISO8601 string comparisons work with Z-formatted timestamps
    end: Optional[str] = None,
    min_mag: Optional[float] = Query(default=None, ge=-2.0, le=12.0),
    max_mag: Optional[float] = Query(default=None, ge=-2.0, le=12.0),
    limit: int = Query(200, ge=1, le=5000),
    session: Session = Depends(get_session),
) -> List[Earthquake]:
    q = select(Earthquake)
    if region_id is not None:
        q = q.where(Earthquake.region_id == region_id)
    if station_id is not None:
        q = q.where(Earthquake.station_id == station_id)
    if start is not None:
        q = q.where(Earthquake.time_utc >= start)
    if end is not None:
        q = q.where(Earthquake.time_utc <= end)
    if min_mag is not None:
        q = q.where(Earthquake.magnitude != None).where(Earthquake.magnitude >= min_mag)  # noqa: E711
    if max_mag is not None:
        q = q.where(Earthquake.magnitude != None).where(Earthquake.magnitude <= max_mag)  # noqa: E711

    q = q.order_by(Earthquake.time_utc.desc()).limit(limit)
    return session.exec(q).all()


@app.get("/earthquakes/{usgs_id}", response_model=Earthquake)
def get_earthquake(usgs_id: str, session: Session = Depends(get_session)) -> Earthquake:
    e = session.exec(select(Earthquake).where(Earthquake.usgs_id == usgs_id)).first()
    if not e:
        raise HTTPException(status_code=404, detail="Earthquake not found")
    return e


# ---------------- SQL query demos (10 queries) ----------------
# Returned as JSON list[dict] to make it easy to show sample rows in report.

@app.get("/sql/{query_key}")
def sql_demo(
    query_key: str,
    session: Session = Depends(get_session),
    region_id: Optional[int] = None,
    state_abbr: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    min_n: int = Query(25, ge=1, le=100000),
    min_mag: float = Query(4.0, ge=-2.0, le=12.0),
    sig_threshold: int = Query(600, ge=0, le=5000),
    min_events: int = Query(10, ge=1, le=100000),
    n: int = Query(10, ge=1, le=500),
) -> List[Dict[str, Any]]:
    sql = QUERIES.get(query_key)
    if not sql:
        raise HTTPException(status_code=404, detail="Unknown query key")

    params: Dict[str, Any] = {
        "region_id": region_id,
        "state_abbr": state_abbr,
        "start": start,
        "end": end,
        "min_n": min_n,
        "min_mag": min_mag,
        "sig_threshold": sig_threshold,
        "min_events": min_events,
        "n": n,
    }

    # q10 needs state_abbr specifically
    if query_key == "q10_region_threshold" and not state_abbr:
        raise HTTPException(status_code=422, detail="state_abbr is required for q10_region_threshold")

    # q04 needs region_id specifically
    if query_key == "q04_monthly_trend_region" and region_id is None:
        raise HTTPException(status_code=422, detail="region_id is required for q04_monthly_trend_region")

    return run_query(session, sql, params)
