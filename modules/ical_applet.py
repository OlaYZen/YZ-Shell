import gi
from datetime import date, datetime, timezone
import re
import unicodedata

gi.require_version('Gtk', '3.0')
from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.centerbox import CenterBox
from fabric.widgets.label import Label
from fabric.widgets.scrolledwindow import ScrolledWindow
from gi.repository import Gtk
from tzlocal import get_localzone
from zoneinfo import ZoneInfo



import modules.icons as icons
from modules.ical_events import ical_manager

local_tz = get_localzone()


class ICalEventSlot(Box):
    """Widget to display a single iCal event"""
    def __init__(self, event_data: dict, **kwargs):
        super().__init__(
            name="ical-event-slot",
            orientation="vertical",
            spacing=4,
            **kwargs
        )
        
        self.event_data = event_data
        
        source_name = event_data.get('source', 'Unknown Calendar')

        title = event_data.get('title', event_data.get('summary', 'Untitled Event'))

        # Removes the ugly Emojis if the user has the offical f1 icals
        if source_name == 'Formula 1':
            emoji_pattern = r'[🏎⏱️🏁]'
            title = re.sub(emoji_pattern, '', title).strip()
            title = unicodedata.normalize('NFKC', title)
                        
        self.title_label = Label(
            name="ical-event-title",
            label=title,
            h_align="start",
            ellipsization="end"
        )
        # Event time and source
        time_str = self._format_event_time()
        location = event_data.get('location', '')
        if (location == "None"):
            display_str = f"{time_str} • {source_name}"  
        else:
            display_str = f'{location} • {time_str} • {source_name}'
        self.time_label = Label(
            name="ical-event-time", 
            label=display_str,
            h_align="start"
        )
        
        # Tooltip with full description
        full_description = event_data.get('description', 'No description available')
        self.set_tooltip_text(full_description)  # Set tooltip text to the description
        
        # Event source/calendar color indicator
        source_color = event_data.get('color', event_data.get('source_color', '#007acc'))
        color_indicator = Label(
            name="ical-event-color",
            markup=f'<span color="{source_color}">●</span>'
        )
        
        # Header with color indicator and title
        header_box = Box(
            orientation="horizontal",
            spacing=8,
            children=[color_indicator, self.title_label]
        )
        
        # Add components to main box
        self.add(header_box)
        self.add(self.time_label)

    def _format_event_time(self) -> str:
        start_str = self.event_data.get('start')
        end_str = self.event_data.get('end')
        all_day = self.event_data.get('all_day', False)

        if not start_str:
            return "All day"

        try:
            if all_day:
                start_date = date.fromisoformat(start_str)
                if end_str:
                    end_date = date.fromisoformat(end_str)
                    # end_date is already adjusted in parsing, so display inclusive range
                    if start_date == end_date:
                        return start_date.strftime("%b %d, %Y")
                    else:
                        return f"{start_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}"
                else:
                    return start_date.strftime("%b %d, %Y")
            else:
                # Timed event formatting (same as before)
                start_dt = datetime.fromisoformat(start_str)
                event_tz = None
                tzname = self.event_data.get('calendar_timezone') or self.event_data.get('X-WR-TIMEZONE')
                if tzname:
                    try:
                        event_tz = ZoneInfo(tzname)
                    except Exception:
                        event_tz = local_tz
                else:
                    event_tz = local_tz

                if start_dt.tzinfo is None:
                    start_dt = start_dt.replace(tzinfo=event_tz)
                else:
                    start_dt = start_dt.astimezone(event_tz)

                if end_str:
                    end_dt = datetime.fromisoformat(end_str)
                    if end_dt.tzinfo is None:
                        end_dt = end_dt.replace(tzinfo=event_tz)
                    else:
                        end_dt = end_dt.astimezone(event_tz)

                    start_dt_local = start_dt.astimezone(local_tz)
                    end_dt_local = end_dt.astimezone(local_tz)

                    if start_dt_local.date() == end_dt_local.date():
                        return f"{start_dt_local.strftime('%H:%M')} - {end_dt_local.strftime('%H:%M')}"
                    else:
                        return f"{start_dt_local.strftime('%b %d %H:%M')} - {end_dt_local.strftime('%b %d %H:%M')}"
                else:
                    start_dt_local = start_dt.astimezone(local_tz)
                    return start_dt_local.strftime('%H:%M')

        except Exception as e:
            print(f"Error formatting event time: {e}")
            return "All day"

class ICalEventsApplet(Box):
    """Applet to display iCal events for a selected date"""
    def __init__(self, **kwargs):
        super().__init__(
            name="ical-events-applet",
            orientation="vertical", 
            spacing=4,
            **kwargs,
        )
        
        self.widgets = kwargs.get("widgets")
        self.selected_date = None
        
        # Back button
        self.back_button = Button(
            name="ical-back",
            child=Label(name="ical-back-label", markup=icons.chevron_left),
            on_clicked=lambda *_: self.widgets.show_notifications() if self.widgets else None
        )
        
        # Title showing selected date
        self.date_label = Label(
            name="ical-date-title",
            label="Events"
        )
        
        # Header
        header_box = CenterBox(
            name="ical-header",
            start_children=[self.back_button],
            center_children=[self.date_label],
            end_children=[Box()]  # Empty box for balance
        )
        
        # Events list container
        self.events_list_box = Box(orientation="vertical", spacing=4)
        
        # Scrolled window for events
        scrolled_window = ScrolledWindow(
            name="ical-events-scrolled-window",
            child=self.events_list_box,
            h_expand=True,
            v_expand=True,
            propagate_width=False,
            propagate_height=False,
        )
        
        # No events message
        self.no_events_label = Label(
            name="ical-no-events",
            label="No events on this date",
            h_align="center",
            v_align="center"
        )
        
        # Add components
        self.add(header_box)
        self.add(scrolled_window)
        self.add(self.no_events_label)
        
        # Initially hide no events label
        self.no_events_label.set_visible(False)
    
    def show_events_for_date(self, selected_date: date):
        """Display events for the specified date, sorted by start time ascending."""
        self.selected_date = selected_date

        date_str = selected_date.strftime("%B %d, %Y")
        self.date_label.set_label(f"Events - {date_str}")

        self._clear_events_list()

        events = ical_manager.get_events_on_date(selected_date)

        print(f"iCal Applet: Found {len(events)} events for {selected_date}")
        for i, event in enumerate(events):
            print(f"iCal Applet: Event {i}: {event}")

        if events:
            self.no_events_label.set_visible(False)

            def get_start_time(event):
                start = event.get('start')
                if not start:
                    return datetime.max.replace(tzinfo=local_tz)
                try:
                    dt = datetime.fromisoformat(start)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=local_tz)
                    else:
                        dt = dt.astimezone(local_tz)
                    return dt
                except Exception:
                    return datetime.max.replace(tzinfo=local_tz)

            sorted_events = sorted(events, key=get_start_time)

            for event in sorted_events:
                event_slot = ICalEventSlot(event)
                self.events_list_box.add(event_slot)
        else:
            self.no_events_label.set_visible(True)

        self.events_list_box.show_all()
    
    def _clear_events_list(self):
        """Clear all events from the list"""
        for child in self.events_list_box.get_children():
            child.destroy()