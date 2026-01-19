import pytest
import json
from unittest.mock import MagicMock
from data_handler.thermal_comfort_model.comfort_calc import (
    estimate_met, estimate_clo, parse_env_from_payload, compute_comfort, EnvReading, UserContext
)
from data_handler.state import snapshot_to_row
from data_handler.llm_utils import build_prompt_from_snapshot, build_multi_user_prompt

def test_estimate_met():
    assert estimate_met("sitting relaxed") == 1.0
    assert estimate_met("exercising") == 2.5
    assert estimate_met("unknown activity") == 1.2  # Default

def test_estimate_clo():
    assert estimate_clo("t-shirt", "shorts") == 0.25 + 0.08
    assert estimate_clo("thick sweater", "warm trousers") == 0.70 + 0.40
    assert estimate_clo("unknown", "unknown") == 0.25 + 0.25  # Item defaults

def test_parse_env_from_payload():
    payload = {
        "environment": {
            "temperature_c": 22.5,
            "humidity_pct": 50.0,
            "pressure_hpa": 1013,
            "gas_kohms": 50
        }
    }
    env = parse_env_from_payload(payload)
    assert env.tdb == 22.5
    assert env.rh == 50.0
    
    assert parse_env_from_payload({}) is None
    assert parse_env_from_payload({"environment": "not a dict"}) is None

def test_compute_comfort():
    env = EnvReading(tdb=25, tr=25, rh=50, v=0.1)
    user = UserContext(uid="test", activity="sitting relaxed", main_task="testing", clothing_upper="t-shirt", clothing_lower="shorts")
    
    result = compute_comfort(env, user)
    assert "pmv" in result
    assert "ppd" in result
    assert result["met"] == 1.0
    assert result["clo"] == 0.33
    assert result["utci"] is not None

def test_snapshot_to_row():
    snapshot = {
        "last_updated": 1700000000,
        "co2_ppm": 800,
        "environment": {"temperature_c": 22, "humidity_pct": 45},
        "comfort": {"pmv": 0.1, "ppd": 5},
        "radar": {"target_count": 2}
    }
    row = snapshot_to_row(snapshot)
    assert row["co2_ppm"] == 800
    assert row["people"] == 2
    assert row["temperature_c"] == 22
    assert row["pmv"] == 0.1

def test_build_prompt_from_snapshot():
    snapshot = {
        "environment": {"temperature_c": 22, "humidity_pct": 45},
        "comfort": {"pmv": 0.1, "ppd": 5},
        "co2_ppm": 800
    }
    user_ctx = UserContext(uid="test", activity="sitting", main_task="coding", clothing_upper="t-shirt", clothing_lower="jeans")
    prompt = build_prompt_from_snapshot(snapshot, user_ctx)
    assert "Temperature: 22 C" in prompt
    assert "Activity: sitting" in prompt
    assert "CO2: 800 ppm" in prompt

def test_build_multi_user_prompt():
    sensor_row = {"temperature_c": 23, "humidity_pct": 50, "co2_ppm": 900, "people": 1}
    users_results = [
        {"User ID": "A", "Activity": "sitting", "Clothing (Upper)": "t-shirt", "Clothing (Lower)": "jeans", "PMV": 0, "PPD (%)": 5, "UTCI (C)": 23}
    ]
    prompt = build_multi_user_prompt(sensor_row, users_results, "How is the air?")
    assert "User question: How is the air?" in prompt
    assert "Indoor Temp: 23 C" in prompt
    assert "User A:" in prompt
    assert "Average PMV: 0" in prompt
