import requests
from datetime import datetime, timedelta

def getPop(lat=37.26, lon=127.05):

    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&hourly=precipitation_probability"
    )

    try:
        data = requests.get(url, timeout=10).json()
        times = data["hourly"]["time"]
        pops = data["hourly"]["precipitation_probability"]

        now = datetime.utcnow() + timedelta(hours=9)
        end_time = now + timedelta(hours=12)

        Pop12h = [
            p for t, p in zip(times, pops)
            if now <= datetime.fromisoformat(t) + timedelta(hours=9) <= end_time
        ]

        if not Pop12h:
            return None

        maxPop12h = max(Pop12h)

        if maxPop12h < 30:
            return 1
        elif maxPop12h < 60:
            return 2
        else:
            return 3

    except Exception as e:
        print(f"Error: {e}")
        return None
