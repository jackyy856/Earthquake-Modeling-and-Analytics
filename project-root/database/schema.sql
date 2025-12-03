--DB schema definition
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS region (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  state_abbr TEXT NOT NULL UNIQUE,
  min_lat REAL NOT NULL,
  max_lat REAL NOT NULL,
  min_lon REAL NOT NULL,
  max_lon REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS station (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  region_id INTEGER NOT NULL,
  network_code TEXT NOT NULL,
  station_code TEXT NOT NULL,
  name TEXT,
  latitude REAL NOT NULL,
  longitude REAL NOT NULL,
  elevation_m REAL,
  start_date_utc TEXT,
  end_date_utc TEXT,
  FOREIGN KEY (region_id) REFERENCES region(id)
);

CREATE TABLE IF NOT EXISTS earthquake (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  usgs_id TEXT NOT NULL UNIQUE,
  time_utc TEXT NOT NULL,
  latitude REAL NOT NULL,
  longitude REAL NOT NULL,
  depth_km REAL,
  magnitude REAL,
  mag_type TEXT,
  place TEXT,
  url TEXT,
  felt INTEGER,
  cdi REAL,
  mmi REAL,
  sig INTEGER,
  tsunami INTEGER,
  region_id INTEGER NOT NULL,
  station_id INTEGER,
  FOREIGN KEY (region_id) REFERENCES region(id),
  FOREIGN KEY (station_id) REFERENCES station(id)
);

-- Indexing strategy
CREATE INDEX IF NOT EXISTS ix_region_state_abbr ON region(state_abbr);

CREATE INDEX IF NOT EXISTS ix_station_region ON station(region_id);
CREATE INDEX IF NOT EXISTS ix_station_codes ON station(network_code, station_code);
CREATE INDEX IF NOT EXISTS ix_station_latlon ON station(latitude, longitude);

CREATE INDEX IF NOT EXISTS ix_eq_region ON earthquake(region_id);
CREATE INDEX IF NOT EXISTS ix_eq_station ON earthquake(station_id);
CREATE INDEX IF NOT EXISTS ix_eq_time ON earthquake(time_utc);
CREATE INDEX IF NOT EXISTS ix_eq_mag ON earthquake(magnitude);
CREATE INDEX IF NOT EXISTS ix_eq_latlon ON earthquake(latitude, longitude);
