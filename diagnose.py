import sqlite3, json, os

conn = sqlite3.connect('backend/database.db')
conn.row_factory = sqlite3.Row

count = conn.execute("SELECT COUNT(*) FROM food_freshness").fetchone()[0]
print("Total rows:", count)

rows = conn.execute("SELECT * FROM food_freshness ORDER BY id DESC LIMIT 3").fetchall()
for r in rows:
    print(dict(r))

conn.close()

# Check analytics endpoint manually
import sys
sys.path.insert(0, 'backend')
try:
    from ml_predictor import MLPredictor
    p = MLPredictor()
    print("Freshness model loaded:", p.is_loaded)
    result = p.predict_freshness({"food_type":"fruits","temperature":5,"humidity":80,"gas":0.3})
    print("Sample prediction:", result)
except Exception as e:
    print("Freshness model error:", e)

# Check image classifier
try:
    import tensorflow as tf
    model = tf.keras.models.load_model('backend/food_classifier.h5')
    with open('backend/food_classifier_labels.json') as f:
        labels = json.load(f)
    print("Image classifier loaded OK. Classes:", labels['num_classes'])
    print("Accuracy:", labels['training_info']['final_accuracy'])
except Exception as e:
    print("Image classifier error:", e)
