# MQTT Setup Notes

## Summary
- Pico 2 W (MicroPython) publishes radar targets over MQTT to a broker on your Pi/HA host (192.168.50.176:1883).
- Payload topic: `sensors/radar/targets` (JSON with up to 3 targets).
- Broker: systemd Mosquitto on the Pi host, configured for anonymous access on all interfaces.


## Broker (Mosquitto) on Pi
Config file `/etc/mosquitto/mosquitto.conf` (anonymous, all interfaces):
```
listener 1883 0.0.0.0
allow_anonymous true
persistence true
persistence_location /var/lib/mosquitto/
log_dest syslog
log_dest stdout
include_dir /etc/mosquitto/conf.d
```
Commands:
```
sudo systemctl enable --now mosquitto
sudo systemctl status mosquitto --no-pager
sudo ss -ltnp | grep 1883        # should show 0.0.0.0:1883
mosquitto_sub -h 127.0.0.1 -t test -v &
mosquitto_pub -h 127.0.0.1 -t test -m hi
```
Firewall (optional, UFW):
```
sudo ufw allow from 192.168.50.0/24 to any port 1883 proto tcp
sudo ufw reload
```

## Pico 2 W publisher (`main.py`)
- Wi-Fi: `thermal_grace_iot_24` / `45_#_101_G.`
- Broker: `192.168.50.176:1883`
- Auth: none (anonymous)
- Client ID: `pico-radar`
- Topic: `sensors/radar/targets`
- Keepalive: 60s
- Publish interval: 100 ms when radar data updates
- JSON payload shape:
```
{
  "timestamp_ms": <int>,
  "targets": [
    {
      "id": 1,
      "angle": <float degrees>,
      "distance_mm": <float mm>,
      "speed_cms": <float cm/s>,
      "x_mm": <int mm>,
      "y_mm": <int mm>
    },
    ... up to 3 targets ...
  ]
}
```
Notes:
- Uses `umqtt.simple` (upload `umqtt/simple.py` to the Pico).
- Auto-reconnects Wi-Fi and MQTT; logs connection status in Thonny.

## Diagnostic script (`wifi_mqtt_diag.py`)
- Connects Wi-Fi, shows MAC/scan, attempts TCP to broker, then MQTT publish to `test/pico`.
- Useful to confirm broker reachability from the Pico before running `main.py`.


## Testing from any LAN host
```
mosquitto_sub -h 192.168.50.176 -t sensors/radar/targets -v &
mosquitto_pub -h 192.168.50.176 -t test/pico -m "hello"
```
If you see payloads on `sensors/radar/targets`, the Pico is publishing and broker is reachable.

## Common pitfalls
- Multiple listeners or leftover conf files causing port conflicts; keep a single listener on 1883.
- Broker bound to localhost only; ensure `0.0.0.0` in the listener.
- Firewall blocking 1883; allow LAN subnet.
- Pico using the wrong MQTT client import; must be `from umqtt.simple import MQTTClient`.
- HA MQTT integration pointing to the wrong host/port or auth mismatch.
