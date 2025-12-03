#pydantic/SQLModel models
from __future__ import annotations

from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


class Region(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    state_abbr: str = Field(index=True, unique=True)
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float

    stations: List["Station"] = Relationship(back_populates="region")
    earthquakes: List["Earthquake"] = Relationship(back_populates="region")


class Station(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    region_id: int = Field(foreign_key="region.id", index=True)
    network_code: str = Field(index=True)
    station_code: str = Field(index=True)
    name: Optional[str] = None

    latitude: float = Field(index=True)
    longitude: float = Field(index=True)
    elevation_m: Optional[float] = None

    start_date_utc: Optional[str] = None
    end_date_utc: Optional[str] = None

    region: Optional[Region] = Relationship(back_populates="stations")
    earthquakes: List["Earthquake"] = Relationship(back_populates="station")


class Earthquake(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    usgs_id: str = Field(index=True, unique=True)
    time_utc: str = Field(index=True)  # ISO8601 UTC string

    latitude: float = Field(index=True)
    longitude: float = Field(index=True)
    depth_km: Optional[float] = None

    magnitude: Optional[float] = Field(default=None, index=True)
    mag_type: Optional[str] = None
    place: Optional[str] = None
    url: Optional[str] = None

    felt: Optional[int] = None
    cdi: Optional[float] = None
    mmi: Optional[float] = None
    sig: Optional[int] = None
    tsunami: Optional[int] = None

    region_id: int = Field(foreign_key="region.id", index=True)
    station_id: Optional[int] = Field(default=None, foreign_key="station.id", index=True)

    region: Optional[Region] = Relationship(back_populates="earthquakes")
    station: Optional[Station] = Relationship(back_populates="earthquakes")


# ---- Response models (non-table) ----

class CountRow(SQLModel):
    label: str
    value: int


class AnyRow(SQLModel):
    # generic dynamic row for /sql endpoints (returned as dicts by API)
    pass
