"""
Live thermal comfort calculator
===============================

What it does
------------
- Listens to MQTT `sensors/pico/air_mmwave` messages and extracts the `environment` payload.
- Loads the latest row from `user_feedback_app/responses.csv` to estimate metabolic rate (MET) and clothing insulation (CLO).
- Computes PMV, PPD (ISO 7730-2005) and UTCI for each incoming environment sample and prints the results.

PMV/PPD inputs and assumptions
------------------------------
- `tdb` (dry-bulb air temperature, C): from MQTT `temperature_c` (live).
- `tr` (mean radiant temperature, C): assumed equal to `tdb` unless future payloads provide it (static assumption).
- `rh` (relative humidity, %): from MQTT `humidity_pct` (live).
- `vr` / `v` (air speed, m/s): hard-coded to 0.1 m/s to approximate still indoor air (static default).
- `met` (metabolic rate, met units): estimated from the most recent feedback row via `estimate_met` mapping; falls back to 1.2 if not found (derived/static).
- `clo` (clothing insulation, clo units): estimated from upper/lower garment labels via `estimate_clo`; falls back to 0.7 if not found (derived/static).
- Model: `pythermalcomfort.models.pmv_ppd_iso` with `model="7730-2005"` (ISO PMV/PPD). Returns `pmv` (thermal sensation index) and `ppd` (percent people dissatisfied).

How PMV/PPD are computed (conceptual)
-------------------------------------
PMV balances human heat gains and losses under steady-state conditions. The ISO model solves for skin heat loss via convection, radiation, sweat evaporation, respiration, and diffusion, then maps the heat balance to the PMV scale (-3 cold to +3 hot). PPD is derived from PMV with the ISO exponential relation $PPD = 100 - 95\,\exp\bigl(-0.03353\,PMV^4 - 0.2179\,PMV^2\bigr)$, meaning even at PMV = 0 at least 5% are dissatisfied.

Run
---
    python thermal_comfort_model/comfort_calc.py

Dependencies
------------
paho-mqtt, pythermalcomfort, matplotlib (optional for future plots).
"""
import csv
import json
import threading
import time
from datetime import date, datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import paho.mqtt.client as mqtt
from pythermalcomfort.models import pmv_ppd_iso, utci

# Paths
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RESPONSES = ROOT / "user_feedback_app" / "responses.csv"


def _resolve_responses_csv() -> Path:
    """Return the first existing responses.csv from common locations."""
    # Keep lookup flexible so the calculator works when run from repo root or module path.
    candidates = [
        DEFAULT_RESPONSES,
        Path(__file__).resolve().parent / "responses.csv",
        Path.cwd() / "user_feedback_app" / "responses.csv",
    ]
    for path in candidates:
        if path.exists():
            return path
    return DEFAULT_RESPONSES

# MQTT settings
MQTT_HOST = "192.168.50.176"
MQTT_PORT = 1883
MQTT_TOPIC_ENV = "sensors/pico/air_mmwave"
CLIENT_ID = "comfort-calc"


@dataclass
class EnvReading:
    tdb: float  # dry bulb temp (C)
    tr: float   # mean radiant temp (C)
    rh: float   # relative humidity (%)
    v: float = 0.1  # air speed (m/s)


@dataclass
class UserContext:
    uid: str
    activity: str
    main_task: str
    clothing_upper: str
    clothing_lower: str


ACTIVITY_MET = {
    "sitting relaxed": 1.0,
    "sitting and typing/talking": 1.2,
    "standing": 1.4,
    "walking slowly": 1.7,
    "walking fast or more": 2.0,
    "exercising": 2.5,
}

UPPER_CLO_CLO = {
    "t-shirt": 0.25,
    "long-sleeve shirt": 0.36,
    "light sweater": 0.45,
    "thick sweater": 0.70,
}

LOWER_CLO_CLO = {
    "shorts": 0.08,
    "light trousers": 0.20,
    "jeans": 0.30,
    "warm trousers": 0.40,
}

DEFAULT_CLO = 0.7  # fallback
DEFAULT_MET = 1.2  # fallback


def latest_user_context(csv_path: Optional[Path] = None) -> Optional[UserContext]:
    """Load the most recent user feedback row to derive activity/clothing inputs."""
    csv_path = csv_path or _resolve_responses_csv()
    if not csv_path.exists():
        return None
    with csv_path.open("r", newline="") as f:
        reader = list(csv.DictReader(f))
    if not reader:
        return None
    row = reader[-1]
    return UserContext(
        uid=row.get("uid", "unknown"),
        activity=row.get("activity", ""),
        main_task=row.get("main_task", ""),
        clothing_upper=row.get("clothing_upper", ""),
        clothing_lower=row.get("clothing_lower", ""),
    )


def all_users_context(csv_path: Optional[Path] = None) -> Dict[str, UserContext]:
    """Load the most recent response for every unique uid in the CSV, filtered to today."""
    csv_path = csv_path or _resolve_responses_csv()
    if not csv_path.exists():
        return {}
    
    today = date.today()
    users: Dict[str, UserContext] = {}
    with csv_path.open("r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            uid = row.get("uid")
            if not uid:
                continue
            
            # Filter for today's data
            ts_str = row.get("timestamp_iso")
            if ts_str:
                try:
                    # Strip timezone for parsing if present
                    if "+" in ts_str:
                        ts_str = ts_str.split("+")[0]
                    dt = datetime.fromisoformat(ts_str)
                    if dt.date() != today:
                        continue
                except ValueError:
                    continue

            users[uid] = UserContext(
                uid=uid,
                activity=row.get("activity", ""),
                main_task=row.get("main_task", ""),
                clothing_upper=row.get("clothing_upper", ""),
                clothing_lower=row.get("clothing_lower", ""),
            )
    return users


def estimate_met(activity: str) -> float:
    """Map a free-form activity string to a MET value with sane fallback."""
    key = activity.strip().lower()
    return ACTIVITY_MET.get(key, DEFAULT_MET)


def estimate_clo(upper: str, lower: str) -> float:
    """Compute total clothing insulation from upper/lower garment labels."""
    upper_clo = UPPER_CLO_CLO.get(upper.strip().lower(), 0.25)
    lower_clo = LOWER_CLO_CLO.get(lower.strip().lower(), 0.25)
    return upper_clo + lower_clo if (upper_clo or lower_clo) else DEFAULT_CLO


def compute_comfort(env: EnvReading, user: Optional[UserContext]) -> Dict[str, float]:
    """Calculate PMV, PPD, MET, CLO, and UTCI for the given environment/user context."""
    met = estimate_met(user.activity if user else "")
    clo = estimate_clo(user.clothing_upper if user else "", user.clothing_lower if user else "")

    pmv_ppd = pmv_ppd_iso(
        tdb=env.tdb,
        tr=env.tr,
        vr=env.v,
        rh=env.rh,
        met=met,
        clo=clo,
        model="7730-2005",
    )
    utci_val = utci(tdb=env.tdb, tr=env.tr, v=env.v, rh=env.rh)

    # pythermalcomfort may return a float or a UTCI object; normalize safely
    def _to_float(val):
        """Normalize different numeric-like UTCI returns to a float when possible."""
        # Common cases: float, Decimal, numpy scalar
        try:
            return float(val)
        except Exception:
            pass
        # Some versions expose .utci or .value
        for attr in ("utci", "value"):
            if hasattr(val, attr):
                try:
                    return float(getattr(val, attr))
                except Exception:
                    continue
        # Last resort: string cast
        try:
            return float(str(val))
        except Exception:
            return None

    utci_num = _to_float(utci_val)
    utci_rounded = round(utci_num, 2) if utci_num is not None else None

    return {
        "pmv": round(pmv_ppd.pmv, 3),
        "ppd": round(pmv_ppd.ppd, 2),
        "met": met,
        "clo": clo,
        "utci": utci_rounded,
    }


def get_multi_user_results(env: EnvReading, users: Dict[str, UserContext]) -> list:
    """Calculate comfort metrics for a collection of users."""
    results = []
    for uid, user in users.items():
        comfort = compute_comfort(env, user)
        results.append({
            "User ID": uid,
            "Activity": user.activity,
            "Clothing (Upper)": user.clothing_upper,
            "Clothing (Lower)": user.clothing_lower,
            "PMV": comfort["pmv"],
            "PPD (%)": comfort["ppd"],
            "UTCI (C)": comfort["utci"],
            "MET": comfort["met"],
            "CLO": comfort["clo"],
        })
    return results

def parse_env_from_payload(payload: dict) -> Optional[EnvReading]:
    """Extract EnvReading from the MQTT JSON payload, guarding against missing fields."""
    env = payload.get("environment") if isinstance(payload, dict) else None
    if not isinstance(env, dict):
        return None
    try:
        tdb = float(env.get("temperature_c"))
        tr = tdb  # assume mean radiant ~= air temp if not provided
        rh = float(env.get("humidity_pct"))
        v = 0.1
        return EnvReading(tdb=tdb, tr=tr, rh=rh, v=v)
    except (TypeError, ValueError):
        return None


def on_connect(client, userdata, flags, rc, properties=None):
    """Subscribe to the environment topic once the MQTT connection is established."""
    if rc == 0:
        print(f"Connected to MQTT {MQTT_HOST}:{MQTT_PORT}")
        client.subscribe(MQTT_TOPIC_ENV, qos=0)
        print(f"Subscribed to {MQTT_TOPIC_ENV}")
    else:
        print(f"MQTT connect failed rc={rc}")


def on_message(client, userdata, msg):
    """Handle incoming MQTT messages: parse payload, compute comfort, and log results."""
    try:
        data = json.loads(msg.payload.decode("utf-8"))
    except json.JSONDecodeError:
        return

    env = parse_env_from_payload(data)
    if not env:
        return

    user = latest_user_context()
    comfort = compute_comfort(env, user)

    print("--- Comfort update ---")
    print(f"Env: tdb={env.tdb}C tr={env.tr}C rh={env.rh}% v={env.v}m/s")
    print(f"User: {user}")
    for k, v in comfort.items():
        print(f"{k}: {v}")
    print()


def mqtt_loop():
    """Maintain a resilient MQTT client loop with auto-reconnect on errors."""
    client = mqtt.Client(client_id=CLIENT_ID)
    if hasattr(mqtt, "CallbackAPIVersion"):
        try:
            client = mqtt.Client(client_id=CLIENT_ID, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        except Exception:
            client = mqtt.Client(client_id=CLIENT_ID)
    client.on_connect = on_connect
    client.on_message = on_message

    while True:
        try:
            client.connect(MQTT_HOST, MQTT_PORT)
            client.loop_forever()
        except Exception as exc:
            print("MQTT disconnected:", exc)
            time.sleep(2)


def main():
    """Entry point: announce startup then block in the MQTT loop."""
    print("Starting comfort calculator. Listening on MQTT topic", MQTT_TOPIC_ENV)
    mqtt_loop()


if __name__ == "__main__":
    main()
