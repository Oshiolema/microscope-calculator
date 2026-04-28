# ============================================================
#  PHASE B — Database Integration
#  Extends Phase A to record every calculation in SQLite.
#  Users must provide a username before calculating.
# ============================================================

import sqlite3
import os
from datetime import datetime

# Reuse the lookup tables from Phase A logic (duplicated here
# so each phase file is self-contained and independently runnable)
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

# Path to the SQLite database file
DB_FILEPATH = os.path.join(os.path.dirname(__file__), "calculations.db")


# ── DATABASE SETUP ────────────────────────────────────────────

def initialise_database():
    """Creates the database and the records table if they don't exist yet."""
    db_link = sqlite3.connect(DB_FILEPATH)
    cursor = db_link.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS specimen_records (
            record_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            operator_name   TEXT    NOT NULL,
            image_size_um   REAL    NOT NULL,
            real_size_value REAL    NOT NULL,
            real_size_unit  TEXT    NOT NULL,
            scope_used      TEXT    NOT NULL,
            logged_at       TEXT    NOT NULL
        )
    """)
    db_link.commit()
    db_link.close()


def save_record_to_db(operator, img_size, real_val, unit, scope):
    """Inserts one calculation record into the database."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db_link = sqlite3.connect(DB_FILEPATH)
    cursor = db_link.cursor()
    cursor.execute("""
        INSERT INTO specimen_records
            (operator_name, image_size_um, real_size_value, real_size_unit, scope_used, logged_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (operator, img_size, real_val, unit, scope, timestamp))
    db_link.commit()
    db_link.close()
    print(f"\n  💾  Record saved to database successfully.")


def fetch_all_records():
    """Returns every row from the specimen_records table."""
    db_link = sqlite3.connect(DB_FILEPATH)
    cursor = db_link.cursor()
    cursor.execute("SELECT * FROM specimen_records ORDER BY record_id DESC")
    rows = cursor.fetchall()
    db_link.close()
    return rows


def delete_record_by_id(target_id):
    """Deletes a single record matching the given record ID."""
    db_link = sqlite3.connect(DB_FILEPATH)
    cursor = db_link.cursor()
    cursor.execute("DELETE FROM specimen_records WHERE record_id = ?", (target_id,))
    affected = cursor.rowcount
    db_link.commit()
    db_link.close()
    return affected > 0


# ── DISPLAY HELPERS ───────────────────────────────────────────

def print_records_table(rows):
    """Prints all saved records in a readable tabular layout."""
    if not rows:
        print("\n  📭  No records found in the database.\n")
        return

    print("\n" + "=" * 90)
    print(f"  {'ID':<5} {'Operator':<15} {'Image Size (µm)':<18} {'Real Size':<18} {'Microscope':<30} {'Date & Time'}")
    print("=" * 90)
    for row in rows:
        rec_id, operator, img_sz, real_val, real_unit, scope, timestamp = row
        real_display = f"{real_val:.6f} {real_unit}"
        print(f"  {rec_id:<5} {operator:<15} {img_sz:<18} {real_display:<18} {scope:<30} {timestamp}")
    print("=" * 90 + "\n")


# ── PHASE B MENU LOGIC ────────────────────────────────────────

def prompt_microscope_choice():
    scope_names = list(SCOPE_CATALOGUE.keys())
    print("\n--- Select Microscope Type ---")
    for idx, name in enumerate(scope_names, start=1):
        print(f"  [{idx}] {name}  ({SCOPE_CATALOGUE[name]}x)")
    while True:
        pick = input("Enter number: ").strip()
        if pick.isdigit() and 1 <= int(pick) <= len(scope_names):
            chosen = scope_names[int(pick) - 1]
            return chosen, SCOPE_CATALOGUE[chosen]
        print("  ⚠  Invalid selection.")


def prompt_output_unit():
    units = list(UNIT_SHIFT_TABLE.keys())
    print("\n--- Select Output Unit ---")
    for idx, u in enumerate(units, start=1):
        print(f"  [{idx}] {u}")
    while True:
        pick = input("Enter number: ").strip()
        if pick.isdigit() and 1 <= int(pick) <= len(units):
            return units[int(pick) - 1]
        print("  ⚠  Invalid selection.")


def run_calculation(operator_name):
    """Handles one full calculation cycle and saves to DB."""
    raw_size = input("\nEnter measured specimen size on image (in µm): ").strip()
    try:
        img_size = float(raw_size)
        if img_size <= 0:
            raise ValueError
    except ValueError:
        print("  ⚠  Invalid size. Please enter a positive number.")
        return

    scope_name, magnification = prompt_microscope_choice()
    output_unit = prompt_output_unit()

    real_size_um = img_size / magnification
    conversion = UNIT_SHIFT_TABLE[output_unit]
    final_result = real_size_um * conversion

    print("\n" + "=" * 55)
    print("         CALCULATION BREAKDOWN")
    print("=" * 55)
    print(f"  Operator                 : {operator_name}")
    print(f"  Measured image size      : {img_size} µm")
    print(f"  Microscope               : {scope_name} ({magnification}x)")
    print(f"  Real size in µm          : {img_size} ÷ {magnification} = {real_size_um:.6f} µm")
    print(f"  Converted to {output_unit:<5}       : {final_result:.6f} {output_unit}")
    print("=" * 55)
    print(f"  ✅  REAL-LIFE SIZE = {final_result:.6f} {output_unit}")
    print("=" * 55)

    save_record_to_db(operator_name, img_size, final_result, output_unit, scope_name)


def manage_records_menu():
    """Sub-menu for viewing and deleting saved records."""
    while True:
        print("\n--- Records Management ---")
        print("  [1] View all records")
        print("  [2] Delete a record by ID")
        print("  [3] Back to main menu")
        choice = input("Choose: ").strip()

        if choice == "1":
            rows = fetch_all_records()
            print_records_table(rows)

        elif choice == "2":
            rows = fetch_all_records()
            print_records_table(rows)
            if rows:
                del_id = input("Enter the Record ID to delete: ").strip()
                if del_id.isdigit():
                    removed = delete_record_by_id(int(del_id))
                    print("  🗑  Record deleted." if removed else "  ⚠  Record ID not found.")
                else:
                    print("  ⚠  Please enter a valid numeric ID.")

        elif choice == "3":
            break
        else:
            print("  ⚠  Invalid option.")


def run_phase_b():
    initialise_database()

    print("\n╔══════════════════════════════════════════╗")
    print("║  MICROSCOPE SIZE CALCULATOR — Phase B    ║")
    print("║  (with Database Integration)             ║")
    print("╚══════════════════════════════════════════╝")

    operator_name = input("\nEnter your username to begin: ").strip()
    while not operator_name:
        print("  ⚠  Username cannot be empty.")
        operator_name = input("Enter your username: ").strip()

    print(f"\n  Welcome, {operator_name}! You are now logged in.")

    while True:
        print("\n--- Main Menu ---")
        print("  [1] Perform a new calculation")
        print("  [2] View / Manage saved records")
        print("  [3] Exit")
        option = input("Choose an option: ").strip()

        if option == "1":
            run_calculation(operator_name)
        elif option == "2":
            manage_records_menu()
        elif option == "3":
            print(f"\n  Goodbye, {operator_name}! All records have been saved.\n")
            break
        else:
            print("  ⚠  Invalid option. Please choose 1, 2, or 3.")


if __name__ == "__main__":
    run_phase_b()