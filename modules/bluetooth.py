from fabric.bluetooth import BluetoothClient, BluetoothDevice
from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.centerbox import CenterBox
from fabric.widgets.image import Image
from fabric.widgets.label import Label
from fabric.widgets.scrolledwindow import ScrolledWindow

import modules.icons as icons


class BluetoothDeviceSlot(CenterBox):
    def __init__(self, device: BluetoothDevice, **kwargs):
        super().__init__(name="bluetooth-device", **kwargs)
        self.device = device
        self.device.connect("changed", self.on_changed)
        self.device.connect(
            "notify::closed", lambda *_: self.device.closed and self.destroy()
        )

        self.connection_label = Label(name="bluetooth-connection", markup=icons.bluetooth_disconnected)
        self.connect_button = Button(
            name="bluetooth-connect",
            label="Connect",
            on_clicked=lambda *_: self.device.set_connecting(not self.device.connected),
            style_classes=["connected"] if self.device.connected else None,
        )

        self.start_children = [
            Box(
                spacing=8,
                h_expand=True,
                h_align="fill",
                children=[
                    Image(icon_name=device.icon_name + "-symbolic", size=16),
                    Label(label=device.name, h_expand=True, h_align="start", ellipsization="end"),
                    self.connection_label,
                ],
            )
        ]
        self.end_children = self.connect_button

        self.device.emit("changed")

    def on_changed(self, *_):
        self.connection_label.set_markup(
            icons.bluetooth_connected if self.device.connected else icons.bluetooth_disconnected
        )
        if self.device.connecting:
            self.connect_button.set_label(
                "Connecting..." if not self.device.connecting else "..."
            )
        else:
            self.connect_button.set_label(
                "Connect" if not self.device.connected else "Disconnect"
            )
        if self.device.connected:
            self.connect_button.add_style_class("connected")
        else:
            self.connect_button.remove_style_class("connected")
        return

class BluetoothConnections(Box):
    def __init__(self, **kwargs):
        super().__init__(
            name="bluetooth",
            spacing=4,
            orientation="vertical",
            **kwargs,
        )

        self.widgets = kwargs["widgets"]

        self.buttons = self.widgets.buttons.bluetooth_button
        self.bt_status_text = self.buttons.bluetooth_status_text
        self.bt_status_button = self.buttons.bluetooth_status_button
        self.bt_icon = self.buttons.bluetooth_icon
        self.bt_label = self.buttons.bluetooth_label
        self.bt_menu_button = self.buttons.bluetooth_menu_button
        self.bt_menu_label = self.buttons.bluetooth_menu_label

        # Try to initialize the Bluetooth client
        try:
            self.client = BluetoothClient(on_device_added=self.on_device_added)
            self.hardware_available = True
            
            # Double-check hardware availability with system-level check
            if not self._check_system_bluetooth_hardware():
                self.hardware_available = False
                self._handle_no_hardware()
                return
                
        except Exception as e:
            # Failed to initialize - check at system level
            self.client = None
            self.hardware_available = self._check_system_bluetooth_hardware()
            if not self.hardware_available:
                self._handle_no_hardware()
                return

        self.scan_label = Label(name="bluetooth-scan-label", markup=icons.radar)
        self.scan_button = Button(
            name="bluetooth-scan",
            child=self.scan_label,
            tooltip_text="Scan for Bluetooth devices",
            on_clicked=lambda *_: self.client.toggle_scan() if self.client else None
        )
        self.back_button = Button(
            name="bluetooth-back",
            child=Label(name="bluetooth-back-label", markup=icons.chevron_left),
            on_clicked=lambda *_: self.widgets.show_notifications()
        )

        if self.client:
            self.client.connect("notify::enabled", lambda *_: self.status_label())
            self.client.connect(
                "notify::scanning",
                lambda *_: self.update_scan_label()
            )

        self.paired_box = Box(spacing=2, orientation="vertical")
        self.available_box = Box(spacing=2, orientation="vertical")

        content_box = Box(spacing=4, orientation="vertical")
        content_box.add(self.paired_box)
        content_box.add(Label(name="bluetooth-section", label="Available"))
        content_box.add(self.available_box)

        self.children = [
            CenterBox(
                name="bluetooth-header",
                start_children=self.back_button,
                center_children=Label(name="applet-title", label="Bluetooth Devices"),
                end_children=self.scan_button
            ),
            ScrolledWindow(
                name="bluetooth-devices",
                min_content_size=(-1, -1),
                child=content_box,
                v_expand=True,
                propagate_width=False,
                propagate_height=False,
            ),
        ]

        if self.client:
            self.client.notify("scanning")
            self.client.notify("enabled")

    def _handle_no_hardware(self):
        """Handle the case when no Bluetooth hardware is available"""
        # Notify the button about no hardware
        if hasattr(self.buttons, '_handle_no_bluetooth_hardware'):
            self.buttons._handle_no_bluetooth_hardware()

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
            
            return False
        except Exception:
            # If all checks fail, assume no hardware
            return False

    def toggle_power(self):
        """Safely toggle Bluetooth power, handling missing hardware"""
        if self.client and self.hardware_available:
            try:
                self.client.toggle_power()
            except Exception:
                # Hardware might have been disconnected
                self.hardware_available = False
                self._handle_no_hardware()
        else:
            # No hardware available - do nothing
            pass

    def status_label(self):
        if not self.client:
            return
            
        print(self.client.enabled)
        if self.client.enabled:
            self.bt_status_text.set_label("Enabled")
            for i in [self.bt_status_button, self.bt_status_text, self.bt_icon, self.bt_label, self.bt_menu_button, self.bt_menu_label]:
                i.remove_style_class("disabled")
            self.bt_icon.set_markup(icons.bluetooth)
        else:
            self.bt_status_text.set_label("Disabled")
            for i in [self.bt_status_button, self.bt_status_text, self.bt_icon, self.bt_label, self.bt_menu_button, self.bt_menu_label]:
                i.add_style_class("disabled")
            self.bt_icon.set_markup(icons.bluetooth_off)

    def on_device_added(self, client: BluetoothClient, address: str):
        if not self.client or not (device := client.get_device(address)):
            return
        slot = BluetoothDeviceSlot(device)

        if device.paired:
            return self.paired_box.add(slot)
        return self.available_box.add(slot)

    def update_scan_label(self):
        if not self.client:
            return
            
        if self.client.scanning:
            self.scan_label.add_style_class("scanning")
            self.scan_button.add_style_class("scanning")
            self.scan_button.set_tooltip_text("Stop scanning for Bluetooth devices")
        else:
            self.scan_label.remove_style_class("scanning")
            self.scan_button.remove_style_class("scanning")
            self.scan_button.set_tooltip_text("Scan for Bluetooth devices")
