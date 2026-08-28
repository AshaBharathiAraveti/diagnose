// ============================================================
//  FreshSense ESP32 - Full Hardware + WiFi Integration
//  Sends real sensor data to Flask backend via HTTP POST
//  v2.1 - Bug fixes: DHT warmup, base_weight auto-set,
//         WiFi resilience, correct tare handling
// ============================================================

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include "HX711.h"
#include <Adafruit_Sensor.h>
#include <DHT.h>

// -----------------------------------------------------------
//  CONFIGURE THESE BEFORE FLASHING
// -----------------------------------------------------------
const char* WIFI_SSID     = "vivo1935";
const char* WIFI_PASSWORD = "6789012345";
const char* SERVER_IP     = "192.168.43.63";  // PC's IP on Asha's A35 hotspot
// -----------------------------------------------------------

// Food type: change via Serial command "food:vegetables"
// Valid: fruits, vegetables, leafy_greens, herbs, dairy,
//        meat, fish, cooked, prepared_meals, snacks
String FOOD_TYPE = "fruits";

// --- Pin Definitions ---
#define DHTPIN    18
#define DHTTYPE   DHT11
#define MQ135_PIN 34
#define HX_DT      4
#define HX_SCK     5

// --- Sensor Objects ---
DHT   dht(DHTPIN, DHTTYPE);
HX711 scale;

// --- Global Sensor Values ---
float g_temperature    = 25.0;  // Last known good value (fallback)
float g_humidity       = 60.0;  // Last known good value (fallback)
float g_gas            = 0.0;
int   g_gas_raw        = 0;
float g_weight         = 0.0;
float g_weight_loss    = 0.0;
bool  g_sensor_ok      = false;
bool  g_dht_ok         = false; // Track if DHT22 has ever given valid reading

// --- Calibration ---
float calibration_factor = -7050;
// base_weight: set to 0 initially.
// It is AUTO-SET the first time a weight > 5g is detected.
// Use Serial command "setbase" to manually re-set it anytime.
float base_weight = 0;

// --- Timing ---
const unsigned long SEND_INTERVAL_MS = 10000;
unsigned long lastSendTime           = 0;

// Flask API URL
String API_URL;

// ============================================================
//  WIFI - no longer restarts on failure, just continues
// ============================================================
void connectWiFi() {
  Serial.print("\n[WiFi] Connecting to ");
  Serial.println(WIFI_SSID);
  WiFi.disconnect(true);
  delay(100);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    attempts++;
    if (attempts > 40) {
      // BUG FIX: was ESP.restart() which loops forever if WiFi is down.
      // Now we continue without WiFi so Serial Monitor still shows sensor data.
      Serial.println("\n[WiFi] Could not connect after 20s.");
      Serial.println("[WiFi] Continuing without WiFi - sensor readings still work.");
      Serial.println("[WiFi] Type 'wifi' to retry connection.");
      return;
    }
  }
  Serial.println("\n[WiFi] Connected!");
  Serial.print("[WiFi] IP: ");
  Serial.println(WiFi.localIP());
  Serial.print("[WiFi] Signal: ");
  Serial.print(WiFi.RSSI());
  Serial.println(" dBm");
}

// ============================================================
//  READ SENSORS - stores results in global variables
// ============================================================
void readSensors() {
  g_sensor_ok = false;

  // --- DHT22 ---
  float t = dht.readTemperature();
  float h = dht.readHumidity();
  if (isnan(t) || isnan(h)) {
    Serial.println("[Sensor] DHT22 FAILED! Using last known values.");
    Serial.println("[Sensor] Check: VCC->3.3V, GND->GND, DATA->GPIO18");
    // NON-FATAL: continue with last known g_temperature / g_humidity
    // This lets MQ135 + HX711 still work and API still gets called
    g_dht_ok = false;
  } else {
    g_temperature = t;
    g_humidity    = h;
    g_dht_ok      = true;
  }

  // --- MQ-135: map ADC (0-4095) to 0.0-3.0 ---
  g_gas_raw = analogRead(MQ135_PIN);
  if (g_gas_raw == 4095) {
    Serial.println("[Sensor] MQ135 reads 4095 = pin floating (sensor disconnected or no 5V power!)");
  }
  g_gas = round(((float)g_gas_raw / 4095.0f * 3.0f) * 100.0f) / 100.0f;

  // --- HX711 Load Cell ---
  if (scale.is_ready()) {
    float raw = scale.get_units(5);

    // Noise floor: treat tiny readings as 0
    if (abs(raw) < 1.0f) raw = 0.0f;
    g_weight = raw;

    // BUG FIX: base_weight was always 0 because it was read right after
    // tare() which zeroes everything. Now it AUTO-SETS on first valid reading.
    if (base_weight < 1.0f && g_weight > 5.0f) {
      base_weight = g_weight;
      Serial.print("[Scale] Base weight AUTO-SET to: ");
      Serial.print(base_weight, 1);
      Serial.println(" g  (food detected on scale)");
    }

    if (base_weight > 1.0f) {
      g_weight_loss = ((base_weight - g_weight) / base_weight) * 100.0f;
      if (g_weight_loss < 0.0f)   g_weight_loss = 0.0f;
      if (g_weight_loss > 100.0f) g_weight_loss = 100.0f;
    } else {
      g_weight_loss = 0.0f;
    }
  } else {
    Serial.println("[Sensor] HX711 not ready. Check DT=GPIO4, SCK=GPIO5.");
    g_weight      = 0.0f;
    g_weight_loss = 0.0f;
    // HX711 not responding is NOT fatal - continue with other sensors
  }

  g_sensor_ok = true; // Always true now unless readSensors() hits a hard error
}

// ============================================================
//  PRINT SENSOR VALUES
// ============================================================
void printSensors() {
  Serial.println("\n========== Sensor Readings ==========");
  Serial.print("Temperature : "); Serial.print(g_temperature, 1); Serial.println(" C");
  Serial.print("Humidity    : "); Serial.print(g_humidity, 1);    Serial.println(" %");
  Serial.print("Gas raw     : "); Serial.println(g_gas_raw);
  Serial.print("Gas norm    : "); Serial.println(g_gas, 2);
  //Serial.print("Weight      : "); Serial.print(g_weight, 1);      Serial.println(" g");
  //Serial.print("Base Weight : "); Serial.print(base_weight, 1);   Serial.println(" g");
 // Serial.print("Weight Loss : "); Serial.print(g_weight_loss, 1); Serial.println(" %");
  Serial.print("Food Type   : "); Serial.println(FOOD_TYPE);
  Serial.print("DHT22 OK    : "); Serial.println(g_dht_ok ? "YES" : "NO - using fallback values!");
  Serial.print("WiFi        : "); Serial.println(WiFi.status() == WL_CONNECTED ? "Connected" : "Disconnected");
  Serial.println("=====================================");
}

// ============================================================
//  SEND TO FLASK API
// ============================================================
void sendToAPI() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[API] WiFi not connected - skipping API call.");
    Serial.println("[API] Type 'wifi' to reconnect.");
    return;
  }

  // Build JSON payload
  StaticJsonDocument<256> doc;
  doc["food_type"]   = FOOD_TYPE;
  doc["temperature"] = g_temperature;
  doc["humidity"]    = g_humidity;
  doc["gas"]         = g_gas;

  String body;
  serializeJson(doc, body);

  Serial.println("[API] Sending...");
  Serial.print("[API] Payload: "); Serial.println(body);

  HTTPClient http;
  http.begin(API_URL);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(8000);

  int code = http.POST(body);

  if (code == 200) {
    String resp = http.getString();
    StaticJsonDocument<1024> jresp;
    DeserializationError err = deserializeJson(jresp, resp);

    if (!err && jresp["success"]) {
      JsonObject d = jresp["data"];

      // Result can be directly in data or nested under data.data
      float freshness = d["freshness_percentage"]     | -1.0f;
      float days      = d["predicted_remaining_days"] | -1.0f;
      float conf      = d["confidence"]               | -1.0f;
      String status   = d["predicted_status"].as<String>();

      if (freshness < 0 && d.containsKey("data")) {
        freshness = d["data"]["freshness_percentage"]     | 0.0f;
        days      = d["data"]["predicted_remaining_days"] | 0.0f;
        conf      = d["data"]["confidence"]               | 0.0f;
        status    = d["data"]["predicted_status"].as<String>();
      }

      Serial.println("[API] ---- Result ----");
      Serial.print("[API] Status    : "); Serial.println(status);
      Serial.print("[API] Freshness : "); Serial.print(freshness, 1); Serial.println("%");
      Serial.print("[API] Days Left : "); Serial.print(days, 1); Serial.println(" days");
      Serial.print("[API] Confidence: "); Serial.print(conf * 100.0f, 1); Serial.println("%");
      Serial.println("[API] ------------------");

      if (status == "fresh")         Serial.println("*** STATUS: FRESH - Good to eat! ***");
      else if (status == "good")     Serial.println("*** STATUS: GOOD - Still fresh. ***");
      else if (status == "moderate") Serial.println("*** STATUS: MODERATE - Consume soon. ***");
      else if (status == "spoiling") Serial.println("*** STATUS: SPOILING - Eat immediately! ***");
      else if (status == "spoiled")  Serial.println("*** STATUS: SPOILED - Do not consume! ***");

    } else {
      Serial.print("[API] Parse error. Raw response: ");
      Serial.println(resp.substring(0, 300));
    }

  } else if (code < 0) {
    Serial.print("[API] Connection failed: ");
    Serial.println(http.errorToString(code));
    Serial.println("[API] Check: Is Flask server running? Is SERVER_IP correct?");
  } else {
    Serial.print("[API] HTTP error: "); Serial.println(code);
    Serial.println(http.getString().substring(0, 200));
  }

  http.end();
}

// ============================================================
//  SERIAL COMMANDS
//  Open Serial Monitor at 115200 baud and type:
//    food:fruits    -> change food type
//    tare           -> zero the scale (empty container first!)
//    setbase        -> record current weight as new base weight
//    status         -> show WiFi + food type + base weight
//    send           -> trigger immediate sensor read + API call
//    debug          -> show raw sensor values for troubleshooting
//    wifi           -> retry WiFi connection
// ============================================================
void handleCommands() {
  if (!Serial.available()) return;
  String cmd = Serial.readStringUntil('\n');
  cmd.trim();

  if (cmd.startsWith("food:")) {
    FOOD_TYPE = cmd.substring(5);
    FOOD_TYPE.trim();
    Serial.print("[CMD] Food type set to: "); Serial.println(FOOD_TYPE);

  } else if (cmd == "tare") {
    // BUG FIX: was reading base_weight right after tare (always ~0).
    // tare now only zeroes the scale. Use "setbase" to record food weight.
    Serial.println("[CMD] Taring scale... Remove all weight from scale first!");
    delay(500);
    scale.tare();
    base_weight = 0;  // Reset - will auto-set when food is detected
    Serial.println("[CMD] Scale zeroed. Place food on scale - base weight will auto-set.");

  } else if (cmd == "setbase") {
    // Manually record current reading as the base weight
    if (scale.is_ready()) {
      float w = scale.get_units(10);
      if (w > 1.0f) {
        base_weight = w;
        Serial.print("[CMD] Base weight manually set to: ");
        Serial.print(base_weight, 1);
        Serial.println(" g");
      } else {
        Serial.println("[CMD] No weight detected on scale. Place food first.");
      }
    } else {
      Serial.println("[CMD] HX711 not ready.");
    }

  } else if (cmd == "status") {
    Serial.println("\n--- Status ---");
    Serial.print("WiFi       : "); Serial.println(WiFi.status() == WL_CONNECTED ? "Connected" : "Disconnected");
    Serial.print("IP         : "); Serial.println(WiFi.localIP());
    Serial.print("Food Type  : "); Serial.println(FOOD_TYPE);
    Serial.print("Base Weight: "); Serial.print(base_weight, 1); Serial.println(" g");
    Serial.print("API URL    : "); Serial.println(API_URL);
    Serial.println("--------------");

  } else if (cmd == "send") {
    Serial.println("[CMD] Manual send triggered...");
    readSensors();
    if (g_sensor_ok) { printSensors(); sendToAPI(); }
    else { Serial.println("[CMD] Sensor read failed."); }

  } else if (cmd == "debug") {
    // Raw sensor values for troubleshooting - does not send to API
    Serial.println("\n--- Debug: Raw Sensor Values ---");
    float t = dht.readTemperature();
    float h = dht.readHumidity();
    Serial.print("DHT22 Temp  : "); Serial.println(isnan(t) ? "FAILED - check wiring!" : String(t, 1) + " C");
    Serial.print("DHT22 Hum   : "); Serial.println(isnan(h) ? "FAILED - check wiring!" : String(h, 1) + " %");
    int mq = analogRead(MQ135_PIN);
    Serial.print("MQ135 ADC   : "); Serial.print(mq);
    if (mq == 4095) Serial.print("  << 4095 = sensor NOT connected or no 5V power!");
    Serial.println();
    Serial.print("HX711 ready : "); Serial.println(scale.is_ready() ? "YES" : "NO - check DT=GPIO4, SCK=GPIO5");
    if (scale.is_ready()) {
      Serial.print("HX711 units : "); Serial.print(scale.get_units(3), 1); Serial.println(" g");
    }
    Serial.print("Base weight : "); Serial.print(base_weight, 1); Serial.println(" g");
    Serial.print("WiFi status : "); Serial.println(WiFi.status() == WL_CONNECTED ? "Connected" : "Disconnected");
    Serial.println("--------------------------------");
    Serial.println("WIRING GUIDE:");
    Serial.println(" DHT22: VCC->3.3V, GND->GND, DATA->GPIO18");
    Serial.println(" MQ135: VCC->5V(!), GND->GND, AOUT->GPIO34");
    Serial.println(" HX711: VCC->3.3V, GND->GND, DT->GPIO4, SCK->GPIO5");
    Serial.println("--------------------------------");

  } else if (cmd == "wifi") {
    connectWiFi();

  } else if (cmd.length() > 0) {
    Serial.println("[CMD] Unknown command.");
    Serial.println("[CMD] Options: food:<type> | tare | setbase | status | send | debug | wifi");
  }
}

// ============================================================
//  SETUP
// ============================================================
void setup() {
  Serial.begin(115200);
  delay(1000);  // Let Serial settle

  Serial.println("\n====================================");
  Serial.println("  FreshSense ESP32 v2.1");
  Serial.println("====================================");
  Serial.println("[Info] Set Serial Monitor to 115200 baud!");

  API_URL = "http://" + String(SERVER_IP) + ":5000/api/predict/freshness";

  // --- DHT22 ---
  // NOTE: Do NOT call pinMode() before dht.begin() - it interferes with
  // the DHT library's internal pin management on ESP32.
  dht.begin();
  // DHT22 needs at least 2 seconds after power-on to stabilize.
  Serial.println("[Init] DHT22 warming up (2s)... GPIO 18");
  delay(2000);

  // Verify DHT22 on startup
  float t = dht.readTemperature();
  float h = dht.readHumidity();
  if (isnan(t) || isnan(h)) {
    Serial.println("[Init] WARNING: DHT22 read failed at startup!");
    Serial.println("[Init] >>> Check: VCC->3.3V, GND->GND, DATA->GPIO18 <<<");
    Serial.println("[Init] Continuing anyway - sensor data will use fallback values.");
  } else {
    g_temperature = t;
    g_humidity    = h;
    g_dht_ok      = true;
    Serial.print("[Init] DHT22 OK - Temp: "); Serial.print(t, 1);
    Serial.print("C  Hum: "); Serial.print(h, 1); Serial.println("%");
  }

  // --- HX711 ---
  scale.begin(HX_DT, HX_SCK);
  scale.set_scale(calibration_factor);
  // Tare the scale with the container EMPTY
  Serial.println("[Init] Taring HX711 (keep scale empty)...");
  scale.tare();
  delay(500);
  // BUG FIX: Do NOT read base_weight here - it will be ~0 right after tare.
  // base_weight is auto-set in readSensors() on the first valid reading > 5g.
  base_weight = 0;
  Serial.println("[Init] HX711 tared. Place food in container - base weight auto-sets on first read.");
  Serial.println("[Init] Or type 'setbase' after placing food to set it manually.");

  // --- MQ-135 ---
  Serial.println("[Init] MQ-135 on GPIO 34.");
  Serial.println("[Init] NOTE: MQ-135 needs ~30s preheat for accurate gas readings.");

  // --- WiFi ---
  connectWiFi();

  Serial.println("\n[Ready] FreshSense running! Sending data every 10s.");
  Serial.println("[Ready] Commands: food:<type> | tare | setbase | status | send | debug | wifi");
  Serial.print("[Ready] API: "); Serial.println(API_URL);
  Serial.println("====================================\n");
}

// ============================================================
//  LOOP
// ============================================================
void loop() {
  handleCommands();

  unsigned long now = millis();
  if (now - lastSendTime >= SEND_INTERVAL_MS) {
    lastSendTime = now;
    readSensors();
    if (g_sensor_ok) {
      printSensors();
      sendToAPI();
    } else {
      Serial.println("[Loop] Sensor read failed - skipping send. Type 'debug' for details.");
    }
  }

  delay(100);
}
