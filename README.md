# 🚀 YZ-Shell: Advanced Hyprland Desktop Shell

<p align="center">
  <em>Documentation images and visual assets are currently being prepared and will be added in a future update.</em>
</p>

<p align="center">
  <a href="https://github.com/hyprwm/Hyprland">
    <img src="https://img.shields.io/badge/A%20hackable%20shell%20for-Hyprland-0092CD?style=for-the-badge&logo=linux&color=0092CD&logoColor=D9E0EE&labelColor=000000" alt="A hackable shell for Hyprland">
  </a>
  <a href="https://github.com/Fabric-Development/fabric/">
    <img src="https://img.shields.io/badge/Powered%20by-Fabric-FAFAFA?style=for-the-badge&logo=python&color=FAFAFA&logoColor=D9E0EE&labelColor=000000" alt="Powered by Fabric">
  </a>
</p>

> ## ⚠️ **DISCLAIMER** ⚠️
> 
> **YZ-Shell is designed specifically for Arch Linux and requires AUR packages and Arch-specific configurations.**
>
> ✅ **SUPPORTED:**
> - Arch Linux
> - Arch-based distributions (Manjaro, EndeavourOS, etc.)
> 
> 🚫 **NOT COMPATIBLE WITH:**
> - NixOS
> - Other Linux distributions

A feature-rich, modular desktop shell for Hyprland with comprehensive functionality including application management, system monitoring, productivity tools, and seamless desktop integration.

> **Note**: This is a fork of [Ax-Shell](https://github.com/Axenide/Ax-Shell) with additional features and enhancements.

## 🔄 Fork Enhancements

This fork includes several enhancements and improvements over the original Ax-Shell:

### **⏰ Enhanced Time Display**
- **Seconds Precision**: Time display in the pill bar now shows seconds (HH:MM:SS) for improved time awareness, upgrading the original format

### **🎵 Interactive Media Controls**
- **Dynamic Playback Indicators**: Media artwork now features a rotation animation during playback and stops when paused or idle, creating a vinyl record effect that provides visual feedback for media state

### **🌤️ Extended Weather Dashboard**
- **3-Day Weather Forecast**: Dashboard now includes upcoming weather information displaying current day plus the next 2 days with temperature and condition previews, featuring current conditions and 4 daily time periods (midnight, morning, noon, evening)
- **Interactive Weather Access**: Weather pill in the bar is now clickable for direct access
- **Automatic Updates**: Weather information refreshes every 10 minutes to ensure current data

### **📊 Improved Network Metrics**
- **Standardized Speed Units**: Network speeds now display in industry-standard units (Mbps, Kbps, bps) instead of MB/s, with consistent bit-per-second (bps) notation across all network measurements

### **🌐 Enhanced Weather Service**
- **Better Weather API**: Switched from wttr.in to the Yr/Met.no weather API (run by the Norwegian Meteorological Institute) for more reliable and accurate weather data. **Fun Fact**: Jeremy Clarkson uses Yr for weather forecasts on his farm

### **📅 Interactive Date Display**
- **Multi-Format Date Switching**: Clock widget now supports instant switching between multiple formats via mouse clicks - left click toggles time/European date (DD/MM/YYYY), right click for American format (MM-DD-YYYY), and middle click for ISO format (YYYY.MM.DD), providing quick access to different date conventions

### **📡 Enhanced Network Management**
- **Smart WiFi Connection**: Automatic detection and prioritization of saved networks with one-click reconnection
- **Secure Network Authentication**: In-dashboard password prompt for protected WiFi networks with show/hide password functionality  
- **Network Hardware Detection**: Robust WiFi hardware detection with graceful fallback when no hardware is available
- **Visual Network Indicators**: Enhanced network status indicators with saved network stars (⭐) and security locks (🔒)
- **Network Grouping**: Intelligent grouping of access points by SSID, showing strongest signal for each network

### **🔵 Enhanced Bluetooth Management**
- **Multi-Level Hardware Detection**: Comprehensive Bluetooth hardware detection using multiple system checks (bluetoothctl, rfkill, hciconfig, sysfs, systemctl)
- **Dynamic Hardware Monitoring**: Periodic hardware checks (every 60 seconds) to detect USB Bluetooth adapters being plugged/unplugged
- **Graceful Hardware Handling**: Proper UI states when no Bluetooth hardware is detected, with clear "No Bluetooth Hardware" messaging
- **Robust Error Recovery**: Fallback mechanisms for hardware detection and connection handling

### **📅 Interactive Calendar with iCal Events**
- **Clickable Event Dates**: Calendar dates with iCal events are now clickable to display event details in the applet tray
- **Visual Event Indicators**: Colored dots on calendar days indicate events, with different colors for different iCal sources
- **Multi-Source Support**: Support for multiple iCal calendars with customizable colors and names per source
- **Event Details Display**: Comprehensive event information including title, time, description, and source calendar
- **Universal Navigation**: Empty days serve as navigation buttons to return to notifications from any applet
- **GTK3 Compatible**: Full GTK3 widget implementation ensuring compatibility and consistent styling

### **🔐 Enhanced WiFi Security Interface**
- **In-Dashboard Password Prompt**: Seamless password entry for secured WiFi networks without leaving the main interface
- **Consistent UI Design**: Password prompt matches calendar width and styling for visual consistency
- **Show/Hide Password**: Toggle password visibility with intuitive eye icon button
- **Smart Network Handling**: Automatic detection of saved networks with priority connection attempts
- **Enhanced Visual Feedback**: Clear network status with security indicators and connection progress

## 📊 Complete Feature List

### **🚀 Application Management**
- Application launcher with fuzzy search
- Dock with pinned and running applications  
- Workspace overview with window previews
- System tray integration
- Auto-hiding dock with smart occlusion detection

### **🧮 Productivity Suite**
- Scientific calculator with history and clipboard integration
- Universal unit converter (20+ categories including live currency rates)
- Tmux session manager (create, attach, rename, kill sessions)
- Persistent clipboard manager with search
- Full Unicode emoji picker
- HEX/RGB/HSV color picker
- OCR text extraction from screen regions
- Personal Kanban board for task management
- Interactive calendar with date selection
- Pin manager for quick file/directory access

### **📊 System Monitoring**
- Real-time CPU, RAM, GPU, and disk usage
- Network connection manager (WiFi/Ethernet)
- Bluetooth device manager
- Battery level and power state monitoring
- Audio volume and brightness controls
- Weather widget with automatic location detection

### **📸 Media Tools**
- Screenshot suite (region, fullscreen, window, mockup mode)
- High-quality screen recording
- MPRIS media player controls
- Dynamic wallpaper manager with adaptive theming
- Image annotation with Swappy integration

### **⚙️ System Integration**
- Hyprland workspace management
- Power menu (shutdown, restart, logout, sleep)
- Game mode toggle for performance optimization
- Pomodoro timer for productivity
- Idle inhibitor for presentations
- Auto-updater with changelog display

### **🎨 Customization**
- Adaptive theming from wallpaper colors (Matugen integration)
- Multiple UI themes (Notch, Panel, Pills)
- Configurable component visibility
- CSS-based styling system
- Corner indicators and visual enhancements

## 📋 Table of Contents

- [🚀 Features Overview](#-features-overview)
- [📱 Core Components](#-core-components)
- [🔧 System Integration](#-system-integration)
- [🌐 External APIs & Services](#-external-apis--services)
- [🔒 Privacy & Security](#-privacy--security)
- [⚙️ Installation](#️-installation)
- [📖 Usage Guide](#-usage-guide)
- [🛠️ Configuration](#️-configuration)
- [🔗 Dependencies](#-dependencies)

## 🚀 Features Overview

### **Application & Window Management**
- **Smart App Launcher** - Fuzzy search, keyboard navigation, dock pinning
- **Workspace Overview** - Visual workspace switcher with window previews
- **Dynamic Dock** - Auto-hiding, window grouping, custom pinning
- **System Tray** - Full system tray integration

### **Productivity Tools**
- **Advanced Calculator** - Scientific functions, history, clipboard integration
- **Unit Converter** - 20+ unit categories, live currency rates
- **Tmux Session Manager** - Create, attach, rename, kill sessions
- **Clipboard Manager** - Persistent clipboard history with search
- **Emoji Picker** - Full Unicode emoji database with search
- **Color Picker** - HEX, RGB, HSV color picking
- **OCR (Optical Character Recognition)** - Extract text from screen regions
- **Kanban Board** - Task management with drag-and-drop
- **Calendar** - Month/year navigation with visual date selection
- **Pin Manager** - Quick access to important files and directories

### **System Monitoring & Controls**
- **Real-time Metrics** - CPU, RAM, GPU, disk usage with live graphs
- **Network Manager** - WiFi, Ethernet connection management  
- **Bluetooth Manager** - Device pairing, connection control
- **Audio Controls** - Volume, brightness, media player controls
- **Battery Monitor** - Charge level, power state indicators
- **Weather Widget** - Current conditions with auto-location

### **Media & Screenshot Tools**
- **Screenshot Suite** - Region, fullscreen, window captures with mockup mode
- **Screen Recorder** - High-quality video recording
- **Media Player Controls** - MPRIS integration for all media players
- **Wallpaper Manager** - Dynamic wallpaper switching with color theming

### **Customization & Theming**
- **Adaptive Theming** - Auto-generates themes from wallpapers using Matugen
- **Multiple Layout Options** - Notch, Panel, and Pills themes
- **Configurable Components** - Show/hide any UI element
- **Custom Styling** - CSS-based theming system

## 📱 Core Components

### **Top Bar**
- **App Launcher Button** - Access to all applications and tools
- **Workspace Indicators** - Current workspace with optional numbering
- **System Tray** - Running applications and system services
- **Network Applet** - Connection status and management
- **Control Center** - Quick settings for audio, brightness, Bluetooth
- **Weather Display** - Current temperature and conditions
- **System Metrics** - CPU, RAM, disk usage indicators
- **Battery Monitor** - Charge level and status
- **Date/Time** - Current date and time display
- **Power Menu** - Shutdown, restart, logout options

### **Notch Panel** (Dynamic overlay)
- **Dashboard** - Central hub for widgets and information
- **Application Launcher** - Enhanced app search and management
- **Tmux Manager** - Terminal session management
- **Wallpaper Selector** - Browse and apply wallpapers
- **Emoji Picker** - Unicode emoji selection
- **Clipboard History** - Persistent clipboard management
- **Calculator** - Scientific calculator with history
- **Unit Converter** - Multi-category unit conversions
- **Kanban Board** - Personal task management
- **Calendar** - Date selection and navigation
- **Pin Manager** - Quick file/directory access
- **Settings** - Complete configuration interface

### **Dock**
- **Application Shortcuts** - Pinned and running applications
- **Window Grouping** - Multiple windows per application
- **Smart Auto-hide** - Context-aware visibility
- **Drag & Drop** - Reorder applications

### **Floating Windows**
- **Notifications** - System notification display
- **Toolbox** - Screenshot, recording, and utility tools
- **Overview** - Workspace and window management
- **Power Menu** - System power options

## 🔧 System Integration

### **Hyprland Integration**
- **Workspace Management** - Real-time workspace tracking
- **Window Operations** - Focus, close, minimize, maximize
- **Monitor Support** - Multi-monitor awareness
- **Special Workspaces** - Named and numbered workspaces

### **System Services**
- **UPower** - Battery and power management
- **NetworkManager** - Network connection management
- **PulseAudio/PipeWire** - Audio control
- **Brightness Control** - Screen brightness adjustment
- **Bluetooth** - Device management via BlueZ

### **File System Integration**
- **XDG Compliance** - Follows XDG Base Directory specification
- **Desktop Entries** - Parses `.desktop` files for applications
- **Icon Themes** - System icon theme support
- **File Manager Integration** - Opens directories in default file manager

## 🌐 External APIs & Services

### **Weather Services**
- **Primary**: [Met.no Weather API](https://api.met.no/) - Norwegian Meteorological Institute
  - **Endpoint**: `https://api.met.no/weatherapi/locationforecast/2.0/compact`
  - **Data**: Current temperature, weather conditions, forecasts
  - **Rate Limiting**: Respects API guidelines with 10-minute intervals

### **Geolocation Services**
- **Primary**: [IP-API](http://ip-api.com/) - IP-based geolocation
  - **Endpoint**: `http://ip-api.com/json/`
  - **Data**: Latitude, longitude, city, country
  - **Fallback**: [IPInfo.io](https://ipinfo.io/) for location data

### **Currency Exchange Rates**
- **Service**: [FloatRates](https://www.floatrates.com/)
  - **Endpoint**: `https://www.floatrates.com/daily/{currency}.json`
  - **Data**: Real-time exchange rates for 168+ currencies
  - **Update Frequency**: Daily rates with caching

### **Software Updates**
- **Repository**: GitHub Releases
  - **Endpoint**: `https://raw.githubusercontent.com/OlaYZen/YZ-Shell/main/version.json`
  - **Data**: Version numbers, changelogs, download URLs
  - **Frequency**: Hourly checks with user-controlled updates

### **Font Downloads**
- **Zed Sans Font**: GitHub Releases
  - **Endpoint**: `https://github.com/zed-industries/zed-fonts/releases/`
  - **Usage**: UI typography (downloaded on first run)

## 🔒 Privacy & Security

### **Local Data Storage**

**Configuration Files** (Stored in `~/.config/YZ-Shell/`)
- `config/config.json` - Main configuration settings
- `config/dock.json` - Dock application pins
- `config/settings_*.py` - UI preferences and themes

**Cache Files** (Stored in `~/.cache/yz-shell/`)
- `calc.json` - Calculator history (local only)
- `conversion.json` - Unit conversion history (local only)
- `fonts_updated` - Font installation tracking
- `updater_snooze.txt` - Update notification preferences

**Personal Data**
- Clipboard history - Stored locally, never transmitted
- Application usage patterns - Local only
- Wallpaper preferences - Local file paths only

### **Network Communications**

**Automatic Requests**
- **Weather Updates**: Every 10 minutes to Met.no API
- **Geolocation**: Once per weather update cycle
- **Update Checks**: Every hour to GitHub (can be disabled)
- **Currency Rates**: On-demand for conversions only

**User-Initiated Requests**
- **Manual Updates**: Only when user clicks update
- **Font Downloads**: Only on first installation

**No Telemetry**
- ❌ No usage analytics
- ❌ No personal data collection
- ❌ No behavioral tracking

### **Security Measures**

**Input Validation**
- Calculator expressions: Sandboxed evaluation with restricted builtins
- Shell commands: Parameterized execution, no user input injection
- File operations: Path validation and sanitization

**Network Security**
- HTTPS for all API calls (except IP-API fallback)
- 10-second timeouts on all requests
- No sensitive data in API requests
- User-Agent identification in weather requests

**Data Protection**
- No passwords or credentials stored
- Local clipboard history with manual clearing options
- Configuration files are user-readable only
- No automatic data synchronization

## ⚙️ Installation

### **Automatic Installation (Arch Linux)**
```bash
curl -fsSL https://raw.githubusercontent.com/OlaYZen/YZ-Shell/main/install.sh | bash
```

### **Manual Installation**

**Dependencies:**
```bash
# Core framework
fabric-git fabric-cli gray matugen

# System tools
brightnessctl cava cliphist hypridle hyprlock hyprpicker 
hyprshot hyprsunset grimblast gpu-screen-recorder imagemagick
libnotify nvtop playerctl swappy swww tesseract tmux upower
uwsm wl-clipboard wlinhibit

# Desktop integration
gnome-bluetooth-3.0 gobject-introspection vte3 webp-pixbuf-loader

# Python packages
python-pygobject python-ijson python-numpy python-pillow 
python-psutil python-pywayland python-requests python-setproctitle
python-toml python-watchdog

# Fonts (automatic)
noto-fonts-emoji ttf-zed-sans-mono-nerd
```

**Installation:**
```bash
git clone https://github.com/OlaYZen/YZ-Shell.git ~/.config/YZ-Shell
uwsm -- app python ~/.config/YZ-Shell/main.py > /dev/null 2>&1 & disown
```

## 📖 Usage Guide

### **Launcher Commands**

**Application Search**
- Type application name to search installed apps
- Use arrow keys to navigate results
- Press Enter to launch selected app
- Press Shift+Enter to pin app to dock

**Calculator Mode** (Prefix: `=`)
```bash
=2+2                    # Basic arithmetic
=sin(45)*pi             # Scientific functions  
=sqrt(144)+log(100)     # Mathematical operations
```

**Unit Converter** (Prefix: `;`)
```bash
;100 USD _ EUR           # Currency conversion
;10 km _ miles           # Distance conversion
;32 fahrenheit _ celsius # Temperature conversion
;1 GB _ MB               # Data size conversion
;5 feet and 6 inches _ cm # Multiple unit conversion
```

**Special Commands** (Prefix: `:`)
```bash
:d          # Open Dashboard
:w          # Open Wallpaper selector
:p          # Open Power menu
:update     # Force update check
```

### **Keyboard Shortcuts**

**Global Navigation**
- `↑/↓` - Navigate lists and menus
- `Enter` - Select/activate item
- `Shift+Enter` - Secondary action (pin to dock, delete history)
- `Escape` - Close current panel/menu

**Calculator/Converter**
- History navigation with arrow keys
- Enter to copy result to clipboard
- Shift+Enter to delete history item

### **Advanced Mouse Operations**

**📸 Screenshot Tools**
- **Left Click**: Normal screenshot (region/fullscreen/window)
- **Right Click**: Mockup screenshot with device frame
- **Shift+Enter**: Keyboard shortcut for mockup mode

**🎨 Color Picker**
- **Left Click**: Copy HEX color format (`#FF5733`)
- **Middle Click**: Copy HSV color format (`hsv(14, 78%, 100%)`)  
- **Right Click**: Copy RGB color format (`rgb(255, 87, 51)`)
- **Keyboard**: Enter (HEX), Shift+Enter (RGB), Ctrl+Enter (HSV)

**🎵 Media Player Controls**
- **Player Icon**:
  - **Left Click**: Switch to next media player
  - **Right Click**: Switch to previous media player  
  - **Middle Click**: Toggle display mode (title/artist/visualizer)
- **Play/Pause Button**:
  - **Left Click**: Previous track
  - **Middle Click**: Play/pause toggle
  - **Right Click**: Next track

**📌 Pin Manager**
- **Empty Cells**:
  - **Left Click**: Select file to pin
  - **Middle Click**: Paste clipboard content as text pin
- **File Pins**:
  - **Double Click**: Open file
  - **Right Click**: Remove pin
- **Text/URL Pins**:
  - **Left Click**: Copy to clipboard (URLs auto-open)
  - **Right Click**: Remove pin

**🖥️ Tmux Sessions**
- **Left Click**: Attach to session
- **Right Click**: Context menu (rename/kill session)
- **R Key**: Quick rename session
- **Enter**: Attach to selected session

**📱 Applications**
- **Left Click**: Launch application
- **Right Click**: Context menu with advanced options
- **Double Click**: Quick launch
- **Shift+Enter**: Pin to dock (in launcher)

**🔧 System Tray**
- **Left Click**: Default action for system tray items
- **Right Click**: Context menu for tray applications

**📊 System Overview**
- **Right Click**: Additional workspace/window management options

### **🔄 Advanced Interaction Features**

**🎯 Context-Aware Actions**
- Most UI elements support multiple interaction modes
- Keyboard modifiers (Shift/Ctrl) change behavior
- Visual feedback for all interactive elements

**⌨️ Power User Features**  
- **Drag & Drop**: Pin files by dragging to pin manager
- **Keyboard Navigation**: Full keyboard control of all interfaces
- **Multi-Modal Operations**: Same element, different actions based on input method
- **Smart Defaults**: Left-click for primary action, right-click for options

**🔀 Cross-Component Integration**
- **Calculator ↔ Clipboard**: Results auto-copy with Enter
- **Converter ↔ Currency**: Live rates on-demand
- **Pin Manager ↔ File System**: Real-time file monitoring
- **Media Player ↔ Multiple Apps**: Seamless switching between players

## 🛠️ Configuration

### **Main Configuration** (`~/.config/YZ-Shell/config/config.json`)

```json
{
  "wallpapers_dir": "/path/to/wallpapers",
  "bar_position": "Top",
  "centered_bar": false,
  "terminal_command": "kitty -e",
  "dock_enabled": true,
  "dock_icon_size": 28,
  "bar_theme": "Pills",
  "dock_theme": "Pills", 
  "panel_theme": "Notch",
  "corners_visible": true,
  "bar_components_visibility": {
    "button_apps": true,
    "systray": true,
    "control": true,
    "network": true,
    "weather": true,
    "battery": true,
    "metrics": true,
    "date_time": true
  }
}
```

### **Component Visibility**
All bar components can be individually toggled:
- App launcher button
- System tray
- Control center  
- Network applet
- Weather widget
- Battery indicator
- System metrics
- Date/time display
- Power menu button

### **Theming Options**
- **Bar Themes**: Pills, Panel, Minimal
- **Dock Themes**: Pills, Panel, Transparent
- **Panel Themes**: Notch, Panel, Overlay
- **Adaptive Colors**: Automatic theme generation from wallpapers

## 🔗 Dependencies

### **Core Framework**
- **[Fabric](https://github.com/Fabric-Development/fabric)** - GTK-based desktop framework
- **[Gray](https://github.com/Fabric-Development/gray)** - Configuration management
- **[Matugen](https://github.com/InioX/matugen)** - Material Design color generation

### **System Integration**
- **Hyprland** - Wayland compositor (required)
- **UWSM** - Session management
- **UPower** - Power management
- **PulseAudio/PipeWire** - Audio system

### **Utility Tools**
- **Grimblast** - Screenshot tool
- **GPU Screen Recorder** - Video recording
- **Swappy** - Screenshot annotation
- **SWWW** - Wallpaper management
- **Tesseract** - OCR engine
- **Cliphist** - Clipboard history
- **Tmux** - Terminal multiplexer

### **Optional Enhancements**
- **Cava** - Audio visualizer
- **Nvtop** - GPU monitoring
- **Hypridle/Hyprlock** - Idle management and screen locking


<h2><sub><img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Travel%20and%20places/Rocket.png" alt="Rocket" width="25" height="25" /></sub> Roadmap</h2>

- [x] App Launcher
- [x] Bluetooth Manager
- [x] Calculator
- [x] Calendar
- [x] Clipboard Manager
- [x] Color Picker
- [x] Customizable UI
- [x] Dashboard
- [x] Dock
- [x] Emoji Picker
- [x] Enhanced Bluetooth Hardware Detection
- [x] Enhanced Network Metrics (Standardized Units)
- [x] Enhanced Time Display (Seconds Precision)
- [x] Enhanced Weather Service (Met.no API)
- [x] Extended Weather Dashboard (3-Day Forecast)
- [x] iCal Support
- [x] Interactive Date Display (Multi-Format)
- [x] Kanban Board
- [x] Network Manager
- [x] Notifications
- [x] OCR
- [x] Pins
- [x] Power Manager
- [x] Power Menu
- [x] Screen Recorder
- [x] Screenshot
- [x] Settings
- [x] Smart WiFi Connection Management
- [x] System Tray
- [x] Terminal
- [x] Tmux Session Manager
- [x] Update checker
- [x] Vertical Layout
- [x] Wallpaper Selector
- [x] Workspaces Overview
- [ ] Multi-monitor support
- [ ] Multimodal AI Assistant
- [ ] OSD
- [ ] OTP Manager

## Support

If you find Ax-Shell useful, please consider supporting the **original project creator**:

<p align="center">
  <a href='https://ko-fi.com/Axenide' target='_blank'>
    <img src='https://img.shields.io/badge/Support%20Original%20Author-Ko--fi-FF5E5B?style=for-the-badge&logo=ko-fi&logoColor=white' alt='Support Original Author on Ko-fi' />
  </a>
</p>

> **Note**: This is a fork with additional features. Please support [Axenide](https://github.com/Axenide), the original creator of Ax-Shell.
