#!/usr/bin/env python3
import os
import argparse
import datetime
from .tracker.activity_tracker import ActivityTracker
from .reporting.report_generator import ReportGenerator
from .config.config_manager import ConfigManager

def main():
    """Main entry point for the activity tracker CLI."""
    parser = argparse.ArgumentParser(description='Track daily activities and generate reports')
    parser.add_argument('--report', action='store_true',
                       help='Generate report without tracking')
    parser.add_argument('--date', type=str,
                       help='Generate report for specific date (YYYY-MM-DD)')
    parser.add_argument('--summary', action='store_true',
                       help='Generate complete summary of all recorded days')
    parser.add_argument('--configure', action='store_true',
                       help='Show configuration file location')
    args = parser.parse_args()

    config_manager = ConfigManager()
    
    if args.summary:
        report_generator = ReportGenerator()
        report = report_generator.generate_complete_summary()
        print(report)
        
        # Save report to file
        summary_file = os.path.join(config_manager.config_path, 'complete_summary.txt')
        with open(summary_file, 'w') as f:
            f.write(report)
        print(f"\nSummary saved to {summary_file}")
    
    elif args.report or args.date:
        report_generator = ReportGenerator()
        report = report_generator.generate_daily_report(args.date)
        print(report)
        
        # Save report to file
        date_str = args.date if args.date else datetime.datetime.now().strftime('%Y-%m-%d')
        report_file = os.path.join(config_manager.config_path, f'report_{date_str}.txt')
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"\nReport saved to {report_file}")
    
    elif args.configure:
        print(f"Configuration file is located at: {config_manager.config_file}")
        print("You can edit this file with a text editor to customize tracking settings.")
    
    else:
        tracker = ActivityTracker()
        tracker.start_tracking()

if __name__ == "__main__":
    main()