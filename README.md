# neardeps
_an iOS shortcut for displaying nearest public transport departures_

## Usage


## API endpoint
At this stage of the project, API endpoint implemented in [app.py](./app.py) can be queried with following arguments:
| Argument | Type | Mandatory? | Description
| --- | --- | --- | --- | 
| `city` | string | yes | City whose GTFS data shall be examined. So far, just `brno` is implemented |
| `lat`  | float  | yes | Latitude coordinate of current user position |
| `lon`  | float  | yes | Longitude coordinate of current user position |
| `time` | str(`HH:MM:SS`) | no | Time for querying public transport departures |
| `date` | str(`YYYY-MM-DD`) | no | Date for querying public transport departures | 

## Motivation


