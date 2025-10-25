# TCE Telegram Monitor

## Overview
This is a Python-based web monitoring bot that scrapes the TCE (tce.by) website for event listings and sends Telegram notifications when events matching specific search criteria are found.

## Project Status
- **Type**: Python console application with Selenium web scraping
- **Last Updated**: October 22, 2025
- **Purpose**: Monitor theater event listings and notify via Telegram when threshold is exceeded

## Key Features
- Web scraping using Selenium with headless Chrome
- Telegram bot integration for notifications
- Configurable search terms and thresholds
- Scheduled execution (originally designed for cron/GitHub Actions)
- Logging to file and console

## Architecture

### Dependencies
- **Python 3.12**: Main runtime
- **Selenium 4.15.2**: Web browser automation
- **Requests 2.31.0**: HTTP client for Telegram API
- **python-dotenv 1.0.0**: Environment variable management
- **BeautifulSoup4 4.12.2**: HTML parsing (installed but not currently used)
- **Chromium + ChromeDriver**: System dependencies for Selenium

### Project Structure
```
.
├── tce_telegram_monitor.py    # Main script
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (not in git)
├── Procfile                   # Process definition
├── workflows/                 # GitHub Actions workflow (original)
└── replit.md                  # This file
```

## Configuration

### Environment Variables
The following variables can be configured in `.env`:

- `BOT_TOKEN`: Telegram bot API token (required for notifications)
- `CHAT_ID`: Telegram chat ID to send messages to
- `SEARCH_TEXT`: Primary search term (default: "Записки юного врача")
- `SEARCH_TEXT_2`: Secondary search term (default: "На чёрной")
- `URL`: Target website URL (default: "https://tce.by/search.html")
- `THRESHOLD`: Minimum events to trigger notification (default: 1)
- `THRESHOLD_2`: Secondary threshold (default: 2)

## Setup in Replit

### Installation
1. Python 3.12 is pre-installed
2. System dependencies (Chromium, ChromeDriver) are installed via Nix
3. Python packages are installed automatically from requirements.txt

### Running the Bot
The script runs once and exits. It:
1. Loads environment variables from `.env`
2. Uses Selenium to navigate to the target website
3. Searches for events matching `SEARCH_TEXT`
4. Counts the results
5. Sends a Telegram notification if count exceeds `THRESHOLD`

### Logs
- Console output: Shows real-time progress
- File output: Saved to `tce_monitor.log`

## Technical Notes

### Selenium Configuration
- Runs in headless mode (no visible browser)
- Uses system-installed ChromeDriver from PATH
- Configured with `--no-sandbox` and `--disable-dev-shm-usage` for container environments
- 20-second timeout for page load and element detection

### Migration from GitHub Actions
- Originally designed to run on GitHub Actions with a cron schedule (every 10 minutes)
- In Replit, runs on-demand via the workflow
- Can be modified to run continuously with a loop if needed

## Flask Web Server

### New Feature: Web Interface
- **File**: `server.py`
- **Port**: 5000
- **Endpoint**: `/run` - запускает скрипт мониторинга по HTTP запросу

Использование:
```
GET http://localhost:5000/run
```
Ответ: "Скрипт выполнен!"

## Recent Changes
- October 25, 2025: Configured GitHub Actions for automated monitoring
  - Set up GitHub Actions workflow to run every 10 minutes
  - Created comprehensive README with setup instructions
  - Configured proper Python 3.11 and Chromium installation
  - Added manual trigger option for workflow
  - Moved workflow to proper .github/workflows/ directory

- October 25, 2025: Completed GitHub import setup
  - Installed Python 3.11 runtime environment
  - Installed all Python dependencies from requirements.txt
  - Installed Chromium and ChromeDriver system dependencies
  - Removed hardcoded API secrets from code for security
  - Set up BOT_TOKEN and CHAT_ID as Replit secrets
  - Created comprehensive Python .gitignore
  - Configured Flask server workflow on port 5000
  - Set up VM deployment configuration
  - Server verified running successfully

- October 22, 2025: Added Flask web server
  - Created `server.py` with `/run` endpoint
  - Updated workflow to run Flask server instead of direct script
  - Installed Flask and dependencies
  
- October 22, 2025: Initial Replit setup
  - Added Chromium and ChromeDriver as system dependencies
  - Updated script to use system ChromeDriver instead of webdriver-manager
  - Moved hardcoded tokens to environment variables for security
  - Converted Windows line endings to Unix format
  - Added comprehensive Python .gitignore rules
  - Created Replit workflow for console execution
