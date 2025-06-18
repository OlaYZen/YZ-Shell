import gi

gi.require_version("Gtk", "3.0")
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.stack import Stack
from gi.repository import GLib, Gtk

import config.data as data
from modules.bluetooth import BluetoothConnections
from modules.buttons import Buttons
from modules.calendar import Calendar
from modules.controls import ControlSliders
from modules.ical_applet import ICalEventsApplet
from modules.metrics import Metrics
from modules.network import NetworkConnections
from modules.vpn_connections import VpnConnections
from modules.network_manager import NetworkManager
from modules.password_prompt import PasswordPrompt
from modules.vpn_prompt import VpnPrompt
from modules.notifications import NotificationHistory
from modules.player import Player


class Widgets(Box):
    def __init__(self, **kwargs):
        super().__init__(
            name="dash-widgets",
            h_align="fill",
            v_align="fill",
            h_expand=True,
            v_expand=True,
            visible=True,
            all_visible=True,
        )

        vertical_layout = False
        if data.PANEL_THEME == "Panel" and (
            data.BAR_POSITION in ["Left", "Right"]
            or data.PANEL_POSITION in ["Start", "End"]
        ):
            vertical_layout = True

        calendar_view_mode = "week" if vertical_layout else "month"

        self.calendar = Calendar(view_mode=calendar_view_mode)

        self.notch = kwargs["notch"]

        self.buttons = Buttons(widgets=self)
        self.bluetooth = BluetoothConnections(widgets=self)

        self.box_1 = Box(
            name="box-1",
            h_expand=True,
            v_expand=True,
        )

        self.box_2 = Box(
            name="box-2",
            h_expand=True,
            v_expand=True,
        )

        self.box_3 = Box(
            name="box-3",
            v_expand=True,
        )

        self.controls = ControlSliders()

        self.calendar = Calendar(widgets=self)

        self.player = Player()

        self.metrics = Metrics()

        self.notification_history = NotificationHistory()

        self.network_connections = NetworkConnections(widgets=self)
        
        self.ical_events = ICalEventsApplet(widgets=self)
        
        self.vpn_connections = VpnConnections(widgets=self)

        self.password_prompt = PasswordPrompt(widgets=self)

        self.vpn_prompt = VpnPrompt(widgets=self)

        self.network_manager = NetworkManager(widgets=self)

        self.calendar_stack = Stack(
            transition_type="slide-left-right",
            children=[
                self.calendar,
                self.password_prompt,
                self.vpn_prompt,
                self.network_manager,
            ]
        )

        GLib.idle_add(lambda: self.calendar_stack.set_visible_child(self.calendar))

        self.calendar_stack_box = Box(
            name="calendar-stack",
            h_expand=False,
            v_expand=True,
            h_align="center",
            children=[
                self.calendar_stack,
            ]
        )

        self.applet_stack = Stack(
            h_expand=True,
            v_expand=True,
            transition_type="slide-left-right",
            children=[
                self.notification_history,
                self.network_connections,
                self.bluetooth,
                self.ical_events,
                self.vpn_connections,
            ]
        )

        self.applet_stack_box = Box(
            name="applet-stack",
            h_expand=True,
            v_expand=True,
            h_align="fill",
            children=[
                self.applet_stack,
            ],
        )

        self.children_1 = [
            Box(
                name="container-sub-1",
                h_expand=True,
                v_expand=True,
                spacing=8,
                children=[
                    self.calendar_stack_box,  # Use the wrapper box instead

                    self.applet_stack_box,
                ]
            ),
            self.metrics,
        ] if not vertical_layout else [
            self.applet_stack_box,
            self.player,

        ]

        self.container_1 = Box(
            name="container-1",
            h_expand=True,
            v_expand=True,
            orientation="h" if not vertical_layout else "v",
            spacing=8,
            children=self.children_1,
        )

        self.container_2 = Box(
            name="container-2",
            h_expand=True,
            v_expand=True,
            orientation="v",
            spacing=8,
            children=[
                self.buttons,
                self.controls,
                self.container_1,
            ],
        )

        if not vertical_layout:
            self.children_3 = [
                self.player,
                self.container_2,
            ]
        else:  # vertical_layout
            self.children_3 = [
                self.container_2,
            ]

        self.container_3 = Box(
            name="container-3",
            h_expand=True,
            v_expand=True,
            orientation="h",
            spacing=8,
            children=self.children_3,
        )

        self.add(self.container_3)

    def show_bluetooth(self):
        self.applet_stack.set_visible_child(self.bluetooth)

    def show_notifications(self):
        self.applet_stack.set_visible_child(self.notification_history)

    def show_vpn(self):
        self.applet_stack.set_visible_child(self.vpn_connections)

    def show_network(self):
        self.notch.open_notch("network_applet")

    def show_network_manager(self):
        self.calendar_stack.set_visible_child(self.network_manager)

    def show_network_password_prompt_debug(self):
        self.calendar_stack.set_visible_child(self.password_prompt)

    def show_calendar(self):
        self.calendar_stack.set_visible_child(self.calendar)

    def show_ical_events(self, selected_date):
        """Show iCal events for the selected date"""
        self.ical_events.show_events_for_date(selected_date)
        self.applet_stack.set_visible_child(self.ical_events)
    
    def is_ical_events_visible(self):
        """Check if the iCal events applet is currently visible"""
        return self.applet_stack.get_visible_child() == self.ical_events
    
    def is_notifications_visible(self):
        """Check if the notification history is currently visible"""
        return self.applet_stack.get_visible_child() == self.notification_history
    
    def show_password_prompt(self, ssid, bssid, on_connect_callback):
        """Show the password prompt in the calendar area"""
        def on_connect(password):
            on_connect_callback(password)
            self.calendar_stack.set_visible_child(self.calendar)

        self.password_prompt.show_for_network(ssid, bssid, on_connect)
        self.calendar_stack.set_visible_child(self.password_prompt)


    def show_vpn_password_prompt(self, vpn_name, on_connect_callback):
        """Show the VPN password prompt in the calendar stack"""
        def on_connect(password):
            on_connect_callback(password)
            self.calendar_stack.set_visible_child(self.network_manager)

        self.vpn_prompt.show_for_vpn(vpn_name, on_connect)
        self.calendar_stack.set_visible_child(self.vpn_prompt)