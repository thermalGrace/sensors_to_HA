import time
import network
import rp2
from umqtt.simple import MQTTClient
import socket

SSID = "thermal_grace_iot_24"
PSK = "45_#_101_G."
# Set BROKER to a host on the same subnet as the Pico (192.168.50.x)
BROKER = "192.168.50.176"
PORT = 1883

rp2.country("NL")
wlan = network.WLAN(network.STA_IF)


def status_name(code):
    names = {
        network.STAT_IDLE: "IDLE",
        network.STAT_CONNECTING: "CONNECTING",
        network.STAT_NO_AP_FOUND: "NO_AP_FOUND",
        network.STAT_CONNECT_FAIL: "CONNECT_FAIL",
        network.STAT_GOT_IP: "GOT_IP",
    }
    return names.get(code, str(code))


def connect_wifi(max_retries=30):
    if wlan.isconnected():
        return True
    wlan.active(True)
    wlan.config(pm=0xA11140)  # performance power mode to improve association stability

    print("MAC:", ":".join(["%02X" % b for b in wlan.config("mac")]))
    print("Scanning for SSIDs...")
    try:
        aps = wlan.scan()
        if not aps:
            print("Scan returned no APs")
        for ap in aps:
            ssid = ap[0].decode()
            rssi = ap[3]
            ch = ap[2]
            if ssid == SSID:
                print("Found target SSID", ssid, "RSSI", rssi, "ch", ch)
            else:
                # Show a few nearby APs for troubleshooting
                print("Seen:", ssid, "RSSI", rssi, "ch", ch)
    except Exception as exc:
        print("Scan failed:", exc)

    wlan.connect(SSID, PSK)
    for i in range(max_retries):
        if wlan.isconnected():
            break
        print(
            "Wi-Fi attempt",
            i + 1,
            "status",
            wlan.status(),
            status_name(wlan.status()),
        )
        time.sleep(0.5)
    if wlan.isconnected():
        print("Wi-Fi connected", wlan.ifconfig())
        return True
    print("Wi-Fi failed, status", wlan.status(), status_name(wlan.status()))
    return False


def test_tcp():
    try:
        addr = socket.getaddrinfo(BROKER, PORT)[0][-1]
        print("TCP: connecting to", addr)
        s = socket.socket()
        s.settimeout(5)
        s.connect(addr)
        print("TCP: connected ok")
        s.close()
        return True
    except Exception as exc:
        print("TCP error:", exc)
        return False


def test_mqtt():
    print("MQTT: connecting to", BROKER, PORT)
    c = MQTTClient("pico-diag", BROKER, port=PORT, keepalive=30)
    c.connect()
    print("MQTT: connected")
    c.publish(b"test/pico", b"hello")
    print("MQTT: published test message")
    c.disconnect()
    print("MQTT: disconnected")


def main():
    if not connect_wifi():
        return
    print("Network ifconfig:", wlan.ifconfig())
    if not test_tcp():
        return
    try:
        test_mqtt()
    except Exception as exc:
        print("MQTT error:", exc)


if __name__ == "__main__":
    main()


