"""
Streamlit survey app to collect thermal comfort context and save responses to CSV.
Run with: streamlit run app.py
"""

import csv
from datetime import datetime, UTC
from pathlib import Path

import streamlit as st

CSV_PATH = Path(__file__).parent / "responses.csv"


def ensure_csv_with_header(columns):
    if not CSV_PATH.exists():
        CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
        with CSV_PATH.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(columns)


def append_response(row_values):
    with CSV_PATH.open("a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(row_values)


def generate_short_id():
    today_key = datetime.now(UTC).strftime("%Y%m%d")
    prefix = f"{today_key}-"
    if not CSV_PATH.exists():
        return f"{prefix}01"

    with CSV_PATH.open("r", newline="") as f:
        reader = csv.reader(f)
        next(reader, None)
        daily_count = 0
        for row in reader:
            if len(row) >= 2 and row[1].startswith(today_key):
                daily_count += 1

    # Human-friendly incrementing ID scoped per day (e.g., 20250101-03).
    return f"{prefix}{daily_count + 1:02d}"


st.set_page_config(page_title="Comfort Survey", page_icon="📋", layout="centered")
st.title("Occupant Comfort Check")
st.markdown(
    "Provide a quick snapshot of your activity, clothing, and how you feel right now."
)

activity = st.radio(
    "How physically active are you right now?",
    [
        "Sitting relaxed",
        "Sitting and typing/talking",
        "Standing",
        "Walking slowly",
        "Walking fast or more",
        "Other (describe)",
    ],
)
activity_other = ""
if activity == "Other (describe)":
    activity_other = st.text_input("Describe your activity", placeholder="e.g. stretching", key="activity_other")

main_task = st.selectbox(
    "What are you mainly doing in this room?",
    [
        "Working at computer",
        "Meeting",
        "Resting",
        "Exercising",
        "Other (describe)",
    ],
    key="main_task",
)
main_task_other = ""
if main_task == "Other (describe)":
    main_task_other = st.text_input("Describe what you're doing", placeholder="e.g. crafting", key="main_task_other")

clothing_upper = st.selectbox(
    "Upper body clothing",
    [
        "T-shirt",
        "Long-sleeve shirt",
        "Light sweater",
        "Thick sweater",
        "Other (describe)",
    ],
    key="clothing_upper",
)
clothing_upper_other = ""
if clothing_upper == "Other (describe)":
    clothing_upper_other = st.text_input("Describe upper body clothing", placeholder="e.g. layered jacket", key="clothing_upper_other")

clothing_lower = st.selectbox(
    "Lower body clothing",
    ["Shorts", "Light trousers", "Jeans", "Warm trousers", "Other (describe)"],
    key="clothing_lower",
)
clothing_lower_other = ""
if clothing_lower == "Other (describe)":
    clothing_lower_other = st.text_input("Describe lower body clothing", placeholder="e.g. thermal leggings", key="clothing_lower_other")

arrival_mode = st.selectbox(
    "How did you arrive just before entering this room?",
    [
        "Walking/cycling",
        "Public transport",
        "Car",
        "Stayed in building",
        "Other (describe)",
    ],
    key="arrival_mode",
)
arrival_mode_other = ""
if arrival_mode == "Other (describe)":
    arrival_mode_other = st.text_input("Describe arrival mode", placeholder="e.g. elevator ride", key="arrival_mode_other")

pre_entry_temp = st.radio(
    "Did you feel warm, neutral, or cool just before entering this room?",
    ["Warm", "Neutral", "Cool", "Other (describe)"],
    key="pre_entry_temp",
)
pre_entry_temp_other = ""
if pre_entry_temp == "Other (describe)":
    pre_entry_temp_other = st.text_input("Describe how you felt", placeholder="e.g. slightly clammy", key="pre_entry_temp_other")

intake = st.multiselect(
    "In the last hour, have you had any of the following?",
    ["Hot drink", "Cold drink", "Hot meal", "Light snack", "Nothing", "Other (describe)"],
)
intake_other = ""
if "Other (describe)" in intake:
    intake_other = st.text_input("Describe other intake", placeholder="e.g. herbal tea", key="intake_other")

current_feel = st.radio(
    "Right now, how do you feel temperature-wise?",
    [
        "Cold (-3)",
        "Cool (-2)",
        "Slightly cool (-1)",
        "Neutral (0)",
        "Slightly warm (+1)",
        "Warm (+2)",
        "Hot (+3)",
        "Other (describe)",
    ],
    key="current_feel",
)
current_feel_other = ""
if current_feel == "Other (describe)":
    current_feel_other = st.text_input("Describe your sensation", placeholder="e.g. unsteady", key="current_feel_other")

notes = st.text_area("Anything else to add?", placeholder="Optional")

submitted = st.button("Submit response")

if submitted:
    columns = [
        "uid",
        "timestamp_iso",
        "activity",
        "main_task",
        "clothing_upper",
        "clothing_lower",
        "arrival_mode",
        "pre_entry_temp",
        "intake",
        "current_feel",
        "notes",
    ]
    ensure_csv_with_header(columns)

    uid = generate_short_id()
    timestamp_iso = datetime.now(UTC).isoformat()

    def resolve_with_other(selection: str, custom_text: str, other_label: str = "Other (describe)") -> str:
        custom = custom_text.strip()
        if selection == other_label:
            return custom if custom else "Other"
        return selection

    activity_value = resolve_with_other(activity, activity_other)
    main_task_value = resolve_with_other(main_task, main_task_other)
    clothing_upper_value = resolve_with_other(clothing_upper, clothing_upper_other)
    clothing_lower_value = resolve_with_other(clothing_lower, clothing_lower_other)
    arrival_mode_value = resolve_with_other(arrival_mode, arrival_mode_other)
    pre_entry_temp_value = resolve_with_other(pre_entry_temp, pre_entry_temp_other)
    intake_filtered = [item for item in intake if item != "Other (describe)"]
    if "Other (describe)" in intake:
        custom_intake = intake_other.strip()
        if custom_intake:
            intake_filtered.append(custom_intake)
        else:
            intake_filtered.append("Other")
    intake_joined = "; ".join(intake_filtered)
    current_feel_value = resolve_with_other(current_feel, current_feel_other)

    row = [
        uid,
        timestamp_iso,
        activity_value,
        main_task_value,
        clothing_upper_value,
        clothing_lower_value,
        arrival_mode_value,
        pre_entry_temp_value,
        intake_joined,
        current_feel_value,
        notes.strip(),
    ]
    append_response(row)
    st.success(f"Saved. Entry ID: {uid}")
    st.balloons()

st.caption(
    "Responses are stored locally in responses.csv. Each submission gets a unique ID."
)
