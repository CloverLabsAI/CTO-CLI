# Worklog CLI

A command-line tool that gives you a daily breakdown of your work by aggregating data from multiple sources, with an AI-powered CTO agent for generating reports and insights.

## Data Sources

- **Google Calendar** - Your meetings and events
- **Chrome History** - What you searched and researched
- **GitHub** - Your code commits
- **Slack** - Messages you sent (optional)

## Features

- **Daily/Weekly/Monthly Summaries** - View formatted work summaries for any time period
- **AI CTO Agent** - Conversational AI that generates standup notes, weekly reports, and answers questions about your work
- **Flexible Date Queries** - Query by specific dates, weeks, or months

## Installation

1. Clone or download this repository

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. (Optional) Make it globally accessible:
   ```bash
   # Add to your shell profile (.bashrc, .zshrc, etc.)
   alias worklog="/path/to/cto_cli/.venv/bin/python /path/to/cto_cli/worklog.py"
   ```

## Setup

Run the setup wizard to configure your credentials:

```bash
python worklog.py setup
```

This will guide you through configuring:
1. GitHub Personal Access Token
2. Google Calendar OAuth credentials
3. Chrome profile selection
4. Slack User OAuth Token (optional)
5. Anthropic API key for AI features (optional)

### Google Calendar Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable the **Google Calendar API**:
   - Go to "APIs & Services" → "Library"
   - Search for "Google Calendar API"
   - Click "Enable"
4. Create OAuth credentials:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Choose "Desktop application"
   - Download the JSON file
5. During `worklog setup`, provide the path to this JSON file

On first run, a browser window will open for you to authorize access to your calendar.

### GitHub Setup

1. Go to [GitHub Settings → Developer Settings → Personal Access Tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Give it a name like "worklog-cli"
4. Select scopes:
   - `repo` (for private repos) OR
   - `public_repo` (for public repos only)
5. Copy the token and provide it during `worklog setup`

### Chrome History

Chrome history is read directly from your local browser database. The setup wizard will detect available Chrome profiles.

**Note:** Chrome must be closed when reading history, or the tool will copy the database first.

### Slack Setup (Optional)

1. Go to [Slack API Apps](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Go to "OAuth & Permissions"
4. Add User Token Scope: `search:read`
5. Install the app to your workspace
6. Copy the **User OAuth Token** (starts with `xoxp-`)
7. Provide it during `worklog setup`

### AI Agent Setup (Optional)

1. Get an API key from [Anthropic Console](https://console.anthropic.com/)
2. Provide it during `worklog setup`

## Usage

### Today's Summary
```bash
python worklog.py
# or: worklog (if you set up the alias)
```

### Yesterday's Summary
```bash
python worklog.py --yesterday
# or: worklog -y
```

### Specific Date
```bash
python worklog.py --date 2024-01-15
# or: worklog -d 2024-01-15
# or: worklog day 2024-01-15
```

### Week Summary
```bash
python worklog.py week              # Current week
python worklog.py week 2            # Week 2 of current year
python worklog.py week 2024-W03     # Week 3 of 2024
```

### Month Summary
```bash
python worklog.py month             # Current month
python worklog.py month january     # January of current year
python worklog.py month 2024-01     # January 2024
```

### AI CTO Agent

Start an interactive conversation with the AI agent:
```bash
python worklog.py chat
```

Ask a single question:
```bash
python worklog.py chat -q "Generate my standup notes"
python worklog.py chat -q "What did I work on this week?"
python worklog.py chat -q "Create a weekly report"
python worklog.py chat -q "Summarize my Slack activity yesterday"
```

Use a different model:
```bash
python worklog.py chat -m claude-opus-4-20250514
```

#### Example AI Agent Interactions

```
You: Generate my standup notes

CTO Agent:
### Standup - January 12, 2026

**Yesterday:**
- Attended Sprint Planning meeting (1h)
- Committed 3 changes to experiments repo (worklog CLI improvements)
- Researched Chrome history database structure

**Today:**
- Team sync at 10:00 AM
- Continue worklog CLI development

**Blockers:**
- None
```

```
You: Create a weekly report

CTO Agent:
### Weekly Report - Week 2

**Key Accomplishments:**
- Implemented AI CTO agent with Claude integration
- Added Slack message integration
- Built flexible date range queries (day/week/month)

**Meetings & Collaboration:**
- 5 meetings totaling 4.5 hours
- Sprint planning, team syncs, 1:1s

**Code Contributions:**
- 12 commits across 2 repositories
- +850 lines added, -120 lines deleted

**Communication:**
- Active discussions in #engineering and #product channels

**Research & Learning:**
- Anthropic API documentation
- Slack API integration patterns
```

## Configuration

Configuration is stored in `~/.worklog/`:

- `config.json` - API tokens and settings
- `google_credentials.json` - Google OAuth client credentials
- `google_token.json` - Your Google OAuth token (auto-generated)

### Config File Structure

```json
{
  "github_token": "ghp_...",
  "github_username": "yourusername",
  "chrome_profile": "Default",
  "slack_token": "xoxp-...",
  "anthropic_api_key": "sk-ant-..."
}
```

## Troubleshooting

### "Cannot access Chrome history"
Chrome locks its database while running. Either:
- Close Chrome before running worklog, OR
- The tool will automatically copy the database (may be slightly outdated)

### "Google credentials not found"
Run `worklog setup` and provide the path to your OAuth credentials JSON file.

### "GitHub authentication failed"
Your token may have expired. Generate a new one at https://github.com/settings/tokens

### "Anthropic API key not configured"
Run `worklog setup` to add your Anthropic API key, or add it manually to `~/.worklog/config.json`

### "Slack API error"
Ensure your Slack token has the `search:read` scope and the app is installed to your workspace.

## Privacy

All data is processed locally. Your credentials are stored in `~/.worklog/` with restricted permissions (readable only by you).

Data is only sent to:
- Google Calendar API (for calendar events)
- GitHub API (for commits)
- Slack API (for messages, if configured)
- Anthropic API (for AI features, if configured)

No data is stored on external servers beyond what these APIs require for operation.

## License

MIT License - Feel free to modify and share!
