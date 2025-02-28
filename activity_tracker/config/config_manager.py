#!/usr/bin/env python3
import os
import json
from pathlib import Path

class ConfigManager:
    """Manages configuration loading, saving, and defaults for the activity tracker."""
    
    DEFAULT_CONFIG = {
        'track_applications': True,
        'track_documents': True,
        'ignored_apps': ['explorer.exe', 'Finder', 'SystemUI'],
        'categories': {
            'Coding': ['vscode', 'pycharm', 'intellij', 'sublime_text', 'vim', 'atom', 'code'],
            'Communication': ['outlook', 'thunderbird', 'slack', 'teams', 'discord', 'zoom'],
            'Browsing': ['chrome', 'firefox', 'safari', 'edge'],
            'Documents': ['word', 'excel', 'powerpoint', 'acrobat', 'pdf'],
            'Terminal': ['terminal', 'cmd', 'powershell', 'iterm2', 'gnome-terminal', 'konsole'],
            'Design': ['photoshop', 'illustrator', 'figma', 'sketch', 'gimp'],
            'Media': ['vlc', 'spotify', 'itunes', 'windows media player'],
            'Other': []
        },
        'sampling_interval': 30
    }
    
    def __init__(self, config_file='activity_config.json'):
        """Initialize the configuration manager.
        
        Args:
            config_file (str): Name of the configuration file
        """
        self.home_dir = str(Path.home())
        self.config_path = os.path.join(self.home_dir, '.activity_tracker')
        self.config_file = os.path.join(self.config_path, config_file)
        self.ensure_config_directory()
        self.config = self.load_config()
        
    def ensure_config_directory(self):
        """Create configuration directory if it doesn't exist."""
        if not os.path.exists(self.config_path):
            os.makedirs(self.config_path)

    def load_config(self):
        """Load configuration from file or create default if it doesn't exist.
        
        Returns:
            dict: The loaded configuration
        """
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            self.save_config(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG

    def save_config(self, config):
        """Save configuration to file.
        
        Args:
            config (dict): Configuration to save
        """
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)

    def get_config(self):
        """Get the current configuration.
        
        Returns:
            dict: The current configuration
        """
        return self.config

    def get_sampling_interval(self):
        """Get the configured sampling interval.
        
        Returns:
            int: Sampling interval in seconds
        """
        return self.config.get('sampling_interval', 30)

    def get_log_path(self, date_str):
        """Get the path for an activity log file.
        
        Args:
            date_str (str): Date string in YYYY-MM-DD format
        
        Returns:
            str: Full path to the activity log file
        """
        return os.path.join(self.config_path, f'activity_{date_str}.json')