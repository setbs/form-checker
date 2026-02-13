import json
import re
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from shutil import which

from playwright.sync_api import TimeoutError, sync_playwright

FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeXDOh_uD7b4LEqVBfkbaMu_TqiR9ObwvnNc41ySPaR-y-y1A/viewform"
CONFIG_PATH = Path(__file__).with_name("config.json")
DEFAULT_REPORT_PATH = Path(__file__).with_name("reports.json")


def load_config():
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Missing config.json. Copy config.example.json to config.json and fill it in."
        )
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def log(message: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {message}")


def write_report(report_path: Path, entry: dict):
    if report_path.exists():
        try:
            data = json.loads(report_path.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                data = []
        except json.JSONDecodeError:
            data = []
    else:
        data = []

    data.append(entry)
    report_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def send_ntfy(config: dict, title: str, message: str):
    topic = config.get("ntfy_topic")
    if not topic:
        return

    server = config.get("ntfy_server", "https://ntfy.sh").rstrip("/")
    url = f"{server}/{topic}"

    req = urllib.request.Request(
        url=url,
        data=message.encode("utf-8"),
        method="POST",
        headers={"Title": title},
    )
    with urllib.request.urlopen(req, timeout=10):
        pass


def check_once(config: dict) -> list[str]:
    email = config["email"]
    name = config["name"]
    courier_id = str(config["courier_id"])

    with sync_playwright() as p:
        chromium_path = which("chromium") or which("chromium-browser")
        launch_kwargs = {"headless": config.get("headless", True)}
        if chromium_path:
            launch_kwargs["executable_path"] = chromium_path

        browser = p.chromium.launch(**launch_kwargs)
        page = browser.new_page()
        page.goto(FORM_URL, wait_until="domcontentloaded")

        # Page 1: email
        try:
            page.get_by_label(
                re.compile(r"Elektroniczna|Email|E-mail|Электронн", re.I)
            ).first.fill(email)
        except TimeoutError:
            page.locator(
                'input[type="email"], input[aria-label*="mail" i], input[aria-label*="почт" i]'
            ).first.fill(email)
        page.get_by_role("button", name=re.compile(r"Dalej|Next|Далее", re.I)).click()

        # Page 2: name + ID + radio
        try:
            page.get_by_label(
                re.compile(r"Imi[ęe] Nazwisko|First and Last name|Имя", re.I)
            ).first.fill(name)
        except TimeoutError:
            page.locator('input[type="text"]').nth(0).fill(name)

        try:
            page.get_by_label(
                re.compile(r"Podaj swoje ID|Please provide your ID|ID|ид", re.I)
            ).first.fill(courier_id)
        except TimeoutError:
            page.locator('input[type="text"]').nth(1).fill(courier_id)

        try:
            page.get_by_role("radio", name=re.compile(r"Chcę przyjąć|I want to accept", re.I)).click()
        except TimeoutError:
            page.locator('div[role="radiogroup"] [role="radio"]').nth(1).click()
        page.get_by_role("button", name=re.compile(r"Dalej|Next|Далее", re.I)).click()

        # Page 3: city
        page.get_by_role("radio", name=re.compile(r"Wrocław|Wroclaw", re.I)).click()
        page.get_by_role("button", name=re.compile(r"Dalej|Next|Далее", re.I)).click()

        # Page 4: shifts dropdown
        try:
            combobox = page.get_by_role("combobox").first
            combobox.click()
            page.wait_for_timeout(500)
            options = [
                o.strip()
                for o in page.get_by_role("option").all_text_contents()
                if o.strip()
            ]
        except TimeoutError:
            options = []
        finally:
            browser.close()

    return options


def main():
    config = load_config()
    poll_minutes = int(config.get("poll_minutes", 10))
    report_path = Path(config.get("report_path", DEFAULT_REPORT_PATH))
    notify_on_found = bool(config.get("notify_on_found", True))

    log("Starting form checker...")
    last_shifts: set[str] = set()
    while True:
        try:
            options = check_once(config)
            if options:
                log(f"Available shifts found: {options}")
            else:
                log("No available shifts.")

            current_shifts = set(options)
            new_shifts = sorted(current_shifts - last_shifts)
            if notify_on_found and new_shifts:
                send_ntfy(
                    config,
                    "New shifts available",
                    f"New shifts: {new_shifts}",
                )
            last_shifts = current_shifts

            write_report(
                report_path,
                {
                    "timestamp": datetime.now().isoformat(),
                    "available": bool(options),
                    "shifts": options,
                    "new_shifts": new_shifts,
                },
            )
        except Exception as e:
            log(f"Error: {e}")
            write_report(
                report_path,
                {
                    "timestamp": datetime.now().isoformat(),
                    "available": False,
                    "shifts": [],
                    "error": str(e),
                },
            )

        log(f"Sleeping for {poll_minutes} minutes...")
        time.sleep(poll_minutes * 60)


if __name__ == "__main__":
    main()
