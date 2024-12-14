import pandas as pd
import math
from flask import Flask, request, jsonify

app = Flask(__name__)

# Load GTFS data
stops = pd.read_csv('brno/stops.txt')
stop_times = pd.read_csv('brno/stop_times.txt')
trips = pd.read_csv('brno/trips.txt')
calendar = pd.read_csv('brno/calendar.txt')

def haversine(lat1: float, lon1: float, lat2: float, lon2:float):
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

def get_departures(stop_id, current_time, day_of_week):
    """Get departures from the stop with active services."""
    # Filter active services
    active_services = calendar[
        (calendar['start_date'] <= day_of_week) &
        (calendar['end_date'] >= day_of_week) 
        #(calendar[day_of_week] == 1)
    ]['service_id'].tolist()

    # Find trips with active services
    active_trips = trips[trips['service_id'].isin(active_services)]['trip_id'].tolist()

    # Filter departures for active trips
    departures = stop_times[
        (stop_times['stop_id'] == stop_id) &
        (stop_times['trip_id'].isin(active_trips)) &
        (stop_times['departure_time'] > current_time)
    ].sort_values('departure_time')

    return departures[['departure_time', 'trip_id']].to_dict(orient='records')

@app.route('/departures', methods=['GET'])
def departures():
    """API endpoint to get departures from the nearest stop."""
    try:
        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))
        current_time = request.args.get('current_time', '12:00:00')  # Default time for testing
        day_of_week = request.args.get('day_of_week', 'monday')  # Default day for testing

        stop_id, stop_name = find_nearest_stop(lat, lon)
        departures = get_departures(stop_id, current_time, day_of_week)

        return jsonify({
            "nearest_stop": stop_name,
            "departures": departures
        })
    except Exception as e:
        raise e
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=51234)
