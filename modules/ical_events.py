import requests
import threading
from datetime import datetime, date, timedelta
from typing import Dict, List, Set
from gi.repository import GLib

try:
    from icalendar import Calendar, Event
    ICALENDAR_AVAILABLE = True
except ImportError:
    ICALENDAR_AVAILABLE = False
    print("Warning: icalendar library not available. iCal support will be disabled.")

import config.data as data


class ICalEventManager:
    def __init__(self):
        self.event_dates: Dict[date, List[dict]] = {}  # date -> list of event info: {'title': str, 'color': str, 'source': str, 'description': str}
        self.last_update = None
        self.update_in_progress = False
        self.listeners = []  # List of callbacks to notify when events are updated
        
    def add_listener(self, callback):
        """Add a callback function to be notified when events are updated."""
        self.listeners.append(callback)
        
    def remove_listener(self, callback):
        """Remove a callback function."""
        if callback in self.listeners:
            self.listeners.remove(callback)
            
    def _notify_listeners(self):
        """Notify all listeners that events have been updated."""
        for callback in self.listeners:
            try:
                GLib.idle_add(callback)
            except Exception as e:
                print(f"Error notifying listener: {e}")
    
    def has_events_on_date(self, target_date: date) -> bool:
        """Check if there are any events on the given date."""
        return target_date in self.event_dates and len(self.event_dates[target_date]) > 0
    
    def get_events_on_date(self, target_date: date) -> List[dict]:
        """Get list of event info for the given date."""
        return self.event_dates.get(target_date, [])
        
    def get_event_colors_on_date(self, target_date: date) -> List[str]:
        """Get list of unique colors for events on the given date."""
        events = self.get_events_on_date(target_date)
        return list(set(event['color'] for event in events))
    
    def get_event_dates_in_month(self, year: int, month: int) -> Set[int]:
        """Get set of day numbers that have events in the given month."""
        event_days = set()
        for event_date in self.event_dates.keys():
            if event_date.year == year and event_date.month == month:
                event_days.add(event_date.day)
        return event_days
    
    def should_update(self) -> bool:
        """Check if events should be updated (every hour or if never updated)."""
        if self.last_update is None:
            return True
        return datetime.now() - self.last_update > timedelta(hours=1)
    
    def force_update_events_async(self, ical_sources: List[dict]):
        """Force update events from iCal sources regardless of last update time."""
        if not ICALENDAR_AVAILABLE:
            print("iCal: icalendar library not available")
            return
            
        if self.update_in_progress:
            print("iCal: Update already in progress, skipping")
            return
            
        if not ical_sources:
            # Clear events if no sources are configured
            print("iCal: No sources configured, clearing events")
            if self.event_dates:  # Only notify if we actually had events to clear
                self.event_dates.clear()
                self._notify_listeners()
            return
        
        print(f"iCal: Force starting update for {len(ical_sources)} sources")
        self.update_in_progress = True
        thread = threading.Thread(target=self._fetch_events_thread, args=(ical_sources,))
        thread.daemon = True
        thread.start()
    
    def update_events_async(self, ical_sources: List[dict]):
        """Update events from iCal sources in a background thread."""
        if not ICALENDAR_AVAILABLE:
            print("iCal: icalendar library not available")
            return
            
        if self.update_in_progress:
            print("iCal: Update already in progress, skipping")
            return
            
        if not ical_sources:
            # Clear events if no sources are configured
            print("iCal: No sources configured, clearing events")
            if self.event_dates:  # Only notify if we actually had events to clear
                self.event_dates.clear()
                self._notify_listeners()
            return
            
        if not self.should_update():
            print("iCal: Events are up to date, skipping update")
            return
            
        print(f"iCal: Starting update for {len(ical_sources)} sources")
        self.update_in_progress = True
        thread = threading.Thread(target=self._fetch_events_thread, args=(ical_sources,))
        thread.daemon = True
        thread.start()
    
    def _fetch_events_thread(self, ical_sources: List[dict]):
        """Fetch and parse iCal events in background thread."""
        try:
            new_event_dates = {}

            # Calculate date range once for all sources (2 years in the past and 2 years in the future)
            now = datetime.now()
            start_date = now.date() - timedelta(days=730)  # 2 years ago
            end_date = now.date() + timedelta(days=730)    # 2 years from now
            print(f"iCal: Using date range {start_date} to {end_date} for all sources")

            def to_iso(dt):
                if isinstance(dt, datetime):
                    return dt.isoformat()
                elif isinstance(dt, date):
                    return dt.isoformat()
                return None

            for source in ical_sources:
                url = source.get('url', '').strip()
                color = source.get('color', '#007acc')
                source_name = source.get('name', 'Unknown Calendar')

                if not url:
                    continue

                try:
                    print(f"iCal: Fetching from {source_name}: {url}")
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    print(f"iCal: Successfully fetched {len(response.content)} bytes from {source_name}")

                    cal = Calendar.from_ical(response.content)
                    print(f"iCal: Processing events from {source_name} between {start_date} and {end_date}")

                    events_found = 0
                    for component in cal.walk():
                        if component.name == "VEVENT":
                            event = Event(component)

                            dtstart = event.get('dtstart')
                            if dtstart is None:
                                continue
                            event_start = dtstart.dt

                            dtend = event.get('dtend')
                            event_end = dtend.dt if dtend else None

                            summary = str(event.get('summary', 'Untitled Event'))
                            description = str(event.get('description', ''))  # Fetch the description

                            # Determine base event date for indexing
                            if isinstance(event_start, datetime):
                                base_event_date = event_start.date()
                            else:
                                base_event_date = event_start

                            # Non-recurring event
                            if start_date <= base_event_date <= end_date:
                                event_info = {
                                    'title': summary,
                                    'description': description,  # Add description here
                                    'color': color,
                                    'source': source_name,
                                    'start': to_iso(event_start),
                                    'end': to_iso(event_end),
                                }
                                if base_event_date not in new_event_dates:
                                    new_event_dates[base_event_date] = []
                                new_event_dates[base_event_date].append(event_info)
                                events_found += 1

                    print(f"iCal: Found {events_found} events from {source_name}")

                except requests.RequestException as e:
                    print(f"Error fetching iCal from {source_name}: {e}")
                except Exception as e:
                    print(f"Error parsing iCal from {source_name}: {e}")

            self.event_dates = new_event_dates
            self.last_update = datetime.now()

            print(f"Updated calendar events: {len(self.event_dates)} days with events")

            GLib.idle_add(self._notify_listeners)

        except Exception as e:
            print(f"Error in iCal update thread: {e}")
        finally:
            self.update_in_progress = False


# Global instance
ical_manager = ICalEventManager()