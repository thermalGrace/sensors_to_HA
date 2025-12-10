"""Simple Python MQTT radar visualizer using matplotlib (2D polar plot).

- Subscribes to sensors/radar/targets on the local broker.
- Plots up to 3 targets in polar coordinates (angle deg, distance mm).
- Keeps a textual table of last values in the terminal.

Usage:
    pip install paho-mqtt matplotlib
    python data_handler/radar_visualizer.py

Close the matplotlib window to exit.
"""
import json
import math
import threading
import time
from typing import List

import matplotlib.pyplot as plt
import paho.mqtt.client as mqtt

BROKER_HOST = "192.168.50.176"
BROKER_PORT = 1883
TOPIC = "sensors/radar/targets"
CLIENT_ID = "python-radar-viz"

# Shared state
latest_targets = []  # list of dicts
last_timestamp = 0
state_lock = threading.Lock()


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"Connected to MQTT {BROKER_HOST}:{BROKER_PORT}")
        client.subscribe(TOPIC, qos=0)
        print(f"Subscribed to {TOPIC}")
    else:
        print(f"MQTT connect failed rc={rc}")


def on_message(client, userdata, msg):
    global latest_targets, last_timestamp
    try:
        data = json.loads(msg.payload.decode("utf-8"))
        targets = data.get("targets", [])
        ts = data.get("timestamp_ms", 0)
    except json.JSONDecodeError:
        return

    with state_lock:
        latest_targets = targets
        last_timestamp = ts

    # Print a compact table to terminal
    rows = []
    for t in targets:
        rows.append(
            f"id={t.get('id')} angle={t.get('angle')}° dist_mm={t.get('distance_mm')} speed_cms={t.get('speed_cms')}"
        )
    if rows:
        print("; ".join(rows))
    else:
        print("No targets (heartbeat)")


def mqtt_thread():
    client = mqtt.Client(client_id=CLIENT_ID)
    # Use modern callback API if available
    if hasattr(mqtt, "CallbackAPIVersion"):
        try:
            client = mqtt.Client(client_id=CLIENT_ID, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        except Exception:
            client = mqtt.Client(client_id=CLIENT_ID)
    client.on_connect = on_connect
    client.on_message = on_message

    while True:
        try:
            client.connect(BROKER_HOST, BROKER_PORT)
            client.loop_forever()
        except Exception as exc:
            print("MQTT disconnected:", exc)
            time.sleep(2)


def polar_plot(targets: List[dict]):
    ax = plt.subplot(111, projection="polar")
    ax.clear()
    ax.set_theta_zero_location("N")  # 0° at top
    ax.set_theta_direction(-1)  # clockwise
    ax.set_rlim(0, 8.0)  # meters
    ax.set_title("RD03D Targets (angle°, distance m)")

    colors = ["tab:red", "tab:blue", "tab:purple"]

    for i, t in enumerate(targets[:3]):
        ang_deg = t.get("angle", 0.0)
        dist_m = t.get("distance_mm", 0.0) / 1000.0
        theta = math.radians(ang_deg)
        ax.plot(theta, dist_m, marker="o", color=colors[i % len(colors)], markersize=8)
        ax.text(theta, dist_m + 0.2, f"T{i+1}", color=colors[i % len(colors)])

    plt.pause(0.01)


def main():
    t = threading.Thread(target=mqtt_thread, daemon=True)
    t.start()

    plt.ion()
    fig = plt.figure(figsize=(6, 6))

    try:
        while True:
            with state_lock:
                targets = list(latest_targets)
                ts = last_timestamp
            polar_plot(targets)
            fig.canvas.draw()
            fig.canvas.flush_events()
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        plt.ioff()
        plt.close(fig)


if __name__ == "__main__":
    main()
