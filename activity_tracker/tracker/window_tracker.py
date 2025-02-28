#!/usr/bin/env python3
import platform
import subprocess
import psutil

class WindowTracker:
    """Tracks active window information across different platforms."""

    _instance = None

    def __new__(cls):
        """Create a singleton instance of WindowTracker."""
        if cls._instance is None:
            cls._instance = super(WindowTracker, cls).__new__(cls)
            cls._instance.__initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the window tracker and check for required dependencies."""
        if not hasattr(self, '__initialized') or not self.__initialized:
            if platform.system() == 'Linux':
                try:
                    # Check for xdotool
                    subprocess.run(['which', 'xdotool'], check=True, capture_output=True)
                except subprocess.CalledProcessError:
                    print("Warning: xdotool is not installed. Please install it for better window tracking.")
                
                try:
                    # Check for wmctrl
                    subprocess.run(['which', 'wmctrl'], check=True, capture_output=True)
                except subprocess.CalledProcessError:
                    print("Error: wmctrl is not installed. Please install it for window tracking to work.")
                    print("Run: sudo apt-get install wmctrl")
            self.__initialized = True

    @classmethod
    def get_active_window_info(cls):
        """Get information about the currently active window.
        
        Returns:
            dict: Dictionary containing app name, window title, and process ID,
                 or None if unable to get window information
        """
        tracker = cls()
        system = platform.system()
        print(f"Debug - Operating System: {system}")  # Debug log
        try:
            if system == 'Windows':
                return tracker._get_windows_info()
            elif system == 'Darwin':
                return tracker._get_macos_info()
            elif system == 'Linux':
                print("Debug - Using Linux window tracking")  # Debug log
                info = tracker._get_linux_info()
                print(f"Debug - Linux window info: {info}")  # Debug log
                return info
            return None
        except Exception as e:
            print(f"Error getting active window: {e}")
            return None

    def _get_windows_info(self):
        """Get active window information for Windows.
        
        Returns:
            dict: Window information for Windows
        """
        import win32gui
        import win32process
        
        window = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(window)
        title = win32gui.GetWindowText(window)
        try:
            process = psutil.Process(pid)
            app_name = process.name()
            return {'app': app_name, 'title': title, 'pid': pid}
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None

    def _get_macos_info(self):
        """Get active window information for macOS.
        
        Returns:
            dict: Window information for macOS
        """
        script = '''
        tell application "System Events"
            set frontApp to name of first application process whose frontmost is true
            set frontAppPath to path of first application process whose frontmost is true
            set windowTitle to ""
            tell process frontApp
                if exists (1st window whose value of attribute "AXMain" is true) then
                    set windowTitle to name of 1st window whose value of attribute "AXMain" is true
                end if
            end tell
            return {frontApp, windowTitle, frontAppPath}
        end tell
        '''
        result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
        if result.returncode == 0:
            output = result.stdout.strip().split(', ')
            if len(output) >= 2:
                return {'app': output[0], 'title': output[1], 'pid': None}
        return None

    def _get_linux_info(self):
        """Get active window information for Linux.
        
        Returns:
            dict: Window information for Linux
        """
        import os
        print("Debug - Attempting Linux window detection")  # Debug log
        
        # Try xdotool first since it's specifically for active window
        try:
            print("Debug - Trying xdotool method")  # Debug log
            window_id = subprocess.check_output(['xdotool', 'getactivewindow']).decode().strip()
            window_pid = subprocess.check_output(['xdotool', 'getwindowpid', window_id]).decode().strip()
            window_name = subprocess.check_output(['xdotool', 'getwindowname', window_id]).decode().strip()
            
            process = psutil.Process(int(window_pid))
            app_name = process.name()
            
            info = {'app': app_name, 'title': window_name, 'pid': int(window_pid)}
            print(f"Debug - xdotool found window: {info}")  # Debug log
            return info

        except Exception as e:
            print(f"Debug - xdotool failed: {e}")
            try:
                # Try wmctrl as fallback
                print("Debug - Trying wmctrl method")  # Debug log
                # Get the active window ID using wmctrl
                active_window = subprocess.check_output(['xprop', '-root', '_NET_ACTIVE_WINDOW']).decode()
                window_id = active_window.split()[-1]
                
                # Get window list and find the active window
                window_list = subprocess.check_output(['wmctrl', '-l', '-p']).decode().strip().split('\n')
                for window in window_list:
                    parts = window.split()
                    if window_id in parts[0]:  # Match window ID
                        pid = int(parts[2])
                        process = psutil.Process(pid)
                        info = {
                            'app': process.name(),
                            'title': ' '.join(parts[4:]),
                            'pid': pid
                        }
                        print(f"Debug - wmctrl found window: {info}")  # Debug log
                        return info
            except Exception as e:
                print(f"Debug - wmctrl failed: {e}")
                try:
                    # Try psutil as last resort
                    print("Debug - Trying psutil as last resort")  # Debug log
                    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                        try:
                            if proc.info['name'] not in ['explorer.exe', 'Finder', 'SystemUI']:
                                info = {
                                    'app': proc.info['name'],
                                    'title': ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else proc.info['name'],
                                    'pid': proc.info['pid']
                                }
                                print(f"Debug - psutil found process: {info}")  # Debug log
                                return info
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                except Exception as e:
                    print(f"Debug - All window detection methods failed: {e}")
                    return None