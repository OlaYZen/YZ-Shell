import calendar
import subprocess
from datetime import datetime, timedelta, date

import gi
from fabric.widgets.centerbox import CenterBox
from fabric.widgets.label import Label

import modules.icons as icons
from modules.ical_events import ical_manager

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk


class Calendar(Gtk.Box):
    def __init__(self, widgets=None, **kwargs):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8, name="calendar")
        self.widgets = widgets

        # Set Monday as the first day of the week (0=Monday, 6=Sunday)
        self.first_weekday = 0

        self.set_halign(Gtk.Align.CENTER)
        self.set_hexpand(False)

        self.current_year = datetime.now().year
        self.current_month = datetime.now().month
        self.current_day = datetime.now().day
        self.previous_key = (self.current_year, self.current_month)

        self.cache_threshold = 1
        self._updating_events = False

        self.month_views = {}

        self.prev_month_button = Gtk.Button(
            name="prev-month-button",
            child=Label(name="month-button-label", markup=icons.chevron_left)
        )
        self.prev_month_button.connect("clicked", self.on_prev_month_clicked)

        self.month_label = Gtk.Label(name="month-label")
        # Make the month label clickable to refresh events
        self.month_button = Gtk.Button(name="month-refresh-button", child=self.month_label)
        self.month_button.connect("clicked", lambda *_: self.force_refresh_events())

        self.next_month_button = Gtk.Button(
            name="next-month-button",
            child=Label(name="month-button-label", markup=icons.chevron_right)
        )
        self.next_month_button.connect("clicked", self.on_next_month_clicked)

        self.header = CenterBox(
            spacing=4,
            name="header",
            start_children=[self.prev_month_button],
            center_children=[self.month_button],
            end_children=[self.next_month_button],
        )

        self.add(self.header)

        self.weekday_row = Gtk.Box(spacing=4, name="weekday-row")
        self.pack_start(self.weekday_row, False, False, 0)

        self.stack = Gtk.Stack(name="calendar-stack")
        self.stack.set_transition_duration(250)
        self.pack_start(self.stack, True, True, 0)

        self.update_header()
        self.update_calendar()
        self.schedule_midnight_update()
        
        # Register for iCal event updates
        ical_manager.add_listener(self.on_events_updated)
        
        # Load iCal events initially (with delay to prevent loop during init)
        GLib.timeout_add(500, self._initial_load_events)

    def _initial_load_events(self):
        """Initial load of events with proper safeguards."""
        print("Calendar: Initial load of iCal events")
        self.load_ical_events()
        return False  # Don't repeat timer

    def schedule_midnight_update(self):
        now = datetime.now()

        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        delta = midnight - now
        seconds_until = delta.total_seconds()
        GLib.timeout_add_seconds(int(seconds_until), self.on_midnight)

    def on_midnight(self):
        now = datetime.now()
        self.current_year = now.year
        self.current_month = now.month
        self.current_day = now.day

        key = (self.current_year, self.current_month)
        if key in self.month_views:
            widget = self.month_views.pop(key)
            self.stack.remove(widget)

        self.update_calendar()
        self.schedule_midnight_update()
        return False

    def update_header(self):

        self.month_label.set_text(
            datetime(self.current_year, self.current_month, 1).strftime("%B %Y").capitalize()
        )

        for child in self.weekday_row.get_children():
            self.weekday_row.remove(child)
        days = self.get_weekday_initials()
        for day in days:
            label = Gtk.Label(label=day.upper(), name="weekday-label")
            self.weekday_row.pack_start(label, True, True, 0)
        self.weekday_row.show_all()

    def update_calendar(self):
        new_key = (self.current_year, self.current_month)

        if new_key > self.previous_key:
            self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
        elif new_key < self.previous_key:
            self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_RIGHT)

        self.previous_key = new_key

        if new_key not in self.month_views:
            month_view = self.create_month_view(self.current_year, self.current_month)
            self.month_views[new_key] = month_view
            self.stack.add_titled(
                month_view,
                f"{self.current_year}_{self.current_month}",
                f"{self.current_year}_{self.current_month}"
            )

        self.stack.set_visible_child_name(f"{self.current_year}_{self.current_month}")
        self.update_header()
        self.stack.show_all()

        self.prune_cache()

    def prune_cache(self):

        def month_index(key):
            year, month = key
            return year * 12 + (month - 1)

        current_index = month_index((self.current_year, self.current_month))
        keys_to_remove = []
        for key in self.month_views:
            if abs(month_index(key) - current_index) > self.cache_threshold:
                keys_to_remove.append(key)
        for key in keys_to_remove:
            widget = self.month_views.pop(key)
            self.stack.remove(widget)

    def create_month_view(self, year, month):
        grid = Gtk.Grid(column_homogeneous=True, row_homogeneous=False, name="calendar-grid")
        cal = calendar.Calendar(firstweekday=self.first_weekday)
        month_days = cal.monthdayscalendar(year, month)

        while len(month_days) < 6:
            month_days.append([0] * 7)

        for row, week in enumerate(month_days):
            for col, day in enumerate(week):
                # Create an overlay to position the event dot
                overlay = Gtk.Overlay()
                
                if day == 0:
                    # Empty day cell
                    label = Label(name="day-empty", markup=icons.dot)
                    day_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, name="day-box")
                    clickable = False
                else:
                    # Regular day cell
                    label = Gtk.Label(label=str(day), name="day-label")
                    clickable = True

                    if (
                        day == self.current_day
                        and month == datetime.now().month
                        and year == datetime.now().year
                    ):
                        label.get_style_context().add_class("current-day")
                
                # Create day button if it's a valid day and we have widgets reference
                if clickable and self.widgets:
                    day_button = Gtk.Button(name="day-button")
                    day_button.set_relief(Gtk.ReliefStyle.NONE)  # No button border
                    day_button.connect("clicked", self._on_day_clicked, year, month, day)
                    
                    # Add special styling for days with events
                    event_date = date(year, month, day)
                    if ical_manager.has_events_on_date(event_date):
                        day_button.get_style_context().add_class("has-events")
                    
                    day_box = day_button
                else:
                    day_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, name="day-box")
                
                top_spacer = Gtk.Box(hexpand=True, vexpand=True)
                middle_box = Gtk.Box(hexpand=True, vexpand=True)
                bottom_spacer = Gtk.Box(hexpand=True, vexpand=True)

                middle_box.pack_start(Gtk.Box(hexpand=True, vexpand=True), True, True, 0)
                middle_box.pack_start(label, False, False, 0)
                middle_box.pack_start(Gtk.Box(hexpand=True, vexpand=True), True, True, 0)
                
                # Add the middle_box as the main child of overlay
                overlay.add(middle_box)
                
                # Add event indicator dots if there are events on this day
                if day > 0:
                    event_date = date(year, month, day)
                    if ical_manager.has_events_on_date(event_date):
                        event_colors = ical_manager.get_event_colors_on_date(event_date)
                        print(f"Calendar: Adding {len(event_colors)} event dots for {event_date} with colors: {event_colors}")
                        
                        # Create a small box to hold multiple colored dots
                        dots_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
                        dots_box.set_halign(Gtk.Align.END)
                        dots_box.set_valign(Gtk.Align.END)
                        
                        # Add up to 3 dots (to avoid overcrowding)
                        for i, color in enumerate(event_colors[:3]):
                            dot = Label(name="event-dot", markup=f'<span color="{color}">●</span>')
                            dot.set_name(f"event-dot-{i}")
                            # Use markup to set color directly - this should work more reliably
                            print(f"Calendar: Set dot {i} to color {color} using markup")
                            dots_box.pack_start(dot, False, False, 0)
                        
                        # If there are more than 3 sources, add an indicator
                        if len(event_colors) > 3:
                            more_dot = Label(name="event-dot", markup="…")
                            dots_box.pack_start(more_dot, False, False, 0)
                        
                        dots_box.show_all()
                        overlay.add_overlay(dots_box)

                # Create content box for the day
                content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, name="day-content")
                content_box.pack_start(top_spacer, True, True, 0)
                content_box.pack_start(overlay, True, True, 0)
                content_box.pack_start(bottom_spacer, True, True, 0)
                
                # Add content to day container (either Button or Box)
                if isinstance(day_box, Gtk.Button):
                    day_box.add(content_box)
                else:
                    day_box.pack_start(content_box, True, True, 0)

                grid.attach(day_box, col, row, 1, 1)
        grid.show_all()
        return grid

    def get_weekday_initials(self):

        return [datetime(2024, 1, i + 1 + self.first_weekday).strftime("%a")[:1] for i in range(7)]
    
    def _on_day_clicked(self, button, year, month, day):
        """Handle day click - show iCal events if any exist for this date"""
        from datetime import date
        selected_date = date(year, month, day)
        
        print(f"Calendar: Day clicked - {selected_date}")
        
        # Check if there are any events on this date
        if ical_manager.has_events_on_date(selected_date):
            events = ical_manager.get_events_on_date(selected_date)
            print(f"Calendar: Found {len(events)} events for {selected_date}")
            
            if self.widgets and hasattr(self.widgets, 'show_ical_events'):
                self.widgets.show_ical_events(selected_date)
                print(f"Calendar: Showing iCal events applet for {selected_date}")
            else:
                print(f"Calendar: No widget handler available for date: {selected_date}")
        else:
            print(f"Calendar: No events found for date: {selected_date}")
            # If any applet other than notifications is currently visible, return to notifications
            if self.widgets and hasattr(self.widgets, 'is_notifications_visible') and not self.widgets.is_notifications_visible():
                print(f"Calendar: An applet is open, returning to notifications")
                self.widgets.show_notifications()
            else:
                print(f"Calendar: Already on notifications, click on day without events ignored")

    def on_prev_month_clicked(self, widget):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.update_calendar()

    def on_next_month_clicked(self, widget):
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.update_calendar()
    
    def load_ical_events(self):
        """Load iCal events from configured sources."""
        try:
            from config.data import load_config
            config = load_config()
            ical_sources = config.get('ical_sources', [])
            # Backward compatibility with old ical_urls
            old_urls = config.get('ical_urls', [])
            if old_urls and not ical_sources:
                ical_sources = [{'url': url, 'color': '#007acc', 'name': f'Calendar {i+1}'} for i, url in enumerate(old_urls)]
            
            print(f"Calendar: Loading iCal events from {len(ical_sources)} sources")
            ical_manager.update_events_async(ical_sources)
        except Exception as e:
            print(f"Error loading iCal events: {e}")
    
    def on_events_updated(self):
        """Called when iCal events are updated - refresh the calendar."""
        if self._updating_events:
            return False  # Prevent recursive calls
            
        print("Calendar: Events updated, clearing cache and refreshing calendar")
        self._updating_events = True
        
        # Clear the current month from cache to force recreation with new events
        current_key = (self.current_year, self.current_month)
        if current_key in self.month_views:
            widget = self.month_views.pop(current_key)
            self.stack.remove(widget)
            print(f"Calendar: Cleared cached view for {current_key}")
        
        # Now update the calendar which will recreate the current month view
        self.update_calendar()
        self._updating_events = False
        return False  # Remove from GLib.idle_add
        
    def force_refresh_events(self):
        """Force refresh iCal events (for manual testing/refresh)."""
        try:
            from config.data import load_config
            config = load_config()
            ical_sources = config.get('ical_sources', [])
            # Backward compatibility with old ical_urls
            old_urls = config.get('ical_urls', [])
            if old_urls and not ical_sources:
                ical_sources = [{'url': url, 'color': '#007acc', 'name': f'Calendar {i+1}'} for i, url in enumerate(old_urls)]
            
            print(f"Calendar: Force refreshing iCal events from {len(ical_sources)} sources")
            ical_manager.force_update_events_async(ical_sources)
        except Exception as e:
            print(f"Error force refreshing iCal events: {e}")
        
    def cleanup(self):
        """Cleanup method to unregister listeners."""
        ical_manager.remove_listener(self.on_events_updated)
