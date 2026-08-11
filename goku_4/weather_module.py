import urllib.request
import json
import logging

logger = logging.getLogger('GOKU.Weather')

class WeatherModule:
    def __init__(self):
        self._cached = None
        self._city = None

    def initialize(self):
        logger.info("Weather module initialized")
        return True

    def get_weather(self, city=None):
        city = city or "current location"
        try:
            url = f"https://wttr.in/{urllib.request.quote(city)}?format=j1"
            req = urllib.request.Request(url, headers={'User-Agent': 'GOKU/1.0'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())

            current = data['current_condition'][0]
            temp_c = current['temp_C']
            temp_f = current['temp_F']
            desc = current['weatherDesc'][0]['value']
            humidity = current['humidity']
            wind_k = current['windspeedKmph']
            feels = current['FeelsLikeC']

            area = data.get('nearest_area', [{}])[0]
            city_name = area.get('areaName', [{}])[0].get('value', city)
            country = area.get('country', [{}])[0].get('value', '')

            self._cached = {
                'city': city_name,
                'country': country,
                'temp_c': temp_c,
                'temp_f': temp_f,
                'desc': desc,
                'humidity': humidity,
                'wind': wind_k,
                'feels': feels
            }

            return self._format_response(self._cached)
        except Exception as e:
            logger.error(f"Weather fetch failed: {e}")
            return None

    def _format_response(self, w):
        return (
            f"Weather in {w['city']}, {w['country']}: {w['desc']}. "
            f"Temperature {w['temp_c']}°C ({w['temp_f']}°F), "
            f"feels like {w['feels']}°C. "
            f"Humidity {w['humidity']}%, wind {w['wind']} km/h."
        )

    def needs_weather(self, query):
        ql = query.lower().strip()
        weather_kw = [
            "weather", "temperature", "how hot", "how cold", "is it raining",
            "is it sunny", "forecast", "climate", "humidity", "wind speed",
            "what's the weather", "whats the weather", "weather today",
            "weather now", "outside temperature", "current weather",
        ]
        return any(k in ql for k in weather_kw)

    def extract_city(self, query):
        ql = query.lower().strip()
        for kw in ["in ", "at ", "for "]:
            if kw in ql:
                city = ql.split(kw, 1)[1].strip().rstrip("?").strip()
                if city:
                    return city
        return None

weather_module = WeatherModule()
