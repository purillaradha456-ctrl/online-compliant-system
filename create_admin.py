"""
Utility script to create or update an administrator account interactively.
Usage:
    py create_admin.py
"""
import getpass
from werkzeug.security import generate_password_hash
from database import get_db, init_db

def create_admin():
    init_db()
    print("=" * 50)
    print("      ResolveDesk - Admin Account Provisioning     ")
    print("=" * 50)

    name = input("Enter Admin Full Name [System Administrator]: ").strip() or "System Administrator"
    email = input("Enter Admin Email [admin@system.com]: ").strip().lower() or "admin@system.com"
    phone = input("Enter Phone Number (optional): ").strip()

    while True:
        password = getpass.getpass("Enter Admin Password: ").strip()
        if len(password) < 6:
            print("Password must be at least 6 characters long. Please try again.")
            continue
        confirm = getpass.getpass("Confirm Admin Password: ").strip()
        if password != confirm:
            print("Passwords do not match. Please try again.")
            continue
        break

    conn = get_db()
    cursor = conn.cursor()

    existing = cursor.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    password_hash = generate_password_hash(password)

    if existing:
        cursor.execute("""
            UPDATE users
            SET name = ?, password_hash = ?, phone = ?, role = 'admin'
            WHERE email = ?
        """, (name, password_hash, phone, email))
        print(f"\n[SUCCESS] Existing account '{email}' updated with new administrator privileges and password.")
    else:
        cursor.execute("""
            INSERT INTO users (name, email, phone, password_hash, role)
            VALUES (?, ?, ?, ?, 'admin')
        """, (name, email, phone, password_hash))
        print(f"\n[SUCCESS] New administrator account '{email}' created successfully.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_admin()
