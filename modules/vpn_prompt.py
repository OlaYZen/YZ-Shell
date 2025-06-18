# vpn_prompt.py
import gi

gi.require_version("Gtk", "3.0")
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.entry import Entry
from fabric.widgets.button import Button
from fabric.widgets.centerbox import CenterBox

import modules.icons as icons

class VpnPrompt(CenterBox):
    """VPN-specific password prompt widget"""
    def __init__(self, **kwargs):
        super().__init__(
            name="vpn-prompt-padding",
            spacing=10,
            h_expand=True,
            v_expand=True,
            **kwargs,
        )
        self.widgets = kwargs.get("widgets")
        self.on_connect_callback = None
        self.vpn_name = ""

        # Back button (optional)
        self.back_button = Button(
            name="vpn-back",
            child=Label(markup=icons.chevron_left),
            on_clicked=lambda *_: self.widgets.show_network_manager(),
        )

        self.vpn_name = Label(
            name="vpn-prompt-info",
            label="VPN_NAME",
        )

        self.vpn_info_text = Label(
            name="password-network-text",
            label="Enter sudo password for",
        )

        self.password_entry = Entry(
            name="vpn-password-entry",
            h_expand=True,
        )
        self.password_entry.connect("activate", self._on_connect_clicked)

        self.show_password_button = Button(
            name="vpn-show-password-button",
            child=Label(markup="👁"),
            on_clicked=self._toggle_password_visibility,
        )

        self.cancel_button = Button(
            name="vpn-password-cancel-button",
            label="Cancel",
            on_clicked=lambda *_: self.widgets.show_network_manager(),
            h_expand=True,
        )

        self.connect_button = Button(
            name="vpn-password-connect-button",
            label="Authenticate",
            on_clicked=self._on_connect_clicked,
            h_expand=True,
        )


        self.children = [
            CenterBox(
                name="applet-header",
                start_children=self.back_button,
                center_children=Label(name="applet-title", label="Enter Password"),
            ),
            Box(
                name="password-content",
                orientation="vertical",
                spacing=12,
                h_expand=True,
                children=[
                    self.vpn_info_text,
                    self.vpn_name,

                    Box( # Password input box
                        orientation="horizontal",
                        spacing=8,
                        h_expand=True,  # Expand to fill available width
                        children=[self.password_entry, self.show_password_button]
                    ),
                    Box(
                        orientation="horizontal",
                        spacing=8,
                        h_expand=True,
                        children=[self.cancel_button, self.connect_button]
                    )
                ]     
            )
        ]

    def show_for_vpn(self, vpn_name, on_connect_callback):
        self.vpn_name.set_label(vpn_name)
        self.on_connect_callback = on_connect_callback
        
        self.password_entry.set_text("")
        self.password_entry.set_visibility(False)
        self.show_password_button.get_child().set_markup("👁")
        self.password_entry.grab_focus()

    def _on_connect_clicked(self, _=None):
        password = self.password_entry.get_text()
        if password and self.on_connect_callback:
            self.on_connect_callback(password)

    def _toggle_password_visibility(self, _):
        current = self.password_entry.get_visibility()
        self.password_entry.set_visibility(not current)
        icon = "👁" if current else "🙈"
        self.show_password_button.get_child().set_markup(icon)