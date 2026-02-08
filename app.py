from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_cors import CORS
import sqlite3
import datetime
import re

app = Flask(__name__)
CORS(app)

DATABASE = "hrms.db"

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS employees(
        employee_id TEXT PRIMARY KEY,
        full_name TEXT NOT NULL,
        email TEXT NOT NULL,
        department TEXT NOT NULL
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS attendance(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id TEXT,
        date TEXT,
        status TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email)

# ---------------- Dashboard ----------------
@app.route("/")
def dashboard():
    return render_template("index.html")

# ---------------- Add Employee Page ----------------
@app.route("/add-page")
def add_employee_page():
    conn = get_db()
    employees = conn.execute("SELECT * FROM employees").fetchall()
    return render_template("add_employee.html", employees=employees)

@app.route("/add", methods=["POST"])
def add_employee():
    data = request.form

    if not is_valid_email(data["email"]):
        return "Invalid Email", 400

    conn = get_db()
    try:
        conn.execute("INSERT INTO employees VALUES (?,?,?,?)",
                     (data["employee_id"], data["full_name"], data["email"], data["department"]))
        conn.commit()
    except sqlite3.IntegrityError:
        return "Employee already exists", 400

    return redirect(url_for("add_employee_page"))

@app.route("/delete/<emp_id>")
def delete_employee(emp_id):
    conn = get_db()
    conn.execute("DELETE FROM employees WHERE employee_id=?", (emp_id,))
    conn.commit()
    return redirect(url_for("add_employee_page"))

# ---------------- Attendance Page ----------------
@app.route("/attendance-page")
def attendance_page():
    conn = get_db()
    employees = conn.execute("SELECT employee_id, full_name FROM employees").fetchall()
    return render_template("mark_attendance.html", employees=employees)

@app.route("/mark/<emp_id>")
def mark_attendance(emp_id):
    conn = get_db()
    conn.execute("INSERT INTO attendance (employee_id, date, status) VALUES (?,?,?)",
                 (emp_id, str(datetime.date.today()), "Present"))
    conn.commit()
    return redirect(url_for("attendance_page"))

@app.route("/attendance/<emp_id>")
def view_attendance(emp_id):
    conn = get_db()
    records = conn.execute("SELECT * FROM attendance WHERE employee_id=?", (emp_id,)).fetchall()
    return render_template("attendance.html", records=records, emp_id=emp_id)

# ---------------- APIs ----------------
@app.route("/api/employees", methods=["GET"])
def api_employees():
    conn = get_db()
    rows = conn.execute("SELECT * FROM employees").fetchall()
    return jsonify([dict(r) for r in rows])

# ---------------- Run ----------------
if __name__ == "__main__":
    app.run(debug=True)