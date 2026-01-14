

11/12/25

[Unit]
Description=Thermal AMG8833 MQTT Publisher
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=zerocluster
WorkingDirectory=/home/zerocluster/sensors_to_HA/AMG-8833-Grid-eye

ExecStart=/home/zerocluster/my_venv/bin/python \
  /home/zerocluster/sensors_to_HA/AMG-8833-Grid-eye/AMG-8833--MQTT.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target




---

sudo systemctl daemon-reload
sudo systemctl restart your-service-name.service


To debug:
sudo systemctl status your-service-name.service
sudo journalctl -u your-service-name.service -e

--
Run manually

sudo -u zerocluster /home/zerocluster/my_venv/bin/python \
  /home/zerocluster/sensors_to_HA/AMG-8833-Grid-eye/AMG-8833--MQTT.py



02/12/25
sudo minicom -D /dev/ttyACM0 -b 256000


01/12/25
venv 
thermal_env
