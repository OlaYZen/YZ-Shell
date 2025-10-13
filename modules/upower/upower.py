import dbus

class UPowerManager():

    def __init__(self):
        self.UPOWER_NAME = "org.freedesktop.UPower"
        self.UPOWER_PATH = "/org/freedesktop/UPower"

        self.DBUS_PROPERTIES = "org.freedesktop.DBus.Properties"
        self.bus = dbus.SystemBus()

    def detect_devices(self):
        upower_proxy = self.bus.get_object(self.UPOWER_NAME, self.UPOWER_PATH)
        upower_interface = dbus.Interface(upower_proxy, self.UPOWER_NAME)

        devices = upower_interface.EnumerateDevices()
        return devices

    def get_display_device(self):
        upower_proxy = self.bus.get_object(self.UPOWER_NAME, self.UPOWER_PATH)
        upower_interface = dbus.Interface(upower_proxy, self.UPOWER_NAME)

        dispdev = upower_interface.GetDisplayDevice()
        return dispdev

    def get_critical_action(self):
        upower_proxy = self.bus.get_object(self.UPOWER_NAME, self.UPOWER_PATH)
        upower_interface = dbus.Interface(upower_proxy, self.UPOWER_NAME)

        critical_action = upower_interface.GetCriticalAction()
        return critical_action

    def get_device_percentage(self, battery):
        battery_proxy = self.bus.get_object(self.UPOWER_NAME, battery)
        battery_proxy_interface = dbus.Interface(battery_proxy, self.DBUS_PROPERTIES)

        return battery_proxy_interface.Get(self.UPOWER_NAME + ".Device", "Percentage")

    def get_full_device_information(self, battery):
        battery_proxy = self.bus.get_object(self.UPOWER_NAME, battery)
        battery_proxy_interface = dbus.Interface(battery_proxy, self.DBUS_PROPERTIES)

        # Use GetAll to retrieve all properties in a single DBus call
        all_properties = battery_proxy_interface.GetAll(self.UPOWER_NAME + ".Device")
        
        # Extract properties with default values for missing keys
        information_table = {
            'HasHistory': all_properties.get('HasHistory', False),
            'HasStatistics': all_properties.get('HasStatistics', False), 
            'IsPresent': all_properties.get('IsPresent', False),
            'IsRechargeable': all_properties.get('IsRechargeable', False),
            'Online': all_properties.get('Online', False),
            'PowerSupply': all_properties.get('PowerSupply', False),
            'Capacity': all_properties.get('Capacity', 0.0),
            'Energy': all_properties.get('Energy', 0.0),
            'EnergyEmpty': all_properties.get('EnergyEmpty', 0.0),
            'EnergyFull': all_properties.get('EnergyFull', 0.0),
            'EnergyFullDesign': all_properties.get('EnergyFullDesign', 0.0),
            'EnergyRate': all_properties.get('EnergyRate', 0.0),
            'Luminosity': all_properties.get('Luminosity', 0.0),
            'Percentage': all_properties.get('Percentage', 0.0),
            'Temperature': all_properties.get('Temperature', 0.0),
            'Voltage': all_properties.get('Voltage', 0.0),
            'TimeToEmpty': all_properties.get('TimeToEmpty', 0),
            'TimeToFull': all_properties.get('TimeToFull', 0),
            'IconName': all_properties.get('IconName', ''),
            'Model': all_properties.get('Model', ''),
            'NativePath': all_properties.get('NativePath', ''),
            'Serial': all_properties.get('Serial', ''),
            'Vendor': all_properties.get('Vendor', ''),
            'State': all_properties.get('State', 0),
            'Technology': all_properties.get('Technology', 0),
            'Type': all_properties.get('Type', 0),
            'WarningLevel': all_properties.get('WarningLevel', 0),
            'UpdateTime': all_properties.get('UpdateTime', 0)
        }

        return information_table

    def is_lid_present(self):
        upower_proxy = self.bus.get_object(self.UPOWER_NAME, self.UPOWER_PATH)
        upower_interface = dbus.Interface(upower_proxy, self.DBUS_PROPERTIES)

        is_lid_present = bool(upower_interface.Get(self.UPOWER_NAME, 'LidIsPresent'))
        return is_lid_present

    def is_lid_closed(self):
        upower_proxy = self.bus.get_object(self.UPOWER_NAME, self.UPOWER_PATH)
        upower_interface = dbus.Interface(upower_proxy, self.DBUS_PROPERTIES)

        is_lid_closed = bool(upower_interface.Get(self.UPOWER_NAME, 'LidIsClosed'))
        return is_lid_closed

    def on_battery(self):
        upower_proxy = self.bus.get_object(self.UPOWER_NAME, self.UPOWER_PATH)
        upower_interface = dbus.Interface(upower_proxy, self.DBUS_PROPERTIES)

        on_battery = bool(upower_interface.Get(self.UPOWER_NAME, 'OnBattery'))
        return on_battery

    def has_wakeup_capabilities(self):
        upower_proxy = self.bus.get_object(self.UPOWER_NAME, self.UPOWER_PATH + "/Wakeups")
        upower_interface = dbus.Interface(upower_proxy, self.DBUS_PROPERTIES)

        has_wakeup_capabilities = bool(upower_interface.Get(self.UPOWER_NAME+ '.Wakeups', 'HasCapability'))
        return has_wakeup_capabilities

    def get_wakeups_data(self):
        upower_proxy = self.bus.get_object(self.UPOWER_NAME, self.UPOWER_PATH + "/Wakeups")
        upower_interface = dbus.Interface(upower_proxy, self.UPOWER_NAME + '.Wakeups')

        data = upower_interface.GetData()
        return data

    def get_wakeups_total(self):
        upower_proxy = self.bus.get_object(self.UPOWER_NAME, self.UPOWER_PATH + "/Wakeups")
        upower_interface = dbus.Interface(upower_proxy, self.UPOWER_NAME + '.Wakeups')

        data = upower_interface.GetTotal()
        return data

    def is_loading(self, battery):
        battery_proxy = self.bus.get_object(self.UPOWER_NAME, battery)
        battery_proxy_interface = dbus.Interface(battery_proxy, self.DBUS_PROPERTIES)

        state = int(battery_proxy_interface.Get(self.UPOWER_NAME + ".Device", "State"))

        if (state == 1):
            return True
        else:
            return False

    def get_state(self, battery):
        battery_proxy = self.bus.get_object(self.UPOWER_NAME, battery)
        battery_proxy_interface = dbus.Interface(battery_proxy, self.DBUS_PROPERTIES)

        state = int(battery_proxy_interface.Get(self.UPOWER_NAME + ".Device", "State"))

        if (state == 0):
            return "Unknown"
        elif (state == 1):
            return "Loading"
        elif (state == 2):
            return "Discharging"
        elif (state == 3):
            return "Empty"
        elif (state == 4):
            return "Fully charged"
        elif (state == 5):
            return "Pending charge"
        elif (state == 6):
            return "Pending discharge"

    def get_controller_devices(self):
        """
        Detect gaming controllers/peripherals with batteries.
        Returns a list of device paths that are likely controllers.
        """
        try:
            devices = self.detect_devices()
            controller_devices = []
            
            for device_path in devices:
                try:
                    device_info = self.get_full_device_information(device_path)
                    if device_info is None:
                        continue
                    
                    # Check if device has battery and is not the main system battery
                    if (device_info.get('IsPresent') and 
                        device_info.get('Percentage', 0) > 0 and
                        not device_info.get('PowerSupply', True)):  # PowerSupply=False indicates peripheral
                        
                        # Additional filtering based on device path or model names
                        device_path_lower = device_path.lower()
                        model = device_info.get('Model', '').lower()
                        vendor = device_info.get('Vendor', '').lower()
                        
                        # Common controller identifiers
                        controller_indicators = [
                            'gamepad', 'controller', 'joystick', 'xbox', 'playstation', 
                            'ps4', 'ps5', 'nintendo', 'switch', 'pro controller',
                            'dualshock', 'dualsense', 'joycon', 'joy-con'
                        ]
                        
                        # Check if any controller indicators are present
                        is_controller = any(
                            indicator in device_path_lower or 
                            indicator in model or 
                            indicator in vendor
                            for indicator in controller_indicators
                        )
                        
                        if is_controller:
                            controller_devices.append({
                                'path': device_path,
                                'model': device_info.get('Model', 'Controller'),
                                'vendor': device_info.get('Vendor', 'Unknown'),
                                'percentage': device_info.get('Percentage', 0),
                                'state': device_info.get('State', 0)
                            })
                            
                except Exception as e:
                    # Skip devices that can't be queried
                    continue
                    
            return controller_devices
            
        except Exception as e:
            print(f"Error detecting controller devices: {e}")
            return []

    def get_controller_info(self, device_path):
        """
        Get detailed information for a specific controller device.
        """
        try:
            device_info = self.get_full_device_information(device_path)
            if device_info is None:
                return None
                
            return {
                'percentage': device_info.get('Percentage', 0),
                'state': device_info.get('State', 0),  # 1=charging, 2=discharging
                'time_to_empty': device_info.get('TimeToEmpty', 0),
                'time_to_full': device_info.get('TimeToFull', 0),
                'model': device_info.get('Model', 'Controller'),
                'vendor': device_info.get('Vendor', 'Unknown')
            }
        except Exception as e:
            print(f"Error getting controller info for {device_path}: {e}")
            return None
