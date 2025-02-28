#!/usr/bin/env python3
import os
import time
import datetime
import json
import subprocess
import platform
import psutil
from pathlib import Path
import argparse

class ActivityTracker:
    def __init__(self, config_file='activity_config.json'):
        self.home_dir = str(Path.home())
        self.config_path = os.path.join(self.home_dir, '.activity_tracker')
        self.config_file = os.path.join(self.config_path, config_file)
        self.today_date = datetime.datetime.now().strftime('%Y-%m-%d')
        self.today_log = os.path.join(self.config_path, f'activity_{self.today_date}.json')
        self.activities = []
        self.current_activity = None
        self.sampling_interval = 30  # seconds
        
        # Create config directory if it doesn't exist
        if not os.path.exists(self.config_path):
            os.makedirs(self.config_path)
            
        # Load config if exists, otherwise create default
        self.load_config()
        
        # Load today's activities if the file exists
        self.load_today_activities()
    
    def load_config(self):
        """Load configuration or create default if doesn't exist"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {
                'track_applications': True,
                'track_documents': True,
                'ignored_apps': ['explorer.exe', 'Finder', 'SystemUI'],
                'categories': {
                    'Coding': ['vscode', 'pycharm', 'intellij', 'sublime_text', 'vim', 'atom'],
                    'Communication': ['outlook', 'thunderbird', 'slack', 'teams', 'discord', 'zoom'],
                    'Browsing': ['chrome', 'firefox', 'safari', 'edge'],
                    'Documents': ['word', 'excel', 'powerpoint', 'acrobat', 'pdf']
                },
                'sampling_interval': 30
            }
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        
        # Update sampling interval from config
        self.sampling_interval = self.config.get('sampling_interval', 30)
    
    def load_today_activities(self):
        """Load today's activities if file exists"""
        if os.path.exists(self.today_log):
            with open(self.today_log, 'r') as f:
                self.activities = json.load(f)
    
    def save_activities(self):
        """Save activities to today's log file"""
        with open(self.today_log, 'w') as f:
            json.dump(self.activities, f, indent=4)
    
    def get_active_window_info(self):
        """Get information about the currently active window"""
        system = platform.system()
        try:
            if system == 'Windows':
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
                
            elif system == 'Darwin':  # macOS
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
                
            elif system == 'Linux':
                try:
                    # Using xdotool to get window info
                    window_id = subprocess.check_output(['xdotool', 'getactivewindow']).decode().strip()
                    window_pid = subprocess.check_output(['xdotool', 'getwindowpid', window_id]).decode().strip()
                    window_name = subprocess.check_output(['xdotool', 'getwindowname', window_id]).decode().strip()
                    
                    process = psutil.Process(int(window_pid))
                    app_name = process.name()
                    
                    return {'app': app_name, 'title': window_name, 'pid': int(window_pid)}
                except (subprocess.SubprocessError, ValueError, psutil.NoSuchProcess, psutil.AccessDenied):
                    return None
            
            return None
        except Exception as e:
            print(f"Error getting active window: {e}")
            return None
    
    def categorize_activity(self, window_info):
        """Categorize the activity based on the application name and window title"""
        if not window_info:
            return "Idle"
            
        app_name = window_info['app'].lower()
        title = window_info['title'].lower()
        
        # Check if app is in ignored list
        if app_name in [x.lower() for x in self.config['ignored_apps']]:
            return "System"
            
        # Check categories
        for category, apps in self.config['categories'].items():
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
        """Log the current user activity"""
        window_info = self.get_active_window_info()
        
        if not window_info:
            return
            
        timestamp = datetime.datetime.now().isoformat()
        category = self.categorize_activity(window_info)
        
        activity = {
            'timestamp': timestamp,
            'app': window_info['app'],
            'title': window_info['title'],
            'category': category,
            'duration': self.sampling_interval  # initial duration is one sampling interval
        }
        
        # If this is the same activity as before, update duration instead of adding new
        if self.current_activity and self.activities and \
           self.current_activity['app'] == window_info['app'] and \
           self.current_activity['title'] == window_info['title']:
            self.activities[-1]['duration'] += self.sampling_interval
            self.current_activity = self.activities[-1]
        else:
            self.activities.append(activity)
            self.current_activity = activity
        
        # Save to file
        self.save_activities()
    
    def generate_daily_report(self):
        """Generate a report of today's activities"""
        if not self.activities:
            return "No activities logged today."
            
        total_time = sum(a['duration'] for a in self.activities)
        category_times = {}
        app_times = {}
        
        for activity in self.activities:
            category = activity['category']
            app = activity['app']
            duration = activity['duration']
            
            category_times[category] = category_times.get(category, 0) + duration
            app_times[app] = app_times.get(app, 0) + duration
        
        # Format report
        report = f"Activity Report for {self.today_date}\n"
        report += "=" * 40 + "\n\n"
        
        # Category breakdown
        report += "Time by Category:\n"
        report += "-" * 20 + "\n"
        for category, time_spent in sorted(category_times.items(), key=lambda x: x[1], reverse=True):
            hours = time_spent / 3600
            report += f"{category}: {hours:.2f} hours ({(time_spent/total_time)*100:.1f}%)\n"
        
        report += "\n"
        
        # Application breakdown
        report += "Time by Application:\n"
        report += "-" * 20 + "\n"
        for app, time_spent in sorted(app_times.items(), key=lambda x: x[1], reverse=True)[:10]:  # Top 10 apps
            minutes = time_spent / 60
            report += f"{app}: {minutes:.1f} minutes\n"
        
        report += "\n"
        
        # Detailed activity list
        report += "Detailed Activities:\n"
        report += "-" * 20 + "\n"
        
        # Group activities by hour for easier reading
        hour_activities = {}
        for activity in self.activities:
            timestamp = datetime.datetime.fromisoformat(activity['timestamp'])
            hour = timestamp.strftime('%H:00')
            if hour not in hour_activities:
                hour_activities[hour] = []
            hour_activities[hour].append(activity)
        
        # Print activities by hour
        for hour, activities in sorted(hour_activities.items()):
            report += f"\n{hour}\n"
            for activity in activities:
                app = activity['app']
                title = activity['title']
                duration = activity['duration'] / 60  # convert to minutes
                if duration >= 1:  # Only show activities that took at least a minute
                    report += f"  - {app}: {title[:50]}{'...' if len(title) > 50 else ''} ({duration:.1f} min)\n"
        
        return report
    
    def start_tracking(self):
        """Start tracking user activity"""
        print(f"Activity tracking started. Sampling every {self.sampling_interval} seconds.")
        print(f"Press Ctrl+C to stop and generate report.")
        
        try:
            while True:
                self.log_current_activity()
                time.sleep(self.sampling_interval)
        except KeyboardInterrupt:
            print("\nTracking stopped.")
            report = self.generate_daily_report()
            print("\n" + report)
            
            # Save report to file
            report_file = os.path.join(self.config_path, f'report_{self.today_date}.txt')
            with open(report_file, 'w') as f:
                f.write(report)
            print(f"\nReport saved to {report_file}")

def main():
    parser = argparse.ArgumentParser(description='Track daily activities and generate reports')
    parser.add_argument('--report', action='store_true', help='Generate report without tracking')
    parser.add_argument('--configure', action='store_true', help='Edit configuration')
    args = parser.parse_args()
    
    tracker = ActivityTracker()
    
    if args.report:
        report = tracker.generate_daily_report()
        print(report)
        
        # Save report to file
        report_file = os.path.join(tracker.config_path, f'report_{tracker.today_date}.txt')
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"\nReport saved to {report_file}")
    elif args.configure:
        print(f"Configuration file is located at: {tracker.config_file}")
        print("You can edit this file with a text editor to customize tracking settings.")
    else:
        tracker.start_tracking()

if __name__ == "__main__":
    main()