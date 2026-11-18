import os, sqlite3
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, g

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "campuscare-demo-change-this-key")
DB = os.environ.get("DATABASE_PATH", "campuscare.db")
ADMIN_USER = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "CampusCare@123")

def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    conn = g.pop("db", None)
    if conn is not None: conn.close()

def init_db():
    with sqlite3.connect(DB) as con:
        con.execute("""CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT, student_name TEXT NOT NULL,
            usn TEXT NOT NULL, place TEXT NOT NULL, category TEXT NOT NULL,
            description TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Pending',
            created_at TEXT NOT NULL)""")

def admin_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get("admin"):
            flash("Please sign in as administrator.", "error")
            return redirect(url_for("admin_login"))
        return fn(*args, **kwargs)
    return wrapped

@app.route("/")
def home():
    rows = db().execute("SELECT * FROM complaints ORDER BY id DESC").fetchall()
    stats = {
        "total": len(rows),
        "pending": sum(x["status"] == "Pending" for x in rows),
        "progress": sum(x["status"] == "In Progress" for x in rows),
        "resolved": sum(x["status"] == "Resolved" for x in rows)
    }
    return render_template("index.html", complaints=rows, stats=stats)

@app.post("/complaint")
def complaint():
    fields = [request.form.get(k, "").strip() for k in ("student_name","usn","place","category","description")]
    if not all(fields):
        flash("Please complete every field before submitting.", "error")
    else:
        db().execute("INSERT INTO complaints(student_name,usn,place,category,description,created_at) VALUES(?,?,?,?,?,?)",
                     (*fields, datetime.now().strftime("%d %b %Y, %I:%M %p")))
        db().commit()
        flash("Your complaint has been registered successfully.", "success")
    return redirect(url_for("home"))

@app.route("/admin/login", methods=["GET","POST"])
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
    return render_template("admin.html", complaints=rows)

@app.post("/admin/update/<int:cid>")
@admin_required
def update(cid):
    status = request.form.get("status")
    if status in ("Pending", "In Progress", "Resolved"):
        db().execute("UPDATE complaints SET status=? WHERE id=?", (status,cid))
        db().commit()
        flash("Complaint status updated.", "success")
    return redirect(url_for("admin"))

@app.get("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("home"))

@app.get("/health")
def health():
    return {"status":"ok","application":"CampusCare"}

with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
