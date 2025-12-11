"""
Live thermal comfort calculator:

- Subscribes to MQTT for environment payloads (expects env in sensors/pico/air_mmwave -> environment).
- Pulls latest user feedback from user_feedback_app/responses.csv to estimate met/clo.
- Computes PMV/PPD (ISO) and UTCI whenever new env data arrives; logs to console.

Run:
    python thermal_comfort_model/comfort_calc.py

Dependencies: paho-mqtt, pythermalcomfort, matplotlib (optional for future plots).
"""
import csv
import json
import threading
import time
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
    csv_path = csv_path or _resolve_responses_csv()
    if not csv_path.exists():
        return None
    with csv_path.open("r", newline="") as f:
        reader = list(csv.DictReader(f))
    if not reader:
        return None
    row = reader[-1]
    return UserContext(
        activity=row.get("activity", ""),
        main_task=row.get("main_task", ""),
        clothing_upper=row.get("clothing_upper", ""),
        clothing_lower=row.get("clothing_lower", ""),
    )


def estimate_met(activity: str) -> float:
    key = activity.strip().lower()
    return ACTIVITY_MET.get(key, DEFAULT_MET)


def estimate_clo(upper: str, lower: str) -> float:
    upper_clo = UPPER_CLO_CLO.get(upper.strip().lower(), 0.25)
    lower_clo = LOWER_CLO_CLO.get(lower.strip().lower(), 0.25)
    return upper_clo + lower_clo if (upper_clo or lower_clo) else DEFAULT_CLO


def compute_comfort(env: EnvReading, user: Optional[UserContext]) -> Dict[str, float]:
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

def parse_env_from_payload(payload: dict) -> Optional[EnvReading]:
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
    if rc == 0:
        print(f"Connected to MQTT {MQTT_HOST}:{MQTT_PORT}")
        client.subscribe(MQTT_TOPIC_ENV, qos=0)
        print(f"Subscribed to {MQTT_TOPIC_ENV}")
    else:
        print(f"MQTT connect failed rc={rc}")


def on_message(client, userdata, msg):
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
    print("Starting comfort calculator. Listening on MQTT topic", MQTT_TOPIC_ENV)
    mqtt_loop()


if __name__ == "__main__":
    main()
