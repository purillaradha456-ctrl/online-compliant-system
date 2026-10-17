import os
import random
import string
import csv
import io
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, send_from_directory, Response, abort
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from dotenv import load_dotenv

load_dotenv()

from database import get_db, init_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "online-complaint-management-secret-key-2026")

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf", "txt", "docx"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB limit

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_tracking_id():
    """Generate a unique tracking code like CMP-2026-X8K2"""
    year = datetime.now().year
    random_code = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"CMP-{year}-{random_code}"

# ----------------- AUTH DECORATORS ----------------- #

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session or session.get("role") != "admin":
            flash("Administrator privileges required to access this resource.", "danger")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# Context processor for templates
@app.context_processor
def inject_user():
    return {
        "current_user_name": session.get("user_name"),
        "current_user_role": session.get("role"),
        "is_logged_in": "user_id" in session
    }

# ----------------- PUBLIC ROUTES ----------------- #

@app.route("/")
def index():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM complaints").fetchone()[0]
    resolved = conn.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Resolved'").fetchone()[0]
    in_progress = conn.execute("SELECT COUNT(*) FROM complaints WHERE status = 'In Progress'").fetchone()[0]
    pending = conn.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Pending'").fetchone()[0]
    conn.close()

    resolution_rate = round((resolved / total * 100), 1) if total > 0 else 100.0

    return render_template(
        "index.html",
        total=total,
        resolved=resolved,
        in_progress=in_progress,
        pending=pending,
        resolution_rate=resolution_rate
    )

@app.route("/track", methods=["GET", "POST"])
def track():
    tracking_id = request.args.get("tracking_id", "").strip() or request.form.get("tracking_id", "").strip()
    complaint = None
    logs = []

    if tracking_id:
        conn = get_db()
        complaint = conn.execute("""
            SELECT c.*, u.name as user_name, u.email as user_email
            FROM complaints c
            JOIN users u ON c.user_id = u.id
            WHERE c.tracking_id = ?
        """, (tracking_id,)).fetchone()

        if complaint:
            logs = conn.execute("""
                SELECT * FROM complaint_logs
                WHERE complaint_id = ?
                ORDER BY created_at ASC
            """, (complaint["id"],)).fetchall()
        else:
            flash(f"No complaint found with Tracking ID: {tracking_id}", "danger")
        conn.close()

    return render_template("track.html", complaint=complaint, logs=logs, tracking_id=tracking_id)

# ----------------- AUTHENTICATION ----------------- #

@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("user_dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("Please fill in all required fields.", "danger")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "warning")
            return render_template("register.html")

        conn = get_db()
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            conn.close()
            flash("An account with this email already exists. Please log in.", "warning")
            return redirect(url_for("login"))

        password_hash = generate_password_hash(password)
        conn.execute("""
            INSERT INTO users (name, email, phone, password_hash, role)
            VALUES (?, ?, ?, ?, 'user')
        """, (name, email, phone, password_hash))
        conn.commit()
        conn.close()

        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        if session.get("role") == "admin":
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("user_dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]
            session["role"] = user["role"]

            flash(f"Welcome back, {user['name']}!", "success")
            if user["role"] == "admin":
                return redirect(url_for("admin_dashboard"))
            return redirect(url_for("user_dashboard"))
        else:
            flash("Invalid email or password. Please try again.", "danger")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("login"))

# ----------------- USER ROUTES ----------------- #

@app.route("/dashboard")
@login_required
def user_dashboard():
    user_id = session["user_id"]
    conn = get_db()

    # Metrics
    total = conn.execute("SELECT COUNT(*) FROM complaints WHERE user_id = ?", (user_id,)).fetchone()[0]
    pending = conn.execute("SELECT COUNT(*) FROM complaints WHERE user_id = ? AND status = 'Pending'", (user_id,)).fetchone()[0]
    in_progress = conn.execute("SELECT COUNT(*) FROM complaints WHERE user_id = ? AND status = 'In Progress'", (user_id,)).fetchone()[0]
    resolved = conn.execute("SELECT COUNT(*) FROM complaints WHERE user_id = ? AND status = 'Resolved'", (user_id,)).fetchone()[0]

    # Filters
    status_filter = request.args.get("status", "").strip()
    category_filter = request.args.get("category", "").strip()
    search_query = request.args.get("q", "").strip()

    query = "SELECT * FROM complaints WHERE user_id = ?"
    params = [user_id]

    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)
    if category_filter:
        query += " AND category = ?"
        params.append(category_filter)
    if search_query:
        query += " AND (tracking_id LIKE ? OR title LIKE ? OR description LIKE ?)"
        term = f"%{search_query}%"
        params.extend([term, term, term])

    query += " ORDER BY created_at DESC"
    complaints = conn.execute(query, params).fetchall()
    conn.close()

    return render_template(
        "user_dashboard.html",
        complaints=complaints,
        total=total,
        pending=pending,
        in_progress=in_progress,
        resolved=resolved,
        status_filter=status_filter,
        category_filter=category_filter,
        search_query=search_query
    )

@app.route("/complaint/new", methods=["GET", "POST"])
@login_required
def new_complaint():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        category = request.form.get("category", "").strip()
        priority = request.form.get("priority", "Medium").strip()
        location = request.form.get("location", "").strip()
        description = request.form.get("description", "").strip()

        if not title or not category or not description:
            flash("Please fill in all mandatory fields (Title, Category, Description).", "danger")
            return render_template("new_complaint.html")

        # Handle optional file upload
        filename = None
        if "attachment" in request.files:
            file = request.files["attachment"]
            if file and file.filename != "" and allowed_file(file.filename):
                safe_name = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                filename = f"{timestamp}_{safe_name}"
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        tracking_id = generate_tracking_id()
        user_id = session["user_id"]
        user_name = session["user_name"]

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO complaints (
                tracking_id, user_id, category, title, description, priority, location, attachment, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Pending')
        """, (tracking_id, user_id, category, title, description, priority, location, filename))
        complaint_id = cursor.lastrowid

        # Insert initial activity log
        cursor.execute("""
            INSERT INTO complaint_logs (complaint_id, status, action_by, remark)
            VALUES (?, ?, ?, ?)
        """, (complaint_id, "Submitted", user_name, "Complaint successfully registered by user."))

        conn.commit()
        conn.close()

        flash(f"Complaint registered successfully! Tracking ID: {tracking_id}", "success")
        return redirect(url_for("complaint_detail", tracking_id=tracking_id))

    return render_template("new_complaint.html")

@app.route("/complaint/<tracking_id>")
@login_required
def complaint_detail(tracking_id):
    conn = get_db()
    complaint = conn.execute("""
        SELECT c.*, u.name as user_name, u.email as user_email, u.phone as user_phone
        FROM complaints c
        JOIN users u ON c.user_id = u.id
        WHERE c.tracking_id = ?
    """, (tracking_id,)).fetchone()

    if not complaint:
        conn.close()
        flash("Complaint not found.", "danger")
        return redirect(url_for("user_dashboard"))

    # Security check: only author or admin can view
    if session.get("role") != "admin" and complaint["user_id"] != session["user_id"]:
        conn.close()
        flash("Unauthorized access to this complaint.", "danger")
        return redirect(url_for("user_dashboard"))

    logs = conn.execute("""
        SELECT * FROM complaint_logs
        WHERE complaint_id = ?
        ORDER BY created_at ASC
    """, (complaint["id"],)).fetchall()
    conn.close()

    return render_template("complaint_detail.html", complaint=complaint, logs=logs)

@app.route("/complaint/<tracking_id>/feedback", methods=["POST"])
@login_required
def submit_feedback(tracking_id):
    rating = request.form.get("rating", type=int)
    comment = request.form.get("comment", "").strip()

    if not rating or rating < 1 or rating > 5:
        flash("Please provide a valid rating between 1 and 5 stars.", "warning")
        return redirect(url_for("complaint_detail", tracking_id=tracking_id))

    conn = get_db()
    complaint = conn.execute("SELECT * FROM complaints WHERE tracking_id = ?", (tracking_id,)).fetchone()

    if not complaint or complaint["user_id"] != session["user_id"]:
        conn.close()
        flash("Complaint not found or unauthorized.", "danger")
        return redirect(url_for("user_dashboard"))

    if complaint["status"] != "Resolved":
        conn.close()
        flash("Feedback can only be submitted for resolved complaints.", "warning")
        return redirect(url_for("complaint_detail", tracking_id=tracking_id))

    conn.execute("""
        UPDATE complaints
        SET feedback_rating = ?, feedback_comment = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (rating, comment, complaint["id"]))

    conn.execute("""
        INSERT INTO complaint_logs (complaint_id, status, action_by, remark)
        VALUES (?, 'Feedback Submitted', ?, ?)
    """, (complaint["id"], session["user_name"], f"User rated {rating}/5 stars: {comment}"))

    conn.commit()
    conn.close()

    flash("Thank you for your valuable feedback!", "success")
    return redirect(url_for("complaint_detail", tracking_id=tracking_id))

# ----------------- ADMIN ROUTES ----------------- #

@app.route("/admin")
@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    conn = get_db()

    total = conn.execute("SELECT COUNT(*) FROM complaints").fetchone()[0]
    pending = conn.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Pending'").fetchone()[0]
    in_progress = conn.execute("SELECT COUNT(*) FROM complaints WHERE status = 'In Progress'").fetchone()[0]
    resolved = conn.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Resolved'").fetchone()[0]
    rejected = conn.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Rejected'").fetchone()[0]

    # Category breakdown
    category_counts = conn.execute("""
        SELECT category, COUNT(*) as count
        FROM complaints
        GROUP BY category
    """).fetchall()

    # Filter parameters
    status_filter = request.args.get("status", "").strip()
    category_filter = request.args.get("category", "").strip()
    priority_filter = request.args.get("priority", "").strip()
    search_query = request.args.get("q", "").strip()

    query = """
        SELECT c.*, u.name as user_name, u.email as user_email
        FROM complaints c
        JOIN users u ON c.user_id = u.id
        WHERE 1=1
    """
    params = []

    if status_filter:
        query += " AND c.status = ?"
        params.append(status_filter)
    if category_filter:
        query += " AND c.category = ?"
        params.append(category_filter)
    if priority_filter:
        query += " AND c.priority = ?"
        params.append(priority_filter)
    if search_query:
        query += " AND (c.tracking_id LIKE ? OR c.title LIKE ? OR u.name LIKE ? OR u.email LIKE ?)"
        term = f"%{search_query}%"
        params.extend([term, term, term, term])

    query += " ORDER BY c.created_at DESC"
    complaints = conn.execute(query, params).fetchall()
    conn.close()

    return render_template(
        "admin_dashboard.html",
        complaints=complaints,
        total=total,
        pending=pending,
        in_progress=in_progress,
        resolved=resolved,
        rejected=rejected,
        category_counts=category_counts,
        status_filter=status_filter,
        category_filter=category_filter,
        priority_filter=priority_filter,
        search_query=search_query
    )

@app.route("/admin/complaint/<tracking_id>", methods=["GET", "POST"])
@admin_required
def admin_manage_complaint(tracking_id):
    conn = get_db()
    complaint = conn.execute("""
        SELECT c.*, u.name as user_name, u.email as user_email, u.phone as user_phone
        FROM complaints c
        JOIN users u ON c.user_id = u.id
        WHERE c.tracking_id = ?
    """, (tracking_id,)).fetchone()

    if not complaint:
        conn.close()
        flash("Complaint not found.", "danger")
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        new_status = request.form.get("status", complaint["status"])
        new_priority = request.form.get("priority", complaint["priority"])
        admin_remark = request.form.get("admin_remark", "").strip()

        cursor = conn.cursor()
        cursor.execute("""
            UPDATE complaints
            SET status = ?, priority = ?, admin_remark = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_status, new_priority, admin_remark, complaint["id"]))

        # Log change in timeline
        action_note = f"Status changed to '{new_status}' with priority '{new_priority}'."
        if admin_remark:
            action_note += f" Remark: {admin_remark}"

        cursor.execute("""
            INSERT INTO complaint_logs (complaint_id, status, action_by, remark)
            VALUES (?, ?, ?, ?)
        """, (complaint["id"], new_status, session["user_name"], action_note))

        conn.commit()
        conn.close()

        flash(f"Complaint {tracking_id} successfully updated.", "success")
        return redirect(url_for("admin_manage_complaint", tracking_id=tracking_id))

    logs = conn.execute("""
        SELECT * FROM complaint_logs
        WHERE complaint_id = ?
        ORDER BY created_at ASC
    """, (complaint["id"],)).fetchall()
    conn.close()

    return render_template("admin_manage.html", complaint=complaint, logs=logs)

@app.route("/admin/export/csv")
@admin_required
def export_csv():
    conn = get_db()
    complaints = conn.execute("""
        SELECT c.tracking_id, u.name, u.email, c.category, c.title, c.priority, c.status,
               c.location, c.admin_remark, c.created_at, c.updated_at
        FROM complaints c
        JOIN users u ON c.user_id = u.id
        ORDER BY c.created_at DESC
    """).fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Tracking ID", "Complainant Name", "Complainant Email", "Category",
        "Title", "Priority", "Status", "Location", "Admin Remark", "Registered On", "Last Updated"
    ])

    for row in complaints:
        writer.writerow([
            row["tracking_id"], row["name"], row["email"], row["category"],
            row["title"], row["priority"], row["status"], row["location"],
            row["admin_remark"], row["created_at"], row["updated_at"]
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=complaints_report.csv"}
    )

# ----------------- ATTACHMENT DOWNLOAD ----------------- #

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# ----------------- MAIN INITIALIZER ----------------- #

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="127.0.0.1", port=5000)
