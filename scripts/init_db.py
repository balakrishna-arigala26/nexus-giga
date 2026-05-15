import sqlite3
import os

# Ensure data directory exists
os.makedirs("data", exist_ok=True)
db_path = "data/factory_inventory.db"

def initialize_database():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create inventory table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipment (
           id TEXT PRIMARY KEY,
           name TEXT NOT NULL,
           status TEXT NOT NULL,
           stock_level INTEGER,
           last_maintenance DATE
        )
    """)

    # Insert mock data (Clear exixsting first to avoid duplicate errors on return)
    cursor.execute("DELETE FROM equipment")

    mock_data = [
        ("V-101", "Vacuum Gripper", "Operational", 12, "2026-03-15"),
        ("M-204", "Conveyor Motor", "Warning - High Temp", 2, "2025-11-02"),
        ("S-009", "Optical Sensor", "Offline", 0, "2026-04-10"),
        ("P-550", "Hydraulic", "Operational", 4, "2026-01-20")
    ]

    cursor.executemany("""
        INSERT INTO equipment (id, name, status, stock_level, last_maintenance)
        VALUES (?, ?, ?, ?, ?)
    """, mock_data)

    conn.commit()
    conn.close()
    print(f"✅ Mock factory database initialized at {db_path}")

if __name__ == "__main__":
    initialize_database()