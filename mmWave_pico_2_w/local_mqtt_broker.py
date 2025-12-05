"""Minimal local MQTT broker for quick Pico testing.

Requires the "amqtt" package ("pip install amqtt").
Run this script on your Raspberry Pi 5 and keep it running while
the Pico publishes radar data.
"""

import asyncio
from amqtt.broker import Broker

BROKER_CONFIG = {
    "listeners": {
        "default": {
            "type": "tcp",
            "bind": "0.0.0.0:1883",
        }
    },
    "sys_interval": 60,
    "auth": {"allow-anonymous": True},
}


async def start_broker():
    broker = Broker(BROKER_CONFIG)
    await broker.start()
    print("[broker] Listening on 0.0.0.0:1883")
    try:
        await asyncio.Future()
    finally:
        await broker.shutdown()


def main():
    try:
        asyncio.run(start_broker())
    except KeyboardInterrupt:
        print("[broker] Stopping")


if __name__ == "__main__":
    main()
