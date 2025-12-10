CREATE TABLE region (
    region_id INTEGER PRIMARY KEY,
    region_name TEXT NOT NULL UNIQUE
);

CREATE TABLE station (
    station_id INTEGER PRIMARY KEY,
    station_name TEXT NOT NULL,
    region_id INTEGER NOT NULL,
    FOREIGN KEY (region_id) REFERENCES region(region_id)
);

CREATE TABLE earthquake (
    earthquake_id TEXT PRIMARY KEY,
    magnitude REAL NOT NULL,
    depth_km REAL,
    time_utc TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    region_id INTEGER NOT NULL,
    FOREIGN KEY (region_id) REFERENCES region(region_id)
);
