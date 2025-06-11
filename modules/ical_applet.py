import gi
from datetime import date, datetime

gi.require_version('Gtk', '3.0')
from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.centerbox import CenterBox
from fabric.widgets.label import Label
from fabric.widgets.scrolledwindow import ScrolledWindow
from gi.repository import Gtk

import modules.icons as icons
from modules.ical_events import ical_manager


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
        
        # Event title
        title = event_data.get('title', event_data.get('summary', 'Untitled Event'))
        self.title_label = Label(
            name="ical-event-title",
            label=title,
            h_align="start",
            ellipsization="end"
        )
        
        # Event time and source
        time_str = self._format_event_time()
        source_name = event_data.get('source', 'Unknown Calendar')
        display_str = f"{time_str} • {source_name}"
        self.time_label = Label(
            name="ical-event-time", 
            label=display_str,
            h_align="start"
        )
        
        # Event description (if available)
        description = event_data.get('description', '')
        if description:
            # Limit description length
            if len(description) > 100:
                description = description[:97] + "..."
            self.desc_label = Label(
                name="ical-event-description",
                label=description,
                h_align="start",
                wrap=True,
                ellipsization="end",
                max_width_chars=50
            )
        else:
            self.desc_label = None
        
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
        if self.desc_label:
            self.add(self.desc_label)
    
    def _format_event_time(self):
        """Format the event time for display"""
        # Check if the event has specific time information
        start_time = self.event_data.get('start')
        end_time = self.event_data.get('end')
        
        # If no start time info, assume it's an all-day event
        if not start_time:
            return "All day"
        
        try:
            if isinstance(start_time, str):
                # Parse ISO format datetime
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            else:
                start_dt = start_time
            
            if end_time:
                if isinstance(end_time, str):
                    end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                else:
                    end_dt = end_time
                
                # Check if it's all day (dates without time)
                if hasattr(start_dt, 'hour') and hasattr(end_dt, 'hour'):
                    return f"{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}"
                else:
                    return "All day"
            else:
                if hasattr(start_dt, 'hour'):
                    return start_dt.strftime('%H:%M')
                else:
                    return "All day"
        except Exception as e:
            print(f"Error formatting event time: {e}")
            # Most calendar events (like birthdays) are all-day events
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
            on_clicked=lambda *_: self.widgets.show_notif() if self.widgets else None
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
        """Display events for the specified date"""
        self.selected_date = selected_date
        
        # Update title
        date_str = selected_date.strftime("%B %d, %Y")
        self.date_label.set_label(f"Events - {date_str}")
        
        # Clear existing events
        self._clear_events_list()
        
        # Get events for this date
        events = ical_manager.get_events_on_date(selected_date)
        
        print(f"iCal Applet: Found {len(events)} events for {selected_date}")
        for i, event in enumerate(events):
            print(f"iCal Applet: Event {i}: {event}")
        
        if events:
            self.no_events_label.set_visible(False)
            
            # Sort events by title since they don't have start times in our structure
            sorted_events = sorted(events, key=lambda e: e.get('title', ''))
            
            for event in sorted_events:
                event_slot = ICalEventSlot(event)
                self.events_list_box.add(event_slot)
        else:
            self.no_events_label.set_visible(True)
        
        # Show all widgets
        self.events_list_box.show_all()
    
    def _clear_events_list(self):
        """Clear all events from the list"""
        for child in self.events_list_box.get_children():
            child.destroy() 