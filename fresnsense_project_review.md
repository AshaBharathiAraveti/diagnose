# 🌿 FreshSense — Complete Project Description
### IoT-Based Real-Time Food Freshness Monitoring System

---

## 1. Project Overview (Elevator Pitch)

**FreshSense** is an end-to-end IoT system that monitors the freshness of food items in real time using environmental sensors and a machine learning model. An **ESP32 microcontroller** continuously reads temperature, humidity, and gas concentration from attached sensors, then sends this data over WiFi to a **Flask backend** running on a PC. The backend feeds the sensor data into a trained **ML model** that predicts:
- Whether the food is **Fresh / Good / Moderate / Spoiling / Spoiled**
- A **freshness percentage** (0–100%)
- **Estimated days remaining** before spoilage
- **Storage recommendations**

All results are saved to a local **SQLite database** and displayed on a **real-time web dashboard** with charts, history, and analytics.

---

## 2. Project Goals

| Goal | Implementation |
|------|---------------|
| Real-time monitoring | ESP32 sends data every 10 seconds |
| ML-based freshness prediction | Trained `custom_food_model.pkl` (Random Forest/sklearn) |
| Data persistence | SQLite database via Flask |
| Visual dashboard | HTML/CSS/JS frontend with Chart.js |
| Multiple food types | 20 food categories supported |
| Portability | Runs on a hotspot — no fixed internet needed |

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        ESP32 Hardware                           │
│  DHT11 (Temp+Humidity) ─┐                                       │
│  MQ-135 (Gas/Air)      ──── ESP32 Microcontroller ─── WiFi ──► │
│  HX711 + Load Cell ─────┘    (every 10 seconds)                 │
└─────────────────────────────────────────────────────────────────┘
                                      │ HTTP POST (JSON)
                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Flask Backend (Python)                        │
│  app.py ──► ml_predictor.py ──► custom_food_model.pkl           │
│     │              │                                            │
│     └──► SQLite Database (database.db)                          │
│     └──► REST API (port 5000)                                   │
└─────────────────────────────────────────────────────────────────┘
                                      │ HTTP (GET/POST)
                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                Web Dashboard (Frontend)                         │
│  index.html + dashboard.js + charts.js + Chart.js               │
│  • Dashboard Tab     • Predict Tab                              │
│  • History Tab       • Analytics Tab                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Hardware Layer (ESP32)

### Microcontroller
- **Board**: ESP32 (runs Arduino C++ code)
- **Firmware**: `esp32_code.ino` (v2.1)
- **Communication**: WiFi HTTP POST to Flask API

### Sensors

| Sensor | Model | GPIO Pin | Measures | Notes |
|--------|-------|----------|----------|-------|
| Temperature & Humidity | DHT11 | GPIO 18 | °C, % RH | 2s warmup needed |
| Gas / Air Quality | MQ-135 | GPIO 34 | Analog 0–4095 → 0.0–3.0 ppm | Needs 5V power; 30s preheat |
| Load Cell (Weight) | HX711 + Load Cell | DT=GPIO4, SCK=GPIO5 | Grams | Weight loss % calculated |

### WiFi Configuration
```cpp
const char* WIFI_SSID     = "Asha's A35";        // Hotspot name
const char* WIFI_PASSWORD = "Ashaaaaa";
const char* SERVER_IP     = "10.32.243.63";       // PC's local IP
```

### Data Sent (JSON Payload)
```json
{
  "food_type":   "fruits",
  "temperature": 26.5,
  "humidity":    68.0,
  "gas":         0.45
}
```

### Key Firmware Features
- **Non-fatal sensor failures**: If DHT11 fails, uses last known values — doesn't crash
- **Auto base-weight**: Scale auto-sets base weight on first reading > 5g
- **Serial commands**: `food:<type>`, `tare`, `setbase`, `status`, `send`, `debug`, `wifi`
- **Resilient WiFi**: Doesn't restart on WiFi failure — continues showing serial data
- **Send interval**: Every 10,000 ms (10 seconds)

### Gas Value Mapping
```
ADC Raw (0–4095) → Normalized: (raw / 4095) × 3.0
4095 = sensor disconnected / no 5V power
```

---

## 5. Backend Layer (Flask + Python)

### Technology Stack
- **Framework**: Flask (Python)
- **Database**: SQLite3 (`database.db`)
- **ML Library**: scikit-learn (joblib, pandas, numpy)
- **API**: RESTful JSON API on port 5000

### File: `app.py`
Central Flask application. Key responsibilities:
1. Serves the frontend (`index.html`) at route `/`
2. Exposes REST API endpoints
3. Loads the ML predictor on startup
4. Auto-creates the SQLite database table on first run

### Database Schema (`food_freshness` table)

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Auto-increment primary key |
| `food_type` | TEXT | e.g. "fruits", "leafy_greens" |
| `temperature` | REAL | In °C |
| `humidity` | REAL | In % |
| `gas` | REAL | Normalized ppm |
| `spoiled` | INTEGER | 0=no, 1=yes |
| `remaining_days` | REAL | Predicted shelf life remaining |
| `freshness_percent` | REAL | 0–100% |
| `ml_predicted_status` | TEXT | fresh/good/moderate/spoiling/spoiled |
| `ml_confidence` | REAL | 0.0–1.0 |
| `ml_predicted_days` | REAL | From ML regressor |
| `ml_freshness_percentage` | REAL | From ML calculation |
| `ml_recommendations` | TEXT | JSON string of advice |
| `timestamp` | TEXT | "YYYY-MM-DD HH:MM:SS" |

### REST API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/predict/freshness` | Main prediction — accepts sensor JSON, returns ML result, saves to DB |
| `GET` | `/api/latest` | Returns most recent DB record (used by dashboard & ESP32 autofill) |
| `GET` | `/api/history` | Paginated history with food/status filters |
| `GET` | `/api/analytics` | Aggregated stats: distribution, trends, food averages |
| `GET` | `/api/food-types` | Returns all 20 food types and 5 categories |
| `GET` | `/api/models/status` | Returns whether ML model is loaded |
| `DELETE` | `/api/clear-history` | Deletes all records |

### CORS
- `flask-cors` is enabled — allows the browser frontend to call the API freely

---

## 6. Machine Learning Layer

### File: `ml_predictor.py`
### Trained Model: `custom_food_model.pkl` (~37 MB, saved with `joblib`)

### Model Structure
The `.pkl` file is a Python **dictionary** with 4 components:

```python
model = {
    'spoilage_classifier':  <sklearn Classifier>,   # predicts 0=fresh, 1=spoiled
    'shelf_life_regressor': <sklearn Regressor>,    # predicts days remaining
    'food_type_encoder':    <LabelEncoder>,         # encodes food type string to int
    'scaler':               <StandardScaler>        # normalizes features
}
```

### Features Used for Prediction

| Feature | Source | Preprocessing |
|---------|--------|--------------|
| `food_type_encoded` | ESP32 / user input | Label encoded |
| `temperature_c` | DHT11 sensor | Standard scaled |
| `humidity_percent` | DHT11 sensor | Standard scaled |
| `gas_ppm` | MQ-135 sensor | Standard scaled |
| `day` | Default = 1 | Standard scaled |

### Prediction Pipeline (step by step)
1. Receive JSON from Flask route
2. `_prepare_input_data()`: Convert to DataFrame, encode food type, scale all features
3. `classifier.predict()` → binary output: `0` (fresh) or `1` (spoiled)
4. `classifier.predict_proba()` → confidence score (0.0–1.0)
5. `regressor.predict()` → estimated remaining days (float)
6. Map to status string using thresholds:
   - `>= 0.9` → **spoiled**
   - `>= 0.7` → **spoiling**
   - `>= 0.5` → **moderate**
   - `>= 0.2` → **good**
   - `< 0.2`  → **fresh**
7. Calculate freshness %:
   - If binary `0` (fresh): `confidence × 100`
   - If binary `1` (spoiled): `(1 − confidence) × 100`
8. Generate recommendations based on temp, humidity, food type

### Fallback Prediction (Rule-Based)
When the ML model is not loaded, a simple rule-based fallback runs:

```python
if temperature > 25 or gas > 1.0:  → "spoiling", freshness=30%, days=2
elif temperature > 15 or gas > 0.7: → "moderate", freshness=60%, days=5
else:                               → "fresh",    freshness=85%, days=7
```

### Unknown Food Type Handling
If the food type wasn't in the training data, it maps to the closest known category (defaults to `'fruits'` or the first known class).

### Training Dataset
- File: `diverse_food_dataset_5000.csv` (5000 rows in project root)
- Features: food_type, temperature_c, humidity_percent, gas_ppm, day
- Labels: spoilage status (binary), remaining days

---

## 7. Frontend Layer (Dashboard)

### Technology: Vanilla HTML + CSS + JavaScript
### Entry Point: `frontend/index.html`
### Scripts: `js/dashboard.js`, `js/charts.js`, `js/chart.min.js` (Chart.js)

### 4 Tabs

#### 📊 Dashboard Tab
- **Summary cards**: Total predictions, Spoilage rate, Avg freshness %, Avg days left
- **ESP32 Live Feed card**: Shows real-time sensor readings (temp, humidity, gas, food type), freshness gauge, status badge, confidence, days left, timestamp — refreshes every 10 seconds
- **Latest Prediction card**: Full details of most recent DB record with gauge visual
- **LIVE indicator**: Briefly flashes green "LIVE · ESP32" when a new record arrives

#### 🔬 Predict Tab
- **Sensor Input form**: Dropdowns for food type, sliders + number inputs for temp/humidity/gas
- **"Read from ESP32" button**: Fetches `/api/latest` and auto-fills the sensor values
- **Results panel**: Animated gauge, status badge, days left, confidence %, recommendations

#### 📋 History Tab
- **Filterable table**: Filter by food type and status
- **Paginated**: 15 records per page with Prev/Next buttons
- **Clear All button**: Deletes all history

#### 📈 Analytics Tab
- **Status Distribution**: Doughnut chart (fresh/spoiling/spoiled counts)
- **Food Type Frequency**: Bar chart (top 10 most-checked food types)
- **Freshness Trend**: Line chart (last 30 predictions over time)
- **Avg Freshness by Food Type**: Radar chart

### Gauge Drawing (Canvas API)
Custom drawn with HTML5 Canvas — arc drawn proportionally to freshness %, colored by status (green=fresh, yellow=moderate, red=spoiled), with glow effect.

### Auto-refresh
Dashboard polls `/api/analytics` and `/api/latest` every **10 seconds** to show live ESP32 data without user interaction.

---

## 8. Supported Food Types (20 total)

| Category | Items |
|----------|-------|
| 🥬 Fresh Produce | leafy_greens, fruits, vegetables, herbs |
| 📦 Packaged Foods | canned_goods, dry_goods, frozen_foods, snacks |
| 🍔 Fast Food | burgers, pizza, sandwiches, fried_items |
| 🍽️ Cooked Food | prepared_meals, leftovers, restaurant_food, homemade |
| 🥩 Proteins | dairy, meat, fish, cooked |

---

## 9. Full Data Flow (End to End)

```
1. ESP32 reads sensors (every 10s)
   └─► DHT11: temperature, humidity
   └─► MQ-135: gas ppm
   └─► HX711: weight (optional)

2. ESP32 builds JSON & sends HTTP POST to:
   http://10.32.243.63:5000/api/predict/freshness

3. Flask receives POST → app.py → ml_predictor.predict_freshness()

4. MLPredictor:
   a. Encodes food_type → integer
   b. Scales all 5 features (StandardScaler)
   c. Runs spoilage_classifier.predict() → 0 or 1
   d. Runs predict_proba() → confidence
   e. Runs shelf_life_regressor.predict() → days
   f. Maps to status string (fresh/good/moderate/spoiling/spoiled)
   g. Calculates freshness % from confidence
   h. Generates storage recommendations

5. Flask saves result to SQLite database

6. Flask returns JSON response to ESP32
   └─► ESP32 prints to Serial Monitor: Status, Freshness%, Days, Confidence

7. Browser Dashboard polls /api/latest every 10s
   └─► Updates ESP32 Live Feed card with latest result
   └─► Updates charts, stats, history
```

---

## 10. How to Run the System

### Step 1: Start the Backend
```bat
cd c:\Users\HP\OneDrive\Desktop\diagnose
start.bat   ← Runs Flask server on port 5000
```
Or manually:
```powershell
cd backend
python app.py
```

### Step 2: Open the Dashboard
Navigate to: `http://localhost:5000` in any browser

### Step 3: Flash & Connect ESP32
- Open `hardware/esp32_code/esp32_code.ino` in Arduino IDE
- Set `SERVER_IP` to your PC's local IP (`ipconfig`)
- Set `WIFI_SSID` and `WIFI_PASSWORD` to your hotspot
- Flash to ESP32 at 115200 baud
- Open Serial Monitor — data sends every 10 seconds

### Port Configuration
- Flask runs on `0.0.0.0:5000` (accessible from all devices on network)
- `allow_port_5000.bat` opens Windows Firewall for port 5000

---

## 11. Key Technical Decisions & Why

| Decision | Reason |
|----------|--------|
| ESP32 (not Arduino Uno) | Has built-in WiFi — can send HTTP requests directly |
| DHT11 (not DHT22) | Available and sufficient for ambient temp/humidity |
| MQ-135 | Detects multiple gases (CO2, ammonia, etc.) useful for spoilage |
| Flask (not Django) | Lightweight, easy to set up, works well with ML libraries |
| SQLite (not MySQL) | Zero-configuration, file-based — perfect for local IoT project |
| Joblib pkl (not TensorFlow) | Sklearn models are smaller, faster to load, no GPU needed |
| Fallback prediction | Makes system robust — works even without the ML model file |
| `use_reloader=False` | Prevents Flask watchdog from restarting when TensorFlow imports files |
| `0.0.0.0` host | Allows ESP32 (on same hotspot) to reach Flask server |

---

## 12. Likely Review Questions & Answers

### Q1: What sensors did you use and why?
**A**: Three sensors:
- **DHT11** (GPIO 18): Measures temperature (°C) and humidity (%). These directly affect spoilage rate — higher temp accelerates bacterial growth.
- **MQ-135** (GPIO 34): Gas/air quality sensor. Detects ethylene, ammonia, CO2 — gases released during food decomposition. Gives a normalized 0–3.0 ppm value.
- **HX711 + Load Cell** (GPIO 4, 5): Measures weight to track weight loss (evaporation/decomposition indicator).

### Q2: What ML model did you use?
**A**: We used a **scikit-learn** model (saved as `custom_food_model.pkl`) consisting of:
- A **spoilage classifier** — binary classifier (fresh=0, spoiled=1)
- A **shelf-life regressor** — predicts remaining days as a float
- A **LabelEncoder** — converts food type strings to integers
- A **StandardScaler** — normalizes all input features

The model was trained on a dataset of 5,000 food samples (`diverse_food_dataset_5000.csv`).

### Q3: What is the accuracy of the model?
**A**: The exact accuracy depends on the training run, but typical sklearn classifiers on this kind of tabular sensor data achieve **85–95% accuracy**. The model includes a confidence score per prediction (via `predict_proba()`), so the system itself reports how certain it is.

### Q4: How does the freshness percentage work?
**A**: It's derived from the classifier's confidence:
- If predicted **fresh (0)**: freshness % = `confidence × 100` (e.g., 92% confident it's fresh → 92% freshness)
- If predicted **spoiled (1)**: freshness % = `(1 − confidence) × 100` (e.g., 85% confident spoiled → 15% freshness)

### Q5: How does the ESP32 communicate with the backend?
**A**: The ESP32 uses the **HTTPClient library** to send an HTTP POST request to the Flask server's `/api/predict/freshness` endpoint with a JSON body containing the sensor readings. The server responds with the ML prediction, which the ESP32 also prints to the Serial Monitor.

### Q6: What happens if the ESP32 loses WiFi?
**A**: The firmware is designed to be non-fatal. If WiFi drops, it skips the API call and prints a message to Serial Monitor. Sensor readings still work locally. The user can type `wifi` in Serial Monitor to trigger a reconnect attempt.

### Q7: What happens if the ML model file is missing?
**A**: The system falls back to a simple **rule-based prediction** based on temperature and gas thresholds:
- Temp > 25°C or gas > 1.0 → "spoiling"
- Temp > 15°C or gas > 0.7 → "moderate"
- Otherwise → "fresh"

### Q8: How is data stored?
**A**: Every prediction (from ESP32 or from the Predict tab) is stored in a **SQLite database** (`database.db`). The table `food_freshness` stores all sensor values, ML outputs, confidence, timestamps, etc.

### Q9: What does the dashboard show?
**A**: Four tabs:
1. **Dashboard** — Live ESP32 feed + latest prediction + summary stats
2. **Predict** — Manual prediction form with ESP32 auto-fill
3. **History** — Full paginated, filterable table of all predictions
4. **Analytics** — Charts: status distribution, food frequency, freshness trend, radar chart

### Q10: How is the frontend connected to the backend?
**A**: The HTML frontend uses JavaScript `fetch()` calls to the Flask REST API at `http://localhost:5000/api/`. The dashboard auto-refreshes every 10 seconds. CORS is enabled so the browser can make cross-origin requests.

### Q11: Why did you choose ESP32 over other microcontrollers?
**A**: ESP32 has **built-in WiFi and Bluetooth**, dual-core processor, and 30+ GPIO pins. This means we can connect multiple sensors AND send data over HTTP without any additional WiFi module — unlike Arduino Uno which would need a separate ESP8266 or SIM card.

### Q12: How does the food type affect the prediction?
**A**: Food type is encoded as a number using `LabelEncoder` and included as a feature in the ML model. Different foods have different natural spoilage rates (e.g., leafy greens spoil in 5 days, canned goods in 30+ days). The model learned these patterns from the training dataset. The recommendations also change per food type (e.g., "store leafy greens in airtight container with paper towel").

### Q13: What is the role of the HX711 load cell?
**A**: It measures the **weight of food** in grams. The system tracks `weight_loss %` = `(base_weight − current_weight) / base_weight × 100`. This is a physical indicator of spoilage since food loses moisture as it decomposes. However, weight data is currently logged but not directly fed into the ML model — it's an additional monitoring metric.

### Q14: What is the database used and why?
**A**: **SQLite** — it's a file-based, serverless SQL database that requires zero configuration. Since this is a local IoT system (not cloud-hosted), SQLite is perfect — fast, reliable, and the whole DB is a single `.db` file you can copy or share.

### Q15: How would you scale this system?
**A**: For production scaling:
- Replace SQLite with **PostgreSQL** or **MySQL**
- Host the Flask backend on **AWS/GCP/Azure** or as a Docker container
- Use **MQTT broker** (e.g., Mosquitto) instead of HTTP for lightweight real-time sensor communication
- Add **user authentication** (JWT)
- Use **TensorFlow/ONNX** model for better accuracy
- Add **mobile app** frontend

---

## 13. Project Folder Structure

```
diagnose/
├── backend/
│   ├── app.py                  ← Flask app, API routes
│   ├── ml_predictor.py         ← ML model loader + predictor
│   ├── custom_food_model.pkl   ← Trained ML model (~37 MB)
│   ├── database.db             ← SQLite database
│   ├── food_classifier.h5      ← (Additional TF model, optional)
│   ├── sensor_simulator.py     ← For testing without ESP32
│   └── requirements.txt        ← Python dependencies
├── frontend/
│   ├── index.html              ← Main dashboard page
│   ├── css/style.css           ← All styling
│   └── js/
│       ├── dashboard.js        ← Core dashboard logic
│       ├── charts.js           ← Chart.js chart builders
│       └── chart.min.js        ← Chart.js library
├── hardware/
│   └── esp32_code/
│       └── esp32_code.ino      ← ESP32 Arduino firmware (v2.1)
├── data/                       ← Training data
├── diverse_food_dataset_5000.csv ← 5000-row training dataset
├── start.bat                   ← One-click server launch
└── allow_port_5000.bat         ← Opens Windows Firewall port 5000
```

---

## 14. Limitations & Future Work

| Limitation | Future Improvement |
|------------|--------------------|
| DHT11 is less accurate than DHT22 | Upgrade to DHT22 or SHT31 |
| MQ-135 needs 30s preheat | Power it continuously; add indicator |
| Weight loss not used in ML model | Include as ML feature |
| SQLite not cloud-ready | Migrate to PostgreSQL + cloud hosting |
| No user authentication | Add JWT-based login |
| 10-second polling interval | Move to WebSockets for true real-time |
| Single food item at a time | Multi-sensor array for multiple foods |
| No alerts/notifications | Add email/SMS alerts on spoilage detection |

---

*Project: FreshSense v2.1 | Stack: ESP32 + Flask + sklearn + SQLite + Vanilla JS*
