import gi

gi.require_version('Gtk', '3.0')
from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.centerbox import CenterBox
from fabric.widgets.entry import Entry
from fabric.widgets.label import Label
from gi.repository import GLib, Gtk

import modules.icons as icons


class PasswordPrompt(Box):
    """In-dashboard password prompt for WiFi networks"""
    def __init__(self, **kwargs):
        super().__init__(
            name="wifi-password-prompt",
            orientation="vertical",
            spacing=8,
            **kwargs,
        )
        
        # Expand to fill available space like calendar does
        self.set_halign(Gtk.Align.FILL)
        self.set_hexpand(True)
        self.set_valign(Gtk.Align.FILL)
        self.set_vexpand(True)
        
        self.widgets = kwargs.get("widgets")
        self.on_connect_callback = None
        self.on_cancel_callback = None
        self.ssid = ""
        self.bssid = ""
        
        # Back button (styled like month navigation buttons)
        self.back_button = Button(
            name="password-back-button",
            child=Label(name="password-back-label", markup=icons.chevron_left)
        )
        self.back_button.connect("clicked", self._on_back_clicked)
        
        # Header with title and back button on the right
        self.title_label = Label(name="password-title", label="Enter Password")
        
        self.header = CenterBox(
            name="password-header",
            spacing=4,
            start_children=[Box()], # Empty box to balance the layout
            center_children=[self.title_label],
            end_children=[self.back_button], # Back button on the right
        )
        
        # Network info labels - separate lines
        self.network_info_text = Label(
            name="password-network-text",
            label="Enter password for",
        )
        
        self.network_ssid_label = Label(
            name="password-network-ssid",
            label="Network Name",
        )
        
        # Password entry
        self.password_entry = Entry(
            name="password-entry",
            placeholder_text="Enter network password",
            visibility=False,
            h_expand=True,  # Expand to fill available width
        )
        self.password_entry.connect("activate", self._on_entry_activate)
        
        # Show/hide password button
        self.show_password_button = Button(
            name="show-password-button",
            child=Label(markup="👁"),
            on_clicked=self._toggle_password_visibility,
        )
        
        # Password input box
        password_box = Box(
            orientation="horizontal",
            spacing=8,
            h_expand=True,  # Expand to fill available width
            children=[self.password_entry, self.show_password_button]
        )
        
        # Action buttons
        self.cancel_button = Button(
            name="password-cancel-button",
            label="Cancel",
            on_clicked=self._on_cancel_clicked,
            h_expand=True,  # Expand to fill available width
        )
        
        self.connect_button = Button(
            name="password-connect-button",
            label="Connect",
            on_clicked=self._on_connect_clicked,
            h_expand=True,  # Expand to fill available width
        )
        
        button_box = Box(
            orientation="horizontal",
            spacing=8,
            h_expand=True,  # Expand to fill available width
            children=[self.cancel_button, self.connect_button]
        )
        
        # Main content area (styled like calendar grid area)
        content_box = Box(
            name="password-content",
            orientation="vertical",
            spacing=12,
            h_expand=True,  # Expand to fill available width
            children=[
                self.network_info_text,
                self.network_ssid_label,
                password_box,
                button_box,
            ]
        )
        
        # Add header and content (same structure as calendar)
        self.add(self.header)
        self.add(content_box)
    
    def show_for_network(self, ssid, bssid, on_connect_callback, on_cancel_callback):
        """Configure and show the password prompt for a specific network"""
        self.ssid = ssid
        self.bssid = bssid
        self.on_connect_callback = on_connect_callback
        self.on_cancel_callback = on_cancel_callback
        
        # Set the SSID on its own line
        self.network_ssid_label.set_label(ssid)
        self.password_entry.set_text("")
        self.password_entry.grab_focus()
    
    def _on_back_clicked(self, _):
        if self.on_cancel_callback:
            self.on_cancel_callback()
    
    def _on_cancel_clicked(self, _):
        if self.on_cancel_callback:
            self.on_cancel_callback()
    
    def _on_connect_clicked(self, _):
        password = self.password_entry.get_text()
        if password and self.on_connect_callback:
            self.on_connect_callback(password)
    
    def _on_entry_activate(self, _):
        # Connect when Enter is pressed in the password field
        self._on_connect_clicked(None)
    
    def _toggle_password_visibility(self, _):
        current_visibility = self.password_entry.get_visibility()
        self.password_entry.set_visibility(not current_visibility)
        
        # Update button icon
        icon = "👁" if current_visibility else "🙈"
        self.show_password_button.get_child().set_markup(icon) 