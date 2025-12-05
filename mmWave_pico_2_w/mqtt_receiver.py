"""Simple MQTT subscriber that prints radar payloads.

Install dependency once:
    pip install paho-mqtt

Run while the broker and Pico publisher are active:
    python mqtt_receiver.py --host 127.0.0.1 --topic sensors/radar/targets
"""

import argparse
import json
from paho.mqtt.client import Client


def handle_message(client, userdata, message):
    try:
        payload = json.loads(message.payload.decode())
    except ValueError:
        print(f"[mqtt] Raw payload: {message.payload}")
        return
    print(f"[mqtt] Topic={message.topic} -> {payload}")


def main():
    parser = argparse.ArgumentParser(description="MQTT radar subscriber")
    parser.add_argument("--host", default="192.168.50.176", help="MQTT broker host")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument("--topic", default="sensors/radar/targets", help="Topic to subscribe")
    parser.add_argument("--username", default=None)
    parser.add_argument("--password", default=None)
    args = parser.parse_args()

    client = Client(client_id="radar-subscriber")
    if args.username and args.password:
        client.username_pw_set(args.username, args.password)

    client.on_message = handle_message
    client.connect(args.host, args.port, keepalive=60)
    client.subscribe(args.topic)
    print(f"[mqtt] Subscribed to {args.topic} on {args.host}:{args.port}")

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("[mqtt] Exiting")
        client.disconnect()


if __name__ == "__main__":
    main()
