"""
Configuration management for Worklog CLI.
Handles storing and loading API credentials securely.
"""

import json
import os
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.prompt import Prompt, Confirm

console = Console()

CONFIG_DIR = Path.home() / ".worklog"
CONFIG_FILE = CONFIG_DIR / "config.json"
CREDENTIALS_FILE = CONFIG_DIR / "google_credentials.json"
TOKEN_FILE = CONFIG_DIR / "google_token.json"


def ensure_config_dir():
    """Ensure the config directory exists."""
    CONFIG_DIR.mkdir(exist_ok=True)
    # Set restrictive permissions
    os.chmod(CONFIG_DIR, 0o700)


def load_config() -> dict:
    """Load configuration from file."""
    if not CONFIG_FILE.exists():
        return {}
    
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def save_config(config: dict):
    """Save configuration to file."""
    ensure_config_dir()
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
    os.chmod(CONFIG_FILE, 0o600)


def is_configured() -> bool:
    """Check if the tool is configured."""
    if not CONFIG_FILE.exists():
        return False
    config = load_config()
    return bool(config.get("github_token"))


def is_ai_configured() -> bool:
    """Check if AI features are configured."""
    config = load_config()
    return bool(config.get("anthropic_api_key"))


def setup_config():
    """Interactive setup wizard."""
    console.print()
    console.print("[bold cyan]Worklog Setup Wizard[/bold cyan]")
    console.print("=" * 40)
    console.print()
    
    config = load_config()
    
    # GitHub Setup
    console.print("[bold]1. GitHub Configuration[/bold]")
    console.print("   Create a personal access token at: https://github.com/settings/tokens")
    console.print("   Required scopes: [cyan]repo[/cyan] (for private repos) or [cyan]public_repo[/cyan] (for public only)")
    console.print()
    
    github_token = Prompt.ask(
        "   GitHub Personal Access Token",
        password=True,
        default=config.get("github_token", "")[:4] + "..." if config.get("github_token") else ""
    )
    if github_token and not github_token.endswith("..."):
        config["github_token"] = github_token
    
    github_username = Prompt.ask(
        "   GitHub Username",
        default=config.get("github_username", "")
    )
    if github_username:
        config["github_username"] = github_username
    
    console.print()
    
    # Google Calendar Setup
    console.print("[bold]2. Google Calendar Configuration[/bold]")
    console.print("   To access Google Calendar, you need OAuth2 credentials.")
    console.print()
    console.print("   [cyan]Option A: Quick setup (recommended)[/cyan]")
    console.print("   1. Go to https://console.cloud.google.com/")
    console.print("   2. Create a new project (or select existing)")
    console.print("   3. Enable the Google Calendar API")
    console.print("   4. Go to 'Credentials' → 'Create Credentials' → 'OAuth client ID'")
    console.print("   5. Choose 'Desktop application'")
    console.print("   6. Download the JSON file")
    console.print()
    
    creds_path = Prompt.ask(
        "   Path to Google OAuth credentials JSON file (or press Enter to skip)",
        default=str(CREDENTIALS_FILE) if CREDENTIALS_FILE.exists() else ""
    )
    
    if creds_path and creds_path != str(CREDENTIALS_FILE):
        # Copy credentials to config dir
        import shutil
        ensure_config_dir()
        shutil.copy(creds_path, CREDENTIALS_FILE)
        os.chmod(CREDENTIALS_FILE, 0o600)
        console.print("   [green]✓ Credentials file copied[/green]")
    
    console.print()
    
    # Chrome Profile Setup
    console.print("[bold]3. Chrome History Configuration[/bold]")
    console.print("   Chrome history is read directly from your local browser database.")
    console.print("   Note: Chrome must be closed when reading history (or we'll copy the database).")
    console.print()

    # Detect Chrome profile
    default_profile = detect_chrome_profile()
    chrome_profile = Prompt.ask(
        "   Chrome profile name",
        default=config.get("chrome_profile", default_profile or "Default")
    )
    config["chrome_profile"] = chrome_profile

    console.print()

    # Slack Setup
    console.print("[bold]4. Slack Configuration (Optional)[/bold]")
    console.print("   To access your Slack messages, you need a User OAuth Token.")
    console.print()
    console.print("   [cyan]Setup steps:[/cyan]")
    console.print("   1. Go to https://api.slack.com/apps")
    console.print("   2. Click 'Create New App' → 'From scratch'")
    console.print("   3. Go to 'OAuth & Permissions'")
    console.print("   4. Add scope: [cyan]search:read[/cyan]")
    console.print("   5. Install to workspace and copy the User OAuth Token")
    console.print()

    slack_token = Prompt.ask(
        "   Slack User OAuth Token (or press Enter to skip)",
        password=True,
        default=config.get("slack_token", "")[:10] + "..." if config.get("slack_token") else ""
    )
    if slack_token and not slack_token.endswith("..."):
        config["slack_token"] = slack_token

    console.print()

    # Anthropic API Key Setup
    console.print("[bold]5. AI Assistant Configuration (Optional)[/bold]")
    console.print("   Get your API key at: https://console.anthropic.com/")
    console.print()

    anthropic_key = Prompt.ask(
        "   Anthropic API Key (or press Enter to skip)",
        password=True,
        default=config.get("anthropic_api_key", "")[:8] + "..." if config.get("anthropic_api_key") else ""
    )
    if anthropic_key and not anthropic_key.endswith("..."):
        config["anthropic_api_key"] = anthropic_key

    console.print()

    # Save config
    save_config(config)
    console.print("[green]✓ Configuration saved to ~/.worklog/config.json[/green]")
    console.print()
    
    # Test connections
    if Confirm.ask("Would you like to test the connections now?", default=True):
        test_connections(config)


def detect_chrome_profile() -> Optional[str]:
    """Detect available Chrome profiles."""
    import platform
    
    system = platform.system()
    
    if system == "Darwin":  # macOS
        chrome_dir = Path.home() / "Library/Application Support/Google/Chrome"
    elif system == "Windows":
        chrome_dir = Path.home() / "AppData/Local/Google/Chrome/User Data"
    else:  # Linux
        chrome_dir = Path.home() / ".config/google-chrome"
    
    if chrome_dir.exists():
        profiles = [d.name for d in chrome_dir.iterdir() if d.is_dir() and (d / "History").exists()]
        if profiles:
            return profiles[0]
    
    return "Default"


def test_connections(config: dict):
    """Test all configured connections."""
    console.print()
    console.print("[bold]Testing connections...[/bold]")
    console.print()
    
    # Test GitHub
    if config.get("github_token"):
        try:
            import requests
            headers = {"Authorization": f"token {config['github_token']}"}
            resp = requests.get("https://api.github.com/user", headers=headers)
            if resp.status_code == 200:
                user = resp.json()
                console.print(f"   [green]✓ GitHub:[/green] Connected as {user['login']}")
            else:
                console.print(f"   [red]✗ GitHub:[/red] Authentication failed ({resp.status_code})")
        except Exception as e:
            console.print(f"   [red]✗ GitHub:[/red] {e}")
    else:
        console.print("   [yellow]○ GitHub:[/yellow] Not configured")
    
    # Test Google Calendar
    if CREDENTIALS_FILE.exists():
        try:
            from sources import test_calendar_connection
            if test_calendar_connection(config):
                console.print("   [green]✓ Google Calendar:[/green] Connected")
            else:
                console.print("   [yellow]○ Google Calendar:[/yellow] Needs authentication (will prompt on first use)")
        except Exception as e:
            console.print(f"   [red]✗ Google Calendar:[/red] {e}")
    else:
        console.print("   [yellow]○ Google Calendar:[/yellow] Credentials not configured")

    # Test Chrome History
    try:
        from sources import test_chrome_access
        if test_chrome_access(config.get("chrome_profile")):
            console.print("   [green]✓ Chrome History:[/green] Accessible")
        else:
            console.print("   [red]✗ Chrome History:[/red] Could not access history database")
    except Exception as e:
        console.print(f"   [red]✗ Chrome History:[/red] {e}")

    # Test Slack
    if config.get("slack_token"):
        try:
            from sources import get_slack_user_info
            user_info = get_slack_user_info(config)
            if user_info:
                console.print(f"   [green]✓ Slack:[/green] Connected as {user_info['user']} ({user_info['team']})")
            else:
                console.print("   [red]✗ Slack:[/red] Could not authenticate")
        except Exception as e:
            console.print(f"   [red]✗ Slack:[/red] {e}")
    else:
        console.print("   [yellow]○ Slack:[/yellow] Not configured")

    # Test Anthropic API
    if config.get("anthropic_api_key"):
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=config["anthropic_api_key"])
            # Make a minimal API call to verify the key works
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            console.print("   [green]✓ Anthropic:[/green] API key valid")
        except Exception as e:
            console.print(f"   [red]✗ Anthropic:[/red] {e}")
    else:
        console.print("   [yellow]○ Anthropic:[/yellow] Not configured")

    console.print()
