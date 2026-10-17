# ResolveDesk - Online Complaint Management System

A web-based **Online Grievance Redressal and Complaint Management System** designed for academic institutions, residential societies, corporate offices, or municipal departments. Built with **Python (Flask)**, **HTML5**, **CSS3**, **JavaScript (ES6)**, and **SQLite3**.

---

## 🌟 Key Features

### 1. Citizen / Student (User) Portal
- **Registration & Authentication**: Secure sign-up and sign-in with password hashing (`werkzeug.security`).
- **Grievance Lodging**:
  - Department categorization (Infrastructure, IT & Network, Sanitation, Hostel, Academic, Billing, Other).
  - Priority assignment (Low, Medium, High, Urgent).
  - Location specification (Block, room number, or floor).
  - Optional image or document attachment upload (PNG, JPG, PDF, DOCX).
- **Unique Tracking Code**: Generates reference numbers formatted like `CMP-2026-XXXX`.
- **Live Visual Stepper**: Progress visualization across 4 stages (*Submitted* → *Under Review* → *In Progress* → *Resolved / Rejected*).
- **Printable Acknowledgment Receipt**: Formatted print view (`Ctrl+P` or button) for physical documentation.
- **Feedback & Rating System**: Users can rate resolution quality (1 to 5 stars) and submit satisfaction notes upon closure.

### 2. Administrator Portal
- **KPI Metrics Dashboard**: Real-time counter of total, pending, in-progress, resolved, and rejected grievances.
- **Multi-criteria Filtering**: Filter complaints by status, category, priority, or search by keyword/tracking ID.
- **Triage & Status Updates**: Change complaint status, elevate/lower priority, and provide official resolution notes.
- **Audit History Trail**: Every action taken by users and admins is logged with timestamps and actor details.
- **Export to CSV**: Instant export of all grievance data for reporting, records, and viva demonstration.

### 3. Public Tracker
- Anyone with a valid Tracking ID can check progress and view official resolution notes without logging in.

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Backend** | Python 3.11+ (Flask Framework) | Routing, session management, business logic, API endpoints |
| **Database** | SQLite3 | Relational database storage with foreign key constraints |
| **Frontend** | HTML5 (Jinja2 Templates) | Semantic UI structure and template rendering |
| **Styling** | CSS3 (Custom Variables, Flexbox, Grid) | Responsive design, glassmorphism accents, print styles |
| **Interactivity**| Vanilla JavaScript | Live filtering, validation, interactive star rating, print handlers |

---

## 📂 Project Directory Structure

```text
online_complaint_system/
│
├── app.py                  # Main Flask application with routes and controllers
├── database.py             # SQLite database initialization, schema DDL, and sample seeds
├── complaints.db           # SQLite database file (auto-created on startup)
├── requirements.txt        # Python package dependencies
├── run.bat                 # One-click Windows runner script
├── test_app.py             # Automated unit tests for all features
├── README.md               # Complete project documentation & viva guide
│
├── static/
│   ├── css/
│   │   └── style.css       # Custom responsive stylesheet with print media queries
│   ├── js/
│   │   └── main.js         # Client-side dynamic search and interaction scripts
│   └── uploads/            # File attachment uploads storage
│
└── templates/              # Jinja2 HTML templates
    ├── base.html           # Master layout with responsive navbar and footer
    ├── index.html          # Public landing page with stats and quick tracker
    ├── track.html          # Public complaint tracking page with stepper
    ├── login.html          # Login page with demo autofill buttons
    ├── register.html       # User registration page
    ├── user_dashboard.html # Complainant dashboard with filters and history
    ├── new_complaint.html  # Complaint submission form
    ├── complaint_detail.html # Detailed view with timeline, receipt print, and feedback
    ├── admin_dashboard.html# Master administrator dashboard
    └── admin_manage.html   # Admin triage and status update panel
```

---

## 🗄️ Database Schema

### 1. `users` Table
Stores registered complainants and administrators.
- `id`: INTEGER PRIMARY KEY AUTOINCREMENT
- `name`: TEXT NOT NULL
- `email`: TEXT UNIQUE NOT NULL
- `phone`: TEXT
- `password_hash`: TEXT NOT NULL (hashed with pbkdf2:sha256)
- `role`: TEXT NOT NULL DEFAULT 'user' (`user` or `admin`)
- `created_at`: TIMESTAMP DEFAULT CURRENT_TIMESTAMP

### 2. `complaints` Table
Stores all grievances filed in the system.
- `id`: INTEGER PRIMARY KEY AUTOINCREMENT
- `tracking_id`: TEXT UNIQUE NOT NULL (e.g. `CMP-2026-8812`)
- `user_id`: INTEGER NOT NULL (Foreign Key → `users.id`)
- `category`: TEXT NOT NULL
- `title`: TEXT NOT NULL
- `description`: TEXT NOT NULL
- `priority`: TEXT NOT NULL DEFAULT 'Medium'
- `location`: TEXT
- `attachment`: TEXT (Filename in `static/uploads`)
- `status`: TEXT NOT NULL DEFAULT 'Pending' (`Pending`, `In Progress`, `Resolved`, `Rejected`)
- `admin_remark`: TEXT
- `feedback_rating`: INTEGER (1 to 5)
- `feedback_comment`: TEXT
- `created_at`: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
- `updated_at`: TIMESTAMP DEFAULT CURRENT_TIMESTAMP

### 3. `complaint_logs` Table
Audit trail logging every status change and remark.
- `id`: INTEGER PRIMARY KEY AUTOINCREMENT
- `complaint_id`: INTEGER NOT NULL (Foreign Key → `complaints.id`)
- `status`: TEXT NOT NULL
- `action_by`: TEXT NOT NULL
- `remark`: TEXT
- `created_at`: TIMESTAMP DEFAULT CURRENT_TIMESTAMP

---

## 🚀 How to Run the Project

### Option A: Using the One-Click Script (Windows)
Double-click `run.bat` or run:
```powershell
.\run.bat
```

### Option B: Manual Execution via Terminal
1. Navigate to the project folder:
   ```powershell
   cd C:\Users\HP\.gemini\antigravity\scratch\online_complaint_system
   ```

2. Install dependencies:
   ```powershell
   py -m pip install -r requirements.txt
   ```

3. Initialize the database and seed demo data:
   ```powershell
   py database.py
   ```

4. Launch the application:
   ```powershell
   py app.py
   ```

5. Open your web browser and visit:
   ```text
   http://127.0.0.1:5000
   ```

---

## 🔑 Authentication & Admin Setup

### 1. Provisioning an Administrator Account
To securely create or reset an administrator account without exposing credentials:
```powershell
py create_admin.py
```
This interactive prompt allows you to choose your own custom administrator email and password securely.

### 2. Environment Variables (.env)
Copy `.env.example` to `.env` to configure your environment secrets:
```powershell
copy .env.example .env
```
Inside `.env`, you can customize:
- `SECRET_KEY`: Random session secret key.
- `ADMIN_EMAIL`: Your custom admin email.
- `ADMIN_PASSWORD`: Your custom admin password.

*(Note: The `.env` file and `complaints.db` database are strictly excluded from Git tracking via `.gitignore` to prevent leaking credentials.)*

---

## 🧪 Running Automated Tests

Run the test suite to verify all endpoints and flows:
```powershell
py test_app.py
```
Expected output:
```text
....
----------------------------------------------------------------------
Ran 4 tests in 0.325s

OK
```

---

## 🎓 Viva Voce / Project Examination Q&A

### Q1: Why did you choose SQLite over MySQL or PostgreSQL for this mini-project?
> **Answer**: SQLite is serverless, zero-configuration, and self-contained in a single disk file (`complaints.db`). It is built directly into Python's standard library (`sqlite3`), making the project portable and easy to run without requiring a separate database server. For enterprise scaling, the schema can be migrated to PostgreSQL or MySQL with minimal changes.

### Q2: How is user password security handled?
> **Answer**: Passwords are never stored in plain text. We use `generate_password_hash` and `check_password_hash` from `werkzeug.security`, which implements the PBKDF2 hashing algorithm with SHA-256 and cryptographic salting to prevent rainbow table attacks.

### Q3: What prevents unauthorized users from accessing admin routes?
> **Answer**: We use Python decorators `@login_required` and `@admin_required`. These decorators inspect Flask's server-side `session` object. If `session['role'] != 'admin'`, the request is aborted or redirected with a flash warning message.

### Q4: How does the tracking feature work without requiring login?
> **Answer**: Each complaint is generated with an indexed, cryptographically random reference ID (`CMP-2026-XXXX`). When entered into the public `/track` endpoint, a parameterized SQL query retrieves the public status and admin remarks while omitting sensitive user credentials.

### Q5: How are file attachments securely stored?
> **Answer**: Uploaded files pass through `secure_filename()` to remove dangerous path traversal sequences (`../`), have file extensions checked against a whitelist (`ALLOWED_EXTENSIONS`), and are prepended with a timestamp to avoid filename collisions.
