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
        self.event_dates: Dict[date, List[dict]] = {}  # date -> list of event info: {'title': str, 'color': str, 'source': str}
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
                            
                            # Get event start date
                            dtstart = event.get('dtstart')
                            if dtstart is None:
                                continue
                                
                            event_start = dtstart.dt
                            summary = str(event.get('summary', 'Untitled Event'))
                            
                            # Handle timezone-aware datetime and date objects
                            if isinstance(event_start, datetime):
                                base_event_date = event_start.date()
                            else:
                                base_event_date = event_start
                            
                            # Check if this is a recurring event
                            rrule = event.get('rrule')
                            if rrule:
                                # Handle recurring events
                                print(f"iCal: Processing recurring event '{summary}' with rule: {rrule}")
                                try:
                                    # Generate recurring instances within our date range
                                    rule_str = rrule.to_ical().decode('utf-8')
                                    
                                    # Simple yearly recurrence handler for birthdays/anniversaries
                                    if 'FREQ=YEARLY' in rule_str:
                                        # Start from the year that would first fall in our range
                                        start_year = max(base_event_date.year, start_date.year)
                                        end_year = min(base_event_date.year + 50, end_date.year)  # Reasonable limit
                                        
                                        for year in range(start_year, end_year + 1):
                                            try:
                                                recurring_date = base_event_date.replace(year=year)
                                                if start_date <= recurring_date <= end_date:
                                                    print(f"iCal: Found recurring instance '{summary}' on {recurring_date} from {source_name}")
                                                    
                                                    if recurring_date not in new_event_dates:
                                                        new_event_dates[recurring_date] = []
                                                    new_event_dates[recurring_date].append({
                                                        'title': summary,
                                                        'color': color,
                                                        'source': source_name
                                                    })
                                                    events_found += 1
                                            except ValueError:
                                                # Handle leap year issues (Feb 29)
                                                continue
                                    else:
                                        # For other recurrence patterns, just add the base event if in range
                                        if start_date <= base_event_date <= end_date:
                                            print(f"iCal: Found complex recurring event '{summary}' on {base_event_date} from {source_name}")
                                            
                                            if base_event_date not in new_event_dates:
                                                new_event_dates[base_event_date] = []
                                            new_event_dates[base_event_date].append({
                                                'title': summary,
                                                'color': color,
                                                'source': source_name
                                            })
                                            events_found += 1
                                            
                                except Exception as e:
                                    print(f"iCal: Error processing recurrence for '{summary}': {e}")
                                    # Fallback to base event
                                    if start_date <= base_event_date <= end_date:
                                        if base_event_date not in new_event_dates:
                                            new_event_dates[base_event_date] = []
                                        new_event_dates[base_event_date].append({
                                            'title': summary,
                                            'color': color,
                                            'source': source_name
                                        })
                                        events_found += 1
                            else:
                                # Non-recurring event - only include if in our date range
                                if start_date <= base_event_date <= end_date:
                                    print(f"iCal: Found single event '{summary}' on {base_event_date} from {source_name}")
                                    
                                    if base_event_date not in new_event_dates:
                                        new_event_dates[base_event_date] = []
                                    new_event_dates[base_event_date].append({
                                        'title': summary,
                                        'color': color,
                                        'source': source_name
                                    })
                                    events_found += 1
                    
                    print(f"iCal: Found {events_found} events from {source_name}")
                                
                except requests.RequestException as e:
                    print(f"Error fetching iCal from {source_name}: {e}")
                except Exception as e:
                    print(f"Error parsing iCal from {source_name}: {e}")
            
            # Update the event dates dictionary
            self.event_dates = new_event_dates
            self.last_update = datetime.now()
            
            print(f"Updated calendar events: {len(self.event_dates)} days with events")
            
            # Notify listeners on the main thread
            GLib.idle_add(self._notify_listeners)
            
        except Exception as e:
            print(f"Error in iCal update thread: {e}")
        finally:
            self.update_in_progress = False


# Global instance
ical_manager = ICalEventManager() 