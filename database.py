import sqlite3
import os
from werkzeug.security import generate_password_hash

from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.path.join(os.path.dirname(__file__), "complaints.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS complaints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tracking_id TEXT UNIQUE NOT NULL,
        user_id INTEGER NOT NULL,
        category TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        priority TEXT NOT NULL DEFAULT 'Medium',
        location TEXT,
        attachment TEXT,
        status TEXT NOT NULL DEFAULT 'Pending',
        admin_remark TEXT,
        feedback_rating INTEGER,
        feedback_comment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS complaint_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        complaint_id INTEGER NOT NULL,
        status TEXT NOT NULL,
        action_by TEXT NOT NULL,
        remark TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_tracking_id ON complaints(tracking_id);
    CREATE INDEX IF NOT EXISTS idx_user_id ON complaints(user_id);
    CREATE INDEX IF NOT EXISTS idx_status ON complaints(status);
    """)

    # Seed Admin User if not exists
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@system.com")
    cursor.execute("SELECT id FROM users WHERE email = ?", (admin_email,))
    admin_exists = cursor.fetchone()
    if not admin_exists:
        admin_name = os.environ.get("ADMIN_NAME", "System Administrator")
        admin_phone = os.environ.get("ADMIN_PHONE", "+1-800-555-0199")
        admin_pass_raw = os.environ.get("ADMIN_PASSWORD", "admin123")
        admin_pass = generate_password_hash(admin_pass_raw)
        cursor.execute("""
            INSERT INTO users (name, email, phone, password_hash, role)
            VALUES (?, ?, ?, ?, ?)
        """, (admin_name, admin_email, admin_phone, admin_pass, "admin"))

    # Seed Sample Regular User if not exists
    cursor.execute("SELECT id FROM users WHERE email = ?", ("student@example.com",))
    user_exists = cursor.fetchone()
    if not user_exists:
        user_pass = generate_password_hash("user123")
        cursor.execute("""
            INSERT INTO users (name, email, phone, password_hash, role)
            VALUES (?, ?, ?, ?, ?)
        """, ("Alex Johnson", "student@example.com", "+1-800-555-0144", user_pass, "user"))
        user_id = cursor.lastrowid

        # Seed sample complaints for the user
        sample_complaints = [
            (
                "CMP-2026-8812",
                user_id,
                "IT & Network",
                "Wi-Fi Connectivity Dropping in Block C Library",
                "The Wi-Fi router on 2nd floor library frequently disconnects during study hours.",
                "High",
                "Library Block C, 2nd Floor",
                None,
                "In Progress",
                "IT team dispatched a technician to test signal repeater."
            ),
            (
                "CMP-2026-7491",
                user_id,
                "Infrastructure",
                "Water Leakage in 3rd Floor Restroom",
                "Continuous faucet drip and puddle forming near washbasin. Requires plumber attention.",
                "Medium",
                "Main Building, Level 3",
                None,
                "Resolved",
                "Plumber replaced valve seal and checked pipes. Fixed on 16-Oct."
            ),
            (
                "CMP-2026-9034",
                user_id,
                "Sanitation",
                "Overflowing Waste Bins near Cafeteria Entrance",
                "Recycling bins have not been emptied since yesterday evening.",
                "Low",
                "Central Cafeteria",
                None,
                "Pending",
                None
            )
        ]

        for cmp_data in sample_complaints:
            cursor.execute("""
                INSERT INTO complaints (
                    tracking_id, user_id, category, title, description, priority, location, attachment, status, admin_remark
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, cmp_data)
            cmp_id = cursor.lastrowid

            # Add initial log
            cursor.execute("""
                INSERT INTO complaint_logs (complaint_id, status, action_by, remark)
                VALUES (?, ?, ?, ?)
            """, (cmp_id, "Submitted", "Alex Johnson", "Complaint registered into system."))

            if cmp_data[8] != "Pending":
                cursor.execute("""
                    INSERT INTO complaint_logs (complaint_id, status, action_by, remark)
                    VALUES (?, ?, ?, ?)
                """, (cmp_id, cmp_data[8], "System Administrator", cmp_data[9] or "Status updated."))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized and seeded successfully.")
