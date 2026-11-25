import os
import re
import sqlite3
import uuid
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "campuscare-demo-change-this-key")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
DB = os.environ.get("DATABASE_PATH", "campuscare.db")
ADMIN_USER = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "CampusCare@123")
UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

FLOORS = ["First Floor", "Second Floor", "Third Floor", "Fourth Floor"]
LOCATIONS = ["Classroom", "Washroom", "Staff Room", "Laboratory", "Corridor", "Staircase", "Office", "Other"]
CATEGORIES = ["Electrical", "Plumbing / Water Supply", "Cleanliness", "Furniture", "Classroom", "Laboratory", "Washroom", "Hostel", "Internet / Network", "Infrastructure", "Other"]
PRIORITIES = ["High", "Medium", "Low"]
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
USN_PATTERN = re.compile(r"^4JK(23|24|25|26)CI0\d{2,3}$", re.IGNORECASE)

def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()

def init_db():
    with sqlite3.connect(DB) as con:
        con.execute("""CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            usn TEXT NOT NULL DEFAULT '',
            place TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TEXT NOT NULL)""")
        existing = {row[1] for row in con.execute("PRAGMA table_info(complaints)")}
        migrations = {
            "user_type": "TEXT NOT NULL DEFAULT 'Student'",
            "identifier": "TEXT NOT NULL DEFAULT ''",
            "floor": "TEXT NOT NULL DEFAULT ''",
            "sub_location": "TEXT NOT NULL DEFAULT ''",
            "priority": "TEXT NOT NULL DEFAULT 'Medium'",
            "photo": "TEXT NOT NULL DEFAULT ''"
        }
        for name, definition in migrations.items():
            if name not in existing:
                con.execute(f"ALTER TABLE complaints ADD COLUMN {name} {definition}")

def admin_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get("admin"):
            flash("Please sign in as administrator.", "error")
            return redirect(url_for("admin_login"))
        return fn(*args, **kwargs)
    return wrapped

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def home():
    rows = db().execute("SELECT * FROM complaints ORDER BY id DESC").fetchall()
    stats = {
        "total": len(rows),
        "pending": sum(x["status"] == "Pending" for x in rows),
        "progress": sum(x["status"] == "In Progress" for x in rows),
        "resolved": sum(x["status"] == "Resolved" for x in rows)
    }
    return render_template("index.html", complaints=rows, stats=stats,
                           floors=FLOORS, locations=LOCATIONS, categories=CATEGORIES)

@app.post("/complaint")
def complaint():
    user_type = request.form.get("user_type", "Student").strip()
    name = request.form.get("student_name", "").strip()
    usn = request.form.get("usn", "").strip().upper()
    identifier = request.form.get("identifier", "").strip()
    floor = request.form.get("floor", "").strip()
    sub_location = request.form.get("sub_location", "").strip()
    custom_location = request.form.get("custom_location", "").strip()
    category = request.form.get("category", "").strip()
    custom_category = request.form.get("custom_category", "").strip()
    description = request.form.get("description", "").strip()
    priority = request.form.get("priority", "Medium").strip()

    if user_type not in ("Student", "Teaching Staff", "Non-Teaching Staff"):
        flash("Please select a valid user type.", "error")
        return redirect(url_for("home") + "#register")
    if not name or not floor or floor not in FLOORS or not sub_location or sub_location not in LOCATIONS or not category or category not in CATEGORIES or not description:
        flash("Please complete all required fields using the available options.", "error")
        return redirect(url_for("home") + "#register")
    if user_type == "Student" and not USN_PATTERN.fullmatch(usn):
        flash("Invalid USN. Use 4JK23CI0XX/XXX, 4JK24CI0XX/XXX, 4JK25CI0XX/XXX or 4JK26CI0XX/XXX.", "error")
        return redirect(url_for("home") + "#register")
    if user_type != "Student" and not identifier:
        flash("Please enter your staff ID / employee number.", "error")
        return redirect(url_for("home") + "#register")
    if priority not in PRIORITIES:
        flash("Please select a valid priority.", "error")
        return redirect(url_for("home") + "#register")
    if sub_location == "Other" and not custom_location:
        flash("Please enter the specific location.", "error")
        return redirect(url_for("home") + "#register")
    if category == "Other" and not custom_category:
        flash("Please enter the complaint category.", "error")
        return redirect(url_for("home") + "#register")

    place_detail = custom_location if sub_location == "Other" else sub_location
    place = f"{floor} · {place_detail}"
    if user_type != "Student":
        usn = ""
    category_value = custom_category if category == "Other" else category

    photo_name = ""
    photo = request.files.get("photo")
    if photo and photo.filename:
        if not allowed_file(photo.filename):
            flash("Please upload a JPG, JPEG, PNG or WEBP image.", "error")
            return redirect(url_for("home") + "#register")
        extension = secure_filename(photo.filename).rsplit(".", 1)[1].lower()
        photo_name = f"{uuid.uuid4().hex}.{extension}"
        photo.save(os.path.join(app.config["UPLOAD_FOLDER"], photo_name))

    db().execute("""INSERT INTO complaints
        (student_name, usn, place, category, description, created_at,
         user_type, identifier, floor, sub_location, priority, photo)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (name, usn, place, category_value, description,
         datetime.now().strftime("%d %b %Y, %I:%M %p"),
         user_type, identifier, floor, place_detail, priority, photo_name))
    db().commit()
    flash("Your complaint has been registered successfully.", "success")
    return redirect(url_for("home") + "#register")

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("username") == ADMIN_USER and request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin"))
        flash("Incorrect admin username or password.", "error")
    return render_template("login.html")

@app.route("/admin")
@admin_required
def admin():
    rows = db().execute("SELECT * FROM complaints ORDER BY id DESC").fetchall()
    floor_summary = []
    for floor in FLOORS:
        floor_rows = [row for row in rows if row["floor"] == floor]
        floor_summary.append({
            "name": floor,
            "total": len(floor_rows),
            "high": sum(row["priority"] == "High" and row["status"] != "Resolved" for row in floor_rows),
            "medium": sum(row["priority"] == "Medium" and row["status"] != "Resolved" for row in floor_rows),
            "low": sum(row["priority"] == "Low" and row["status"] != "Resolved" for row in floor_rows)
        })
    return render_template("admin.html", complaints=rows, floor_summary=floor_summary)

@app.post("/admin/update/<int:cid>")
@admin_required
def update(cid):
    status = request.form.get("status")
    if status in ("Pending", "In Progress", "Resolved"):
        db().execute("UPDATE complaints SET status=? WHERE id=?", (status, cid))
        db().commit()
        flash("Complaint status updated.", "success")
    return redirect(url_for("admin"))

@app.get("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("home"))

@app.errorhandler(413)
def too_large(error):
    flash("Image is too large. Please upload an image smaller than 5 MB.", "error")
    return redirect(url_for("home") + "#register")

@app.get("/health")
def health():
    return {"status": "ok", "application": "CampusCare"}

with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
