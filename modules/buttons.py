import subprocess

import gi
from fabric.utils.helpers import exec_shell_command_async
from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.label import Label
from gi.repository import Gdk, GLib, Gtk # type: ignore

import config.data as data

gi.require_version('Gtk', '3.0')
import modules.icons as icons
from services.network import NetworkClient

class NetworkButton(Box):
    def __init__(self, **kwargs):
        self.widgets_instance = kwargs.pop("widgets")
        self.network_client = NetworkClient()
        self._animation_timeout_id = None
        self._animation_step = 0
        self._animation_direction = 1


        def add_hover_cursor(widget):
            widget.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
            widget.connect("enter-notify-event", lambda w, e: w.get_window().set_cursor(Gdk.Cursor.new_from_name(w.get_display(), "pointer")) if w.get_window() else None)
            widget.connect("leave-notify-event", lambda w, e: w.get_window().set_cursor(None) if w.get_window() else None)


        self.network_icon = Label(
            name="network-icon",
            markup=None,
        )
        self.network_label = Label(
            name="network-label",
            label="Wi-Fi",
            justification="left",
        )
        self.network_label_box = Box(children=[self.network_label, Box(h_expand=True)])
        self.network_ssid = Label(
            name="network-ssid",
            justification="left",
        )
        self.network_ssid_box = Box(children=[self.network_ssid, Box(h_expand=True)])
        self.network_text = Box(
            name="network-text",
            orientation="v",
            h_align="start",
            v_align="center",
            children=[self.network_label_box, self.network_ssid_box],
        )
        self.network_status_box = Box(
            h_align="start",
            v_align="center",
            spacing=10,

            children=[self.network_icon, self.network_text],
        )
        self.network_status_button = Button(
            name="network-status-button",
            h_expand=True,
            child=self.network_status_box,
            on_clicked=lambda *_: self.network_client.wifi_device.toggle_wifi() if self.network_client.wifi_device else None,
        )
        add_hover_cursor(self.network_status_button)

        # Enable events on the child box
        self.network_status_box.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        # self.network_status_box.connect("button-press-event", self._on_network_status_button_press)

        self.network_menu_label = Label(
            name="network-menu-label",
            markup=icons.chevron_right,
        )
        # Existing network_menu_button creation
        self.network_menu_button = Button(
            name="network-menu-button",
            child=self.network_menu_label,
            on_clicked=lambda *_: self.widgets_instance.show_network_manager(), #show_network
        )
        add_hover_cursor(self.network_menu_button)

        # Add right-click event handling on the arrow button
        self.network_menu_button.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        # self.network_menu_button.connect("button-press-event", self._on_network_menu_button_press)

        super().__init__(
            name="network-button",
            orientation="h",
            h_align="fill",
            v_align="fill",
            h_expand=True,
            v_expand=True,
            spacing=0,
            children=[self.network_status_button, self.network_menu_button],
        )

        self.widgets_list_internal = [self, self.network_icon, self.network_label,
                       self.network_ssid, self.network_status_button,
                       self.network_menu_button, self.network_menu_label]

        self.network_client.connect('device-ready', self._on_wifi_ready)

        GLib.idle_add(self._initial_update)

    def _initial_update(self):
        # Check if Wi-Fi device is available, if not schedule another check
        if not self.network_client.wifi_device:
            # Schedule another check in case the device isn't ready yet
            GLib.timeout_add_seconds(2, self._check_wifi_hardware_delayed)
        else:
            self.update_state()
        return False

    # def _on_network_status_button_press(self, widget, event):
    #     # Right-click is button 3
    #     if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
    #         # Show the network manager applet
    #         self.widgets_instance.show_network_manager()
    #         return True  # Stop further handling
    #     return False  # Propagate other events
    
    # def _on_network_menu_button_press(self, widget, event):
    #     if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
    #         self.widgets_instance.show_network_manager()
    #         return True  # Stop further handling
    #     return False  # Propagate other events

    def _check_wifi_hardware_delayed(self):
        """Delayed check for Wi-Fi hardware availability"""
        # Always call update_state to properly check all device combinations
        self.update_state()
        return False  # Don't repeat this timeout

    def _on_wifi_ready(self, *args):
        if self.network_client.wifi_device:
            self.network_client.wifi_device.connect('notify::enabled', self.update_state)
            self.network_client.wifi_device.connect('notify::ssid', self.update_state)
        
        # Also connect to ethernet device if available
        if self.network_client.ethernet_device:
            self.network_client.ethernet_device.connect('notify::internet', self.update_state)
        
        # Always call update_state to handle all device combinations
            self.update_state()

    def _handle_no_wifi_hardware(self):
        """Handle the case when no Wi-Fi hardware is available"""
        self.network_icon.set_markup(icons.wifi_off)
        self.network_ssid.set_label("No Wi-Fi Hardware")
        
        # Gray out the entire button
        for widget in self.widgets_list_internal:
            widget.add_style_class("disabled")
        
        # Disable the button functionality
        # self.network_status_button.set_sensitive(False)
        # self.network_menu_button.set_sensitive(False)

    def _animate_searching(self):
        """Animate wifi icon when searching for networks"""
        wifi_icons = [icons.wifi_0, icons.wifi_1, icons.wifi_2, icons.wifi_3, icons.wifi_2, icons.wifi_1]

        wifi = self.network_client.wifi_device
        if not self.network_icon or not wifi or not wifi.enabled:
            self._stop_animation()
            return False

        if wifi.state == "activated" and wifi.ssid != "Disconnected":
            self._stop_animation()
            return False

        GLib.idle_add(self.network_icon.set_markup, wifi_icons[self._animation_step])

        self._animation_step = (self._animation_step + 1) % len(wifi_icons)

        return True

    def _start_animation(self):
        if self._animation_timeout_id is None:
            self._animation_step = 0
            self._animation_direction = 1

            self._animation_timeout_id = GLib.timeout_add(500, self._animate_searching)

    def _stop_animation(self):
        if self._animation_timeout_id is not None:
            GLib.source_remove(self._animation_timeout_id)
            self._animation_timeout_id = None

    def update_state(self, *args):
        """Update the button state based on network status"""
        wifi = self.network_client.wifi_device
        ethernet = self.network_client.ethernet_device



        # Check ethernet connection first (priority over Wi-Fi)
        if ethernet and ethernet.internet == "activated":
            self._stop_animation()
            self.network_icon.set_markup(icons.world)
            self.network_label.set_label("Ethernet")
            self.network_ssid.set_label("Connected")
            
            # Remove disabled styling
            for widget in self.widgets_list_internal:
                widget.remove_style_class("disabled")
            return

        # Only show disconnected ethernet if Wi-Fi is also not connected
        # (We want to prioritize showing connected Wi-Fi over disconnected ethernet)
        if ethernet and ethernet.internet != "activated" and (not wifi or not wifi.enabled or wifi.state != "activated" or wifi.ssid == "Disconnected"):
            # Check if ethernet is available but disconnected and Wi-Fi is also not connected
            self._stop_animation()
            self.network_icon.set_markup(icons.world_off)
            self.network_label.set_label("Ethernet")
            self.network_ssid.set_label("Disconnected")
            for widget in self.widgets_list_internal:
                widget.add_style_class("disabled")
            return

        # If no Wi-Fi hardware is available, handle accordingly
        if not wifi:
            # If we get here, there's no ethernet connection and no Wi-Fi hardware
            self._stop_animation()
            self.network_icon.set_markup(icons.wifi_off)
            self.network_label.set_label("Wi-Fi")
            self.network_ssid.set_label("No Wi-Fi Hardware")
            for widget in self.widgets_list_internal:
                widget.add_style_class("disabled")
            return

        # Wi-Fi logic (when ethernet is not connected and Wi-Fi hardware exists)
        if wifi and not wifi.enabled:
            self._stop_animation()
            self.network_icon.set_markup(icons.wifi_off)
            self.network_label.set_label("Wi-Fi")
            for widget in self.widgets_list_internal:
                widget.add_style_class("disabled")
            self.network_ssid.set_label("Disabled")
            return

        # Remove disabled styling for enabled Wi-Fi
        for widget in self.widgets_list_internal:
            widget.remove_style_class("disabled")

        # Wi-Fi enabled logic
        if wifi and wifi.enabled:
            if wifi.state == "activated" and wifi.ssid != "Disconnected":
                self._stop_animation()
                self.network_label.set_label("Wi-Fi")
                self.network_ssid.set_label("Connected")

                # Set Wi-Fi icon based on signal strength, default to wifi_1 if strength unavailable
                if hasattr(wifi, 'strength') and wifi.strength > 0:
                    strength = wifi.strength
                    if strength < 25:
                        self.network_icon.set_markup(icons.wifi_0)
                    elif strength < 50:
                        self.network_icon.set_markup(icons.wifi_1)
                    elif strength < 75:
                        self.network_icon.set_markup(icons.wifi_2)
                    else:
                        self.network_icon.set_markup(icons.wifi_3)
                else:
                    # Default icon when strength is unavailable
                    self.network_icon.set_markup(icons.wifi_1)
            else:
                self.network_label.set_label("Wi-Fi")
                self.network_ssid.set_label("Enabled")
                self._start_animation()

class BluetoothButton(Box):
    def __init__(self, **kwargs):
        super().__init__(
            name="bluetooth-button",
            orientation="h",
            h_align="fill",
            v_align="fill",
            h_expand=True,
            v_expand=True,
        )
        self.widgets = kwargs["widgets"]

        self.bluetooth_icon = Label(
            name="bluetooth-icon",
            markup=icons.bluetooth,
        )
        self.bluetooth_label = Label(
            name="bluetooth-label",
            label="Bluetooth",
            justification="left",
        )
        self.bluetooth_label_box = Box(children=[self.bluetooth_label, Box(h_expand=True)])
        self.bluetooth_status_text = Label(
            name="bluetooth-status",
            label="Disabled",
            justification="left",
        )
        self.bluetooth_status_box = Box(children=[self.bluetooth_status_text, Box(h_expand=True)])
        self.bluetooth_text = Box(
            orientation="v",
            h_align="start",
            v_align="center",
            children=[self.bluetooth_label_box, self.bluetooth_status_box],
        )
        self.bluetooth_status_container = Box(
            h_align="start",
            v_align="center",
            spacing=10,
            children=[self.bluetooth_icon, self.bluetooth_text],
        )
        self.bluetooth_status_button = Button(
            name="bluetooth-status-button",
            h_expand=True,
            child=self.bluetooth_status_container,
            on_clicked=lambda *_: self._toggle_bluetooth(),
        )
        add_hover_cursor(self.bluetooth_status_button)
        self.bluetooth_menu_label = Label(
            name="bluetooth-menu-label",
            markup=icons.chevron_right,
        )
        self.bluetooth_menu_button = Button(
            name="bluetooth-menu-button",
            on_clicked=lambda *_: self.widgets.show_bluetooth(),
            child=self.bluetooth_menu_label,
        )
        add_hover_cursor(self.bluetooth_menu_button)

        self.add(self.bluetooth_status_button)
        self.add(self.bluetooth_menu_button)

        self.widgets_list_internal = [self, self.bluetooth_icon, self.bluetooth_label,
                       self.bluetooth_status_text, self.bluetooth_status_button,
                       self.bluetooth_menu_button, self.bluetooth_menu_label]

        # Initialize status tracking
        self._last_known_enabled = None
        self._status_connected = False
        
        # Check for Bluetooth hardware availability after widgets are initialized
        GLib.idle_add(self._check_bluetooth_hardware)
        
        # Set up periodic hardware check to detect dynamic changes (every 60 seconds)
        GLib.timeout_add_seconds(60, self._periodic_hardware_check)
        
        # Set up periodic status check (every 2 seconds) for real-time updates
        GLib.timeout_add_seconds(2, self._update_bluetooth_status)

    def _toggle_bluetooth(self):
        """Toggle Bluetooth power, but only if hardware is available"""
        # First check if hardware is still available
        if not self._check_system_bluetooth_hardware():
            if not hasattr(self, '_hardware_unavailable_notified'):
                self._handle_no_bluetooth_hardware()
                self._hardware_unavailable_notified = True
            return
            
        try:
            if hasattr(self.widgets, 'bluetooth'):
                self.widgets.bluetooth.toggle_power()
        except Exception:
            # Hardware not available or error occurred
            self._handle_no_bluetooth_hardware()

    def refresh_hardware_status(self):
        """Refresh the Bluetooth hardware status"""
        if self._check_system_bluetooth_hardware():
            # Hardware is available, remove disabled styling if it was applied
            for widget in self.widgets_list_internal:
                widget.remove_style_class("disabled")
            self.bluetooth_status_button.set_sensitive(True)
            self.bluetooth_menu_button.set_sensitive(True)
            self.bluetooth_icon.set_markup(icons.bluetooth)
            self._hardware_unavailable_notified = False
            # Connect to status updates if not already connected
            self._connect_to_bluetooth_status()
            # Update status immediately
            self._update_bluetooth_status()
        else:
            # No hardware available
            self._handle_no_bluetooth_hardware()

    def _check_bluetooth_hardware(self):
        """Check if Bluetooth hardware is available"""
        try:
            # Try to access the bluetooth client through the widgets hierarchy
            if (hasattr(self.widgets, 'bluetooth') and 
                hasattr(self.widgets.bluetooth, 'client')):
                
                # Check if the client has the expected properties/methods
                client = self.widgets.bluetooth.client
                if hasattr(client, 'enabled') and hasattr(client, 'toggle_power'):
                    # Hardware seems to be available
                    # Connect to status updates and update status
                    self._connect_to_bluetooth_status()
                    self._update_bluetooth_status()
                    return False
                else:
                    # Client exists but doesn't have expected properties
                    self._handle_no_bluetooth_hardware()
                    return False
            else:
                # Schedule another check in case bluetooth module isn't ready yet  
                GLib.timeout_add_seconds(3, self._check_bluetooth_hardware_delayed)
                return False
        except Exception as e:
            # Exception occurred - likely no hardware
            self._handle_no_bluetooth_hardware()
            return False

    def _check_bluetooth_hardware_delayed(self):
        """Delayed check for Bluetooth hardware availability"""
        try:
            if (hasattr(self.widgets, 'bluetooth') and 
                hasattr(self.widgets.bluetooth, 'client')):
                
                client = self.widgets.bluetooth.client
                
                # Try to access the enabled property - this will fail if no hardware
                try:
                    _ = client.enabled
                    # If we get here, hardware is available
                    # Connect to status updates and update status
                    self._connect_to_bluetooth_status()
                    self._update_bluetooth_status()
                    return False
                except Exception:
                    # Failed to access enabled property - no hardware
                    self._handle_no_bluetooth_hardware()
                    return False
            else:
                # Still no bluetooth client found after delay - try system check
                if not self._check_system_bluetooth_hardware():
                    self._handle_no_bluetooth_hardware()
                return False
        except Exception:
            # Exception occurred - try system check as fallback
            if not self._check_system_bluetooth_hardware():
                self._handle_no_bluetooth_hardware()
            return False

    def _check_system_bluetooth_hardware(self):
        """Check for Bluetooth hardware at system level"""
        try:
            import subprocess
            import os
            
            # Method 1: Check bluetoothctl list (most reliable)
            try:
                result = subprocess.run(['bluetoothctl', 'list'], 
                                      capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    # Check if any controllers are listed
                    output = result.stdout.strip()
                    if output and 'Controller' in output:
                        return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            # Method 2: Check rfkill list bluetooth
            try:
                result = subprocess.run(['rfkill', 'list', 'bluetooth'], 
                                      capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    output = result.stdout.strip()
                    # Check if any bluetooth devices are listed
                    if output and ': Bluetooth' in output:
                        return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            # Method 3: Check hciconfig for active controllers
            try:
                result = subprocess.run(['hciconfig'], 
                                      capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    output = result.stdout.strip()
                    # Only return True if we see actual controller info, not just "hci"
                    if output and 'BD Address' in output:
                        return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            # Method 4: Check /sys/class/bluetooth for actual devices
            try:
                bt_path = '/sys/class/bluetooth'
                if os.path.exists(bt_path):
                    devices = os.listdir(bt_path)
                    # Filter out just directories that look like bluetooth controllers
                    bt_controllers = [d for d in devices if d.startswith('hci')]
                    if bt_controllers:
                        # Check if any controller is actually functional
                        for controller in bt_controllers:
                            ctrl_path = os.path.join(bt_path, controller)
                            if os.path.exists(os.path.join(ctrl_path, 'address')):
                                return True
            except Exception:
                pass
            
            # Method 5: Check systemctl status bluetooth
            try:
                result = subprocess.run(['systemctl', 'is-active', 'bluetooth'], 
                                      capture_output=True, text=True, timeout=3)
                if result.returncode == 0 and result.stdout.strip() == 'active':
                    # Bluetooth service is active, but we need to verify hardware
                    # Try to get adapter info via dbus
                    try:
                        result = subprocess.run(['dbus-send', '--system', '--print-reply', 
                                               '--dest=org.bluez', '/', 
                                               'org.freedesktop.DBus.ObjectManager.GetManagedObjects'], 
                                              capture_output=True, text=True, timeout=3)
                        if result.returncode == 0 and 'adapter' in result.stdout.lower():
                            return True
                    except (subprocess.TimeoutExpired, FileNotFoundError):
                        pass
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            return False
        except Exception:
            # If all checks fail, assume no hardware
            return False

    def _handle_no_bluetooth_hardware(self):
        """Handle the case when no Bluetooth hardware is available"""
        self.bluetooth_icon.set_markup(icons.bluetooth_off)
        self.bluetooth_status_text.set_label("No Bluetooth Hardware")
        
        # Gray out the entire button
        for widget in self.widgets_list_internal:
            widget.add_style_class("disabled")
        
        # Disable the button functionality
        self.bluetooth_status_button.set_sensitive(False)
        self.bluetooth_menu_button.set_sensitive(False)
        
        # Reset status connection state
        self._status_connected = False
        self._last_known_enabled = None

    def _connect_to_bluetooth_status(self):
        """Connect to bluetooth client status updates"""
        if self._status_connected:
            return
            
        try:
            if (hasattr(self.widgets, 'bluetooth') and 
                hasattr(self.widgets.bluetooth, 'client') and
                hasattr(self.widgets.bluetooth.client, 'connect')):
                
                client = self.widgets.bluetooth.client
                # Connect to the enabled property changes
                client.connect('notify::enabled', self._on_bluetooth_status_changed)
                self._status_connected = True
        except Exception as e:
            # If connection fails, we'll rely on periodic updates
            pass

    def _on_bluetooth_status_changed(self, client, param):
        """Handle bluetooth status changes"""
        GLib.idle_add(self._update_bluetooth_status)

    def _update_bluetooth_status(self):
        """Update bluetooth status display"""
        try:
            if (hasattr(self.widgets, 'bluetooth') and 
                hasattr(self.widgets.bluetooth, 'client')):
                
                client = self.widgets.bluetooth.client
                
                # Check if we can access the enabled property
                try:
                    enabled = client.enabled
                    
                    # Only update if status actually changed
                    if self._last_known_enabled != enabled:
                        self._last_known_enabled = enabled
                        
                        if enabled:
                            self.bluetooth_status_text.set_label("Enabled")
                            self.bluetooth_icon.set_markup(icons.bluetooth)
                            for widget in self.widgets_list_internal:
                                widget.remove_style_class("disabled")
                        else:
                            self.bluetooth_status_text.set_label("Disabled")
                            self.bluetooth_icon.set_markup(icons.bluetooth_off)
                            for widget in self.widgets_list_internal:
                                widget.add_style_class("disabled")
                except Exception:
                    # Failed to access enabled property - might be hardware issue
                    if not self._check_system_bluetooth_hardware():
                        self._handle_no_bluetooth_hardware()
            else:
                # No bluetooth client available yet
                if not self._check_system_bluetooth_hardware():
                    self._handle_no_bluetooth_hardware()
        except Exception:
            # If all fails, fall back to system check
            if not self._check_system_bluetooth_hardware():
                self._handle_no_bluetooth_hardware()
        
        return True  # Continue periodic updates

    def _periodic_hardware_check(self):
        """Periodic hardware check to detect dynamic changes"""
        self.refresh_hardware_status()
        return True  # Repeat the check every 60 seconds

class NightModeButton(Button):
    def __init__(self):
        self.night_mode_icon = Label(
            name="night-mode-icon",
            markup=icons.night,
        )
        self.night_mode_label = Label(
            name="night-mode-label",
            label="Night Mode",
            justification="left",
        )
        self.night_mode_label_box = Box(children=[self.night_mode_label, Box(h_expand=True)])
        self.night_mode_status = Label(
            name="night-mode-status",
            label="Enabled",
            justification="left",
        )
        self.night_mode_status_box = Box(children=[self.night_mode_status, Box(h_expand=True)])
        self.night_mode_text = Box(
            name="night-mode-text",
            orientation="v",
            h_align="start",
            v_align="center",
            children=[self.night_mode_label_box, self.night_mode_status_box],
        )
        self.night_mode_box = Box(
            h_align="start",
            v_align="center",
            spacing=10,
            children=[self.night_mode_icon, self.night_mode_text],
        )

        super().__init__(
            name="night-mode-button",
            h_expand=True,
            child=self.night_mode_box,
            on_clicked=self.toggle_hyprsunset,
        )
        add_hover_cursor(self)

        self.widgets = [self, self.night_mode_label, self.night_mode_status, self.night_mode_icon]
        self.check_hyprsunset()

    def toggle_hyprsunset(self, *args):
        """
        Toggle the 'hyprsunset' process:
          - If running, kill it and mark as 'Disabled'.
          - If not running, start it and mark as 'Enabled'.
        """
        GLib.Thread.new("hyprsunset-toggle", self._toggle_hyprsunset_thread, None)
    
    def _toggle_hyprsunset_thread(self, user_data):
        """Background thread to check and toggle hyprsunset without blocking UI."""
        try:
            subprocess.check_output(["pgrep", "hyprsunset"])
            exec_shell_command_async("pkill hyprsunset")
            GLib.idle_add(self.night_mode_status.set_label, "Disabled")
            GLib.idle_add(self._add_disabled_style)
        except subprocess.CalledProcessError:
            exec_shell_command_async("hyprsunset -t 3500")
            GLib.idle_add(self.night_mode_status.set_label, "Enabled")
            GLib.idle_add(self._remove_disabled_style)
    
    def _add_disabled_style(self):
        """Helper to add disabled style to all widgets."""
        for widget in self.widgets:
            widget.add_style_class("disabled")
    
    def _remove_disabled_style(self):
        """Helper to remove disabled style from all widgets."""
        for widget in self.widgets:
            widget.remove_style_class("disabled")

    def check_hyprsunset(self, *args):
        """
        Update the button state based on whether hyprsunset is running.
        """
        GLib.Thread.new("hyprsunset-check", self._check_hyprsunset_thread, None)
    
    def _check_hyprsunset_thread(self, user_data):
        """Background thread to check hyprsunset status without blocking UI."""
        try:
            subprocess.check_output(["pgrep", "hyprsunset"])
            GLib.idle_add(self.night_mode_status.set_label, "Enabled")
            GLib.idle_add(self._remove_disabled_style)
        except subprocess.CalledProcessError:
            GLib.idle_add(self.night_mode_status.set_label, "Disabled")
            GLib.idle_add(self._add_disabled_style)

class CaffeineButton(Button):
    def __init__(self):
        self.caffeine_icon = Label(
            name="caffeine-icon",
            markup=icons.coffee,
        )
        self.caffeine_label = Label(
            name="caffeine-label",
            label="Caffeine",
            justification="left",
        )
        self.caffeine_label_box = Box(children=[self.caffeine_label, Box(h_expand=True)])
        self.caffeine_status = Label(
            name="caffeine-status",
            label="Enabled",
            justification="left",
        )
        self.caffeine_status_box = Box(children=[self.caffeine_status, Box(h_expand=True)])
        self.caffeine_text = Box(
            name="caffeine-text",
            orientation="v",
            h_align="start",
            v_align="center",
            children=[self.caffeine_label_box, self.caffeine_status_box],
        )
        self.caffeine_box = Box(
            h_align="start",
            v_align="center",
            spacing=10,
            children=[self.caffeine_icon, self.caffeine_text],
        )
        super().__init__(
            name="caffeine-button",
            h_expand=True,
            child=self.caffeine_box,
            on_clicked=self.toggle_inhibit,
        )
        add_hover_cursor(self)

        self.widgets = [self, self.caffeine_label, self.caffeine_status, self.caffeine_icon]
        self.check_inhibit()

    def toggle_inhibit(self, *args, external=False):
        """
        Toggle the 'yz-inhibit' process:
          - If running, kill it and mark as 'Disabled' (add 'disabled' class).
          - If not running, start it and mark as 'Enabled' (remove 'disabled' class).
        """
        GLib.Thread.new("caffeine-toggle", self._toggle_inhibit_thread, external)
    
    def _toggle_inhibit_thread(self, external):
        """Background thread to toggle inhibit without blocking UI."""
        try:
            subprocess.check_output(["pgrep", "yz-inhibit"])
            exec_shell_command_async("pkill yz-inhibit")
            GLib.idle_add(self.caffeine_status.set_label, "Disabled")
            GLib.idle_add(self._add_disabled_style)
        except subprocess.CalledProcessError:
            exec_shell_command_async(f"python {data.HOME_DIR}/.config/{data.APP_NAME_CAP}/scripts/inhibit.py")
            GLib.idle_add(self.caffeine_status.set_label, "Enabled")
            GLib.idle_add(self._remove_disabled_style)

        if external:
            # Different if enabled or disabled
            status = "Disabled" if self.caffeine_status.get_label() == "Disabled" else "Enabled"
            message = "Disabled 💤" if status == "Disabled" else "Enabled ☀️"
            exec_shell_command_async(f"notify-send '☕ Caffeine' '{message}' -a '{data.APP_NAME_CAP}' -e")
    
    def _add_disabled_style(self):
        """Helper to add disabled style to all widgets."""
        for widget in self.widgets:
            widget.add_style_class("disabled")
    
    def _remove_disabled_style(self):
        """Helper to remove disabled style from all widgets."""
        for widget in self.widgets:
            widget.remove_style_class("disabled")

    def check_inhibit(self, *args):
        GLib.Thread.new("caffeine-check", self._check_inhibit_thread, None)
    
    def _check_inhibit_thread(self, user_data):
        """Background thread to check inhibit status without blocking UI."""
        try:
            subprocess.check_output(["pgrep", "yz-inhibit"])
            GLib.idle_add(self.caffeine_status.set_label, "Enabled")
            GLib.idle_add(self._remove_disabled_style)
        except subprocess.CalledProcessError:
            GLib.idle_add(self.caffeine_status.set_label, "Disabled")
            GLib.idle_add(self._add_disabled_style)

def add_hover_cursor(widget):
    widget.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
    widget.connect(
        "enter-notify-event",
        lambda w, e: w.get_window().set_cursor(Gdk.Cursor.new_from_name(w.get_display(), "pointer")) if w.get_window() else None,
    )
    widget.connect(
        "leave-notify-event",
        lambda w, e: w.get_window().set_cursor(None) if w.get_window() else None,
    )

class wifiButton(Box):
    def __init__(self, **kwargs):
        super().__init__(
            name="network-manager-button",
            orientation="h",
            h_expand=True,
            v_expand=True,
            spacing=0,
        )

        self.widgets = kwargs["widgets"]
        self.network_client = NetworkClient()

        self.wifi_icon = Label(
            name="network-manager-icon",
            markup=icons.wifi_off,
        )
        self.wifi_label = Label(
            name="network-manager-label",
            label="Wi-Fi",
            justification="left",
        )
        self.wifi_label_box = Box(children=[self.wifi_label, Box(h_expand=True)])

        self.wifi_status = Label(
            name="network-manager-status",
            label="Initializing...",
            justification="left",
        )
        self.wifi_status_box = Box(children=[self.wifi_status, Box(h_expand=True)])

        self.wifi_text = Box(
            name="network-manager-text",
            orientation="v",
            h_align="start",
            v_align="center",
            children=[self.wifi_label_box, self.wifi_status_box],
        )

        self.wifi_status_button = Button(
            name="network-manager-status-button",
            h_expand=True,
            child=Box(
                orientation="h",
                spacing=6,
                children=[self.wifi_icon, self.wifi_text],
            ),
            on_clicked=self.toggle_wifi,
        )
        add_hover_cursor(self.wifi_status_button)

        self.wifi_menu_label = Label(
            name="network-manager-menu-label",
            markup=icons.chevron_right,
        )
        self.wifi_menu_button = Button(
            name="network-manager-menu-button",
            child=self.wifi_menu_label,
        )
        add_hover_cursor(self.wifi_menu_button)

        # Pack buttons into the box
        self.pack_start(self.wifi_status_button, True, True, 0)
        self.pack_start(self.wifi_menu_button, False, False, 0)

        # Initialize widgets list for styling
        self.widgets_list = [
            self,
            self.wifi_icon,
            self.wifi_label,
            self.wifi_status,
            self.wifi_status_button,
            self.wifi_menu_button,
            self.wifi_menu_label,
        ]

        # Set up network monitoring
        self.network_client.connect("device-ready", self._on_device_ready)
        GLib.idle_add(self.check_wifi)

    def _on_device_ready(self, *args):
        if self.network_client.wifi_device:
            self.network_client.wifi_device.connect('notify::enabled', self.check_wifi)
            self.network_client.wifi_device.connect('notify::ssid', self.check_wifi)
            self.network_client.wifi_device.connect('changed', self.check_wifi)
        self.check_wifi()

    def toggle_wifi(self, *args):
        if self.network_client.wifi_device:
            self.network_client.wifi_device.toggle_wifi()
            # Give a short delay before updating status
            GLib.timeout_add(500, self.check_wifi)

    def check_wifi(self, *args):
        if not self.network_client.wifi_device:
            self.wifi_status.set_label("No Hardware")
            self.wifi_icon.set_markup(icons.wifi_off)
            for w in self.widgets_list:
                w.add_style_class("disabled")
            return

        wifi = self.network_client.wifi_device
        
        if not wifi.enabled:
            self.wifi_status.set_label("Disabled")
            self.wifi_icon.set_markup(icons.wifi_off)
            for w in self.widgets_list:
                w.add_style_class("disabled")
        elif wifi.state == "activated" and wifi.ssid != "Disconnected":
            self.wifi_status.set_label(wifi.ssid)
            
            # Set Wi-Fi icon based on signal strength
            if wifi.strength > 0:
                strength = wifi.strength
                if strength < 25:
                    self.wifi_icon.set_markup(icons.wifi_0)
                elif strength < 50:
                    self.wifi_icon.set_markup(icons.wifi_1)
                elif strength < 75:
                    self.wifi_icon.set_markup(icons.wifi_2)
                else:
                    self.wifi_icon.set_markup(icons.wifi_3)
                
            for w in self.widgets_list:
                w.remove_style_class("disabled")
        elif wifi.enabled:
            self.wifi_status.set_label("Enabled")
            self.wifi_icon.set_markup(icons.wifi_1)
            for w in self.widgets_list:
                w.remove_style_class("disabled")
        else:
            self.wifi_status.set_label("Disconnected")
            self.wifi_icon.set_markup(icons.wifi_off)
            for w in self.widgets_list:
                w.add_style_class("disabled")
        
        return False  # Don't repeat if called from timeout

class ethernetButton(Box):
    def __init__(self, **kwargs):
        super().__init__(
            name="network-manager-button",
            orientation="h",
            h_expand=True,
            v_expand=True,
            spacing=0,
        )
        self.add_style_class("ethernet-button")

        self.widgets = kwargs["widgets"]
        self.network_client = NetworkClient()

        self.ethernet_icon = Label(
            name="network-manager-icon",
            markup=icons.world_off,
        )
        self.ethernet_label = Label(
            name="network-manager-label",
            label="Ethernet",
            justification="left",
        )
        self.ethernet_label_box = Box(children=[self.ethernet_label, Box(h_expand=True)])

        self.ethernet_status = Label(
            name="network-manager-status",
            label="Initializing...",
            justification="left",
        )
        self.ethernet_status_box = Box(children=[self.ethernet_status, Box(h_expand=True)])

        self.ethernet_text = Box(
            name="network-manager-text",
            orientation="v",
            h_align="start",
            v_align="center",
            children=[self.ethernet_label_box, self.ethernet_status_box],
        )

        self.ethernet_status_button = Button(
            name="network-manager-status-button",
            h_expand=True,
            child=Box(
                orientation="h",
                spacing=6,
                children=[self.ethernet_icon, self.ethernet_text],
            ),
            on_clicked=self.toggle_ethernet,
        )
        add_hover_cursor(self.ethernet_status_button)

        # Pack buttons into the box
        self.pack_start(self.ethernet_status_button, True, True, 0)

        # Initialize widgets list for styling
        self.widgets_list = [
            self,
            self.ethernet_icon,
            self.ethernet_label,
            self.ethernet_status,
            self.ethernet_status_button,
        ]

        # Set up network monitoring
        self.network_client.connect("device-ready", self._on_device_ready)
        GLib.idle_add(self.check_ethernet)
        
        # Periodic check every 3 seconds to ensure state stays current
        GLib.timeout_add_seconds(3, self.check_ethernet)

    def _on_device_ready(self, *args):
        if self.network_client.ethernet_device:
            self.network_client.ethernet_device.connect('changed', self.check_ethernet)
        self.check_ethernet()

    def toggle_ethernet(self, *args):
        # Ethernet can't really be toggled like Wi-Fi, so just refresh status
        # In a future version, this could open ethernet settings or try to reconnect
        self.check_ethernet()

    def check_ethernet(self, *args):
        if not self.network_client.ethernet_device:
            self.ethernet_status.set_label("No Hardware")
            self.ethernet_icon.set_markup(icons.world_off)
            for w in self.widgets_list:
                w.add_style_class("disabled")
            return True  # Continue periodic checks

        ethernet = self.network_client.ethernet_device
        
        if ethernet.internet == "activated":
            self.ethernet_status.set_label("Connected")
            self.ethernet_icon.set_markup(icons.world)
            for w in self.widgets_list:
                w.remove_style_class("disabled")
        elif ethernet.internet == "activating":
            self.ethernet_status.set_label("Connecting...")
            self.ethernet_icon.set_markup(icons.world)
            for w in self.widgets_list:
                w.remove_style_class("disabled")
        else:
            self.ethernet_status.set_label("Disconnected")
            self.ethernet_icon.set_markup(icons.world_off)
            for w in self.widgets_list:
                w.add_style_class("disabled")
        
        return True  # Continue periodic checks

class VpnButton(Box):
    def __init__(self, **kwargs):
        import subprocess
        import concurrent.futures
        from pathlib import Path
        
        super().__init__(
            name="network-manager-button",
            orientation="h",
            h_expand=True,
            v_expand=True,
            spacing=0,
        )

        self.widgets = kwargs["widgets"]
        self.current_vpn_name = None
        self.previous_vpn_name = None
        
        # VPN system constants (same as vpn_connections.py)
        self.VPN_CONFIG_DIR = Path.home() / ".config" / "YZ-Shell" / "VPN"
        self.PREVIOUS_VPN_FILE = Path.home() / ".config" / "YZ-Shell" / "previous_vpn.txt"
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        
        # Pending sudo state
        self._pending_sudo_callback = None
        self._pending_sudo_vpn_name = None
        self._pending_sudo_action = None  # "up" or "down"
        self._pending_sudo_password = None

        self.vpn_icon = Label(
            name="network-manager-icon",
            markup=icons.vpnOff,
        )
        self.vpn_label = Label(
            name="network-manager-label",
            label="VPN",
            justification="left",
        )
        self.vpn_label_box = Box(children=[self.vpn_label, Box(h_expand=True)])

        self.vpn_status = Label(
            name="network-manager-status",
            label="Checking...",
            justification="left",
        )
        self.vpn_status_box = Box(children=[self.vpn_status, Box(h_expand=True)])

        self.vpn_text = Box(
            name="network-manager-text",
            orientation="v",
            h_align="start",
            v_align="center",
            children=[self.vpn_label_box, self.vpn_status_box],
        )

        self.vpn_status_button = Button(
            name="network-manager-status-button",
            h_expand=True,
            child=Box(
                orientation="h",
                spacing=6,
                children=[self.vpn_icon, self.vpn_text],
            ),
            on_clicked=self.toggle_vpn,
            tooltip_text="Click to connect to previous VPN or disconnect current VPN",
        )
        add_hover_cursor(self.vpn_status_button)

        self.vpn_menu_label = Label(
            name="network-manager-menu-label",
            markup=icons.chevron_right,
        )
        self.vpn_menu_button = Button(
            name="network-manager-menu-button",
            child=self.vpn_menu_label,
        )
        add_hover_cursor(self.vpn_menu_button)

        # Pack buttons into the box
        self.pack_start(self.vpn_status_button, True, True, 0)
        self.pack_start(self.vpn_menu_button, False, False, 0)

        # Initialize widgets list for styling
        self.widgets_list = [
            self,
            self.vpn_icon,
            self.vpn_label,
            self.vpn_status,
            self.vpn_status_button,
            self.vpn_menu_button,
            self.vpn_menu_label,
        ]

        # Initial VPN state check
        GLib.idle_add(self.check_vpn)
        # Periodic check every 10 seconds
        GLib.timeout_add_seconds(10, self.check_vpn)

    def is_vpn_connected(self, vpn_name):
        """Check if a specific VPN is connected using wireguard"""
        try:
            result = subprocess.run(
                ["wg", "show", "interfaces"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            interfaces = result.stdout.strip().split()
            return vpn_name in interfaces
        except subprocess.CalledProcessError:
            return False

    def get_previous_connected_vpn(self):
        """Get the previously connected VPN from file"""
        if self.PREVIOUS_VPN_FILE.exists():
            try:
                prev = self.PREVIOUS_VPN_FILE.read_text().strip()
                if prev:
                    return prev
            except Exception:
                pass
        return None

    def save_previous_connected_vpn(self, vpn_name):
        """Save the previous VPN to file"""
        try:
            if vpn_name:
                self.PREVIOUS_VPN_FILE.write_text(vpn_name)
            elif self.PREVIOUS_VPN_FILE.exists():
                self.PREVIOUS_VPN_FILE.unlink()
        except Exception as e:
            print(f"Failed to save previous VPN: {e}")

    def get_interface_name(self, vpn_name):
        """Extract the interface name from a VPN name that may include subdirectories.
        WireGuard interfaces use only the filename, not the full path.
        """
        from pathlib import Path
        return Path(vpn_name).stem

    def get_current_connected_vpn(self):
        """Get the currently connected VPN"""
        if not self.VPN_CONFIG_DIR.exists():
            return None
        vpn_files = sorted(self.VPN_CONFIG_DIR.rglob("*.conf"))
        for vpn_file in vpn_files:
            # Use relative path from VPN_CONFIG_DIR to create unique name
            relative_path = vpn_file.relative_to(self.VPN_CONFIG_DIR)
            vpn_name = str(relative_path.with_suffix(''))  # Remove .conf extension
            interface_name = self.get_interface_name(vpn_name)
            if self.is_vpn_connected(interface_name):
                return vpn_name
        return None

    def get_available_vpns(self):
        """Get list of available VPN configurations"""
        if not self.VPN_CONFIG_DIR.exists():
            return []
        vpn_files = sorted(self.VPN_CONFIG_DIR.rglob("*.conf"))
        vpn_names = []
        for vpn_file in vpn_files:
            # Use relative path from VPN_CONFIG_DIR to create unique name
            relative_path = vpn_file.relative_to(self.VPN_CONFIG_DIR)
            vpn_name = str(relative_path.with_suffix(''))  # Remove .conf extension
            vpn_names.append(vpn_name)
        return vpn_names

    def toggle_vpn(self, *args):
        """Handle VPN button click - connect to previous VPN or disconnect current"""
        current_vpn = self.get_current_connected_vpn()
        
        if current_vpn:
            # Disconnect current VPN
            self.vpn_status.set_label("Disconnecting...")
            self._disconnect_vpn(current_vpn, self._on_disconnect_result)
        else:
            # Connect to previous VPN if available
            previous_vpn = self.get_previous_connected_vpn()
            available_vpns = self.get_available_vpns()
            
            if previous_vpn and previous_vpn in available_vpns:
                # Connect to previous VPN
                self.vpn_status.set_label("Connecting...")
                self._connect_to_vpn(previous_vpn, self._on_connect_result)
            elif available_vpns:
                # Connect to first available VPN if no previous
                self.vpn_status.set_label("Connecting...")
                self._connect_to_vpn(available_vpns[0], self._on_connect_result)
            else:
                # No VPNs available
                self.vpn_status.set_label("No VPNs")

    def _connect_to_vpn(self, vpn_name, callback):
        """Connect to a VPN with sudo password prompt"""
        interface_name = self.get_interface_name(vpn_name)
        if self.is_vpn_connected(interface_name):
            GLib.idle_add(callback, True)
            return

        self._pending_sudo_vpn_name = vpn_name
        self._pending_sudo_callback = callback
        self._pending_sudo_action = "up"
        self._pending_sudo_password = None

        if self.widgets:
            self.widgets.show_vpn_password_prompt(
                vpn_name,
                self._on_sudo_password_entered,
            )
        else:
            GLib.idle_add(callback, False)

    def _disconnect_vpn(self, vpn_name, callback):
        """Disconnect from a VPN with sudo password prompt"""
        interface_name = self.get_interface_name(vpn_name)
        if not self.is_vpn_connected(interface_name):
            GLib.idle_add(callback, True)
            return

        self._pending_sudo_vpn_name = vpn_name
        self._pending_sudo_callback = callback
        self._pending_sudo_action = "down"
        self._pending_sudo_password = None

        if self.widgets:
            self.widgets.show_vpn_password_prompt(
                vpn_name,
                self._on_sudo_password_entered,
            )
        else:
            GLib.idle_add(callback, False)

    def _on_sudo_password_entered(self, password):
        """Handle sudo password entry"""
        if not password:
            # User cancelled
            if self._pending_sudo_callback:
                GLib.idle_add(self._pending_sudo_callback, False)
            self._clear_pending_sudo()
            GLib.idle_add(self.check_vpn)
            return

        self._pending_sudo_password = password
        self._start_wg_quick_action()

    def _start_wg_quick_action(self):
        """Start the wg-quick action in background thread"""
        def task():
            return self._run_wg_quick(
                self._pending_sudo_vpn_name,
                self._pending_sudo_action,
                self._pending_sudo_password,
            )

        def done(future):
            try:
                success, output = future.result()
                if success:
                    if self._pending_sudo_action == "up":
                        self.save_previous_connected_vpn(self._pending_sudo_vpn_name)
                    elif self._pending_sudo_action == "down":
                        self.save_previous_connected_vpn(self._pending_sudo_vpn_name)

                    GLib.idle_add(self._pending_sudo_callback, True)
                    GLib.idle_add(self.check_vpn)
                else:
                    GLib.idle_add(self._pending_sudo_callback, False)
                    GLib.idle_add(self.check_vpn)
            except Exception as e:
                print(f"Exception in wg-quick task: {e}")
                GLib.idle_add(self._pending_sudo_callback, False)
                GLib.idle_add(self.check_vpn)
            finally:
                self._clear_pending_sudo()

        future = self.executor.submit(task)
        future.add_done_callback(done)

    def _run_wg_quick(self, vpn_name, action, sudo_password):
        """Run wg-quick command with sudo"""
        import subprocess
        
        # Handle both simple names and subfolder paths
        config_path = self.VPN_CONFIG_DIR / f"{vpn_name}.conf"
        cmd = ["sudo", "-k", "-S", "wg-quick", action, str(config_path)]
        
        try:
            proc = subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                input=sudo_password + "\n",
                text=True,
                timeout=15,
            )
            # Check stderr for sudo password failure messages
            stderr_lower = proc.stderr.lower()
            if "incorrect password" in stderr_lower or "try again" in stderr_lower:
                return False, "Incorrect sudo password"
            return True, proc.stdout
        except subprocess.CalledProcessError as e:
            stderr_lower = e.stderr.lower() if e.stderr else ""
            if "incorrect password" in stderr_lower or "try again" in stderr_lower:
                return False, "Incorrect sudo password"
            return False, e.stderr
        except subprocess.TimeoutExpired:
            return False, "Command timed out"

    def _clear_pending_sudo(self):
        """Clear pending sudo state"""
        self._pending_sudo_callback = None
        self._pending_sudo_vpn_name = None
        self._pending_sudo_action = None
        self._pending_sudo_password = None

    def _on_connect_result(self, success):
        """Handle connection result"""
        if success:
            GLib.idle_add(self.check_vpn)
            # Refresh VPN applet if it exists
            if hasattr(self.widgets, 'vpn_connections'):
                GLib.idle_add(self.widgets.vpn_connections._load_vpn_connections)
        else:
            self.vpn_status.set_label("Connection failed")

    def _on_disconnect_result(self, success):
        """Handle disconnection result"""
        if success:
            GLib.idle_add(self.check_vpn)
            # Refresh VPN applet if it exists
            if hasattr(self.widgets, 'vpn_connections'):
                GLib.idle_add(self.widgets.vpn_connections._load_vpn_connections)
        else:
            self.vpn_status.set_label("Disconnect failed")

    def check_vpn(self, *args):
        """Check VPN status and update UI"""
        try:
            current_vpn = self.get_current_connected_vpn()
            available_vpns = self.get_available_vpns()
            previous_vpn = self.get_previous_connected_vpn()
            
            # Check if VPN state has changed
            old_vpn_name = getattr(self, 'current_vpn_name', None)
            vpn_state_changed = False
            
            if current_vpn:
                # VPN is connected - highlight the button
                if self.current_vpn_name != current_vpn:
                    vpn_state_changed = True
                self.current_vpn_name = current_vpn
                # Show just the interface name for display, not the full path
                display_name = self.get_interface_name(current_vpn)
                self.vpn_status.set_label(f"Connected ({display_name})")
                self.vpn_icon.set_markup(icons.vpnOn)
                for w in self.widgets_list:
                    w.remove_style_class("disabled")
            elif available_vpns:
                # VPNs available but not connected - don't highlight
                if self.current_vpn_name is not None:
                    vpn_state_changed = True
                self.current_vpn_name = None
                self.vpn_status.set_label("Disconnected")
                self.vpn_icon.set_markup(icons.vpnOff)
                for w in self.widgets_list:
                    w.add_style_class("disabled")
            else:
                # No VPNs available - don't highlight
                if self.current_vpn_name is not None:
                    vpn_state_changed = True
                self.current_vpn_name = None
                self.vpn_status.set_label("No VPNs")
                self.vpn_icon.set_markup(icons.vpnOff)
                for w in self.widgets_list:
                    w.add_style_class("disabled")
            
            # Refresh VPN applet if state changed
            if vpn_state_changed and hasattr(self.widgets, 'vpn_connections'):
                GLib.idle_add(self.widgets.vpn_connections._load_vpn_connections)
                    
        except Exception as e:
            print(f"Error checking VPN status: {e}")
            self.vpn_status.set_label("Error")
            self.vpn_icon.set_markup(icons.vpnOff)
            for w in self.widgets_list:
                w.add_style_class("disabled")
        
        return True  # Continue periodic checks

class Buttons(Gtk.Grid):
    def __init__(self, **kwargs):
        super().__init__(name="buttons-grid")
        self.set_row_homogeneous(True)
        self.set_column_homogeneous(True)
        self.set_row_spacing(4)
        self.set_column_spacing(4)
        self.set_vexpand(False)

        self.widgets = kwargs["widgets"]

        self.network_button = NetworkButton(widgets=self.widgets)
        self.bluetooth_button = BluetoothButton(widgets=self.widgets)
        self.night_mode_button = NightModeButton()
        self.caffeine_button = CaffeineButton()

        if data.PANEL_THEME == "Panel" and (data.BAR_POSITION in ["Left", "Right"] or data.PANEL_POSITION in ["Start", "End"]):

            self.attach(self.network_button, 0, 0, 1, 1)
            self.attach(self.bluetooth_button, 1, 0, 1, 1)
            self.attach(self.night_mode_button, 0, 1, 1, 1)
            self.attach(self.caffeine_button, 1, 1, 1, 1)
        else:

            self.attach(self.network_button, 0, 0, 1, 1)
            self.attach(self.bluetooth_button, 1, 0, 1, 1)
            self.attach(self.night_mode_button, 2, 0, 1, 1)
            self.attach(self.caffeine_button, 3, 0, 1, 1)

        self.show_all()
