# Form Checker

Checks a Google Form for available courier shifts every N minutes.

## Setup

1. Install dependencies.
2. Install Playwright browsers.
3. Create `config.json` from the example.

## Commands

- Install deps: `pip install -r requirements.txt`
- Install browsers: `playwright install`
- Run: `python check_shifts.py`

## Config

Copy `config.example.json` to `config.json` and fill it in.

Fields:
- `email`
- `name`
- `courier_id`
- `poll_minutes`
- `headless`
- `report_path`
- `notify_on_found`
- `ntfy_server`
- `ntfy_topic`

## Ntfy notifications (iOS)

1. Install the ntfy app on iOS.
2. Pick a topic name (any string).
3. Put it into `ntfy_topic` in your config.
4. Subscribe to `https://ntfy.sh/<your-topic>` in the app.
