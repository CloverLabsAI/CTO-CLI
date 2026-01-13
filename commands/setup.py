"""
Setup command handler for Worklog CLI.
"""

from config import setup_config


def cmd_setup(args):
    """Run interactive setup."""
    setup_config()
