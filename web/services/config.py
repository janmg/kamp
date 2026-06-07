"""Configuration for the merged Zomerkamp roster application."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _read_secret_file(path: str) -> str | None:
    secret_path = Path(path)
    if not secret_path.is_absolute():
        secret_path = Path(__file__).resolve().parent / secret_path
    if not secret_path.exists():
        return None
    return secret_path.read_text(encoding="utf-8").strip() or None

DB_USER = os.getenv("DB_USER", "zomerkamp_user")
DB_PASSWORD_FILE = os.getenv("DB_PASSWORD_FILE", ".db_password")
DB_PASSWORD = _read_secret_file(DB_PASSWORD_FILE) or os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "10.0.0.5")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "zomerkamp")

DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
)

EVENT_DAYS = 4
TIME_BLOCKS = ["07:00-07:30", "07:30-09:00", "09:00-13:00", "13:00-15:30", "15:30-18:00", "18:00-21:00"]

PUBLIC_URL = os.getenv("PUBLIC_URL", "https://zomerkamp.janmg.com")

# Passcode authentication
PASSCODE_FILE = os.getenv("PASSCODE_FILE", ".passcode")
PASSCODE = _read_secret_file(PASSCODE_FILE) or os.getenv("PASSCODE", "ntc")

# Admin passcode - use to log in as admin (can view emails)
ADMIN_PASSCODE_FILE = os.getenv("ADMIN_PASSCODE_FILE", ".admin_passcode")
ADMIN_PASSCODE = _read_secret_file(ADMIN_PASSCODE_FILE) or os.getenv("ADMIN_PASSCODE", "")

PUBLIC_URL = os.getenv("PUBLIC_URL", "https://zomerkamp.janmg.com")
# Read from a single .twilio file (key=value, one per line):
#   ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
#   AUTH_TOKEN=your_auth_token
#   FROM=+12015551234
# Hardcoded values below are used as fallback when the file is absent.

def _parse_twilio_file(path: str = ".twilio") -> dict[str, str]:
    p = Path(path)
    if not p.is_absolute():
        p = Path(__file__).resolve().parent / p
    if not p.exists():
        return {}
    result: dict[str, str] = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, val = line.partition("=")
            result[key.strip()] = val.strip()
    return result

_twilio = _parse_twilio_file()

TWILIO_ACCOUNT_SID: str = _twilio.get("ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN:  str = _twilio.get("AUTH_TOKEN",  "")
TWILIO_FROM:        str = _twilio.get("FROM",        "+358400000000")  # E.164, e.g. +12015551234
SMS_ENABLED = False
#SMS_ENABLED = bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_FROM)
