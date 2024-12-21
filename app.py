from dataclasses import dataclass
import os
from typing import NamedTuple
import pandas as pd
import math
from flask import Flask, request, jsonify
from datetime import datetime
from zoneinfo import ZoneInfo
from colorama import Style, Fore


@dataclass
class CLR:
    ERR = Fore.RED
    SUC = Fore.GREEN
    RST = Style.RESET_ALL

CITIES_FOLDER = "./cities"
NUMBER_OF_FETCHED_DEPARTURES = 10
PORT = int(os.environ["ND_PORT"])


app = Flask(__name__)


class CityData(NamedTuple):
    """Class for better organization of cities' GTFS data"""
    stops: pd.DataFrame
    stop_times: pd.DataFrame
    trips: pd.DataFrame
    calendar: pd.DataFrame
    routes: pd.DataFrame


def initialize_gtfs() -> dict[str, CityData]:
    """Looks through workspace and tries to find all cities
    and their GTFS data"""
    ret = dict()
    for city in os.listdir(CITIES_FOLDER):
        j = os.path.join
        path_to_city = j(CITIES_FOLDER, city)
        try:
            ret[city] = CityData(
                stops = pd.read_csv(j(path_to_city, "stops.txt")),
                stop_times = pd.read_csv(j(path_to_city, "stop_times.txt")),
                trips = pd.read_csv(j(path_to_city, "trips.txt")),
                calendar = pd.read_csv(j(path_to_city, "calendar.txt")),
                routes = pd.read_csv(j(path_to_city, "routes.txt"))
            )   
        except Exception as e:
            print(f"{CLR.ERR}Error when loading files from {path_to_city} folder. Terminating{CLR.RST}\n{str(e)}")
    return ret


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on the Earth."""
    R = 6371  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def find_nearest_stop(city: str, lat: float, lon: float) -> tuple[str, str]:
    """Find the nearest stop to the given `lat` and `lon`.
    Returns ID and name of said stop."""
    global cities_data
    # Current City Data parsing
    ccd = cities_data[city]
    ccd.stops['distance'] = ccd.stops.apply(lambda row: haversine(lat, lon, row['stop_lat'], row['stop_lon']), axis=1)
    nearest_stop = ccd.stops.loc[ccd.stops['distance'].idxmin()]
    return nearest_stop['stop_id'], nearest_stop['stop_name']


def parse_gtfs_time(time_str):
    """Parse a GTFS time string (HH:MM:SS) that may exceed 24 hours."""
    hours, minutes, seconds = map(int, time_str.split(":"))
    if hours >= 24:
        # Normalize hours by subtracting 24 and keep track of overflow
        hours = hours - 24
    return datetime.strptime(f"{hours:02}:{minutes:02}:{seconds:02}", "%H:%M:%S").time()


def get_departures(city: str, stop_id: str, current_time: str, current_date: str):
    """Get departures from the stop with active services."""
    global cities_data
    ccd = cities_data[city]
    current_time_obj = datetime.strptime(current_time, "%H:%M:%S").time()
    current_date_obj = datetime.strptime(current_date, "%Y-%m-%d").date()
    # Get day name (e.g., 'monday')
    day_of_week = current_date_obj.strftime("%A").lower() 
    # Convert current_date to an integer in YYYYMMDD format
    current_date_int = int(current_date_obj.strftime("%Y%m%d"))
    # Filter active services based on the calendar
    active_services = ccd.calendar[
        (ccd.calendar['start_date'] <= current_date_int) &
        (ccd.calendar['end_date'] >= current_date_int) &
        (ccd.calendar[day_of_week] == 1)
    ]['service_id'].tolist()
    # Find trips with active services
    active_trips = ccd.trips[ccd.trips['service_id'].isin(active_services)]
    # Merge trips with routes to get `route_short_name` and include `trip_headsign`
    trips_with_routes = active_trips.merge(
        ccd.routes[['route_id', 'route_short_name']],
        on='route_id',
        how='left'
    )
    # Filter departures for active trips
    stop_departures = ccd.stop_times[
        (ccd.stop_times['stop_id'] == stop_id) &
        (ccd.stop_times['trip_id'].isin(trips_with_routes['trip_id']))
    ].copy()
    # Parse and normalize departure times
    stop_departures['departure_time'] = stop_departures['departure_time'].apply(parse_gtfs_time)
    upcoming_departures = stop_departures[stop_departures['departure_time'] > current_time_obj]
    # Merge with trips_with_routes to include `route_short_name` and `trip_headsign`
    upcoming_departures = upcoming_departures.merge(
        trips_with_routes[['trip_id', 'route_short_name', 'trip_headsign']],
        on='trip_id',
        how='left'
    )
    # Sort departures by time
    upcoming_departures = upcoming_departures.sort_values('departure_time')
    # Convert departure_time to strings for JSON serialization
    upcoming_departures['departure_time'] = upcoming_departures['departure_time'].apply(lambda t: t.strftime("%H:%M:%S"))
    # Return the results as a dictionary
    return upcoming_departures[['route_short_name', 'trip_headsign', 'departure_time', 'trip_id']].head(NUMBER_OF_FETCHED_DEPARTURES).to_dict(orient="records")


@app.route('/departures', methods=['GET'])
def departures():
    """
    API endpoint to get departures from the nearest stop. Arguments:
    - city: (`brno`, `ostrava` ... ) 
    - lat: float
    - lon: float
    - time (optional) str `HH:MM:SS`
    - date (optional) str `YYYY-MM-DD`
    """
    try:
        # Get query parameters
        city = str(request.args.get('city'))
        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))
        current_time = request.args.get('time', datetime.now(ZoneInfo("Europe/Prague")).strftime("%H:%M:%S"))
        current_date = request.args.get('date', datetime.now().strftime("%Y-%m-%d"))
        # Find nearest stop
        stop_id, stop_name = find_nearest_stop(city, lat, lon)
        # Get departures
        departures = get_departures(city, stop_id, current_time, current_date)
        return jsonify({
            "nearest_stop": stop_name,
            "departures": departures
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    global cities_data
    cities_data: dict[str, CityData] = initialize_gtfs()
    app.run(host='0.0.0.0', port=PORT)
