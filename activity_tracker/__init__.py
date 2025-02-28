"""Activity Tracker - A tool for tracking and analyzing computer usage patterns.

This package provides functionality to track active windows and applications,
categorize activities, and generate detailed reports about computer usage.
"""

from .tracker.activity_tracker import ActivityTracker
from .reporting.report_generator import ReportGenerator
from .config.config_manager import ConfigManager

__version__ = '1.0.0'
__author__ = 'Activity Tracker Team'

__all__ = ['ActivityTracker', 'ReportGenerator', 'ConfigManager']