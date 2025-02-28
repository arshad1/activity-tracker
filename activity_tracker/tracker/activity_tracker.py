#!/usr/bin/env python3
import os
import time
import json
import datetime
import signal
import sys
import subprocess
import threading
from pynput import keyboard
from .window_tracker import WindowTracker
from ..config.config_manager import ConfigManager

class ActivityTracker:
    """Tracks and logs user activity based on active windows."""

    def __init__(self, config_file='activity_config.json'):
        """Initialize the activity tracker.
        
        Args:
            config_file (str): Name of the configuration file
        """
        self.config_manager = ConfigManager(config_file)
        self.today_date = datetime.datetime.now().strftime('%Y-%m-%d')
        self.activities = []
        self.current_activity = None
        self.sampling_interval = self.config_manager.get_sampling_interval()
        self._last_mouse_pos = None
        self._last_window_title = None
        self._last_key_state = None
        self._load_today_activities()
        
        # Keyboard activity monitoring
        self.is_typing = False
        self.last_keypress_time = time.time()
        self.keyboard_listener = None
        self.typing_inactivity_threshold = 2.0  # Consider user not typing after 2 seconds of keyboard inactivity
        
        # User activity tracking
        self.last_activity_time = time.time()
        self.idle_threshold = 30  # 30 seconds of inactivity to be considered idle
        self.is_idle = False
        
        # Start keyboard monitoring
        self._start_keyboard_monitoring()

    def _on_key_press(self, key):
        """Callback for keyboard press events."""
        self.last_keypress_time = time.time()
        self.last_activity_time = time.time()  # Update last activity time on key press
        if not self.is_typing:
            self.is_typing = True
            print("Debug - User started typing")
        
        # Reset idle state if user was idle
        if self.is_idle:
            self.is_idle = False
            print("Debug - User no longer idle (keyboard activity)")

    def _start_keyboard_monitoring(self):
        """Start keyboard monitoring in a separate thread."""
        try:
            self.keyboard_listener = keyboard.Listener(on_press=self._on_key_press)
            self.keyboard_listener.start()
            print("Debug - Keyboard monitoring started successfully")
        except Exception as e:
            print(f"Debug - Failed to start keyboard monitoring: {e}")
            # Fallback to the old method if pynput initialization fails
            self.keyboard_listener = None

    def _stop_keyboard_monitoring(self):
        """Stop keyboard monitoring."""
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None

    def _check_typing_status(self):
        """Check if user is currently typing based on recent keypresses."""
        if not self.keyboard_listener:
            return False  # If keyboard monitoring is not available
            
        current_time = time.time()
        elapsed = current_time - self.last_keypress_time
        
        # Update typing status based on elapsed time since last keypress
        if self.is_typing and elapsed > self.typing_inactivity_threshold:
            self.is_typing = False
            print(f"Debug - User stopped typing (inactive for {elapsed:.2f} seconds)")
            
        return self.is_typing

    def _load_today_activities(self):
        """Load today's activities if file exists."""
        today_log = self.config_manager.get_log_path(self.today_date)
        if os.path.exists(today_log):
            with open(today_log, 'r') as f:
                self.activities = json.load(f)

    def _save_activities(self):
        """Save activities to today's log file."""
        today_log = self.config_manager.get_log_path(self.today_date)
        with open(today_log, 'w') as f:
            json.dump(self.activities, f, indent=4)

    def categorize_activity(self, window_info):
        """Categorize the activity based on the application name and window title.
        
        Args:
            window_info (dict): Information about the active window
            
        Returns:
            str: Category of the activity
        """
        if not window_info:
            return "Idle"

        config = self.config_manager.get_config()
        app_name = window_info['app'].lower()
        title = window_info['title'].lower()

        # Check if app is in ignored list
        if app_name in [x.lower() for x in config['ignored_apps']]:
            return "System"

        # Check categories
        for category, apps in config['categories'].items():
            if any(app.lower() in app_name for app in apps):
                return category

        # Special categorization based on window title
        if "email" in title or "mail" in title:
            return "Communication"
        if "document" in title or ".doc" in title or ".txt" in title:
            return "Documents"
        if "code" in title or "script" in title or any(ext in title for ext in ['.py', '.js', '.html', '.css', '.java', '.go', '.c', '.cpp']):
            return "Coding"

        # Default category
        return "Other"

    def log_current_activity(self):
        """Log the current user activity."""
        timestamp = datetime.datetime.now().isoformat()
        
        if self.is_idle:
            print("Debug - Logging activity as Idle due to inactivity")
            activity = {
                'timestamp': timestamp,
                'app': 'Idle',
                'title': 'User inactive',
                'category': 'Idle',
                'duration': self.sampling_interval
            }
        else:
            window_info = WindowTracker.get_active_window_info()
            
            print(f"Debug - Current window info: {window_info}")  # Debug log

            if not window_info:
                print("Debug - No window info detected, marking as Idle")  # Debug log
                activity = {
                    'timestamp': timestamp,
                    'app': 'Idle',
                    'title': 'User inactive',
                    'category': 'Idle',
                    'duration': self.sampling_interval
                }
            else:
                category = self.categorize_activity(window_info)
                is_typing = self._check_typing_status()
                title_suffix = " (typing)" if is_typing else ""
                print(f"Debug - Active window detected: {window_info['app']} - {window_info['title']} - Typing: {is_typing}")
                
                activity = {
                    'timestamp': timestamp,
                    'app': window_info['app'],
                    'title': window_info['title'] + title_suffix,
                    'category': category,
                    'duration': self.sampling_interval,
                    'is_typing': is_typing
                }

        # If this is the same activity as before, update duration instead of adding new
        if not self.is_idle and self.current_activity and self.activities and 'app' in activity:
            # Consider same activity if app and title match, or if only typing status changed
            is_same_activity = (
                self.current_activity.get('app') == activity.get('app') and
                self.current_activity.get('title', '').replace(" (typing)", "") == activity.get('title', '').replace(" (typing)", "")
            )
            if is_same_activity:
                self.activities[-1]['duration'] += self.sampling_interval
                # Update typing status in case it changed
                if 'is_typing' in activity:
                    self.activities[-1]['is_typing'] = activity['is_typing']
                    self.activities[-1]['title'] = activity['title']
                self.current_activity = self.activities[-1]
                return

        # If different activity or no current activity, add new one
        self.activities.append(activity)
        self.current_activity = activity

        # Save to file
        self._save_activities()

    def handle_exit(self, signum, frame):
        """Handle exit signals gracefully."""
        print("\nTracking stopped.")
        self._stop_keyboard_monitoring()
        sys.exit(0)

    def check_idle_status(self):
        """Check if user has been inactive for the idle threshold period."""
        current_time = time.time()
        idle_duration = current_time - self.last_activity_time
        
        # If idle duration exceeds threshold, mark as idle
        if idle_duration >= self.idle_threshold:
            if not self.is_idle:  # Only log transition to idle once
                self.is_idle = True
                print(f"Debug - User is now idle (inactive for {idle_duration:.1f} seconds)")
            return True
        return False

    def start_tracking(self):
        """Start tracking user activity."""
        print(f"Activity tracking started. Sampling every {self.sampling_interval} seconds.")
        print(f"Press Ctrl+C to stop tracking.")
        print(f"Debug - Using {self.idle_threshold}s idle threshold for mouse and keyboard")

        # Set up signal handlers for graceful exit
        signal.signal(signal.SIGINT, self.handle_exit)
        signal.signal(signal.SIGTERM, self.handle_exit)

        try:
            while True:
                try:
                    # Get current mouse position
                    try:
                        mouse_info = subprocess.check_output(['xdotool', 'getmouselocation']).decode()
                        current_mouse = mouse_info.strip()
                        
                        # Check for mouse movement
                        if self._last_mouse_pos is None:
                            self._last_mouse_pos = current_mouse
                        elif current_mouse != self._last_mouse_pos:
                            print(f"Debug - Mouse movement detected {current_mouse} -- {self._last_mouse_pos}")
                            self.last_activity_time = time.time()  # Update last activity time
                            if self.is_idle:
                                self.is_idle = False
                                print("Debug - User no longer idle (mouse movement)")
                    except Exception as e:
                        print(f"Debug - Error getting mouse position: {e}")

                    # Get active window info for title comparison
                    try:
                        window_id = subprocess.check_output(['xdotool', 'getactivewindow']).decode().strip()
                        window_title = subprocess.check_output(['xdotool', 'getwindowname', window_id]).decode().strip()
                        
                        # Detect window title changes
                        if self._last_window_title is None:
                            self._last_window_title = window_title
                        elif window_title != self._last_window_title:
                            print("Debug - Window changed")
                            self.last_activity_time = time.time()  # Update last activity time
                            self._last_window_title = window_title
                            if self.is_idle:
                                self.is_idle = False
                                print("Debug - User no longer idle (window change)")
                    except Exception as e:
                        print(f"Debug - Error getting window info: {e}")
                    
                    # Update mouse position for next comparison
                    self._last_mouse_pos = current_mouse
                    
                    # Check if user is idle
                    self.check_idle_status()
                    
                    # Log the current activity (idle or active)
                    self.log_current_activity()

                except Exception as e:
                    print(f"Debug - Error during tracking: {e}")
                
                time.sleep(self.sampling_interval)

        except Exception as e:
            print(f"Error during tracking: {e}")
            self._stop_keyboard_monitoring()
            self.handle_exit(None, None)