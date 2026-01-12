# Worklog CLI

A command-line tool that gives you a daily breakdown of your work by aggregating data from:

- 📅 **Google Calendar** - Your meetings and events
- 🔍 **Chrome History** - What you searched and researched
- 💻 **GitHub** - Your code commits

## Installation

1. Clone or download this repository

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. (Optional) Make it globally accessible:
   ```bash
   # Add to your shell profile (.bashrc, .zshrc, etc.)
   alias worklog="python /path/to/worklog/worklog.py"
   ```

## Setup

Run the setup wizard to configure your credentials:

```bash
python worklog.py setup
```

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

Chrome history is read directly from your local browser database. No additional setup needed!

**Note:** Chrome must be closed when reading history, or the tool will copy the database first.

## Usage

### Today's Summary
```bash
python worklog.py
# or just: worklog (if you set up the alias)
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
```

### Past Week
```bash
python worklog.py week
```

## Example Output

```
╔══════════════════════════════════════════════════════════════╗
║           Work Summary for Monday, January 15, 2024          ║
╚══════════════════════════════════════════════════════════════╝

📅 Calendar Events
╭────────────────────┬──────────────────────────────┬────────────╮
│ Time               │ Event                        │ Duration   │
├────────────────────┼──────────────────────────────┼────────────┤
│ 09:00 - 09:30      │ Daily Standup                │ 30m        │
│ 10:00 - 11:00      │ Sprint Planning              │ 1h 0m      │
│ 14:00 - 15:00      │ 1:1 with Manager             │ 1h 0m      │
╰────────────────────┴──────────────────────────────┴────────────╯

🔍 Search History
╭────────────┬────────────────────────────────────┬──────────────╮
│ Time       │ Search Query / Page Title          │ URL          │
├────────────┼────────────────────────────────────┼──────────────┤
│ 09:45      │ python async best practices        │ google.com...│
│ 10:30      │ FastAPI documentation              │ fastapi.ti...│
│ 11:15      │ PostgreSQL index optimization      │ postgresql...│
╰────────────┴────────────────────────────────────┴──────────────╯

💻 GitHub Commits
╭────────────┬─────────────────────────┬─────────────────────────┬─────────────╮
│ Time       │ Repository              │ Commit Message          │ Changes     │
├────────────┼─────────────────────────┼─────────────────────────┼─────────────┤
│ 16:30      │ myorg/api-service       │ Add user authentication │ +245/-32    │
│ 14:15      │ myorg/api-service       │ Fix database connection │ +12/-8      │
│ 11:00      │ myorg/frontend          │ Update dashboard styles │ +89/-45     │
╰────────────┴─────────────────────────┴─────────────────────────┴─────────────╯

📊 Summary
 Metric                Value
 Calendar events       3
 Searches/pages        15
 Commits               3
 Lines added           +346
 Lines deleted         -85
```

## Configuration

Configuration is stored in `~/.worklog/`:

- `config.json` - API tokens and settings
- `google_credentials.json` - Google OAuth client credentials
- `google_token.json` - Your Google OAuth token (auto-generated)

## Troubleshooting

### "Cannot access Chrome history"
Chrome locks its database while running. Either:
- Close Chrome before running worklog, OR
- The tool will automatically copy the database (may be slightly outdated)

### "Google credentials not found"
Run `worklog setup` and provide the path to your OAuth credentials JSON file.

### "GitHub authentication failed"
Your token may have expired. Generate a new one at https://github.com/settings/tokens

## Privacy

All data is processed locally. Your credentials are stored in `~/.worklog/` with restricted permissions (readable only by you). No data is sent to any third-party servers except the official Google and GitHub APIs.

## License

MIT License - Feel free to modify and share!
