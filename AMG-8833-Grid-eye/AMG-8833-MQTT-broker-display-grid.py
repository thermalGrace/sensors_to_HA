import json
import paho.mqtt.client as mqtt
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy as np

MQTT_BROKER = "192.168.50.62"
MQTT_PORT = 1883
MQTT_TOPIC = "sensors/thermal/amg8833"

class ThermalGridDisplay:
    def __init__(self):
        self.client = None
        self.latest_pixels = None
        self.latest_thermistor = None
        self.running = True
        
        # Setup matplotlib with interactive mode
        plt.ion()
        plt.rcParams.update({'font.size': 16})
        self.fig, self.ax = plt.subplots(figsize=(12, 9))
        
        pix_res = (8, 8)
        zz = np.zeros(pix_res)
        self.im1 = self.ax.imshow(zz, vmin=15, vmax=40)
        self.cbar = self.fig.colorbar(self.im1, fraction=0.0475, pad=0.03)
        self.cbar.set_label('Temperature [C]', labelpad=10)
        
        # Handle window close event
        self.fig.canvas.mpl_connect('close_event', self.on_close)
        
        plt.show(block=False)

    def on_close(self, event):
        """Called when window is closed"""
        self.running = False

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("MQTT: connected")
            client.subscribe(MQTT_TOPIC)
        else:
            print(f"MQTT: connection failed with code {rc}")

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            self.latest_pixels = payload.get("pixels", [])
            self.latest_thermistor = payload.get("thermistor_temp_c", 0)
        except Exception as e:
            print(f"Error parsing message: {e}")

    def connect_mqtt(self):
        self.client = mqtt.Client(client_id="thermal-display")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
        print("MQTT: connecting...")
        self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
        self.client.loop_start()

    def run(self):
        self.connect_mqtt()
        
        pix_res = (8, 8)
        
        try:
            while self.running and plt.fignum_exists(self.fig.number):
                if self.latest_pixels:
                    pixels_array = np.reshape(self.latest_pixels, pix_res)
                    self.im1.set_data(pixels_array)
                    self.fig.canvas.draw()
                    self.fig.canvas.flush_events()
                    
                    if self.latest_thermistor:
                        self.ax.set_title(f"Thermistor: {self.latest_thermistor:.2f}°C")
                
                plt.pause(0.1)
        
        except KeyboardInterrupt:
            print("Keyboard interrupt...")
        finally:
            print("Shutting down...")
            self.client.loop_stop()
            plt.close('all')
            
if __name__ == "__main__":
    display = ThermalGridDisplay()
    display.run()