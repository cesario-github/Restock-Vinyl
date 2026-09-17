"""
Restock-Checker fuer die GTA 6: The Album - Limited Edition Vinyl
==================================================================
"""

import os
import sys
import requests

PRODUCT_URL = "https://www.gtavi-thealbum.com/en-eu/products/grand-theft-auto-vi-the-album-limited-edition-vinyl"

OUT_OF_STOCK_PATTERNS = [
    "sold out",
    "ausverkauft",
    "out of stock",
    "nicht verfügbar",
    "nicht verfuegbar",
    "notify me",
]

STATE_FILE = "last_state.txt"

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


def fetch_page(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        )
    }
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.text.lower()


def is_out_of_stock(html: str) -> bool:
    return any(pattern in html for pattern in OUT_OF_STOCK_PATTERNS)


def read_last_state() -> str:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return "unknown"


def write_last_state(state: str) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write(state)


def notify_discord(message: str) -> None:
    if not DISCORD_WEBHOOK_URL:
        return
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": message}, timeout=10)
    except requests.RequestException as exc:
        print(f"Discord-Benachrichtigung fehlgeschlagen: {exc}", file=sys.stderr)


def notify_telegram(message: str) -> None:
    if not (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID):
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(
            url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message}, timeout=10
        )
    except requests.RequestException as exc:
        print(f"Telegram-Benachrichtigung fehlgeschlagen: {exc}", file=sys.stderr)


def main() -> None:
    if "PASTE-DIE-ECHTE-PRODUKTSEITE-HIER-EIN" in PRODUCT_URL:
        print(
            "FEHLER: Bitte zuerst PRODUCT_URL in restock_checker.py durch die "
            "echte Produktseite ersetzen.",
            file=sys.stderr,
        )
        sys.exit(1)

    html = fetch_page(PRODUCT_URL)
    currently_out = is_out_of_stock(html)
    current_state = "out" if currently_out else "in"
    last_state = read_last_state()

    print(f"Letzter bekannter Status: {last_state} | Aktueller Status: {current_state}")

    if current_state == "in" and last_state != "in":
        message = (
            "🚨 WIEDER VERFÜGBAR (mutmaßlich) — sofort prüfen und bestellen:\n"
            f"{PRODUCT_URL}"
        )
        notify_discord(message)
        notify_telegram(message)
        print("Statuswechsel erkannt -> Benachrichtigung gesendet.")

    write_last_state(current_state)


if __name__ == "__main__":
    main()
