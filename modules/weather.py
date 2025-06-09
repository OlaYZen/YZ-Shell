import gi
import requests
import threading
import urllib.parse
from gi.repository import Gtk, GLib

from fabric.widgets.label import Label
from fabric.widgets.box import Box

gi.require_version("Gtk", "3.0")
import config.data as data
import modules.icons as icons


class Weather(Box):
    def __init__(self, **kwargs) -> None:
        super().__init__(name="weather", orientation="h", spacing=8, **kwargs)
        self.label = Label(name="weather-label", markup=icons.loader)
        self.lat = None
        self.lon = None
        self.add(self.label)
        self.show_all()
        self.enabled = True
        self.session = requests.Session()
        GLib.timeout_add_seconds(600, self.fetch_weather)
        self.fetch_weather()

    def get_coordinates(self):
        """Get coordinates using IP-based geolocation"""
        try:
            response = self.session.get("http://ip-api.com/json/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'success':
                    self.lat = data.get('lat')
                    self.lon = data.get('lon')
                    print(f"Auto-detected location: {data.get('city', 'Unknown')}, {data.get('country', 'Unknown')} ({self.lat}, {self.lon})")
                    return True
                else:
                    print(f"Geolocation failed: {data.get('message', 'Unknown error')}")
            else:
                print(f"Geolocation service returned status code: {response.status_code}")
        except Exception as e:
            print(f"Error fetching coordinates: {e}")
        
        # Fallback coordinates (New York)
        self.lat = 40.7128
        self.lon = 74.0060
        print(f"Using fallback coordinates: {self.lat}, {self.lon}")
        return False

    def get_weather_emoji(self, weather_code):
        # Map Met API weather codes to emojis
        weather_emojis = {
            "clearsky_day": "☀️",
            "clearsky_night": "🌙",
            "fair_day": "🌤️",
            "fair_night": "🌤️",
            "partlycloudy_day": "⛅",
            "partlycloudy_night": "☁️",
            "cloudy": "☁️",
            "rainshowers_day": "🌦️",
            "rainshowers_night": "🌧️",
            "rain": "🌧️",
            "thunder": "⛈️",
            "sleet": "🌨️",
            "snow": "❄️",
            "fog": "🌫️",
            "lightrain": "🌦️",
            "heavyrain": "🌧️",
            "lightsleet": "🌨️",
            "heavysleet": "🌨️",
            "lightsnow": "🌨️",
            "heavysnow": "❄️",
            "lightrainshowers_day": "🌦️",
            "heavyrainshowers_day": "🌧️",
            "lightrainshowers_night": "🌧️",
            "heavyrainshowers_night": "🌧️"
        }
        return weather_emojis.get(weather_code.lower(), "🌡️")

    def set_visible(self, visible):
        """Override to track external visibility setting"""
        self.enabled = visible

        if visible and hasattr(self, 'has_weather_data') and self.has_weather_data:
            super().set_visible(True)
        else:
            super().set_visible(visible)

    def get_location(self):
        try:
            response = requests.get("https://ipinfo.io/json")
            if response.status_code == 200:
                data = response.json()
                return data.get("city", "")
            else:
                print("Error getting location from ipinfo.")
        except Exception as e:
            print(f"Error getting location: {e}")
        return ""

    def fetch_weather(self):
        GLib.Thread.new("weather-fetch", self._fetch_weather_thread)
        return True

    def _fetch_weather_thread(self):
        # Get coordinates automatically
        if not self.get_coordinates():
            self.has_weather_data = False
            GLib.idle_add(self.label.set_markup, f"{icons.cloud_off} Location Error")
            GLib.idle_add(super().set_visible, False)
            return
        
        url = f'https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={self.lat}&lon={self.lon}&altitude=90'
        try:
            response = requests.get(url, headers={'User-Agent': 'weather-app/1.0'})
            if response.status_code == 200:
                data = response.json()["properties"]["timeseries"][0]["data"]
                temp = data["instant"]["details"]["air_temperature"]
                weather_code = data["next_1_hours"]["summary"]["symbol_code"]
                print(f"Debug - Weather code: {weather_code}")  # Debug line
                emoji = self.get_weather_emoji(weather_code)
                GLib.idle_add(self.label.set_label, f"{emoji} {temp}°C")
                self.has_weather_data = True
            else:
                self.has_weather_data = False
                GLib.idle_add(self.label.set_markup, f"{icons.cloud_off} Unavailable")
                GLib.idle_add(super().set_visible, False)
        except Exception as e:
            self.has_weather_data = False
            print(f"Error fetching weather: {e}")
            GLib.idle_add(self.label.set_markup, f"{icons.cloud_off} Error")
            GLib.idle_add(super().set_visible, False)
