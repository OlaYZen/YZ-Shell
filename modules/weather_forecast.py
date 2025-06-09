import gi
import requests
import threading
from datetime import datetime, timedelta
from gi.repository import Gtk, GLib

from fabric.widgets.label import Label
from fabric.widgets.box import Box

gi.require_version("Gtk", "3.0")
import modules.icons as icons


class WeatherForecast(Box):
    def __init__(self, **kwargs) -> None:
        super().__init__(name="weather-forecast", orientation="v", spacing=16, **kwargs)
        self.session = requests.Session()
        self.lat = None
        self.lon = None
        self.city_name = "Unknown Location"
        self.current_weather_emoji = icons.radar
        
        # Title
        self.title = Label(
            name="weather-forecast-title",
            markup=f"<span size='large' weight='bold'>{self.current_weather_emoji} {self.city_name}</span>",
            h_align="center"
        )
        self.add(self.title)
        
        # Loading indicator
        self.loading_label = Label(
            name="weather-loading",
            markup=f"{icons.loader} Loading weather data...",
            h_align="center"
        )
        self.add(self.loading_label)
        
        # Container for forecast days
        self.forecast_container = Box(
            name="forecast-container",
            orientation="h",
            spacing=12,
            visible=False,
            h_expand=True,
            h_align="center"
        )
        self.add(self.forecast_container)
        
        # Error label
        self.error_label = Label(
            name="weather-error",
            markup=f"{icons.cloud_off} Unable to load weather data",
            h_align="center",
            visible=False
        )
        self.add(self.error_label)
        
        self.show_all()
        self.fetch_weather_forecast()
        
        # Update every 30 minutes
        GLib.timeout_add_seconds(1800, self.fetch_weather_forecast)

    def get_coordinates(self):
        """Get coordinates using IP-based geolocation"""
        try:
            response = self.session.get("http://ip-api.com/json/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'success':
                    self.lat = data.get('lat')
                    self.lon = data.get('lon')
                    city = data.get('city', 'Unknown')
                    country = data.get('country', 'Unknown')
                    self.city_name = f"{city}, {country}"
                    print(f"Auto-detected location: {self.city_name} ({self.lat}, {self.lon})")
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
        self.city_name = "Unknown Location"
        print(f"Using fallback coordinates: {self.lat}, {self.lon}")
        return False

    def _update_title(self):
        """Update the title with the city name and current weather emoji"""
        self.title.set_markup(f"<span size='large' weight='bold'>{self.current_weather_emoji} {self.city_name}</span>")
        return GLib.SOURCE_REMOVE

    def get_weather_emoji(self, weather_code):
        # Map Met.no API weather codes to emojis
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

    def get_day_name(self, date):
        """Get day name for the date"""
        today = datetime.now().date()
        if date == today:
            return "Today"
        elif date == today + timedelta(days=1):
            return "Tomorrow"
        else:
            return date.strftime("%A")

    def get_time_period_name(self, hour):
        """Get time period name based on hour"""
        if 22 <= hour or hour < 6:
            return "Night"
        elif 6 <= hour < 12:
            return "Morning"
        elif 12 <= hour < 18:
            return "Afternoon"
        else:  # 18 <= hour < 22
            return "Evening"

    def create_time_period_widget(self, period_name, temp, emoji):
        """Create a widget for a specific time period"""
        period_box = Box(
            name=f"forecast-period-{period_name.lower()}",
            orientation="v",
            spacing=4,
            h_align="center"
        )
        
        # Time period label
        period_label = Label(
            name="forecast-period-name",
            markup=f"<span size='small'>{period_name}</span>",
            h_align="center"
        )
        
        # Weather emoji
        emoji_label = Label(
            name="forecast-period-emoji",
            markup=f"<span size='large'>{emoji}</span>",
            h_align="center"
        )
        
        # Temperature
        temp_label = Label(
            name="forecast-period-temp",
            markup=f"<span size='small' weight='bold'>{temp}°</span>",
            h_align="center"
        )
        
        period_box.add(period_label)
        period_box.add(emoji_label)
        period_box.add(temp_label)
        
        return period_box

    def create_day_forecast(self, date, periods_data):
        """Create a forecast widget for a single day with detailed time periods"""
        day_name = self.get_day_name(date)
        
        # Main day container
        day_box = Box(
            name="forecast-day",
            orientation="v",
            spacing=8,
            h_expand=True
        )
        
        # Day name header
        day_header = Label(
            name="forecast-day-name",
            markup=f"<span size='medium' weight='bold'>{day_name}</span>",
            h_align="center"
        )
        
        # Time periods container
        periods_box = Box(
            name="forecast-periods",
            orientation="h",
            spacing=16,
            h_align="center",
            h_expand=True
        )
        
        # Add time period widgets
        for period_name in ["Night", "Morning", "Afternoon", "Evening"]:
            if period_name in periods_data:
                period_data = periods_data[period_name]
                period_widget = self.create_time_period_widget(
                    period_name,
                    period_data['temp'],
                    period_data['emoji']
                )
                periods_box.add(period_widget)
        
        day_box.add(day_header)
        day_box.add(periods_box)
        
        # Add separator line
        separator = Label(name="forecast-separator", markup="<span size='small' color='black'>─────────────────────────────</span>")
        day_box.add(separator)
        
        return day_box

    def fetch_weather_forecast(self):
        """Start the weather fetch in a separate thread"""
        GLib.Thread.new("weather-forecast-fetch", self._fetch_weather_forecast_thread)
        return True

    def _fetch_weather_forecast_thread(self):
        """Fetch weather data from Met.no API"""
        # Get coordinates automatically
        if not self.get_coordinates():
            GLib.idle_add(self._show_error)
            return
        
        url = f'https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={self.lat}&lon={self.lon}&altitude=90'
        
        try:
            response = self.session.get(url, headers={'User-Agent': 'weather-forecast-app/1.0'})
            
            if response.status_code == 200:
                data = response.json()
                timeseries = data["properties"]["timeseries"]
                
                # Get current weather emoji for title
                if timeseries:
                    current_data = timeseries[0]["data"]
                    if "next_1_hours" in current_data and "summary" in current_data["next_1_hours"]:
                        current_weather_code = current_data["next_1_hours"]["summary"].get("symbol_code")
                        if current_weather_code:
                            self.current_weather_emoji = self.get_weather_emoji(current_weather_code)
                    elif "next_6_hours" in current_data and "summary" in current_data["next_6_hours"]:
                        current_weather_code = current_data["next_6_hours"]["summary"].get("symbol_code")
                        if current_weather_code:
                            self.current_weather_emoji = self.get_weather_emoji(current_weather_code)
                
                # Update title with current weather emoji
                GLib.idle_add(self._update_title)
                
                # Group data by date and time periods
                daily_data = {}
                today = datetime.now().date()
                
                for entry in timeseries:
                    time_str = entry["time"]
                    time_obj = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                    date = time_obj.date()
                    hour = time_obj.hour
                    
                    # Process next 5 days (including today)
                    days_diff = (date - today).days
                    if days_diff < 0 or days_diff > 2:
                        continue
                    
                    if date not in daily_data:
                        daily_data[date] = {
                            'Night': {'temps': [], 'codes': []},
                            'Morning': {'temps': [], 'codes': []},
                            'Afternoon': {'temps': [], 'codes': []},
                            'Evening': {'temps': [], 'codes': []}
                        }
                    
                    # Determine time period
                    period = self.get_time_period_name(hour)
                    
                    # Extract temperature
                    if "instant" in entry["data"] and "details" in entry["data"]["instant"]:
                        temp = entry["data"]["instant"]["details"].get("air_temperature")
                        if temp is not None:
                            daily_data[date][period]['temps'].append(int(temp))
                    
                    # Extract weather code
                    weather_code = None
                    if "next_6_hours" in entry["data"] and "summary" in entry["data"]["next_6_hours"]:
                        weather_code = entry["data"]["next_6_hours"]["summary"].get("symbol_code")
                    elif "next_1_hours" in entry["data"] and "summary" in entry["data"]["next_1_hours"]:
                        weather_code = entry["data"]["next_1_hours"]["summary"].get("symbol_code")
                    
                    if weather_code:
                        daily_data[date][period]['codes'].append(weather_code)
                
                # Process daily data and create widgets
                forecast_widgets = []
                for date in sorted(daily_data.keys()):
                    day_data = daily_data[date]
                    periods_data = {}
                    
                    for period in ['Night', 'Morning', 'Afternoon', 'Evening']:
                        period_info = day_data[period]
                        
                        if period_info['temps'] and period_info['codes']:
                            # Use average temperature for the period
                            avg_temp = int(sum(period_info['temps']) / len(period_info['temps']))
                            
                            # Use most common weather code for the period
                            most_common_code = max(set(period_info['codes']), 
                                                 key=period_info['codes'].count)
                            
                            emoji = self.get_weather_emoji(most_common_code)
                            
                            periods_data[period] = {
                                'temp': avg_temp,
                                'emoji': emoji
                            }
                        elif period_info['temps']:
                            # Have temperature but no weather code
                            avg_temp = int(sum(period_info['temps']) / len(period_info['temps']))
                            periods_data[period] = {
                                'temp': avg_temp,
                                'emoji': "🌡️"
                            }
                    
                    if periods_data:  # Only create widget if we have data
                        day_widget = self.create_day_forecast(date, periods_data)
                        forecast_widgets.append(day_widget)
                
                # Update UI in main thread
                GLib.idle_add(self._update_forecast_ui, forecast_widgets)
                
            else:
                GLib.idle_add(self._show_error)
                
        except Exception as e:
            print(f"Error fetching weather forecast: {e}")
            GLib.idle_add(self._show_error)

    def _update_forecast_ui(self, forecast_widgets):
        """Update the UI with forecast data"""
        # Clear existing forecast
        for child in self.forecast_container.get_children():
            self.forecast_container.remove(child)
        
        # Add new forecast widgets
        for widget in forecast_widgets:
            self.forecast_container.add(widget)
        
        # Show/hide appropriate elements
        self.loading_label.set_visible(False)
        self.error_label.set_visible(False)
        self.forecast_container.set_visible(True)
        self.forecast_container.show_all()
        
        return GLib.SOURCE_REMOVE

    def _show_error(self):
        """Show error message"""
        self.loading_label.set_visible(False)
        self.forecast_container.set_visible(False)
        self.error_label.set_visible(True)
        
        return GLib.SOURCE_REMOVE 