#API data fetching script
from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Tuple
import xml.etree.ElementTree as ET

import httpx
from sqlmodel import Session, select

from database import engine, init_db, reset_db_file
from models import Region, Station, Earthquake


USGS_EVENT_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
IRIS_STATION_URL = "https://service.iris.edu/fdsnws/station/1/query"

DEFAULT_REGIONS = [
    # Narrow by default to keep DB smaller; adjust freely.
    # Bounding boxes are approximate.
    ("Arizona", "AZ", 31.0, 37.0, -115.0, -109.0),
    ("California", "CA", 32.0, 42.0, -124.5, -114.0),
    ("Nevada", "NV", 35.0, 42.0, -120.0, -114.0),
]


def iso_utc_from_ms(ms: int) -> str:
    dt = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
    return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class RegionDef:
    name: str
    abbr: str
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float


def upsert_regions(session: Session, regions: List[RegionDef]) -> List[Region]:
    existing = {r.state_abbr: r for r in session.exec(select(Region)).all()}
    out: List[Region] = []
    for rd in regions:
        if rd.abbr in existing:
            r = existing[rd.abbr]
            r.name = rd.name
            r.min_lat, r.max_lat, r.min_lon, r.max_lon = rd.min_lat, rd.max_lat, rd.min_lon, rd.max_lon
        else:
            r = Region(
                name=rd.name,
                state_abbr=rd.abbr,
                min_lat=rd.min_lat,
                max_lat=rd.max_lat,
                min_lon=rd.min_lon,
                max_lon=rd.max_lon,
            )
            session.add(r)
        out.append(r)
    session.commit()
    # Refresh IDs
    out = session.exec(select(Region).where(Region.state_abbr.in_([r.abbr for r in regions]))).all()
    return out


def fetch_stations_for_region(
    client: httpx.Client, rd: RegionDef, timeout_s: float = 60.0
) -> bytes:
    params = {
        "level": "station",
        "minlat": rd.min_lat,
        "maxlat": rd.max_lat,
        "minlon": rd.min_lon,
        "maxlon": rd.max_lon,
        "format": "xml",
    }
    resp = client.get(IRIS_STATION_URL, params=params, timeout=timeout_s)
    resp.raise_for_status()
    return resp.content


def parse_stationxml(xml_bytes: bytes) -> List[Dict[str, object]]:
    """
    Extract stations from StationXML (network/station + lat/lon/elev + dates).
    """
    root = ET.fromstring(xml_bytes)

    # StationXML uses namespaces; ignore exact URI by matching localnames.
    def local(tag: str) -> str:
        return tag.split("}")[-1]

    stations: List[Dict[str, object]] = []
    for net in root.iter():
        if local(net.tag) != "Network":
            continue
        net_code = net.attrib.get("code")
        if not net_code:
            continue

        for sta in list(net):
            if local(sta.tag) != "Station":
                continue
            sta_code = sta.attrib.get("code")
            if not sta_code:
                continue

            name = sta.findtext(".//{*}Site/{*}Name")
            lat_text = sta.findtext(".//{*}Latitude")
            lon_text = sta.findtext(".//{*}Longitude")
            elev_text = sta.findtext(".//{*}Elevation")
            start_date = sta.attrib.get("startDate")
            end_date = sta.attrib.get("endDate")

            if lat_text is None or lon_text is None:
                continue

            stations.append(
                {
                    "network_code": net_code,
                    "station_code": sta_code,
                    "name": name,
                    "latitude": float(lat_text),
                    "longitude": float(lon_text),
                    "elevation_m": float(elev_text) if elev_text is not None else None,
                    "start_date_utc": start_date,
                    "end_date_utc": end_date,
                }
            )

    # de-dup by (network, station)
    seen = set()
    deduped = []
    for s in stations:
        k = (s["network_code"], s["station_code"])
        if k in seen:
            continue
        seen.add(k)
        deduped.append(s)
    return deduped


def upsert_stations(session: Session, region: Region, station_rows: List[Dict[str, object]]) -> int:
    existing = session.exec(select(Station).where(Station.region_id == region.id)).all()
    idx = {(s.network_code, s.station_code): s for s in existing}

    added = 0
    for row in station_rows:
        key = (row["network_code"], row["station_code"])
        if key in idx:
            s = idx[key]
            s.name = row.get("name")  # type: ignore[assignment]
            s.latitude = float(row["latitude"])  # type: ignore[arg-type]
            s.longitude = float(row["longitude"])  # type: ignore[arg-type]
            s.elevation_m = row.get("elevation_m")  # type: ignore[assignment]
            s.start_date_utc = row.get("start_date_utc")  # type: ignore[assignment]
            s.end_date_utc = row.get("end_date_utc")  # type: ignore[assignment]
        else:
            s = Station(
                region_id=region.id,
                network_code=str(row["network_code"]),
                station_code=str(row["station_code"]),
                name=(row.get("name") if row.get("name") else None),
                latitude=float(row["latitude"]),
                longitude=float(row["longitude"]),
                elevation_m=(float(row["elevation_m"]) if row.get("elevation_m") is not None else None),
                start_date_utc=(str(row["start_date_utc"]) if row.get("start_date_utc") else None),
                end_date_utc=(str(row["end_date_utc"]) if row.get("end_date_utc") else None),
            )
            session.add(s)
            added += 1

    session.commit()
    return added


def fetch_earthquakes_for_region(
    client: httpx.Client,
    rd: RegionDef,
    start: str,
    end: str,
    min_mag: float,
    limit: int,
    timeout_s: float = 60.0,
) -> Dict:
    params = {
        "format": "geojson",
        "starttime": start,
        "endtime": end,
        "minlatitude": rd.min_lat,
        "maxlatitude": rd.max_lat,
        "minlongitude": rd.min_lon,
        "maxlongitude": rd.max_lon,
        "minmagnitude": min_mag,
        "orderby": "time",
        "limit": limit,
    }
    resp = client.get(USGS_EVENT_URL, params=params, timeout=timeout_s)
    resp.raise_for_status()
    return resp.json()


def assign_nearest_station_id(stations: List[Station], lat: float, lon: float) -> Optional[int]:
    if not stations:
        return None
    best_id = None
    best_d2 = float("inf")
    # fast approximation: squared degrees distance (good enough for “nearest station” assignment)
    for s in stations:
        dlat = lat - s.latitude
        dlon = lon - s.longitude
        d2 = dlat * dlat + dlon * dlon
        if d2 < best_d2:
            best_d2 = d2
            best_id = s.id
    return best_id


def upsert_earthquakes(
    session: Session,
    region: Region,
    geojson: Dict,
    per_region_stations: List[Station],
) -> int:
    existing_ids = {e.usgs_id for e in session.exec(select(Earthquake.usgs_id)).all()}
    added = 0

    for feature in geojson.get("features", []):
        props = feature.get("properties", {}) or {}
        geom = feature.get("geometry", {}) or {}
        coords = geom.get("coordinates", None)
        if not coords or len(coords) < 3:
            continue

        usgs_id = feature.get("id")
        if not usgs_id or usgs_id in existing_ids:
            continue

        lon, lat, depth_km = coords[0], coords[1], coords[2]
        time_ms = props.get("time")
        if time_ms is None:
            continue

        station_id = assign_nearest_station_id(per_region_stations, float(lat), float(lon))

        e = Earthquake(
            usgs_id=str(usgs_id),
            time_utc=iso_utc_from_ms(int(time_ms)),
            latitude=float(lat),
            longitude=float(lon),
            depth_km=(float(depth_km) if depth_km is not None else None),
            magnitude=(float(props["mag"]) if props.get("mag") is not None else None),
            mag_type=(props.get("magType") if props.get("magType") else None),
            place=(props.get("place") if props.get("place") else None),
            url=(props.get("url") if props.get("url") else None),
            felt=(int(props["felt"]) if props.get("felt") is not None else None),
            cdi=(float(props["cdi"]) if props.get("cdi") is not None else None),
            mmi=(float(props["mmi"]) if props.get("mmi") is not None else None),
            sig=(int(props["sig"]) if props.get("sig") is not None else None),
            tsunami=(int(props["tsunami"]) if props.get("tsunami") is not None else None),
            region_id=region.id,
            station_id=station_id,
        )
        session.add(e)
        existing_ids.add(usgs_id)
        added += 1

    session.commit()
    return added


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true", help="Delete DB file and rebuild")
    ap.add_argument("--start", default="2024-01-01", help="YYYY-MM-DD")
    ap.add_argument("--end", default="2024-12-31", help="YYYY-MM-DD")
    ap.add_argument("--min-mag", type=float, default=2.5)
    ap.add_argument("--limit", type=int, default=1000, help="Max quakes per region per fetch")
    ap.add_argument("--no-stations", action="store_true")
    ap.add_argument("--no-earthquakes", action="store_true")
    args = ap.parse_args()

    if args.reset:
        reset_db_file()

    init_db()

    regions = [RegionDef(*r) for r in DEFAULT_REGIONS]

    with Session(engine) as session:
        db_regions = upsert_regions(session, regions)

    with httpx.Client(headers={"User-Agent": "iee305-term-project/1.0"}) as client:
        with Session(engine) as session:
            # Stations
            if not args.no_stations:
                for rd in regions:
                    region = session.exec(select(Region).where(Region.state_abbr == rd.abbr)).one()
                    xml_bytes = fetch_stations_for_region(client, rd)
                    station_rows = parse_stationxml(xml_bytes)
                    added = upsert_stations(session, region, station_rows)
                    print(f"[stations] {rd.abbr}: +{added}")

            # Earthquakes
            if not args.no_earthquakes:
                for rd in regions:
                    region = session.exec(select(Region).where(Region.state_abbr == rd.abbr)).one()
                    stations = session.exec(select(Station).where(Station.region_id == region.id)).all()
                    gj = fetch_earthquakes_for_region(
                        client, rd, start=args.start, end=args.end, min_mag=args.min_mag, limit=args.limit
                    )
                    added = upsert_earthquakes(session, region, gj, stations)
                    print(f"[earthquakes] {rd.abbr}: +{added}")

            # Counts
            region_count = session.exec(select(Region)).count()
            station_count = session.exec(select(Station)).count()
            quake_count = session.exec(select(Earthquake)).count()
            print(f"[counts] regions={region_count}, stations={station_count}, earthquakes={quake_count}")


if __name__ == "__main__":
    main()
