import subprocess
from pathlib import Path
import concurrent.futures

from gi.repository import GLib, Gtk # type: ignore
from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.centerbox import CenterBox
from fabric.widgets.label import Label
from gi.repository import Pango # type: ignore

import modules.icons as icons

VPN_CONFIG_DIR = Path.home() / ".config" / "YZ-Shell" / "VPN"
PREVIOUS_VPN_FILE = Path.home() / ".config" / "YZ-Shell" / "previous_vpn.txt"

executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)


def is_vpn_connected(vpn_name):
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


def get_interface_name(vpn_name):
    """Extract the interface name from a VPN name that may include subdirectories.
    WireGuard interfaces use only the filename, not the full path.
    """
    return Path(vpn_name).stem


class VpnConnectionSlot(CenterBox):
    def __init__(self, vpn_name, is_active, is_previous, on_connect, on_disconnect, **kwargs):
        super().__init__(name="wifi-ap-slot", **kwargs)  # same as Wi-Fi slot

        self.vpn_name = vpn_name
        self.is_active = is_active
        self.is_previous = is_previous
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect

        star_label = None
        if is_active:
            star_label = Label(markup="⭐", name="wifi-saved-icon")
        elif is_previous and not is_active:
            star_label = Label(markup="⭐", name="wifi-saved-icon")

        vpn_label = Label(label=vpn_name, ellipsization=Pango.EllipsizeMode.END)

        left_children = [vpn_label]
        if star_label:
            left_children.insert(0, star_label)

        left_box = Box(spacing=4, children=left_children)

        self.buttons_box = Box(spacing=4)

        if is_active:
            self.disconnect_button = Button(
                name="wifi-connect-button",  # same as Wi-Fi connect button
                label="Connected",
                sensitive=False,  # disable button like Wi-Fi connected button
                style_classes=["connected"],  # add connected style class
                on_clicked=self._on_disconnect_clicked,
            )
            self.buttons_box.add(self.disconnect_button)
        else:
            self.connect_button = Button(
                name="wifi-connect-button",
                label="Connect",
                on_clicked=self._on_connect_clicked,
            )
            self.buttons_box.add(self.connect_button)

        self.set_start_children([left_box])
        self.set_end_children([self.buttons_box])

    def _on_connect_clicked(self, _):
        self.connect_button.set_label("Connecting...")
        self.connect_button.set_sensitive(False)
        self.on_connect(self.vpn_name, self._on_connect_result)

    def _on_connect_result(self, success):
        if success:
            self.connect_button.set_label("Connected")
            self.connect_button.set_sensitive(False)
        else:
            self.connect_button.set_label("Connect")
            self.connect_button.set_sensitive(True)

    def _on_disconnect_clicked(self, _):
        self.disconnect_button.set_label("Disconnecting...")
        self.disconnect_button.set_sensitive(False)
        self.on_disconnect(self.vpn_name, self._on_disconnect_result)

    def _on_disconnect_result(self, success):
        if success:
            self.disconnect_button.set_label("Disconnected")
        else:
            self.disconnect_button.set_label("Disconnect")
            self.disconnect_button.set_sensitive(True)


class VpnConnections(Box):
    def __init__(self, widgets=None, **kwargs):
        super().__init__(
            name="vpn-connections",
            orientation=Gtk.Orientation.VERTICAL,
            spacing=4,
            h_expand=True,
            v_expand=True,
            **kwargs,
        )

        self.widgets = widgets  # Reference to Widgets instance for showing VPN prompt
        self.back_button = Button(
            name="network-back",
            child=Label(name="network-back-label", markup=icons.chevron_left),
            on_clicked=lambda *_: self.widgets.show_notifications() #type: ignore
        )

        self.refresh_button_icon = Label(name="network-refresh-label", markup=icons.reload)
        self.refresh_button = Button(
            name="network-refresh",
            child=self.refresh_button_icon,
            tooltip_text="Reload VPN files",
            on_clicked=self._load_vpn_connections
        )
        
        header_box = CenterBox(
            name="network-header",
            start_children=[self.back_button],
            center_children=[Label(name="applet-title", label="VPN Connections")],
            end_children=[Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4, children=[self.refresh_button])]
        )
        self.add(header_box)

        self.stack = Gtk.Stack()
        self.add(self.stack)

        self.vpn_list_box = Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.stack.add_named(self.vpn_list_box, "vpn_list")

        self.vpn_slots = []
        self.current_vpn = None
        self.previous_vpn = None

        self.status_label = Label(label="Loading VPN connections...", h_expand=True, halign=Gtk.Align.CENTER)
        self.vpn_list_box.add(self.status_label)

        # Pending sudo state
        self._pending_sudo_callback = None
        self._pending_sudo_vpn_name = None
        self._pending_sudo_action = None  # "up" or "down"
        self._pending_sudo_password = None

        # Pending switch state for seamless VPN switching
        self._pending_switch_target_vpn = None
        self._pending_switch_callback = None

        self._load_vpn_connections()
        self.stack.set_visible_child_name("vpn_list")

    def _clear_vpn_list(self):
        for slot in self.vpn_slots:
            slot.destroy()
        self.vpn_slots = []

    def _get_previous_connected_vpn(self):
        if PREVIOUS_VPN_FILE.exists():
            try:
                prev = PREVIOUS_VPN_FILE.read_text().strip()
                if prev:
                    return prev
            except Exception:
                pass
        return None

    def _save_previous_connected_vpn(self, vpn_name):
        try:
            if vpn_name:
                PREVIOUS_VPN_FILE.write_text(vpn_name)
            elif PREVIOUS_VPN_FILE.exists():
                PREVIOUS_VPN_FILE.unlink()
        except Exception as e:
            print(f"Failed to save previous VPN: {e}")

    def _get_current_connected_vpn(self):
        vpn_files = sorted(VPN_CONFIG_DIR.rglob("*.conf"))
        for vpn_file in vpn_files:
            # Use relative path from VPN_CONFIG_DIR to create unique name
            relative_path = vpn_file.relative_to(VPN_CONFIG_DIR)
            vpn_name = str(relative_path.with_suffix(''))  # Remove .conf extension
            interface_name = get_interface_name(vpn_name)
            if is_vpn_connected(interface_name):
                return vpn_name
        return None

    def _load_vpn_connections(self, *args):
        self.status_label.set_visible(True)
        self.status_label.set_label("Loading VPN connections...")

        self._clear_vpn_list()

        vpn_files = sorted(VPN_CONFIG_DIR.rglob("*.conf"))
        if not vpn_files:
            self.status_label.set_label(f"No WireGuard configurations found.\n\nPlace your WireGuard .conf files in:\n{VPN_CONFIG_DIR}\n(subfolders are supported)")
            self.status_label.set_visible(True)
            return

        self.current_vpn = self._get_current_connected_vpn()
        self.previous_vpn = self._get_previous_connected_vpn()

        show_previous_star = self.current_vpn is None

        for vpn_file in vpn_files:
            # Use relative path from VPN_CONFIG_DIR to create unique name
            relative_path = vpn_file.relative_to(VPN_CONFIG_DIR)
            vpn_name = str(relative_path.with_suffix(''))  # Remove .conf extension
            is_active = (vpn_name == self.current_vpn)
            is_previous = show_previous_star and (vpn_name == self.previous_vpn)

            slot = VpnConnectionSlot(
                vpn_name,
                is_active,
                is_previous,
                on_connect=self._connect_to_vpn,
                on_disconnect=self._disconnect_vpn,
            )
            self.vpn_slots.append(slot)
            self.vpn_list_box.add(slot)

        # Hide the status label after loading
        self.status_label.set_visible(False)
        if self.status_label.get_parent():
            self.vpn_list_box.remove(self.status_label)

    def _connect_to_vpn(self, vpn_name, callback):
        interface_name = get_interface_name(vpn_name)
        if is_vpn_connected(interface_name):
            self.current_vpn = vpn_name
            GLib.idle_add(self._load_vpn_connections)
            GLib.idle_add(callback, True)
            return

        # If connected to a different VPN, disconnect first with single password prompt
        if self.current_vpn and self.current_vpn != vpn_name:
            self._pending_switch_target_vpn = vpn_name
            self._pending_switch_callback = callback

            if self.widgets:
                self.widgets.show_vpn_password_prompt(
                    vpn_name,
                    self._on_sudo_password_for_switch_entered,
                )
            else:
                GLib.idle_add(callback, False)
            return

        # No VPN connected or same VPN requested, proceed normally
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

    def _on_sudo_password_for_switch_entered(self, password):
        if not password:
            # User cancelled
            if self._pending_switch_callback:
                GLib.idle_add(self._pending_switch_callback, False)
            self._clear_pending_switch()
            self._show_vpn_list()
            return

        # Save password for both disconnect and connect
        self._pending_sudo_password = password

        # Start disconnecting current VPN
        self._pending_sudo_vpn_name = self.current_vpn
        self._pending_sudo_action = "down"
        self._pending_sudo_callback = self._after_disconnect_for_switch
        self._start_wg_quick_action()

    def _after_disconnect_for_switch(self, success):
        if not success:
            # Disconnect failed, abort switch
            if self._pending_switch_callback:
                GLib.idle_add(self._pending_switch_callback, False)
            self._clear_pending_switch()
            self._show_vpn_list()
            return

        # Disconnect succeeded, now connect to target VPN
        self._pending_sudo_vpn_name = self._pending_switch_target_vpn
        self._pending_sudo_action = "up"
        self._pending_sudo_callback = self._pending_switch_callback

        # Reuse the same password
        self._start_wg_quick_action()

        # Clear switch state after starting connect
        self._clear_pending_switch()

    def _clear_pending_switch(self):
        self._pending_switch_target_vpn = None
        self._pending_switch_callback = None

    def _disconnect_vpn(self, vpn_name, callback):
        interface_name = get_interface_name(vpn_name)
        if not is_vpn_connected(interface_name):
            if self.current_vpn == vpn_name:
                self.current_vpn = None
            GLib.idle_add(self._load_vpn_connections)
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

    def _start_wg_quick_action(self):
        def task():
            return self._run_wg_quick(
                self._pending_sudo_vpn_name,
                self._pending_sudo_action,
                self._pending_sudo_password,
            )

        def done(future):
            try:
                success, output = future.result()
                print(f"wg-quick finished: success={success}, output={output!r}")
                if success:
                    if self._pending_sudo_action == "up":
                        self.previous_vpn = self.current_vpn
                        self.current_vpn = self._pending_sudo_vpn_name
                        self._save_previous_connected_vpn(self.previous_vpn)
                    elif self._pending_sudo_action == "down":
                        if self.current_vpn == self._pending_sudo_vpn_name:
                            self.previous_vpn = self.current_vpn
                            self.current_vpn = None
                            self._save_previous_connected_vpn(self.previous_vpn)

                    GLib.idle_add(self._load_vpn_connections)
                    GLib.idle_add(self._pending_sudo_callback, True)
                    GLib.idle_add(self._show_vpn_list)
                else:
                    print(f"wg-quick failed: {output}")
                    GLib.idle_add(self._pending_sudo_callback, False)
                    GLib.idle_add(self._show_vpn_list)
            except Exception as e:
                print(f"Exception in wg-quick task: {e}")
                GLib.idle_add(self._pending_sudo_callback, False)
                GLib.idle_add(self._show_vpn_list)

        future = executor.submit(task)
        future.add_done_callback(done)

    def _run_wg_quick(self, vpn_name, action, sudo_password):
        # Handle both simple names and subfolder paths
        config_path = VPN_CONFIG_DIR / f"{vpn_name}.conf"
        cmd = ["sudo", "-k", "-S", "wg-quick", action, str(config_path)]
        print(f"Running command: {' '.join(cmd)} with sudo_password={'***' if sudo_password else None}")
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
                print("Incorrect sudo password detected.")
                return False, "Incorrect sudo password"
            print(f"Command succeeded: {proc.stdout}")
            return True, proc.stdout
        except subprocess.CalledProcessError as e:
            stderr_lower = e.stderr.lower() if e.stderr else ""
            if "incorrect password" in stderr_lower or "try again" in stderr_lower:
                print("Incorrect sudo password detected in exception.")
                return False, "Incorrect sudo password"
            print(f"Command failed: {e.stderr}")
            return False, e.stderr
        except subprocess.TimeoutExpired:
            print("Command timed out")
            return False, "Command timed out"

    def _show_vpn_list(self):
        self.stack.set_visible_child(self.vpn_list_box)

    def _on_sudo_password_entered(self, password):
        if not password:
            # User cancelled
            if self._pending_sudo_callback:
                GLib.idle_add(self._pending_sudo_callback, False)
            self._pending_sudo_password = None
            self._pending_sudo_vpn_name = None
            self._pending_sudo_callback = None
            self._pending_sudo_action = None
            self._show_vpn_list()
            return

        self._pending_sudo_password = password
        self._start_wg_quick_action()
