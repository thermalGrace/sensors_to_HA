// Processing sketch to visualize radar targets via MQTT (no serial)
// Requires the "MQTT" library in Processing (Contribution Manager -> Libraries -> search "MQTT")
// Broker/topic should match the Pico publisher: sensors/radar/targets JSON payload

import mqtt.*;
import processing.data.*;

MQTTClient mqtt;

// MQTT configuration
String BROKER = "tcp://192.168.50.176:1883"; // set to your broker IP
String TOPIC  = "sensors/radar/targets";
String CLIENT_ID = "processing-radar-" + (int)random(0, 10_000);

float[] angle = new float[3];
float[] distance = new float[3];
float[] speed = new float[3];
color[] targetColor = { color(255,0,0), color(0,128,255), color(180,0,255) }; // red, blue, purple

int radarRadius;
PFont radarFont;
boolean connected = false;

void setup() {
  size(1600, 900);
  radarRadius = height - 150;
  radarFont = createFont("Arial", 16);
  textFont(radarFont);
  for (int i=0;i<3;i++) {
    angle[i]=0;
    distance[i]=0;
    speed[i]=0;
  }
  initMqtt();
}

void draw() {
  background(0);
  translate(width/2, height - 70);
  drawRadarDisplay();
  // Draw all three targets
  for (int i=0;i<3;i++) {
    displayTarget(angle[i], distance[i], speed[i], targetColor[i], i);
  }
  drawStatus();
}

void initMqtt() {
  mqtt = new MQTTClient(this);
  try {
    mqtt.connect(BROKER, CLIENT_ID);
    mqtt.subscribe(TOPIC);
    connected = true;
    println("MQTT connected to", BROKER, "topic", TOPIC);
  } catch(Exception e) {
    connected = false;
    println("MQTT connect failed:", e.getMessage());
  }
}

// Called by MQTT library on incoming message
void messageReceived(String topic, byte[] payload) {
  String msg = new String(payload);
  try {
    JSONObject root = parseJSONObject(msg);
    if (root == null) return;
    JSONArray targets = root.getJSONArray("targets");
    if (targets == null) return;
    int n = min(targets.size(), 3);
    for (int i = 0; i < n; i++) {
      JSONObject t = targets.getJSONObject(i);
      angle[i] = t.getFloat("angle", 0);
      distance[i] = t.getFloat("distance_mm", 0);
      speed[i] = t.getFloat("speed_cms", 0);
    }
    // Zero out any unused slots
    for (int i = n; i < 3; i++) {
      angle[i] = 0;
      distance[i] = 0;
      speed[i] = 0;
    }
  } catch(Exception e) {
    println("Parse error:", e.getMessage(), "msg=", msg);
  }
}

void drawRadarDisplay(){
  stroke(0, 255, 0);
  strokeWeight(1);
  noFill();
  for(int r = radarRadius/4; r <= radarRadius; r += radarRadius/4) {
    arc(0, 0, r*2, r*2, radians(-150), radians(-30));
  }
  int[] angles = {-60, -45, -30, -15, 0, 15, 30, 45, 60};
  for(int i = 0; i < angles.length; i++){
    float currentAngle = angles[i];
    float rad = radians(currentAngle - 90);
    float x = radarRadius * cos(rad);
    float y = radarRadius * sin(rad);
    strokeWeight(1);
    stroke(0, 255, 0);
    line(0, 0, x, y);
    fill(0, 255, 0);
    noStroke();
    textAlign(CENTER, CENTER);
    textSize(14);
    float tx = (radarRadius + 20) * cos(rad);
    float ty = (radarRadius + 20) * sin(rad);
    text(currentAngle + "°", tx, ty);
  }
  stroke(0,255,0);
  line(0,0,0,-radarRadius);
}

void displayTarget(float angleDeg, float distanceMM, float spd, color dotColor, int index){
  if(distanceMM <= 8000){
    float scaledDist = map(distanceMM, 0, 8000, 0, radarRadius);
    float rad = radians(angleDeg - 90);
    float x = scaledDist * cos(rad);
    float y = scaledDist * sin(rad);
    fill(dotColor);
    noStroke();
    ellipse(x, y, 14, 14);
    // Display info for each target at separate vertical offsets
    fill(dotColor);
    textSize(16);
    textAlign(LEFT, CENTER);
    float yOffset = -radarRadius - 50 + 55*index;
    float spacing = 18;
    text("Target " + (index+1), -width/2 + 20, yOffset-10);
    fill(255);
    text("Angle: " + nf(angleDeg,1,1) + "°",    -width/2 + 40, yOffset + 0*spacing);
    text("Distance: " + nf(distanceMM/1000.0,1,2) + " m", -width/2 + 40, yOffset + 1*spacing);
    text("Speed: " + nf(spd,1,2) + " cm/s",      -width/2 + 40, yOffset + 2*spacing);
  }
}

void drawStatus() {
  resetMatrix();
  fill(255);
  textAlign(LEFT, TOP);
  textSize(14);
  String status = connected ? "MQTT: connected" : "MQTT: disconnected";
  text(status + "  broker=" + BROKER + "  topic=" + TOPIC, 10, 10);
}
