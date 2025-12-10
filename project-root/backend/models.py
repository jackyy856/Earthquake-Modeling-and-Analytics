from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List


class Region(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    stations: List["Station"] = Relationship(back_populates="region")
    earthquakes: List["Earthquake"] = Relationship(back_populates="region")


class Station(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    region_id: int = Field(foreign_key="region.id")

    region: Optional["Region"] = Relationship(back_populates="stations")
    earthquakes: List["Earthquake"] = Relationship(back_populates="station")


class Earthquake(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    magnitude: float
    depth: float
    time: float

    region_id: int = Field(foreign_key="region.id")
    station_id: Optional[int] = Field(default=None, foreign_key="station.id")

    region: Optional["Region"] = Relationship(back_populates="earthquakes")
    station: Optional["Station"] = Relationship(back_populates="earthquakes")
