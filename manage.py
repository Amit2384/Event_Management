#!/usr/bin/env python3
"""
Django's command-line utility for administrative tasks.
This script is used to manage your Event Management System project.
It allows you to run the development server, execute migrations,
create superusers, collect static files, and more.
"""

import os
import sys


def main():
    """Run administrative tasks."""
    # Ensure the settings module points to the correct Django project
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_system.settings')

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Make sure it is installed and "
            "available on your PYTHONPATH environment variable. "
            "You can install dependencies using 'pip install -r requirements.txt'."
        ) from exc

    # Execute command line arguments (example: runserver, migrate, createsuperuser, etc.)
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()