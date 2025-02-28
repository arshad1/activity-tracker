#!/usr/bin/env python3
import os
import json
import datetime
from ..config.config_manager import ConfigManager

class ReportGenerator:
    """Generates activity reports from logged data."""

    def __init__(self, config_file='activity_config.json'):
        """Initialize the report generator.
        
        Args:
            config_file (str): Name of the configuration file
        """
        self.config_manager = ConfigManager(config_file)

    def generate_daily_report(self, date=None):
        """Generate a report of activities for the specified date or today.
        
        Args:
            date (str, optional): Date string in YYYY-MM-DD format
            
        Returns:
            str: Formatted report string
        """
        if date is None:
            date = datetime.datetime.now().strftime('%Y-%m-%d')

        activity_file = self.config_manager.get_log_path(date)
        if not os.path.exists(activity_file):
            return f"No activities logged for {date}."

        try:
            with open(activity_file, 'r') as f:
                activities = json.load(f)
        except json.JSONDecodeError:
            return f"Error: Invalid activity data for {date}."

        if not activities:
            return f"No activities logged for {date}."

        total_time = sum(a['duration'] for a in activities)
        category_times = {}
        app_times = {}

        for activity in activities:
            category = activity['category']
            app = activity['app']
            duration = activity['duration']

            category_times[category] = category_times.get(category, 0) + duration
            app_times[app] = app_times.get(app, 0) + duration

        # Format report
        report = f"Activity Report for {date}\n"
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
        for app, time_spent in sorted(app_times.items(), key=lambda x: x[1], reverse=True)[:10]:
            minutes = time_spent / 60
            report += f"{app}: {minutes:.1f} minutes\n"

        report += "\n"

        # Detailed activity list
        report += "Detailed Activities:\n"
        report += "-" * 20 + "\n"

        # Group activities by hour for easier reading
        hour_activities = {}
        for activity in activities:
            timestamp = datetime.datetime.fromisoformat(activity['timestamp'])
            hour = timestamp.strftime('%H:00')
            if hour not in hour_activities:
                hour_activities[hour] = []
            hour_activities[hour].append(activity)

        # Print activities by hour
        for hour, hour_acts in sorted(hour_activities.items()):
            report += f"\n{hour}\n"
            for activity in hour_acts:
                app = activity['app']
                title = activity['title']
                duration = activity['duration'] / 60  # convert to minutes
                if duration >= 1:  # Only show activities that took at least a minute
                    report += f"  - {app}: {title[:50]}{'...' if len(title) > 50 else ''} ({duration:.1f} min)\n"

        return report

    def generate_complete_summary(self):
        """Generate a summary report for all recorded days.
        
        Returns:
            str: Formatted summary report
        """
        # Get all activity files
        activity_files = [f for f in os.listdir(self.config_manager.config_path)
                         if f.startswith('activity_') and f.endswith('.json')]

        if not activity_files:
            return "No activity data found."

        # Collect data from all files
        all_days = {}
        category_totals = {}
        app_totals = {}
        total_time_all = 0

        for file in activity_files:
            date = file.replace('activity_', '').replace('.json', '')
            file_path = os.path.join(self.config_manager.config_path, file)

            try:
                with open(file_path, 'r') as f:
                    activities = json.load(f)

                if not isinstance(activities, list):
                    print(f"Warning: Skipping {file} - invalid format")
                    continue

                if not activities:
                    continue

                # Daily totals
                day_total = sum(a.get('duration', 0) for a in activities if isinstance(a, dict))
                all_days[date] = day_total
                total_time_all += day_total

                # Category and app totals
                for activity in activities:
                    category = activity['category']
                    app = activity['app']
                    duration = activity['duration']

                    category_totals[category] = category_totals.get(category, 0) + duration
                    app_totals[app] = app_totals.get(app, 0) + duration

            except (json.JSONDecodeError, Exception) as e:
                print(f"Warning: Error processing {file}: {e}")
                continue

        # Format report
        report = "Complete Activity Summary\n"
        report += "=" * 40 + "\n\n"

        # Summary by day
        report += "Time by Day:\n"
        report += "-" * 20 + "\n"
        for date, time_spent in sorted(all_days.items()):
            hours = time_spent / 3600
            report += f"{date}: {hours:.2f} hours\n"

        report += "\n"

        # Category breakdown
        report += "Time by Category:\n"
        report += "-" * 20 + "\n"
        for category, time_spent in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
            hours = time_spent / 3600
            report += f"{category}: {hours:.2f} hours ({(time_spent/total_time_all)*100:.1f}%)\n"

        report += "\n"

        # Application breakdown
        report += "Time by Application:\n"
        report += "-" * 20 + "\n"
        for app, time_spent in sorted(app_totals.items(), key=lambda x: x[1], reverse=True)[:15]:
            hours = time_spent / 3600
            report += f"{app}: {hours:.2f} hours\n"

        return report