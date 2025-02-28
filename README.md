# Activity Tracker

A Python tool for tracking and analyzing computer usage patterns. This application monitors active windows and applications, categorizes activities, and generates detailed reports about your computer usage.

## Features

- Cross-platform support (Windows, macOS, Linux)
- Real-time activity tracking
- Activity categorization
- Daily and summary reports
- Configurable tracking settings
- Idle detection

## Installation

### Prerequisites

- Python 3.6 or higher
- Platform-specific dependencies:
  - Windows: pywin32
  - Linux: xdotool
  - macOS: No additional dependencies

### Installing from source

```bash
git clone https://github.com/yourusername/activity-tracker.git
cd activity-tracker
pip install .
```

## Usage

### Start Tracking

To start tracking your activities:

```bash
activity-tracker
```

The tracker will run in the foreground and log your activities. Press Ctrl+C to stop tracking.

### Generate Reports

Generate a report for today:
```bash
activity-tracker --report
```

Generate a report for a specific date:
```bash
activity-tracker --date 2024-02-26
```

Generate a complete summary of all recorded days:
```bash
activity-tracker --summary
```

### Configuration

The configuration file is located at `~/.activity_tracker/activity_config.json`. You can view its location using:

```bash
activity-tracker --configure
```

Example configuration:
```json
{
    "track_applications": true,
    "track_documents": true,
    "ignored_apps": ["explorer.exe", "Finder", "SystemUI"],
    "categories": {
        "Coding": ["vscode", "pycharm", "intellij"],
        "Communication": ["outlook", "slack", "teams"],
        "Browsing": ["chrome", "firefox", "safari"],
        "Documents": ["word", "excel", "powerpoint"]
    },
    "sampling_interval": 30
}
```

## Project Structure

```
activity_tracker/
├── __init__.py
├── cli.py
├── config/
│   ├── __init__.py
│   └── config_manager.py
├── tracker/
│   ├── __init__.py
│   ├── activity_tracker.py
│   └── window_tracker.py
└── reporting/
    ├── __init__.py
    └── report_generator.py
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.