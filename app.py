import pandas as pd
import math
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# Load GTFS data
stops = pd.read_csv('brno/stops.txt')
stop_times = pd.read_csv('brno/stop_times.txt')
trips = pd.read_csv('brno/trips.txt')
calendar = pd.read_csv('brno/calendar.txt')
routes = pd.read_csv('brno/routes.txt')

def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great-circle distance between two points on the Earth."""
    R = 6371  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def find_nearest_stop(lat, lon):
    """Find the nearest stop to the given latitude and longitude."""
    stops['distance'] = stops.apply(lambda row: haversine(lat, lon, row['stop_lat'], row['stop_lon']), axis=1)
    nearest_stop = stops.loc[stops['distance'].idxmin()]
    return nearest_stop['stop_id'], nearest_stop['stop_name']

def parse_gtfs_time(time_str):
    """Parse a GTFS time string (HH:MM:SS) that may exceed 24 hours."""
    hours, minutes, seconds = map(int, time_str.split(":"))
    if hours >= 24:
        # Normalize hours by subtracting 24 and keep track of overflow
        hours = hours - 24
    return datetime.strptime(f"{hours:02}:{minutes:02}:{seconds:02}", "%H:%M:%S").time()

def get_departures(stop_id, current_time, current_date):
    """Get departures from the stop with active services."""
    # Parse the current time and day
    current_time = datetime.strptime(current_time, "%H:%M:%S").time()
    day_of_week = current_date.strftime("%A").lower()  # Get day name (e.g., 'monday')

    # Convert current_date to an integer in YYYYMMDD format
    current_date_int = int(current_date.strftime("%Y%m%d"))

    # Filter active services based on the calendar
    active_services = calendar[
        (calendar['start_date'] <= current_date_int) &
        (calendar['end_date'] >= current_date_int) &
        (calendar[day_of_week] == 1)
    ]['service_id'].tolist()

    # Find trips with active services
    active_trips = trips[trips['service_id'].isin(active_services)]

    # Merge trips with routes to get `route_short_name` and include `trip_headsign`
    trips_with_routes = active_trips.merge(
        routes[['route_id', 'route_short_name']],
        on='route_id',
        how='left'
    )

    # Filter departures for active trips
    stop_departures = stop_times[
        (stop_times['stop_id'] == stop_id) &
        (stop_times['trip_id'].isin(trips_with_routes['trip_id']))
    ].copy()

    # Parse and normalize departure times
    stop_departures['departure_time'] = stop_departures['departure_time'].apply(parse_gtfs_time)
    upcoming_departures = stop_departures[stop_departures['departure_time'] > current_time]

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
    return upcoming_departures[['departure_time', 'trip_id', 'route_short_name', 'trip_headsign']].to_dict(orient='records')







@app.route('/departures', methods=['GET'])
def departures():
    """API endpoint to get departures from the nearest stop."""
    try:
        # Get query parameters
        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))
        current_time = request.args.get('current_time', datetime.now().strftime("%H:%M:%S"))
        current_date = request.args.get('current_date', datetime.now().strftime("%Y-%m-%d"))
        
        # Convert current_date to datetime object
        current_date = datetime.strptime(current_date, "%Y-%m-%d").date()

        # Find nearest stop
        stop_id, stop_name = find_nearest_stop(lat, lon)

        # Get departures
        departures = get_departures(stop_id, current_time, current_date)

        return jsonify({
            "nearest_stop": stop_name,
            "departures": departures
        })
    except Exception as e:
        raise e
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=51234)
