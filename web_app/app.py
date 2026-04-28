# ============================================================
#  PHASE D — Flask Web Application
#  Serves the web-based GUI with full calculation + database
#  functionality. Image upload supported.
# ============================================================

from flask import Flask, request, jsonify, render_template, send_from_directory
import sqlite3
import os
from datetime import datetime

bioscope_app = Flask(__name__)

# Folder where uploaded specimen images will be saved
SPECIMEN_UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(SPECIMEN_UPLOAD_FOLDER, exist_ok=True)
bioscope_app.config["UPLOAD_FOLDER"] = SPECIMEN_UPLOAD_FOLDER

# Database lives one level up (same as phase_a, phase_b files)
DB_FILEPATH = os.path.join(os.path.dirname(__file__), "..", "calculations.db")

# ── LOOKUP TABLES ─────────────────────────────────────────────

SCOPE_CATALOGUE = {
    "Light Microscope (40x)":           40,
    "Light Microscope (100x)":          100,
    "Light Microscope (400x)":          400,
    "Light Microscope (1000x)":         1000,
    "Scanning Electron Microscope":     10000,
    "Transmission Electron Microscope": 100000,
    "Confocal Microscope":              600,
    "Fluorescence Microscope":          500,
}

UNIT_SHIFT_TABLE = {
    "nm":  1000,
    "µm":  1,
    "mm":  0.001,
    "cm":  0.0001,
    "m":   0.000001,
}


# ── DATABASE HELPERS ──────────────────────────────────────────

def initialise_database():
    conn = sqlite3.connect(DB_FILEPATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS specimen_records (
            record_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            operator_name   TEXT NOT NULL,
            image_size_um   REAL NOT NULL,
            real_size_value REAL NOT NULL,
            real_size_unit  TEXT NOT NULL,
            scope_used      TEXT NOT NULL,
            logged_at       TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def db_insert_record(operator, img_size, real_val, unit, scope):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_FILEPATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO specimen_records
            (operator_name, image_size_um, real_size_value, real_size_unit, scope_used, logged_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (operator, img_size, real_val, unit, scope, timestamp))
    conn.commit()
    conn.close()


def db_fetch_all_records():
    conn = sqlite3.connect(DB_FILEPATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM specimen_records ORDER BY record_id DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def db_remove_record(rid):
    conn = sqlite3.connect(DB_FILEPATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM specimen_records WHERE record_id = ?", (rid,))
    affected = cur.rowcount
    conn.commit()
    conn.close()
    return affected > 0


# ── ROUTES ────────────────────────────────────────────────────

@bioscope_app.route("/")
def serve_homepage():
    """Renders the main calculator page."""
    return render_template("index.html",
                           scope_options=list(SCOPE_CATALOGUE.keys()),
                           unit_options=list(UNIT_SHIFT_TABLE.keys()))


@bioscope_app.route("/calculate", methods=["POST"])
def handle_calculation():
    """
    Accepts form data: username, image file, measured size, scope, unit.
    Returns JSON with the result and breakdown.
    """
    operator = request.form.get("username", "").strip()
    raw_size  = request.form.get("measured_size", "").strip()
    scope_key = request.form.get("scope_type", "")
    unit_key  = request.form.get("output_unit", "")
    image_file = request.files.get("specimen_image")

    # Validate inputs
    errors = []
    if not operator:
        errors.append("Username is required.")
    if not raw_size:
        errors.append("Measured size is required.")
    if scope_key not in SCOPE_CATALOGUE:
        errors.append("Invalid microscope type selected.")
    if unit_key not in UNIT_SHIFT_TABLE:
        errors.append("Invalid output unit selected.")

    if errors:
        return jsonify({"success": False, "errors": errors}), 400

    try:
        img_size = float(raw_size)
        if img_size <= 0:
            raise ValueError
    except ValueError:
        return jsonify({"success": False, "errors": ["Measured size must be a positive number."]}), 400

    # Save uploaded image
    saved_filename = None
    if image_file and image_file.filename:
        safe_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{image_file.filename}"
        image_file.save(os.path.join(bioscope_app.config["UPLOAD_FOLDER"], safe_name))
        saved_filename = safe_name

    # Perform calculation
    magnification = SCOPE_CATALOGUE[scope_key]
    conversion    = UNIT_SHIFT_TABLE[unit_key]
    real_um       = img_size / magnification
    final_result  = real_um * conversion

    # Save to database
    db_insert_record(operator, img_size, final_result, unit_key, scope_key)

    return jsonify({
        "success": True,
        "operator": operator,
        "image_size_um": img_size,
        "scope": scope_key,
        "magnification": magnification,
        "real_size_um": round(real_um, 8),
        "final_result": round(final_result, 8),
        "unit": unit_key,
        "image_saved": saved_filename,
        "breakdown": [
            f"Measured size on image: {img_size} µm",
            f"Microscope: {scope_key} (magnification: {magnification}×)",
            f"Formula: {img_size} ÷ {magnification} = {real_um:.8f} µm",
            f"Converted to {unit_key}: {real_um:.8f} × {conversion} = {final_result:.8f} {unit_key}",
        ]
    })


@bioscope_app.route("/records", methods=["GET"])
def get_all_records():
    """Returns all calculation records as JSON."""
    rows = db_fetch_all_records()
    return jsonify({"success": True, "records": rows})


@bioscope_app.route("/records/<int:record_id>", methods=["DELETE"])
def remove_one_record(record_id):
    """Deletes the record matching the given ID."""
    removed = db_remove_record(record_id)
    if removed:
        return jsonify({"success": True, "message": f"Record {record_id} deleted."})
    return jsonify({"success": False, "message": "Record not found."}), 404


# ── ENTRY POINT ───────────────────────────────────────────────

if __name__ == "__main__":
    initialise_database()
    bioscope_app.run(debug=True)