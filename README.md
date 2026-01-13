# CTO CLI

An AI-powered command-line tool that gives you a daily breakdown of your work by aggregating data from multiple sources, with an intelligent CTO agent for generating reports and insights.

## Quick Install

```bash
curl -sSL https://raw.githubusercontent.com/CloverLabsAI/CTO-CLI/main/install.sh | bash
```

Then add `~/.local/bin` to your PATH (if not already):
```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

Run setup to configure your credentials:
```bash
cto setup
```

## Data Sources

- **Google Calendar** - Your meetings and events
- **Chrome History** - What you searched and researched
- **GitHub** - Your code commits
- **Slack** - Messages you sent (optional)

## Features

- **Daily/Weekly/Monthly Summaries** - View formatted work summaries for any time period
- **AI CTO Agent** - Conversational AI that generates standup notes, weekly reports, and answers questions about your work
- **Flexible Date Queries** - Query by specific dates, weeks, or months

## Usage

### Today's Summary
```bash
cto                    # Show today's work summary
cto --yesterday        # Show yesterday's summary
cto --date 2024-01-15  # Show summary for a specific date
```

### Week/Month Summaries
```bash
cto week               # Current week
cto week 2             # Week 2 of current year
cto month              # Current month
cto month january      # January of current year
```

### AI CTO Agent

Start an interactive conversation:
```bash
cto chat
```

Ask a single question:
```bash
cto chat -q "Generate my standup notes"
cto chat -q "What did I work on this week?"
cto chat -q "Create a weekly report"
```

#### Example Interactions

```
You: Generate my standup notes

CTO Agent:
### Standup - January 12, 2026

**Yesterday:**
- Attended Sprint Planning meeting (1h)
- Committed 3 changes to experiments repo
- Researched Chrome history database structure

**Today:**
- Team sync at 10:00 AM
- Continue CLI development

**Blockers:**
- None
```

## Setup Guide

Run `cto setup` to configure all integrations. Here's what you'll need:

### GitHub
1. Go to [GitHub Settings → Personal Access Tokens](https://github.com/settings/tokens)
2. Generate a new token with `repo` scope
3. Provide the token during setup

### Google Calendar
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project and enable the **Google Calendar API**
3. Create OAuth credentials (Desktop application)
4. Download the JSON file and provide its path during setup

### Slack (Optional)
1. Go to [Slack API Apps](https://api.slack.com/apps)
2. Create an app with `search:read` scope
3. Install to your workspace and copy the User OAuth Token

### AI Agent (Optional)
1. Get an API key from [Anthropic Console](https://console.anthropic.com/)
2. Provide it during setup

## Configuration

Configuration is stored in `~/.worklog/`:
- `config.json` - API tokens and settings
- `google_credentials.json` - Google OAuth credentials
- `google_token.json` - Google OAuth token (auto-generated)

## Manual Installation

If you prefer not to use the install script:

```bash
git clone https://github.com/CloverLabsAI/CTO-CLI.git
cd CTO-CLI
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Cannot access Chrome history" | Close Chrome or the tool will copy the database |
| "Google credentials not found" | Run `cto setup` and provide OAuth JSON path |
| "GitHub authentication failed" | Generate a new token at github.com/settings/tokens |
| "Anthropic API key not configured" | Run `cto setup` to add your API key |

## Privacy

All data is processed locally. Credentials are stored in `~/.worklog/` with restricted permissions. Data is only sent to the respective APIs (Google, GitHub, Slack, Anthropic) as needed.

## License

MIT License
