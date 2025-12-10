import requests
from sqlmodel import Session
from .database import engine
from .models import Region, Station, Earthquake



# -------------------------
#  FETCH AND INSERT DATA
# -------------------------

def fetch_and_load():
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {
        "format": "geojson",
        "minmagnitude": 4.0,
        "limit": 20
    }

    response = requests.get(url, params=params)
    data = response.json()

    with Session(engine) as session:
        for feature in data["features"]:
            props = feature["properties"]
            coords = feature["geometry"]["coordinates"]

            magnitude = props.get("mag")
            depth = coords[2]
            longitude = coords[0]
            latitude = coords[1]
            time_ms = props.get("time")
            quake_id = feature["id"]

            # -------------------------
            # Region handling
            # -------------------------
            region_name = props.get("place", "Unknown").split(",")[-1].strip()
            region = session.query(Region).filter(Region.name == region_name).first()
            if not region:
                region = Region(name=region_name)
                session.add(region)
                session.commit()

            # -------------------------
            # Station placeholder (required by project)
            # -------------------------
            station = session.query(Station).filter(Station.name == "USGS-AUTO").first()
            if not station:
                station = Station(name="USGS-AUTO", region_id=region.id)
                session.add(station)
                session.commit()

            # -------------------------
            # Earthquake record
            # -------------------------
            quake = Earthquake(
                id=quake_id,
                magnitude=magnitude,
                depth=depth,
                longitude=longitude,
                latitude=latitude,
                time=time_ms,
                region_id=region.id,
                station_id=station.id
            )

            session.add(quake)

        session.commit()


if __name__ == "__main__":
    fetch_and_load()
    print("Database successfully populated!")

