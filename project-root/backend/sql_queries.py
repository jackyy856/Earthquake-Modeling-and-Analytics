from __future__ import annotations

from typing import Any, Dict, List, Optional
from sqlmodel import Session
from sqlalchemy import text


QUERIES: Dict[str, str] = {
    # Q01: Earthquake counts by region (GROUP BY)
    "q01_counts_by_region": """
    SELECT r.name AS region, COUNT(e.id) AS quake_count
    FROM region r
    LEFT JOIN earthquake e ON e.region_id = r.id
    WHERE (:start IS NULL OR e.time_utc >= :start)
      AND (:end IS NULL OR e.time_utc <= :end)
    GROUP BY r.id
    ORDER BY quake_count DESC, r.name ASC;
    """,

    # Q02: Average magnitude by region with minimum number of quakes (HAVING)
    "q02_avg_mag_by_region_min_n": """
    SELECT r.name AS region,
           COUNT(e.id) AS quake_count,
           ROUND(AVG(e.magnitude), 3) AS avg_mag
    FROM region r
    JOIN earthquake e ON e.region_id = r.id
    WHERE e.magnitude IS NOT NULL
      AND (:start IS NULL OR e.time_utc >= :start)
      AND (:end IS NULL OR e.time_utc <= :end)
    GROUP BY r.id
    HAVING COUNT(e.id) >= :min_n
    ORDER BY avg_mag DESC, quake_count DESC;
    """,

    # Q03: Top-N strongest quakes (JOIN + ORDER + LIMIT)
    "q03_top_n_strongest": """
    SELECT e.usgs_id,
           e.time_utc,
           r.name AS region,
           e.magnitude,
           e.depth_km,
           e.place
    FROM earthquake e
    JOIN region r ON r.id = e.region_id
    WHERE e.magnitude IS NOT NULL
    ORDER BY e.magnitude DESC, e.time_utc DESC
    LIMIT :n;
    """,

    # Q04: Monthly trend for a region (strftime + GROUP BY)
    "q04_monthly_trend_region": """
    SELECT strftime('%Y-%m', e.time_utc) AS month,
           COUNT(*) AS quake_count
    FROM earthquake e
    WHERE e.region_id = :region_id
      AND (:start IS NULL OR e.time_utc >= :start)
      AND (:end IS NULL OR e.time_utc <= :end)
    GROUP BY month
    ORDER BY month ASC;
    """,

    # Q05: Magnitude buckets (CASE)
    "q05_magnitude_buckets": """
    SELECT
      CASE
        WHEN e.magnitude IS NULL THEN 'Unknown'
        WHEN e.magnitude < 2.5 THEN '<2.5'
        WHEN e.magnitude < 4.0 THEN '2.5-3.9'
        WHEN e.magnitude < 6.0 THEN '4.0-5.9'
        ELSE '6.0+'
      END AS bucket,
      COUNT(*) AS quake_count
    FROM earthquake e
    WHERE (:region_id IS NULL OR e.region_id = :region_id)
    GROUP BY bucket
    ORDER BY
      CASE bucket
        WHEN '<2.5' THEN 1
        WHEN '2.5-3.9' THEN 2
        WHEN '4.0-5.9' THEN 3
        WHEN '6.0+' THEN 4
        ELSE 5
      END;
    """,

    # Q06: Station counts per region (JOIN + GROUP BY)
    "q06_station_counts_by_region": """
    SELECT r.name AS region, COUNT(s.id) AS station_count
    FROM region r
    LEFT JOIN station s ON s.region_id = r.id
    GROUP BY r.id
    ORDER BY station_count DESC, r.name ASC;
    """,

    # Q07: Regions with frequent significant events (HAVING + threshold)
    "q07_regions_with_many_sig": """
    SELECT r.name AS region,
           COUNT(*) AS sig_quake_count
    FROM earthquake e
    JOIN region r ON r.id = e.region_id
    WHERE e.sig IS NOT NULL
      AND e.sig >= :sig_threshold
      AND (:start IS NULL OR e.time_utc >= :start)
      AND (:end IS NULL OR e.time_utc <= :end)
    GROUP BY r.id
    HAVING COUNT(*) >= :min_events
    ORDER BY sig_quake_count DESC;
    """,

    # Q08: Top stations by assigned earthquakes (JOIN + GROUP BY)
    "q08_top_stations_by_assigned_quakes": """
    SELECT s.network_code,
           s.station_code,
           r.name AS region,
           COUNT(e.id) AS assigned_quake_count
    FROM station s
    JOIN region r ON r.id = s.region_id
    LEFT JOIN earthquake e ON e.station_id = s.id
    GROUP BY s.id
    ORDER BY assigned_quake_count DESC, region ASC
    LIMIT :n;
    """,

    # Q09: Quakes above their region’s average magnitude (correlated subquery)
    "q09_quakes_above_region_avg": """
    SELECT e.usgs_id, e.time_utc, r.name AS region, e.magnitude, e.place
    FROM earthquake e
    JOIN region r ON r.id = e.region_id
    WHERE e.magnitude IS NOT NULL
      AND e.magnitude > (
        SELECT AVG(e2.magnitude)
        FROM earthquake e2
        WHERE e2.region_id = e.region_id
          AND e2.magnitude IS NOT NULL
      )
    ORDER BY e.magnitude DESC, e.time_utc DESC
    LIMIT :n;
    """,

    # Q10: Parameterized region + magnitude threshold (your “strong example”)
    "q10_region_threshold": """
    SELECT e.usgs_id,
           e.time_utc,
           r.name AS region,
           e.magnitude,
           e.depth_km,
           e.place,
           e.url
    FROM earthquake e
    JOIN region r ON r.id = e.region_id
    WHERE r.state_abbr = :state_abbr
      AND e.magnitude IS NOT NULL
      AND e.magnitude >= :min_mag
      AND (:start IS NULL OR e.time_utc >= :start)
      AND (:end IS NULL OR e.time_utc <= :end)
    ORDER BY e.time_utc DESC
    LIMIT :n;
    """,
}


def run_query(session: Session, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    params = params or {}
    rows = session.exec(text(sql), params).all()
    # SQLAlchemy returns Row objects; convert to plain dicts.
    out: List[Dict[str, Any]] = []
    for r in rows:
        mapping = getattr(r, "_mapping", None)
        if mapping is not None:
            out.append(dict(mapping))
        else:
            # fallback for some drivers
            out.append(dict(r))
    return out
