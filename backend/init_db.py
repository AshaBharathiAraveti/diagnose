import sqlite3

# Connect to SQLite database (creates file if not exists)
conn = sqlite3.connect("database.db")

cursor = conn.cursor()

# Create table with ML prediction fields
cursor.execute("""
CREATE TABLE IF NOT EXISTS food_freshness (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    food_type TEXT,
    temperature REAL,
    humidity REAL,
    gas REAL,
    spoiled INTEGER,
    remaining_days REAL,
    freshness_percent REAL,
    ml_predicted_status TEXT,
    ml_confidence REAL,
    ml_predicted_days REAL,
    ml_freshness_percentage REAL,
    ml_recommendations TEXT,
    timestamp TEXT
)
""")

conn.commit()
conn.close()

print("Database and table created successfully")