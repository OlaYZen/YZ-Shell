import gi

gi.require_version('Gtk', '3.0')
gi.require_version('NM', '1.0')
from fabric.utils import bulk_connect
from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.centerbox import CenterBox
from fabric.widgets.image import Image
from fabric.widgets.label import Label
from fabric.widgets.scrolledwindow import ScrolledWindow
from fabric.widgets.entry import Entry
from gi.repository import NM, GLib, Gtk

import modules.icons as icons
from services.network import NetworkClient


def group_access_points_by_ssid(access_points):
    """Group access points by SSID and return the strongest one for each network"""
    ssid_groups = {}
    
    for ap_data in access_points:
        ssid = ap_data.get("ssid", "Unknown")
        strength = ap_data.get("strength", 0)
        
        # Skip hidden networks or invalid SSIDs
        if not ssid or ssid == "Unknown" or ssid.strip() == "":
            continue
            
        # If we haven't seen this SSID before, or this one has stronger signal
        if ssid not in ssid_groups or strength > ssid_groups[ssid].get("strength", 0):
            ssid_groups[ssid] = ap_data
    
    # Return list of access points, sorted by signal strength
    unique_networks = list(ssid_groups.values())
    return sorted(unique_networks, key=lambda x: x.get("strength", 0), reverse=True)


class WifiAccessPointSlot(CenterBox):
    def __init__(self, ap_data: dict, network_service: NetworkClient, wifi_service, widgets=None, **kwargs):
        super().__init__(name="wifi-ap-slot", **kwargs)
        self.ap_data = ap_data
        self.network_service = network_service
        self.wifi_service = wifi_service
        self.widgets = widgets

        ssid = ap_data.get("ssid", "Unknown SSID")
        icon_name = ap_data.get("icon-name", "network-wireless-signal-none-symbolic")

        self.is_active = False
        active_ap_details = ap_data.get("active-ap")
        if active_ap_details and hasattr(active_ap_details, 'get_bssid') and active_ap_details.get_bssid() == ap_data.get("bssid"):
            self.is_active = True
        
        # Check if network is saved
        self.is_saved = network_service.is_network_saved(ssid) if ssid != "Unknown SSID" else False
        
        # Add lock icon for secured networks
        icons_to_add = []
        
        # Add saved network indicator
        if self.is_saved:
            icons_to_add.append(Label(markup="⭐", name="wifi-saved-icon"))
        
        # Add lock icon for secured networks
        if ap_data.get("secured", False):
            icons_to_add.append(Label(markup="🔒", name="wifi-lock-icon"))
        
        # Build the SSID box
        ssid_children = [
            Image(icon_name=icon_name, size=24),
            Label(label=ssid, ellipsization="end"),
        ]
        ssid_children.extend(icons_to_add)
        
        ssid_box = Box(spacing=4, children=ssid_children)
        
        # Determine button text and style
        if self.is_active:
            button_text = "Connected"
            button_sensitive = False
            button_classes = ["connected"]
        elif self.is_saved:
            button_text = "Connect"  # Saved networks just say "Connect"
            button_sensitive = True
            button_classes = ["saved"]
        else:
            button_text = "Connect"
            button_sensitive = True
            button_classes = None
        
        self.connect_button = Button(
            name="wifi-connect-button",
            label=button_text,
            sensitive=button_sensitive,
            on_clicked=self._on_connect_clicked,
            style_classes=button_classes,
        )

        self.set_start_children([ssid_box])
        self.set_end_children([self.connect_button])

    def _on_connect_clicked(self, _):
        if not self.is_active and self.ap_data.get("bssid"):
            self.connect_button.set_label("Connecting...")
            self.connect_button.set_sensitive(False)
            
            ssid = self.ap_data.get("ssid", "Unknown SSID")
            
            # If network is saved, try to connect directly
            if self.is_saved:
                self.network_service.connect_wifi_bssid(self.ap_data["bssid"], None, ssid)
                # Set timeout to reset button if connection fails
                GLib.timeout_add_seconds(10, self._reset_button_on_timeout)
                return
            
            # For new networks, check if secured and ask for password if needed
            if self.ap_data.get("secured", False):
                # Get the widgets instance to show password prompt
                if self.widgets and hasattr(self.widgets, 'show_password_prompt'):
                    self.widgets.show_password_prompt(ssid, self.ap_data["bssid"], self._handle_password_response)
                else:
                    # Fallback: just reset the button
                    self.connect_button.set_label("Connect")
                    self.connect_button.set_sensitive(True)
            else:
                # Open network, connect directly
                self.network_service.connect_wifi_bssid(self.ap_data["bssid"], None, ssid)
                # Set timeout to reset button if connection fails
                GLib.timeout_add_seconds(10, self._reset_button_on_timeout)

    def _reset_button_on_timeout(self):
        # Only reset if still in connecting state and not actually connected
        if self.connect_button.get_label() == "Connecting..." and not self.is_active:
            self.connect_button.set_label("Connect")
            self.connect_button.set_sensitive(True)
        return False  # Don't repeat the timeout

    def _handle_password_response(self, password):
        if password:
            ssid = self.ap_data.get("ssid", "Unknown SSID")
            self.network_service.connect_wifi_bssid(self.ap_data["bssid"], password, ssid)
            # Set timeout to reset button if connection fails
            GLib.timeout_add_seconds(10, self._reset_button_on_timeout)
        else:
            # Reset button if no password entered
            self.connect_button.set_label("Connect")
            self.connect_button.set_sensitive(True)


class NetworkConnections(Box):
    def __init__(self, **kwargs):
        super().__init__(
            name="network-connections",
            orientation="vertical",
            spacing=4,
            **kwargs,
        )
        self.widgets = kwargs.get("widgets")
        self.network_client = NetworkClient()

        self.status_label = Label(label="Initializing Wi-Fi...", h_expand=True, h_align="center")

        self.back_button = Button(
            name="network-back",
            child=Label(name="network-back-label", markup=icons.chevron_left),
            on_clicked=lambda *_: self.widgets.show_notif()
        )
        

        self.wifi_toggle_button_icon = Label(markup=icons.wifi_3)
        self.wifi_toggle_button = Button(
            name="wifi-toggle-button",
            child=self.wifi_toggle_button_icon,
            tooltip_text="Toggle Wi-Fi",
            on_clicked=self._toggle_wifi
        )
        

        self.refresh_button_icon = Label(name="network-refresh-label", markup=icons.reload)
        self.refresh_button = Button(
            name="network-refresh",
            child=self.refresh_button_icon,
            tooltip_text="Scan for Wi-Fi networks",
            on_clicked=self._refresh_access_points
        )

        header_box = CenterBox(
            name="network-header",
            start_children=[self.back_button],
            center_children=[Label(name="network-title", label="Wi-Fi Networks")],
            end_children=[Box(orientation="horizontal", spacing=4, children=[self.refresh_button])]
        )

        self.ap_list_box = Box(orientation="vertical", spacing=4)
        scrolled_window = ScrolledWindow(
            name="network-ap-scrolled-window",
            child=self.ap_list_box,
            h_expand=True,
            v_expand=True,
            propagate_width=False,
            propagate_height=False,
        )

        self.add(header_box)
        self.add(self.status_label)
        self.add(scrolled_window)

        self.network_client.connect("device-ready", self._on_device_ready)
        self.wifi_toggle_button.set_sensitive(False)
        self.refresh_button.set_sensitive(False)

    def _on_device_ready(self, _client):

        if self.network_client.wifi_device:
            self.network_client.wifi_device.connect("changed", self._load_access_points)
            self.network_client.wifi_device.connect("notify::enabled", self._update_wifi_status_ui)
            self._update_wifi_status_ui() 
            if self.network_client.wifi_device.enabled:
                self._load_access_points() 
            else:
                self.status_label.set_label("Wi-Fi disabled.")
                self.status_label.set_visible(True)
        else:
            self.status_label.set_label("Wi-Fi device not available.")
            self.status_label.set_visible(True)
            self.wifi_toggle_button.set_sensitive(False)
            self.refresh_button.set_sensitive(False)

    def _update_wifi_status_ui(self, *args):
        if self.network_client.wifi_device:
            enabled = self.network_client.wifi_device.enabled
            self.wifi_toggle_button.set_sensitive(True)
            self.refresh_button.set_sensitive(enabled)
            
            if enabled:
                self.wifi_toggle_button_icon.set_markup(icons.wifi_3)
            else:
                self.wifi_toggle_button_icon.set_markup(icons.wifi_off)
                self.status_label.set_label("Wi-Fi disabled.")
                self.status_label.set_visible(True)
                self._clear_ap_list()
            
            if enabled and not self.ap_list_box.get_children():
                GLib.idle_add(self._refresh_access_points)
        else:
            self.wifi_toggle_button.set_sensitive(False)
            self.refresh_button.set_sensitive(False)

    def _toggle_wifi(self, _):
        if self.network_client.wifi_device:
            self.network_client.wifi_device.toggle_wifi()

    def _refresh_access_points(self, _=None): 
        if self.network_client.wifi_device and self.network_client.wifi_device.enabled:
            self.status_label.set_label("Scanning for Wi-Fi networks...")
            self.status_label.set_visible(True)
            self._clear_ap_list() 
            self.network_client.wifi_device.scan() 
        return False 

    def _clear_ap_list(self):
        for child in self.ap_list_box.get_children():
            child.destroy()

    def _load_access_points(self, *args):
        if not self.network_client.wifi_device or not self.network_client.wifi_device.enabled:
            self._clear_ap_list()
            self.status_label.set_label("Wi-Fi disabled.")
            self.status_label.set_visible(True)
            return

        self._clear_ap_list()
        
        access_points = self.network_client.wifi_device.access_points
        
        if not access_points:
            self.status_label.set_label("No Wi-Fi networks found.")
            self.status_label.set_visible(True)
        else:
            self.status_label.set_visible(False) 
            # Group by SSID and show only strongest signal for each network
            unique_networks = group_access_points_by_ssid(access_points)
            for ap_data in unique_networks:
                slot = WifiAccessPointSlot(ap_data, self.network_client, self.network_client.wifi_device, widgets=self.widgets)
                self.ap_list_box.add(slot)
        self.ap_list_box.show_all()


class DashboardNetworkConnections(Box):
    """Network connections widget specifically designed for the dashboard"""
    def __init__(self, **kwargs):
        super().__init__(
            name="dashboard-network-connections",
            orientation="vertical",
            spacing=4,
            h_expand=True,
            v_expand=True,
            **kwargs,
        )
        self.network_client = NetworkClient()

        self.status_label = Label(label="Initializing Wi-Fi...", h_expand=True, h_align="center")

        self.wifi_toggle_button_icon = Label(markup=icons.wifi_3)
        self.wifi_toggle_button = Button(
            name="wifi-toggle-button",
            child=self.wifi_toggle_button_icon,
            tooltip_text="Toggle Wi-Fi",
            on_clicked=self._toggle_wifi
        )

        self.refresh_button_icon = Label(name="network-refresh-label", markup=icons.reload)
        self.refresh_button = Button(
            name="network-refresh",
            child=self.refresh_button_icon,
            tooltip_text="Scan for Wi-Fi networks",
            on_clicked=self._refresh_access_points
        )

        header_box = CenterBox(
            name="network-header",
            start_children=[Label(name="network-title", label="Wi-Fi Networks", h_expand=True, h_align="start")],
            end_children=[Box(orientation="horizontal", spacing=4, children=[
                self.wifi_toggle_button,
                self.refresh_button
            ])]
        )

        self.ap_list_box = Box(orientation="vertical", spacing=4)
        scrolled_window = ScrolledWindow(
            name="network-ap-scrolled-window",
            child=self.ap_list_box,
            h_expand=True,
            v_expand=True,
            propagate_width=False,
            propagate_height=False,
        )

        self.add(header_box)
        self.add(self.status_label)
        self.add(scrolled_window)

        self.network_client.connect("device-ready", self._on_device_ready)
        self.wifi_toggle_button.set_sensitive(False)
        self.refresh_button.set_sensitive(False)

    def _on_device_ready(self, _client):
        if self.network_client.wifi_device:
            self.network_client.wifi_device.connect("changed", self._load_access_points)
            self.network_client.wifi_device.connect("notify::enabled", self._update_wifi_status_ui)
            self._update_wifi_status_ui() 
            if self.network_client.wifi_device.enabled:
                self._load_access_points() 
            else:
                self.status_label.set_label("Wi-Fi disabled.")
                self.status_label.set_visible(True)
        else:
            self.status_label.set_label("Wi-Fi device not available.")
            self.status_label.set_visible(True)
            self.wifi_toggle_button.set_sensitive(False)
            self.refresh_button.set_sensitive(False)

    def _update_wifi_status_ui(self, *args):
        if self.network_client.wifi_device:
            enabled = self.network_client.wifi_device.enabled
            self.wifi_toggle_button.set_sensitive(True)
            self.refresh_button.set_sensitive(enabled)
            
            if enabled:
                self.wifi_toggle_button_icon.set_markup(icons.wifi_3)
            else:
                self.wifi_toggle_button_icon.set_markup(icons.wifi_off)
                self.status_label.set_label("Wi-Fi disabled.")
                self.status_label.set_visible(True)
                self._clear_ap_list()
            
            if enabled and not self.ap_list_box.get_children():
                GLib.idle_add(self._refresh_access_points)
        else:
            self.wifi_toggle_button.set_sensitive(False)
            self.refresh_button.set_sensitive(False)

    def _toggle_wifi(self, _):
        if self.network_client.wifi_device:
            self.network_client.wifi_device.toggle_wifi()

    def _refresh_access_points(self, _=None): 
        if self.network_client.wifi_device and self.network_client.wifi_device.enabled:
            self.status_label.set_label("Scanning for Wi-Fi networks...")
            self.status_label.set_visible(True)
            self._clear_ap_list() 
            self.network_client.wifi_device.scan() 
        return False 

    def _clear_ap_list(self):
        for child in self.ap_list_box.get_children():
            child.destroy()

    def _load_access_points(self, *args):
        if not self.network_client.wifi_device or not self.network_client.wifi_device.enabled:
            self._clear_ap_list()
            self.status_label.set_label("Wi-Fi disabled.")
            self.status_label.set_visible(True)
            return

        self._clear_ap_list()
        
        access_points = self.network_client.wifi_device.access_points
        
        if not access_points:
            self.status_label.set_label("No Wi-Fi networks found.")
            self.status_label.set_visible(True)
        else:
            self.status_label.set_visible(False) 
            # Group by SSID and show only strongest signal for each network
            unique_networks = group_access_points_by_ssid(access_points)
            for ap_data in unique_networks:
                slot = WifiAccessPointSlot(ap_data, self.network_client, self.network_client.wifi_device)
                self.ap_list_box.add(slot)
        self.ap_list_box.show_all()
