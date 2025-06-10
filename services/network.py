from typing import Any, List, Literal

import gi
from fabric.core.service import Property, Service, Signal
from fabric.utils import bulk_connect, exec_shell_command_async
from gi.repository import Gio
from loguru import logger

try:
    gi.require_version("NM", "1.0")
    from gi.repository import NM
except ValueError:
    logger.error("Failed to start network manager")


class Wifi(Service):
    """A service to manage the wifi connection."""

    @Signal
    def changed(self) -> None: ...

    @Signal
    def enabled(self) -> bool: ...

    def __init__(self, client: NM.Client, device: NM.DeviceWifi, **kwargs):
        self._client: NM.Client = client
        self._device: NM.DeviceWifi = device
        self._ap: NM.AccessPoint | None = None
        self._ap_signal: int | None = None
        super().__init__(**kwargs)

        self._client.connect(
            "notify::wireless-enabled",
            lambda *args: self.notifier("enabled", args),
        )
        if self._device:
            bulk_connect(
                self._device,
                {
                    "notify::active-access-point": lambda *args: self._activate_ap(),
                    "access-point-added": lambda *args: self.emit("changed"),
                    "access-point-removed": lambda *args: self.emit("changed"),
                    "state-changed": lambda *args: self.ap_update(),
                },
            )
            self._activate_ap()

    def ap_update(self):
        self.emit("changed")
        for sn in [
            "enabled",
            "internet",
            "strength",
            "frequency",
            "access-points",
            "ssid",
            "state",
            "icon-name",
        ]:
            self.notify(sn)

    def _activate_ap(self):
        if self._ap:
            self._ap.disconnect(self._ap_signal)
        self._ap = self._device.get_active_access_point()
        if not self._ap:
            return

        self._ap_signal = self._ap.connect(
            "notify::strength", lambda *args: self.ap_update()
        )  # type: ignore

    def toggle_wifi(self):
        self._client.wireless_set_enabled(not self._client.wireless_get_enabled())

    # def set_active_ap(self, ap):
    #     self._device.access

    def scan(self):
        self._device.request_scan_async(
            None,
            lambda device, result: [
                device.request_scan_finish(result),
                self.emit("changed"),
            ],
        )

    def notifier(self, name: str, *args):
        self.notify(name)
        self.emit("changed")
        return

    @Property(bool, "read-write", default_value=False)
    def enabled(self) -> bool:  # type: ignore
        return bool(self._client.wireless_get_enabled())

    @enabled.setter
    def enabled(self, value: bool):
        self._client.wireless_set_enabled(value)

    @Property(int, "readable")
    def strength(self):
        return self._ap.get_strength() if self._ap else -1

    @Property(str, "readable")
    def icon_name(self):
        if not self._ap:
            return "network-wireless-disabled-symbolic"

        if self.internet == "activated":
            return {
                80: "network-wireless-signal-excellent-symbolic",
                60: "network-wireless-signal-good-symbolic",
                40: "network-wireless-signal-ok-symbolic",
                20: "network-wireless-signal-weak-symbolic",
                00: "network-wireless-signal-none-symbolic",
            }.get(
                min(80, 20 * round(self._ap.get_strength() / 20)),
                "network-wireless-no-route-symbolic",
            )
        if self.internet == "activating":
            return "network-wireless-acquiring-symbolic"

        return "network-wireless-offline-symbolic"

    @Property(int, "readable")
    def frequency(self):
        return self._ap.get_frequency() if self._ap else -1

    @Property(int, "readable")
    def internet(self):
        return {
            NM.ActiveConnectionState.ACTIVATED: "activated",
            NM.ActiveConnectionState.ACTIVATING: "activating",
            NM.ActiveConnectionState.DEACTIVATING: "deactivating",
            NM.ActiveConnectionState.DEACTIVATED: "deactivated",
        }.get(
            self._device.get_active_connection().get_state(),
            "unknown",
        )

    @Property(object, "readable")
    def access_points(self) -> List[object]:
        points: list[NM.AccessPoint] = self._device.get_access_points()

        def make_ap_dict(ap: NM.AccessPoint):
            try:
                # Check if the access point is secured
                flags = ap.get_flags()
                wpa_flags = ap.get_wpa_flags()
                rsn_flags = ap.get_rsn_flags()
                
                # Try different ways to check for privacy/security
                try:
                    is_secured = bool(wpa_flags or rsn_flags or (flags & NM.Flags80211ApFlags.PRIVACY))
                except:
                    # Fallback: just check WPA/RSN flags
                    is_secured = bool(wpa_flags or rsn_flags)
                
                return {
                    "bssid": ap.get_bssid(),
                    # "address": ap.get_
                    "last_seen": ap.get_last_seen(),
                    "ssid": NM.utils_ssid_to_utf8(ap.get_ssid().get_data())
                    if ap.get_ssid()
                    else "Unknown",
                    "active-ap": self._ap,
                    "strength": ap.get_strength(),
                    "frequency": ap.get_frequency(),
                    "secured": is_secured,
                    "flags": flags,
                    "wpa_flags": wpa_flags,
                    "rsn_flags": rsn_flags,
                    "icon-name": {
                        80: "network-wireless-signal-excellent-symbolic",
                        60: "network-wireless-signal-good-symbolic",
                        40: "network-wireless-signal-ok-symbolic",
                        20: "network-wireless-signal-weak-symbolic",
                        00: "network-wireless-signal-none-symbolic",
                    }.get(
                        min(80, 20 * round(ap.get_strength() / 20)),
                        "network-wireless-no-route-symbolic",
                    ),
                }
            except Exception as e:
                print(f"Error processing access point: {e}")
                # Return basic info if there's an error
                return {
                    "bssid": ap.get_bssid(),
                    "last_seen": ap.get_last_seen(),
                    "ssid": NM.utils_ssid_to_utf8(ap.get_ssid().get_data())
                    if ap.get_ssid()
                    else "Unknown",
                    "active-ap": self._ap,
                    "strength": ap.get_strength(),
                    "frequency": ap.get_frequency(),
                    "secured": False,  # Default to unsecured if we can't determine
                    "flags": 0,
                    "wpa_flags": 0,
                    "rsn_flags": 0,
                    "icon-name": {
                        80: "network-wireless-signal-excellent-symbolic",
                        60: "network-wireless-signal-good-symbolic",
                        40: "network-wireless-signal-ok-symbolic",
                        20: "network-wireless-signal-weak-symbolic",
                        00: "network-wireless-signal-none-symbolic",
                    }.get(
                        min(80, 20 * round(ap.get_strength() / 20)),
                        "network-wireless-no-route-symbolic",
                    ),
                }

        return list(map(make_ap_dict, points))

    @Property(str, "readable")
    def ssid(self):
        if not self._ap:
            return "Disconnected"
        ssid = self._ap.get_ssid().get_data()
        return NM.utils_ssid_to_utf8(ssid) if ssid else "Unknown"

    @Property(int, "readable")
    def state(self):
        return {
            NM.DeviceState.UNMANAGED: "unmanaged",
            NM.DeviceState.UNAVAILABLE: "unavailable",
            NM.DeviceState.DISCONNECTED: "disconnected",
            NM.DeviceState.PREPARE: "prepare",
            NM.DeviceState.CONFIG: "config",
            NM.DeviceState.NEED_AUTH: "need_auth",
            NM.DeviceState.IP_CONFIG: "ip_config",
            NM.DeviceState.IP_CHECK: "ip_check",
            NM.DeviceState.SECONDARIES: "secondaries",
            NM.DeviceState.ACTIVATED: "activated",
            NM.DeviceState.DEACTIVATING: "deactivating",
            NM.DeviceState.FAILED: "failed",
        }.get(self._device.get_state(), "unknown")


class Ethernet(Service):
    """A service to manage the ethernet connection."""

    @Signal
    def changed(self) -> None: ...

    @Signal
    def enabled(self) -> bool: ...

    @Property(int, "readable")
    def speed(self) -> int:
        return self._device.get_speed()

    @Property(str, "readable")
    def internet(self) -> str:
        return {
            NM.ActiveConnectionState.ACTIVATED: "activated",
            NM.ActiveConnectionState.ACTIVATING: "activating",
            NM.ActiveConnectionState.DEACTIVATING: "deactivating",
            NM.ActiveConnectionState.DEACTIVATED: "deactivated",
        }.get(
            self._device.get_active_connection().get_state(),
            "disconnected",
        )

    @Property(str, "readable")
    def icon_name(self) -> str:
        network = self.internet
        if network == "activated":
            return "network-wired-symbolic"

        elif network == "activating":
            return "network-wired-acquiring-symbolic"

        elif self._device.get_connectivity != NM.ConnectivityState.FULL:
            return "network-wired-no-route-symbolic"

        return "network-wired-disconnected-symbolic"

    def __init__(self, client: NM.Client, device: NM.DeviceEthernet, **kwargs) -> None:
        super().__init__(**kwargs)
        self._client: NM.Client = client
        self._device: NM.DeviceEthernet = device

        for pn in (
            "active-connection",
            "icon-name",
            "internet",
            "speed",
            "state",
        ):
            self._device.connect(f"notify::{pn}", lambda *_: self.notifier(pn))

        self._device.connect("notify::speed", lambda *_: print(_))

    def notifier(self, pn):
        self.notify(pn)
        self.emit("changed")


class NetworkClient(Service):
    """A service to manage the network connections."""

    @Signal
    def device_ready(self) -> None: ...

    def __init__(self, **kwargs):
        self._client: NM.Client | None = None
        self.wifi_device: Wifi | None = None
        self.ethernet_device: Ethernet | None = None
        super().__init__(**kwargs)
        NM.Client.new_async(
            cancellable=None,
            callback=self._init_network_client,
            **kwargs,
        )

    def _init_network_client(self, client: NM.Client, task: Gio.Task, **kwargs):
        self._client = client
        wifi_device: NM.DeviceWifi | None = self._get_device(NM.DeviceType.WIFI)  # type: ignore
        ethernet_device: NM.DeviceEthernet | None = self._get_device(
            NM.DeviceType.ETHERNET
        )

        if wifi_device:
            self.wifi_device = Wifi(self._client, wifi_device)

        if ethernet_device:
            self.ethernet_device = Ethernet(client=self._client, device=ethernet_device)

        # Always emit device-ready signal, even if no devices found
            self.emit("device-ready")
        self.notify("primary-device")

    def _get_device(self, device_type) -> Any:
        devices: List[NM.Device] = self._client.get_devices()  # type: ignore
        return next(
            (
                x
                for x in devices
                if x.get_device_type() == device_type
            ),
            None,
        )

    def _get_primary_device(self) -> Literal["wifi", "wired"] | None:
        if not self._client:
            return None
        return (
            "wifi"
            if "wireless"
            in str(self._client.get_primary_connection().get_connection_type())
            else "wired"
            if "ethernet"
            in str(self._client.get_primary_connection().get_connection_type())
            else None
        )

    def get_saved_connections(self):
        """Get list of saved WiFi connection SSIDs"""
        if not self._client:
            return []
        
        saved_connections = []
        try:
            connections = self._client.get_connections()
            for conn in connections:
                if conn.get_connection_type() == "802-11-wireless":
                    wireless_setting = conn.get_setting_wireless()
                    if wireless_setting:
                        ssid_bytes = wireless_setting.get_ssid()
                        if ssid_bytes:
                            ssid = NM.utils_ssid_to_utf8(ssid_bytes.get_data())
                            if ssid:
                                saved_connections.append(ssid)
        except Exception as e:
            print(f"Error getting saved connections: {e}")
        
        return saved_connections
    
    def is_network_saved(self, ssid):
        """Check if a network is already saved in NetworkManager"""
        saved_networks = self.get_saved_connections()
        return ssid in saved_networks
    
    def activate_saved_connection(self, ssid):
        """Try to activate a saved connection by SSID"""
        if not self._client or not self.wifi_device:
            return False
            
        try:
            connections = self._client.get_connections()
            for conn in connections:
                if conn.get_connection_type() == "802-11-wireless":
                    wireless_setting = conn.get_setting_wireless()
                    if wireless_setting:
                        ssid_bytes = wireless_setting.get_ssid()
                        if ssid_bytes:
                            saved_ssid = NM.utils_ssid_to_utf8(ssid_bytes.get_data())
                            if saved_ssid == ssid:
                                # Found the saved connection, try to activate it
                                self._client.activate_connection_async(
                                    conn, self.wifi_device._device, None, None,
                                    lambda client, result: self._on_connection_activated(client, result, ssid)
                                )
                                return True
        except Exception as e:
            print(f"Error activating saved connection: {e}")
        
        return False
    
    def _on_connection_activated(self, client, result, ssid):
        """Callback for connection activation"""
        try:
            client.activate_connection_finish(result)
            print(f"Successfully activated saved connection for {ssid}")
        except Exception as e:
            print(f"Failed to activate saved connection for {ssid}: {e}")

    def connect_wifi_bssid(self, bssid, password=None, ssid=None):
        # First, check if this is a saved network and try to activate it
        if ssid and ssid != "Unknown" and self.is_network_saved(ssid):
            print(f"Found saved connection for {ssid}, attempting to activate...")
            if self.activate_saved_connection(ssid):
                return  # Successfully started activation process
            else:
                print(f"Failed to activate saved connection, falling back to new connection")
        
        # Try connecting by SSID first (more reliable), fallback to BSSID if needed
        if ssid and ssid != "Unknown":
            # Connect by SSID (preferred method)
            if password:
                exec_shell_command_async(
                    f"nmcli device wifi connect '{ssid}' password '{password}'", 
                    lambda *args: print(f"Connection result: {args}")
                )
            else:
                exec_shell_command_async(
                    f"nmcli device wifi connect '{ssid}'", 
                    lambda *args: print(f"Connection result: {args}")
                )
        else:
            # Fallback to BSSID method
            if password:
                exec_shell_command_async(
                    f"nmcli device wifi connect {bssid} password '{password}'", 
                    lambda *args: print(f"Connection result: {args}")
                )
            else:
                exec_shell_command_async(
                    f"nmcli device wifi connect {bssid}", 
                    lambda *args: print(f"Connection result: {args}")
                )

    @Property(str, "readable")
    def primary_device(self) -> Literal["wifi", "wired"] | None:
        return self._get_primary_device()
