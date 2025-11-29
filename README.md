# Turnip
An easy way to edit GitHub repository files locally with automatic syncing.

## Features
- Automatic sync between local files and GitHub
- Cross-platform support (Windows, macOS, Linux)
- Clean, intuitive CLI interface
- Quick setup and easy to use

## Prerequisites
- **Python 3.6+** - [Download here](https://python.org)
- **Git** - [Download here](https://git-scm.com)
- **GitHub Personal Access Token** - [Create one here](https://github.com/settings/tokens)

## Installation

1. Download `turnip-setup.py` from the [latest release](https://github.com/advait-malli/Turnip/releases)
2. Run the installer:
   ```bash
   python3 turnip-setup.py
   ```
3. Follow the setup prompts to enter your GitHub credentials
4. Restart your terminal or run:
   ```bash
   # macOS/Linux
   source ~/.bashrc  # or ~/.zshrc
   
   # Windows: manually add to PATH (instructions provided during setup)
   ```
   
## Usage

Start a new session:
```bash
turnip
```

Enter your repository name when prompted, then use these commands:
- `sync` - Sync local changes to GitHub
- `close` - Sync and close session
- `close -dontsync` - Close without syncing
- `<command>` - Run shell commands in the repo directory

## Support
- Report issues on [GitHub Issues](https://github.com/advait-malli/Turnip/issues)
- Make sure your GitHub token has repo permissions

---
Made with ❤️ by Advait Malli.
