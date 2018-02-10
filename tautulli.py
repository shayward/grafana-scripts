import requests
import geohash

from datetime import datetime, timezone
from influxdb import InfluxDBClient

# noinspection PyUnresolvedReferences
from requests.packages.urllib3.exceptions import InsecureRequestWarning
# noinspection PyUnresolvedReferences
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

current_time = datetime.now(timezone.utc).astimezone().isoformat()

activity = requests.get('https://plexpy.domain.tld/api/v2'
                       '?apikey=xxxxxxxxxxxx&cmd=get_activity').json()['response']['data']

sessions = {d['session_id']: d for d in activity['sessions']}

influx_payload = [
    {
        "measurement": "Plex",
        "tags": {
            "server": "Tautulli"
        },
        "time": current_time,
        "fields": {
            "stream_count": int(activity['stream_count'])
        }
    }
]

for session in sessions.keys():
    lookup = requests.get('http://freegeoip.net/json/{}'.format(sessions[session]['ip_address_public'])).json()
    influx_payload.append(
        {
            "measurement": "Plex",
            "tags": {
                "server": "Tautulli",
                "type": "Session",
                "region_code": lookup['region_code']
            },
            "time": current_time,
            "fields": {
                "name": sessions[session]['friendly_name'],
                "title": sessions[session]['full_title'],
                "quality": '{}p'.format(sessions[session]['video_resolution']),
                "transcode_decision": sessions[session]['transcode_decision'],
                "location": lookup['city'],
            }
        }
    )


influx = InfluxDBClient('grafana.domain.tld', 8086, 'root', 'root', 'plex')
influx.write_points(influx_payload)
