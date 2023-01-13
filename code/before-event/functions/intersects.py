import datetime
import json


def intersects(event, userId):
    with open('data/events.json', 'r', encoding="utf8") as f:
        # Unix timestamps for the start and end times of the first interval
        data = json.loads(f.read())

    ts1_start = data[event]["startTime"]
    ts1_end = data[event]["endTime"]

    with open('data/{}.json'.format(userId), 'r', encoding="utf8") as user_events_file:
        user_events = json.load(user_events_file)

    for user_event in user_events["events"]:
        ts2_start = user_events["events"][user_event]['startTime']
        ts2_end = user_events["events"][user_event]['endTime']

        # Convert the timestamps to datetime objects
        ts1_start_dt = datetime.datetime.fromtimestamp(ts1_start)
        ts1_end_dt = datetime.datetime.fromtimestamp(ts1_end)
        ts2_start_dt = datetime.datetime.fromtimestamp(ts2_start)
        ts2_end_dt = datetime.datetime.fromtimestamp(ts2_end)

        # Calculate the difference between the start and end times of each interval
        ts1_duration = ts1_end_dt - ts1_start_dt
        ts2_duration = ts2_end_dt - ts2_start_dt

        # Check if the intervals intersect
        if ts1_start_dt + ts2_duration > ts2_start_dt and ts2_start_dt + ts1_duration > ts1_start_dt:
            return True

    return False
