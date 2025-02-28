from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="activity-tracker",
    version="1.0.0",
    author="Activity Tracker Team",
    description="A tool for tracking and analyzing computer usage patterns",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/activity-tracker",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Office/Business :: News/Diary",
        "Topic :: System :: Monitoring",
    ],
    python_requires=">=3.6",
    install_requires=[
        "psutil>=5.7.0",
        "pywin32;platform_system=='Windows'",
    ],
    entry_points={
        "console_scripts": [
            "activity-tracker=activity_tracker.cli:main",
        ],
    },
)