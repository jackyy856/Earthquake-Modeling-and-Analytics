from sqlmodel import Session
from sqlalchemy import text
from datetime import datetime

from backend.models import Earthquake, Region, Station


# ---------------- Q1 ----------------
def q1_recent_large_quakes(session: Session, min_mag: float, days: int):
    cutoff = datetime.utcnow().timestamp() * 1000 - days * 86400000

    rows = (
        session.query(Earthquake, Region)
        .join(Region, Earthquake.region_id == Region.id)
        .filter(Earthquake.magnitude >= min_mag)
        .filter(Earthquake.time >= cutoff)
        .order_by(Earthquake.time.desc())
        .all()
    )

    return [
        {
            "earthquake_id": e.id,
            "magnitude": e.magnitude,
            "depth": e.depth,
            "time": e.time,
            "region": r.name
        }
        for e, r in rows
    ]


# ---------------- Q2 ----------------
def q2_quakes_with_regions(session: Session):
    rows = (
        session.query(Earthquake, Region)
        .join(Region)
        .all()
    )

    return [
        {
            "earthquake_id": e.id,
            "magnitude": e.magnitude,
            "depth": e.depth,
            "time": e.time,
            "region": r.name
        }
        for e, r in rows
    ]


# ---------------- Q3 ----------------
def q3_region_avg(session: Session):
    cutoff = datetime.utcnow().timestamp() * 1000 - 365 * 86400000

    sql = text("""
        SELECT region.name,
               AVG(earthquake.magnitude),
               AVG(earthquake.depth)
        FROM earthquake
        JOIN region ON earthquake.region_id = region.id
        WHERE earthquake.time >= :cutoff
        GROUP BY region.name
    """)

    rows = session.execute(sql, {"cutoff": cutoff}).all()

    return [
        {"region": r[0], "avg_magnitude": r[1], "avg_depth": r[2]}
        for r in rows
    ]


# ---------------- Q4 ----------------
def q4_frequent_big_quakes(session: Session):
    sql = text("""
        SELECT region.name, COUNT(*)
        FROM earthquake
        JOIN region ON earthquake.region_id = region.id
        WHERE earthquake.magnitude >= 4.0
        GROUP BY region.name
        HAVING COUNT(*) >= 50
    """)

    rows = session.execute(sql).all()

    return [{"region": r[0], "count": r[1]} for r in rows]


# ---------------- Q5 ----------------
def q5_above_avg(session: Session):
    sql = text("""
        WITH counts AS (
            SELECT region_id, COUNT(*) as c
            FROM earthquake
            GROUP BY region_id
        ),
        avg_c AS (
            SELECT AVG(c) AS avg_val FROM counts
        )
        SELECT region.name, counts.c
        FROM counts
        JOIN region ON region.id = counts.region_id
        JOIN avg_c
        WHERE counts.c > avg_val
    """)

    rows = session.execute(sql).all()

    return [{"region": r[0], "count": r[1]} for r in rows]


# ---------------- Q6 ----------------
def q6_top10(session: Session):
    sql = text("""
        SELECT region.name, COUNT(*)
        FROM earthquake
        JOIN region ON earthquake.region_id = region.id
        GROUP BY region.name
        ORDER BY COUNT(*) DESC
        LIMIT 10
    """)

    rows = session.execute(sql).all()

    return [{"region": r[0], "count": r[1]} for r in rows]


# ---------------- Q7 ----------------
def q7_station_activity(session: Session):
    cutoff = datetime.utcnow().timestamp() * 1000 - 365 * 86400000

    sql = text("""
        SELECT station.name, COUNT(*)
        FROM earthquake
        JOIN station ON earthquake.station_id = station.id
        WHERE earthquake.time >= :cutoff
        GROUP BY station.name
    """)

    rows = session.execute(sql, {"cutoff": cutoff}).all()

    return [{"station": r[0], "count": r[1]} for r in rows]


# ---------------- Q8 ----------------
def q8_shallow_percent(session: Session):
    sql = text("""
        SELECT region.name,
               SUM(CASE WHEN depth < 20 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)
        FROM earthquake
        JOIN region ON earthquake.region_id = region.id
        GROUP BY region.name
    """)

    rows = session.execute(sql).all()

    return [{"region": r[0], "percent_shallow": r[1]} for r in rows]


# ---------------- Q9 ----------------
def q9_strongest(session: Session):
    sql = text("""
        SELECT region.name, earthquake.magnitude, earthquake.time
        FROM earthquake
        JOIN region ON earthquake.region_id = region.id
        WHERE (earthquake.region_id, earthquake.magnitude) IN (
            SELECT region_id, MAX(magnitude)
            FROM earthquake
            GROUP BY region_id
        )
    """)

    rows = session.execute(sql).all()

    return [{"region": r[0], "magnitude": r[1], "time": r[2]} for r in rows]


# ---------------- Q10 ----------------
def q10_region_filter(session: Session, region: str, min_mag: float, start: int, end: int):
    sql = text("""
        SELECT earthquake.id, magnitude, time
        FROM earthquake
        JOIN region ON earthquake.region_id = region.id
        WHERE region.name = :region
          AND magnitude >= :min_mag
          AND time BETWEEN :start AND :end
    """)

    rows = session.execute(sql, {
        "region": region,
        "min_mag": min_mag,
        "start": start,
        "end": end
    }).all()

    return [{"earthquake_id": r[0], "magnitude": r[1], "time": r[2]} for r in rows]
