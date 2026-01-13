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
- **Linear** - Issues, projects, and audit logs (optional)

## Features

- **Daily/Weekly/Monthly Summaries** - View formatted work summaries for any time period
- **AI CTO Agent** - Conversational AI that generates standup notes, weekly reports, and answers questions about your work
- **Linear Integration** - Query your Linear workspace, search issues, view projects, and analyze audit logs
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
cto chat -q "What are my open Linear issues?"
cto chat -q "Show me the audit logs from last week"
```

#### Example Interactions

```
You: Generate my standup notes

CTO Agent:
### Standup - January 12, 2026

**Yesterday:**
- Attended Sprint Planning meeting (1h)
- Committed 3 changes to experiments repo
- Worked on ENG-123: Add user authentication

**Today:**
- Team sync at 10:00 AM
- Continue CLI development

**Blockers:**
- None
```

```
You: What Linear issues am I working on?

CTO Agent:
You currently have 5 issues assigned:

**In Progress:**
- ENG-156: Implement Linear MCP integration
- ENG-148: Add audit log viewer

**Todo:**
- ENG-162: Update documentation
- ENG-163: Add unit tests
- ENG-170: Performance optimization
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
2. Create an app and add these User Token Scopes:
   - `search:read` - Search messages
   - `im:history`, `im:read` - DMs
   - `mpim:history`, `mpim:read` - Group DMs
   - `channels:history`, `channels:read` - Public channels
   - `groups:history`, `groups:read` - Private channels
   - `users:read` - User names
3. Install to your workspace and copy the User OAuth Token

### Linear (Optional)
1. Go to [Linear Settings → API](https://linear.app/settings/api)
2. Click "Create key" under Personal API keys
3. Give it a label (e.g., "CTO CLI")
4. Copy the generated key and provide it during setup

**Note:** Audit logs require Linear Plus plan and admin access.

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
| "Linear API key not configured" | Run `cto setup` to add your Linear API key |
| "Anthropic API key not configured" | Run `cto setup` to add your API key |

## Privacy

All data is processed locally. Credentials are stored in `~/.worklog/` with restricted permissions. Data is only sent to the respective APIs (Google, GitHub, Slack, Linear, Anthropic) as needed.

## License

MIT License
