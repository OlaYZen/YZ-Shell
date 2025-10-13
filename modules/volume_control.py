import gi
import threading
import time
from typing import Dict, List, Optional

gi.require_version("Gtk", "3.0")
from fabric.utils.helpers import get_desktop_applications
from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.centerbox import CenterBox
from fabric.widgets.image import Image
from fabric.widgets.label import Label
from fabric.widgets.scale import Scale
from fabric.widgets.scrolledwindow import ScrolledWindow
from gi.repository import GLib, Gtk, Pango

import modules.icons as icons
from utils.icon_resolver import IconResolver

try:
    import pulsectl
    from pulsectl import PulseVolumeInfo
    PULSECTL_AVAILABLE = True
except ImportError:
    PULSECTL_AVAILABLE = False
    print("Warning: pulsectl library not available. Volume control will be disabled.")


class AudioStream:
    """Represents an audio stream with volume control"""
    
    def __init__(self, index: int, name: str, description: str, volume: float, muted: bool):
        self.index = index
        self.name = name
        self.description = description
        self.volume = volume
        self.muted = muted
        self.volume_percent = int(volume * 100)


class AudioController:
    """Controller for handling audio operations"""
    
    def __init__(self):
        self.running = True
        self.listeners = []
        self.update_thread = None
        self.should_update = False  # Only update when needed
        self._control_pulse = None  # Separate connection for volume control
        
    def add_listener(self, callback):
        """Add a callback function to be notified when streams are updated."""
        self.listeners.append(callback)
        
    def remove_listener(self, callback):
        """Remove a callback function."""
        if callback in self.listeners:
            self.listeners.remove(callback)
    
    def _notify_listeners(self, streams):
        """Notify all listeners that streams have been updated."""
        for callback in self.listeners:
            try:
                GLib.idle_add(callback, streams)
            except Exception as e:
                print(f"Error notifying listener: {e}")
    
    def start(self):
        """Start the audio controller"""
        if not PULSECTL_AVAILABLE:
            print("Cannot start audio controller: pulsectl not available")
            return
            
        if self.update_thread and self.update_thread.is_alive():
            return
            
        self.running = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
    
    def stop(self):
        """Stop the audio controller"""
        self.running = False
        if self._control_pulse:
            try:
                self._control_pulse.close()
            except:
                pass
            self._control_pulse = None
    
    def enable_updates(self):
        """Enable periodic updates"""
        self.should_update = True
    
    def disable_updates(self):
        """Disable periodic updates"""
        self.should_update = False
    
    def _update_loop(self):
        """Main thread loop for audio operations - using separate pulse connection"""
        pulse = None
        try:
            # Create a separate pulse connection for this thread
            pulse = pulsectl.Pulse('yz-shell-volume-control-monitor', threading_lock=True)
            
            while self.running:
                try:
                    # Only update when widget is visible
                    if self.should_update:
                        streams = self._get_streams_safe(pulse)
                        self._notify_listeners(streams)
                    time.sleep(0.5)  # Update every 0.5 seconds for better responsiveness
                except Exception as e:
                    print(f"Error updating streams: {e}")
                    time.sleep(5)  # Wait longer on error
        except Exception as e:
            print(f"Failed to connect to PipeWire: {e}")
            self._notify_listeners([])  # Notify with empty list on connection failure
        finally:
            if pulse:
                try:
                    pulse.close()
                except:
                    pass
    
    def _get_streams_safe(self, pulse_connection) -> List[AudioStream]:
        """Get all available audio streams using a specific pulse connection"""
        streams = []
        try:
            # Get sink inputs (playing audio) using the provided connection
            for sink_input in pulse_connection.sink_input_list():
                name = sink_input.proplist.get('application.name', 'Unknown App')
                description = sink_input.proplist.get('application.process.binary', 'Unknown')
                volume = sink_input.volume.value_flat
                muted = sink_input.mute
                
                streams.append(AudioStream(
                    index=sink_input.index,
                    name=name,
                    description=description,
                    volume=volume,
                    muted=muted
                ))
        except Exception as e:
            print(f"Error getting streams: {e}")
            
        return streams
    
    def get_streams(self) -> List[AudioStream]:
        """Get all available audio streams using a fresh connection"""
        try:
            # Create a fresh connection for each query to avoid threading issues
            with pulsectl.Pulse('yz-shell-volume-query', threading_lock=True) as pulse:
                return self._get_streams_safe(pulse)
        except Exception as e:
            print(f"Error getting streams: {e}")
            return []
    
    def set_volume(self, stream_index: int, volume: float):
        """Set volume for a specific stream with thread-safe connection"""
        try:
            # Validate volume range first
            if not (0.0 <= volume <= 1.0):
                return
                
            # Use a fresh connection for volume control to avoid threading issues
            with pulsectl.Pulse('yz-shell-volume-set', threading_lock=True) as pulse:
                # Get the current sink input to determine channel count
                sink_inputs = pulse.sink_input_list()
                target_input = None
                for sink_input in sink_inputs:
                    if sink_input.index == stream_index:
                        target_input = sink_input
                        break
                
                if not target_input:
                    # Stream no longer exists, silently ignore
                    return
                    
                # Create proper volume structure with correct channel count
                channel_count = len(target_input.volume.values)
                if channel_count <= 0:
                    return
                    
                volume_struct = PulseVolumeInfo(volume, channel_count)
                pulse.sink_input_volume_set(stream_index, volume_struct)
        except Exception as e:
            # Silently handle errors to prevent crashes during rapid volume changes
            pass
    
    def set_mute(self, stream_index: int, muted: bool):
        """Set mute state for a specific stream with thread-safe connection"""
        try:
            # Use a fresh connection for mute control to avoid threading issues
            with pulsectl.Pulse('yz-shell-volume-mute', threading_lock=True) as pulse:
                pulse.sink_input_mute(stream_index, muted)
        except Exception as e:
            # Silently handle errors to prevent crashes
            pass


class StreamWidget(Box):
    """Widget for controlling a single audio stream"""
    
    def __init__(self, stream: AudioStream, controller: AudioController, volume_control=None):
        super().__init__(
            name="volume-stream-slot",
            orientation="vertical",
            spacing=8,
        )
        
        self.stream = stream
        self.controller = controller
        self.volume_control = volume_control
        
        # Volume update throttling
        self._pending_volume = None
        self._volume_update_source_id = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the UI for this stream widget"""
        
        # App icon and name header
        header_box = Box(
            orientation="horizontal",
            spacing=8,
            h_expand=True
        )
        
        # Try to get app icon
        app_icon = None
        if self.volume_control:
            icon_pixbuf = self.volume_control.get_app_icon(self.stream.name, size=24)
            if icon_pixbuf:
                app_icon = Image(
                    name="volume-stream-icon",
                    pixbuf=icon_pixbuf
                )
        
        # App name and description in a vertical box
        text_box = Box(
            orientation="vertical",
            spacing=2,
            h_expand=True
        )
        
        name_label = Label(
            name="volume-stream-title",
            label=self.stream.name,
            h_align="start",
            ellipsization="end"
        )
        
        desc_label = Label(
            name="volume-stream-description",
            label=self.stream.description,
            h_align="start",
            ellipsization="end"
        )
        
        text_box.add(name_label)
        text_box.add(desc_label)
        
        # Add icon (if available) and text to header
        if app_icon:
            header_box.add(app_icon)
        header_box.add(text_box)
        
        # Volume control row
        volume_box = Box(
            orientation="horizontal",
            spacing=8,
            h_expand=True
        )
        
        volume_label = Label(
            name="volume-stream-volume-label",
            label="Volume:"
        )
        
        self.volume_slider = Scale(
            name="volume-stream-slider",
            orientation="horizontal",
            h_expand=True,
            increments=(1, 10),
            has_origin=True
        )
        # Set range and value after initialization
        self.volume_slider.set_range(0, 100)
        self.volume_slider.set_digits(0)  # No decimal places
        self.volume_slider.set_draw_value(False)  # Don't draw value on slider itself
        self.volume_slider.set_value(max(1, self.stream.volume_percent))  # Ensure minimum of 1% to avoid zero lock
        
        # Widget created successfully
        
        self.volume_value = Label(
            name="volume-stream-value",
            label=f"{self.stream.volume_percent}%"
        )
        
        volume_box.add(volume_label)
        volume_box.add(self.volume_slider)
        volume_box.add(self.volume_value)
        
        # Mute button
        self.mute_button = Button(
            name="volume-stream-mute-button",
            label="Mute" if not self.stream.muted else "Unmute",
            on_clicked=self.on_mute_clicked
        )
        
        # Connect signals
        self.volume_slider.connect("value-changed", self.on_volume_changed)
        
        # Add widgets to layout
        self.add(header_box)
        self.add(volume_box)
        self.add(self.mute_button)
    
    def on_volume_changed(self, slider):
        """Handle volume slider change with throttling to prevent crashes"""
        value = int(slider.get_value())
        self.volume_value.set_label(f"{value}%")
        
        # Store the pending volume change
        volume_float = value / 100.0
        volume_float = max(0.0, min(1.0, volume_float))
        self._pending_volume = volume_float
        
        # Throttle volume updates to prevent overwhelming PulseAudio
        if self._volume_update_source_id is None:
            self._volume_update_source_id = GLib.timeout_add(50, self._update_volume_callback)
    
    def _update_volume_callback(self):
        """Throttled volume update callback"""
        if self._pending_volume is not None:
            try:
                self.controller.set_volume(self.stream.index, self._pending_volume)
                self._pending_volume = None
            except Exception as e:
                print(f"Error updating volume: {e}")
        
        # Reset the source ID and stop the timer
        self._volume_update_source_id = None
        return False  # Don't repeat the timer
    
    def on_mute_clicked(self, button):
        """Handle mute button click"""
        muted = not self.stream.muted
        self.controller.set_mute(self.stream.index, muted)
        self.mute_button.set_label("Mute" if not muted else "Unmute")
        self.stream.muted = muted
    
    def update_stream(self, stream: AudioStream):
        """Update the widget with new stream data"""
        self.stream = stream
        
        # Block signal to prevent infinite loop during updates
        self.volume_slider.handler_block_by_func(self.on_volume_changed)
        # Ensure we don't set to exactly 0 if the stream is not muted (avoid zero lock)
        display_volume = stream.volume_percent if stream.muted else max(1, stream.volume_percent)
        self.volume_slider.set_value(float(display_volume))
        self.volume_slider.handler_unblock_by_func(self.on_volume_changed)
        
        self.volume_value.set_label(f"{stream.volume_percent}%")
        self.mute_button.set_label("Mute" if not stream.muted else "Unmute")
    
    def destroy(self):
        """Clean up when widget is destroyed"""
        # Cancel any pending volume updates
        if self._volume_update_source_id is not None:
            GLib.source_remove(self._volume_update_source_id)
            self._volume_update_source_id = None
        super().destroy()


class VolumeControl(Box):
    """Main volume control widget for individual application volumes"""
    
    def __init__(self, widgets=None, **kwargs):
        super().__init__(
            name="volume-control",
            orientation="vertical",
            spacing=4,
            h_expand=True,
            v_expand=True,
            **kwargs,
        )
        
        self.widgets = widgets  # Reference to Widgets instance
        self.audio_controller = AudioController()
        self.stream_widgets: Dict[int, StreamWidget] = {}
        self.is_visible = False
        
        # Icon resolution setup (similar to dock)
        self.icon_resolver = IconResolver()
        self._all_apps = get_desktop_applications()
        self.app_identifiers = self._build_app_identifiers_map()
        
        # Back button
        self.back_button = Button(
            name="volume-back",
            child=Label(name="volume-back-label", markup=icons.chevron_left),
            on_clicked=self._on_back_clicked
        )
        
        # Refresh button
        self.refresh_button = Button(
            name="volume-refresh",
            child=Label(name="volume-refresh-label", markup=icons.reload),
            tooltip_text="Refresh audio streams",
            on_clicked=self._manual_refresh
        )
        
        # Header
        header_box = CenterBox(
            name="volume-header",
            start_children=[self.back_button],
            center_children=[Label(name="applet-title", label="Volume Control")],
            end_children=[Box(orientation="horizontal", spacing=4, children=[self.refresh_button])]
        )
        self.add(header_box)
        
        # Status label
        self.status_label = Label(
            name="volume-status",
            label="Connecting to audio system...",
            h_align="center",
            v_align="center"
        )
        
        # Streams list container
        self.streams_list_box = Box(orientation="vertical", spacing=4)
        
        # Scrolled window for streams
        scrolled_window = ScrolledWindow(
            name="volume-streams-scrolled-window",
            child=self.streams_list_box,
            h_expand=True,
            v_expand=True,
            propagate_width=False,
            propagate_height=False,
        )
        
        # Main content stack
        self.content_stack = Gtk.Stack()
        self.content_stack.add_named(self.status_label, "status")
        self.content_stack.add_named(scrolled_window, "streams")
        
        self.add(self.content_stack)
        
        # Set up audio controller
        self.audio_controller.add_listener(self.update_streams)
        
        # Start with status view
        self.content_stack.set_visible_child_name("status")
        
        # Start audio controller when widget is realized
        self.connect("realize", lambda *_: self.audio_controller.start())
        
    def _manual_refresh(self, button):
        """Manually refresh the streams"""
        try:
            streams = self.audio_controller.get_streams()
            self.update_streams(streams)
        except Exception as e:
            print(f"Manual refresh failed: {e}")
    
    def update_streams(self, streams: List[AudioStream]):
        """Update the streams display"""
        if not PULSECTL_AVAILABLE:
            self.status_label.set_label("Audio control not available\n(pulsectl library missing)")
            self.content_stack.set_visible_child_name("status")
            return
        
        if not streams:
            self.status_label.set_label("No active audio streams found")
            self.content_stack.set_visible_child_name("status")
            # Clear widgets when no streams
            for widget in self.stream_widgets.values():
                widget.destroy()
            self.stream_widgets.clear()
            return
        
        # Get current stream indices
        current_indices = {stream.index for stream in streams}
        existing_indices = set(self.stream_widgets.keys())
        
        # Remove widgets for streams that no longer exist
        for index in existing_indices - current_indices:
            if index in self.stream_widgets:
                self.stream_widgets[index].destroy()
                del self.stream_widgets[index]
        
        # Update existing widgets and create new ones
        for stream in streams:
            if stream.index in self.stream_widgets:
                # Update existing widget
                self.stream_widgets[stream.index].update_stream(stream)
            else:
                # Create new widget with volume control reference for icon access
                widget = StreamWidget(stream, self.audio_controller, volume_control=self)
                self.stream_widgets[stream.index] = widget
                self.streams_list_box.add(widget)
                widget.show_all()
        
        # Show streams view
        self.content_stack.set_visible_child_name("streams")
    
    def _on_back_clicked(self, button):
        """Handle back button click"""
        self.hide_volume_control()
        if self.widgets:
            self.widgets.show_notifications()
    
    def show_volume_control(self):
        """Show the volume control interface"""
        self.is_visible = True
        self.audio_controller.enable_updates()
        # This method can be called when opening the volume control
        streams = self.audio_controller.get_streams()
        self.update_streams(streams)
    
    def hide_volume_control(self):
        """Hide the volume control interface and stop updates"""
        self.is_visible = False
        self.audio_controller.disable_updates()
    
    def _build_app_identifiers_map(self):
        """Build a mapping of app identifiers (class names, executables, names) to DesktopApp objects"""
        identifiers = {}
        for app in self._all_apps:
            # Map by name
            if app.name:
                identifiers[app.name.lower()] = app
                
            # Map by display name
            if app.display_name:
                identifiers[app.display_name.lower()] = app
                
            # Map by window class
            if app.window_class:
                identifiers[app.window_class.lower()] = app
                
            # Map by executable basename
            if app.executable:
                exe_basename = app.executable.split('/')[-1].lower()
                identifiers[exe_basename] = app
                
            # Map by command line basename
            if app.command_line:
                cmd_base = app.command_line.split()[0].split('/')[-1].lower()
                identifiers[cmd_base] = app
                
        return identifiers

    def find_app(self, app_name: str):
        """Find a DesktopApp object by various identifiers using the pre-built map."""
        if not app_name:
            return None
            
        # Try direct lookup first
        normalized_name = app_name.lower()
        app = self.app_identifiers.get(normalized_name)
        if app:
            return app
            
        # Try some common variations
        variations = [
            normalized_name.replace(' ', ''),  # Remove spaces
            normalized_name.replace('-', ''),  # Remove hyphens
            normalized_name.replace('_', ''),  # Remove underscores
            normalized_name.split('.')[0],     # Remove file extensions
            normalized_name.split()[0] if ' ' in normalized_name else normalized_name,  # First word only
        ]
        
        for variation in variations:
            app = self.app_identifiers.get(variation)
            if app:
                return app
                
        return None

    def get_app_icon(self, app_name: str, size: int = 24):
        """Get app icon pixbuf for the given app name"""
        if not app_name:
            return None
            
        # Find desktop app
        desktop_app = self.find_app(app_name)
        
        # Try to get icon from desktop app
        icon_pixbuf = None
        if desktop_app:
            icon_pixbuf = desktop_app.get_icon_pixbuf(size=size)
        
        # Fallback to icon resolver
        if not icon_pixbuf:
            icon_pixbuf = self.icon_resolver.get_icon_pixbuf(app_name, size)
        
        # Try some common app name variations
        if not icon_pixbuf:
            variations = [
                app_name.lower(),
                app_name.lower().replace(' ', '-'),
                app_name.lower().replace(' ', '_'),
                app_name.split()[0].lower() if ' ' in app_name else app_name.lower(),
            ]
            
            for variation in variations:
                icon_pixbuf = self.icon_resolver.get_icon_pixbuf(variation, size)
                if icon_pixbuf:
                    break
        
        # Final fallbacks
        if not icon_pixbuf:
            icon_pixbuf = self.icon_resolver.get_icon_pixbuf("application-x-executable", size)
            if not icon_pixbuf:
                icon_pixbuf = self.icon_resolver.get_icon_pixbuf("application-x-executable-symbolic", size)
                
        return icon_pixbuf

    def destroy(self):
        """Clean up when widget is destroyed"""
        if self.audio_controller:
            self.audio_controller.remove_listener(self.update_streams)
            self.audio_controller.stop()
        super().destroy()
