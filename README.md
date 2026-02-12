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
