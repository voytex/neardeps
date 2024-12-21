# neardeps
_an iOS shortcut for displaying nearest public transport departures_

## General
This repository contains source code and auxiliary files for deploying Docker container - **back-end** and download link for iCloud shortcut - **front-end**. 
> [!TIP]
> If the user does not want to deploy their own Docker container, they can use author's one. It can be found on following link:
> 
> [`http://gtfs.vojtechlukas.cz/departures`](http://gtfs.vojtechlukas.cz/departures)
> 
> This endpoint is set as default in the iOS shortcut. 

> [!WARNING]
> Author's endpoint is provided AS IS with no warranty. Data it returns are based on public source ([data.brno](https://data.brno.cz/datasets/379d2e9a7907460c8ca7fda1f3e84328/about)).


## iOS shortcut
### Usage
1. Download Shortcut from **Releases** or directly from this [link](https://www.icloud.com/shortcuts/497dde190bca4e229b83d160a694268b)
1. Allow access to current location
1. Run the shortcut from your Apple device (iPhone/Watch/Macbook...)
1. After fetching data from server, the shortcut will display **earliest public transport departures** from your **nearest stop** based on your **current location**


## API endpoint
### Arguments
At this stage of the project, API endpoint `/departures` implemented in [app.py](./app.py) can be queried with following arguments:
| Argument | Type | Mandatory? | Description
| --- | --- | --- | --- | 
| `city` | str | yes | City whose GTFS data shall be examined. So far, just `brno` is implemented |
| `lat`  | float  | yes | Latitude GPS coordinate of current user position |
| `lon`  | float  | yes | Longitude GPS coordinate of current user position |
| `time` | str(`HH:MM:SS`) | no | Time for querying public transport departures. Omitted = current time |
| `date` | str(`YYYY-MM-DD`) | no | Date for querying public transport departures. Omitted = current date | 

### Example Usage
```
domain.com/departures?city=brno&lat=49.123&lon=16.456
```
- returns JSON with earliest departures from nearest (based on `lat` and `lon` fields) public transport stop
```
domain.com/departures?city=brno&lat=49.123&lon=16.456&date=2024-12-31&time=12:35:00
```
- returns JSON with departures on Dec 31 2024 at nearest (based on `lat` and `lon` fields) public transport stop

### Returns
Following request
```
http://domain.com/departures?
  lat=49.21630&
  lon=16.57843&
  city=brno&
  time=1:00:00&
  date=2024-12-15
```
returns JSON with following structure and values:
```json
{
  "departures": [
    {
      "departure_time": "01:12:00",
      "route_short_name": "N89",
      "trip_headsign": "U Luhu",
      "trip_id": 56550
    },
    {
      "departure_time": "02:12:00",
      "route_short_name": "N89",
      "trip_headsign": "U Luhu",
      "trip_id": 56557
    },
    {
      "departure_time": "03:12:00",
      "route_short_name": "N89",
      "trip_headsign": "U Luhu",
      "trip_id": 56563
    },
    // ...
    }
  ],
  "nearest_stop": "Makovského náměstí"
}
```

## Motivation


