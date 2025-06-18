from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.label import Label
import modules.icons as icons
from fabric.widgets.centerbox import CenterBox

from modules.buttons import VpnButton
from modules.buttons import wifiButton
from modules.buttons import ethernetButton


class NetworkManager(Box):
    def __init__(self, **kwargs):
        super().__init__(
            name="applet-padding",
            orientation="v",
            spacing=10,
            h_expand=True,
            v_expand=True,
            **kwargs,
        )
        self.widgets = kwargs["widgets"]

        self.back_button = Button(
            name="bluetooth-back",
            child=Label(name="bluetooth-back-label", markup=icons.chevron_left),
            on_clicked=lambda *_: self.widgets.show_calendar(),
        )

        # Create VPN button, passing widgets for callbacks
        self.vpn_button = VpnButton(widgets=self.widgets)

        self.wifi_button = wifiButton(widgets=self.widgets)

        self.ethernet_button = ethernetButton(widgets=self.widgets)

        # Connect vpn_menu_button clicked signal properly
        self.vpn_button.vpn_menu_button.connect(
            "clicked", lambda button: self.widgets.show_vpn()
        )

        self.wifi_button.wifi_menu_button.connect(
            "clicked", lambda button: self.widgets.show_network()
        )

        self.children = [
            CenterBox(
                name="applet-header",
                start_children=self.back_button,
                center_children=Label(name="applet-title", label="Network Manager"),
            ),
            Box(
                spacing=50,
                w_expand=True,         
                orientation="vertical",
                name="applet-header",
                children=[
                    self.wifi_button,
                    self.ethernet_button,
                    self.vpn_button
                ]
            ),
        ]