"""
Flask Backend for IoT Food Freshness Scoring System
Handles: freshness prediction, history, and analytics
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime
import sqlite3
import json
import os
import logging
import numpy as np
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_here = os.path.dirname(os.path.abspath(__file__))
_frontend = os.path.join(_here, '..', 'frontend')

app = Flask(
    __name__,
    template_folder=os.path.join(_frontend),
    static_folder=os.path.join(_frontend),
    static_url_path=''
)

CORS(app)

# ─── ML Models ────────────────────────────────────────────────────────────────
from ml_predictor import MLPredictor
ml_predictor = MLPredictor()


# ─── Database ─────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), "database.db"))
    conn.row_factory = sqlite3.Row
    return conn


def ensure_db():
    """Create tables if they don't exist."""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS food_freshness (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            food_type            TEXT,
            temperature          REAL,
            humidity             REAL,
            gas                  REAL,
            spoiled              INTEGER,
            remaining_days       REAL,
            freshness_percent    REAL,
            ml_predicted_status  TEXT,
            ml_confidence        REAL,
            ml_predicted_days    REAL,
            ml_freshness_percentage REAL,
            ml_recommendations   TEXT,
            timestamp            TEXT
        );
    """)
    conn.commit()
    conn.close()


ensure_db()

# ─── Helpers ──────────────────────────────────────────────────────────────────
FOOD_TYPES = [
    "leafy_greens", "fruits", "vegetables", "herbs",
    "canned_goods", "dry_goods", "frozen_foods", "snacks",
    "burgers", "pizza", "sandwiches", "fried_items",
    "prepared_meals", "leftovers", "restaurant_food", "homemade",
    "dairy", "meat", "fish", "cooked"
]

FOOD_CATEGORIES = {
    "Fresh Produce":  {"items": ["leafy_greens", "fruits", "vegetables", "herbs"],  "icon": "🥬"},
    "Packaged Foods": {"items": ["canned_goods", "dry_goods", "frozen_foods", "snacks"], "icon": "📦"},
    "Fast Food":      {"items": ["burgers", "pizza", "sandwiches", "fried_items"],  "icon": "🍔"},
    "Cooked Food":    {"items": ["prepared_meals", "leftovers", "restaurant_food", "homemade"], "icon": "🍽️"},
    "Proteins":       {"items": ["dairy", "meat", "fish", "cooked"], "icon": "🥩"},
}

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    return render_template("index.html")


# ──── Prediction ─────────────────────────────────────
@app.route("/api/predict/freshness", methods=["POST"])
def predict_freshness():
    try:
        data = request.get_json(force=True)
        required = ["food_type", "temperature", "humidity", "gas"]
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({"success": False, "error": f"Missing fields: {missing}"}), 400

        result = ml_predictor.predict_freshness(data)

        if result.get("success") or result.get("fallback_prediction"):
            pred = result if result.get("success") else result["fallback_prediction"]

            conn = get_db()
            conn.execute("""
                INSERT INTO food_freshness
                (food_type, temperature, humidity, gas, spoiled, remaining_days, freshness_percent,
                 ml_predicted_status, ml_confidence, ml_predicted_days, ml_freshness_percentage,
                 ml_recommendations, timestamp)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                data["food_type"],
                float(data["temperature"]),
                float(data["humidity"]),
                float(data["gas"]),
                1 if pred.get("predicted_status","") in ["spoiled","spoiling"] else 0,
                pred.get("predicted_remaining_days", 0),
                pred.get("freshness_percentage", 0),
                pred.get("predicted_status", ""),
                pred.get("confidence", 0),
                pred.get("predicted_remaining_days", 0),
                pred.get("freshness_percentage", 0),
                json.dumps(pred.get("recommendations", {})),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            conn.commit()
            conn.close()

        return jsonify({
            "success": True,
            "data": result,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    except Exception as e:
        logger.exception("Prediction error")
        return jsonify({"success": False, "error": str(e)}), 500


# ──── Food Types & Categories ─────────────────────────
@app.route("/api/food-types", methods=["GET"])
def get_food_types():
    return jsonify({
        "success": True,
        "data": {
            "food_types": FOOD_TYPES,
            "categories": FOOD_CATEGORIES
        }
    })


# ──── History ─────────────────────────────────────────
@app.route("/api/history", methods=["GET"])
def get_history():
    page     = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    food_filter  = request.args.get("food_type", "")
    status_filter = request.args.get("status", "")
    offset   = (page - 1) * per_page

    conn = get_db()
    where_clauses, params = [], []
    if food_filter:
        where_clauses.append("food_type = ?"); params.append(food_filter)
    if status_filter:
        where_clauses.append("ml_predicted_status = ?"); params.append(status_filter)
    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    total = conn.execute(f"SELECT COUNT(*) FROM food_freshness {where_sql}", params).fetchone()[0]
    rows  = conn.execute(
        f"SELECT * FROM food_freshness {where_sql} ORDER BY timestamp DESC LIMIT ? OFFSET ?",
        params + [per_page, offset]
    ).fetchall()
    conn.close()

    return jsonify({
        "success": True,
        "data": [dict(r) for r in rows],
        "pagination": {"page": page, "per_page": per_page, "total": total,
                       "pages": (total + per_page - 1) // per_page}
    })


@app.route("/api/latest", methods=["GET"])
def get_latest():
    conn = get_db()
    row = conn.execute("SELECT * FROM food_freshness ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    if not row:
        return jsonify({})
    d = dict(row)
    d["ml_predicted_status"] = _norm_status(d.get("ml_predicted_status"))
    return jsonify(d)


# ──── Analytics ───────────────────────────────────────
def _norm_status(s):
    """Normalise raw classifier output ('0'/'1') to human labels."""
    if s in ("0", 0):   return "fresh"
    if s in ("1", 1):   return "spoiled"
    if s in (None, ""): return "unknown"
    return str(s).strip()


@app.route("/api/analytics", methods=["GET"])
def get_analytics():
    conn = get_db()
    rows = [dict(r) for r in conn.execute("SELECT * FROM food_freshness ORDER BY timestamp ASC").fetchall()]
    conn.close()

    if not rows:
        return jsonify({"success": True, "data": {"empty": True}})

    # Status distribution (normalised)
    status_dist = {}
    for r in rows:
        s = _norm_status(r.get("ml_predicted_status"))
        status_dist[s] = status_dist.get(s, 0) + 1

    # Food type frequency
    food_freq = {}
    for r in rows:
        ft = r.get("food_type") or "unknown"
        food_freq[ft] = food_freq.get(ft, 0) + 1
    food_freq_sorted = sorted(food_freq.items(), key=lambda x: x[1], reverse=True)[:10]

    # Freshness over time (last 30)
    freshness_trend = [
        {
            "timestamp":  r["timestamp"],
            "freshness":  r.get("ml_freshness_percentage") or 0,
            "food_type":  r.get("food_type", ""),
            "status":     _norm_status(r.get("ml_predicted_status"))
        }
        for r in rows[-30:]
    ]

    # Average sensor values + freshness by food type
    food_sensor_avgs = {}
    for r in rows:
        ft = r.get("food_type") or "unknown"
        if ft not in food_sensor_avgs:
            food_sensor_avgs[ft] = {"temps": [], "humidities": [], "gases": [], "freshness": []}
        if r.get("temperature") is not None:
            food_sensor_avgs[ft]["temps"].append(r["temperature"])
        if r.get("humidity") is not None:
            food_sensor_avgs[ft]["humidities"].append(r["humidity"])
        if r.get("gas") is not None:
            food_sensor_avgs[ft]["gases"].append(r["gas"])
        if r.get("ml_freshness_percentage") is not None:
            food_sensor_avgs[ft]["freshness"].append(r["ml_freshness_percentage"])

    avg_by_food = {
        ft: {
            "avg_temp":      round(np.mean(vals["temps"])      if vals["temps"]      else 0, 1),
            "avg_humidity":  round(np.mean(vals["humidities"]) if vals["humidities"] else 0, 1),
            "avg_gas":       round(np.mean(vals["gases"])      if vals["gases"]      else 0, 2),
            "avg_freshness": round(np.mean(vals["freshness"])  if vals["freshness"]  else 0, 1),
            "count":         len(vals["freshness"])
        }
        for ft, vals in food_sensor_avgs.items()
    }

    # Summary stats — normalise status for spoilage count too
    total         = len(rows)
    spoiled_count = sum(
        1 for r in rows
        if _norm_status(r.get("ml_predicted_status")) in ("spoiled", "spoiling")
    )
    fresh_vals = [r["ml_freshness_percentage"] for r in rows if r.get("ml_freshness_percentage") is not None]
    days_vals  = [r["ml_predicted_days"]       for r in rows if r.get("ml_predicted_days")       is not None]
    avg_fresh  = float(np.mean(fresh_vals)) if fresh_vals else 0.0
    avg_days   = float(np.mean(days_vals))  if days_vals  else 0.0

    return jsonify({
        "success": True,
        "data": {
            "summary": {
                "total_predictions":  total,
                "spoiled_count":      spoiled_count,
                "spoilage_rate":      round(spoiled_count / total * 100, 1) if total else 0,
                "avg_freshness":      round(avg_fresh, 1),
                "avg_remaining_days": round(avg_days,  1)
            },
            "status_distribution": status_dist,
            "food_type_frequency":  dict(food_freq_sorted),
            "freshness_trend":      freshness_trend,
            "food_sensor_averages": avg_by_food
        }
    })


@app.route("/api/models/status", methods=["GET"])
def model_status():
    fs = ml_predictor.get_model_status()
    return jsonify({
        "success": True,
        "data": {
            "freshness_model": fs
        }
    })


@app.route("/api/clear-history", methods=["DELETE"])
def clear_history():
    conn = get_db()
    conn.execute("DELETE FROM food_freshness")
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "History cleared"})


if __name__ == "__main__":
    # use_reloader=False prevents Flask from restarting itself when TensorFlow
    # touches its own .py files during import (triggers watchdog endlessly).
    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=False)