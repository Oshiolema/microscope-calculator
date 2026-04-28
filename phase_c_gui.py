# ============================================================
#  PHASE C — Python Tkinter GUI
#  Replaces the command-line interface with a full GUI.
#  All Phase A and Phase B functionality is available here.
#  NOTE: This file is kept for inspection during marking.
#        The web-based interface (Phase D) is the active app.
# ============================================================

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import sqlite3
import os
from datetime import datetime

# ── DATA TABLES ───────────────────────────────────────────────

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

DB_FILEPATH = os.path.join(os.path.dirname(__file__), "calculations.db")


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


def save_record(operator, img_size, real_val, unit, scope):
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


def fetch_all():
    conn = sqlite3.connect(DB_FILEPATH)
    cur = conn.cursor()
    cur.execute("SELECT * FROM specimen_records ORDER BY record_id DESC")
    rows = cur.fetchall()
    conn.close()
    return rows


def delete_by_id(rid):
    conn = sqlite3.connect(DB_FILEPATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM specimen_records WHERE record_id = ?", (rid,))
    affected = cur.rowcount
    conn.commit()
    conn.close()
    return affected > 0


# ── MAIN APPLICATION WINDOW ───────────────────────────────────

class MicroscopeApp(tk.Tk):
    """Root window for the Phase C Tkinter GUI."""

    def __init__(self):
        super().__init__()
        initialise_database()
        self.title("Microscope Size Calculator — Phase C")
        self.geometry("700x620")
        self.resizable(False, False)
        self.configure(bg="#fdf0f5")

        self.uploaded_image_path = tk.StringVar(value="No image selected")
        self.result_text = tk.StringVar(value="—")

        self._build_header()
        self._build_form()
        self._build_result_area()
        self._build_history_section()

    def _build_header(self):
        header_frame = tk.Frame(self, bg="#f7a8c4", pady=12)
        header_frame.pack(fill="x")
        tk.Label(
            header_frame,
            text="🔬  Microscope Size Calculator",
            font=("Georgia", 18, "bold"),
            bg="#f7a8c4",
            fg="#4a0030"
        ).pack()
        tk.Label(
            header_frame,
            text="Calculate the real-life size of your specimen",
            font=("Georgia", 10),
            bg="#f7a8c4",
            fg="#7a1050"
        ).pack()

    def _build_form(self):
        form_outer = tk.Frame(self, bg="#fdf0f5", padx=30, pady=16)
        form_outer.pack(fill="x")

        label_config = dict(bg="#fdf0f5", fg="#4a0030", font=("Georgia", 10, "bold"), anchor="w")
        entry_config = dict(font=("Courier", 10), relief="flat", bd=2, bg="#fff5f9", fg="#330022")

        # Username
        tk.Label(form_outer, text="Username:", **label_config).grid(row=0, column=0, sticky="w", pady=4)
        self.username_entry = tk.Entry(form_outer, width=36, **entry_config)
        self.username_entry.grid(row=0, column=1, pady=4, padx=8)

        # Image upload
        tk.Label(form_outer, text="Specimen Image:", **label_config).grid(row=1, column=0, sticky="w", pady=4)
        img_frame = tk.Frame(form_outer, bg="#fdf0f5")
        img_frame.grid(row=1, column=1, sticky="w", pady=4, padx=8)
        tk.Button(
            img_frame, text="Browse…", command=self._browse_image,
            bg="#f7a8c4", fg="#4a0030", font=("Georgia", 9, "bold"),
            relief="flat", cursor="hand2", padx=8
        ).pack(side="left")
        tk.Label(img_frame, textvariable=self.uploaded_image_path,
                 bg="#fdf0f5", fg="#888", font=("Courier", 8)).pack(side="left", padx=6)

        # Measured size
        tk.Label(form_outer, text="Measured Size (µm):", **label_config).grid(row=2, column=0, sticky="w", pady=4)
        self.size_entry = tk.Entry(form_outer, width=36, **entry_config)
        self.size_entry.grid(row=2, column=1, pady=4, padx=8)

        # Microscope type dropdown
        tk.Label(form_outer, text="Microscope Type:", **label_config).grid(row=3, column=0, sticky="w", pady=4)
        self.scope_var = tk.StringVar()
        scope_dropdown = ttk.Combobox(
            form_outer, textvariable=self.scope_var,
            values=list(SCOPE_CATALOGUE.keys()), state="readonly", width=34
        )
        scope_dropdown.grid(row=3, column=1, pady=4, padx=8)
        scope_dropdown.set(list(SCOPE_CATALOGUE.keys())[0])

        # Output unit dropdown
        tk.Label(form_outer, text="Output Unit:", **label_config).grid(row=4, column=0, sticky="w", pady=4)
        self.unit_var = tk.StringVar()
        unit_dropdown = ttk.Combobox(
            form_outer, textvariable=self.unit_var,
            values=list(UNIT_SHIFT_TABLE.keys()), state="readonly", width=34
        )
        unit_dropdown.grid(row=4, column=1, pady=4, padx=8)
        unit_dropdown.set("µm")

        # Calculate button
        tk.Button(
            form_outer, text="  Calculate Real Size  ",
            command=self._perform_calculation,
            bg="#f7689a", fg="white", font=("Georgia", 11, "bold"),
            relief="flat", cursor="hand2", pady=6
        ).grid(row=5, column=0, columnspan=2, pady=14)

    def _build_result_area(self):
        result_frame = tk.Frame(self, bg="#fff5f9", padx=20, pady=12, relief="flat", bd=1)
        result_frame.pack(fill="x", padx=30)
        tk.Label(result_frame, text="Result:", bg="#fff5f9", fg="#4a0030",
                 font=("Georgia", 10, "bold")).pack(anchor="w")
        self.result_label = tk.Label(
            result_frame, textvariable=self.result_text,
            bg="#fff5f9", fg="#c0006a",
            font=("Courier", 13, "bold"), wraplength=600, justify="left"
        )
        self.result_label.pack(anchor="w", pady=4)

    def _build_history_section(self):
        hist_frame = tk.Frame(self, bg="#fdf0f5", padx=30, pady=10)
        hist_frame.pack(fill="both", expand=True)

        btn_row = tk.Frame(hist_frame, bg="#fdf0f5")
        btn_row.pack(fill="x")
        tk.Button(btn_row, text="View History", command=self._load_history,
                  bg="#f7a8c4", fg="#4a0030", font=("Georgia", 9, "bold"),
                  relief="flat", cursor="hand2", padx=10, pady=4).pack(side="left", padx=4)
        tk.Button(btn_row, text="Delete Selected", command=self._delete_selected,
                  bg="#ffccd5", fg="#4a0030", font=("Georgia", 9, "bold"),
                  relief="flat", cursor="hand2", padx=10, pady=4).pack(side="left", padx=4)

        columns = ("ID", "User", "Image Size", "Real Size", "Microscope", "Time")
        self.history_tree = ttk.Treeview(hist_frame, columns=columns, show="headings", height=6)
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=100, anchor="center")
        self.history_tree.pack(fill="both", expand=True, pady=8)

    def _browse_image(self):
        filepath = filedialog.askopenfilename(
            title="Select Specimen Image",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.tiff"), ("All Files", "*.*")]
        )
        if filepath:
            self.uploaded_image_path.set(os.path.basename(filepath))
            self._selected_image_full_path = filepath

    def _perform_calculation(self):
        username = self.username_entry.get().strip()
        if not username:
            messagebox.showwarning("Missing Username", "Please enter your username.")
            return

        if self.uploaded_image_path.get() == "No image selected":
            messagebox.showwarning("No Image", "Please upload a specimen image.")
            return

        raw_size = self.size_entry.get().strip()
        try:
            img_size = float(raw_size)
            if img_size <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Size", "Please enter a valid positive number for the measured size.")
            return

        scope_name = self.scope_var.get()
        output_unit = self.unit_var.get()
        magnification = SCOPE_CATALOGUE[scope_name]
        conversion = UNIT_SHIFT_TABLE[output_unit]

        real_um = img_size / magnification
        final_result = real_um * conversion

        breakdown = (
            f"Image Size: {img_size} µm  |  Scope: {scope_name} ({magnification}x)\n"
            f"Real Size (µm): {img_size} ÷ {magnification} = {real_um:.6f} µm\n"
            f"➜  REAL-LIFE SIZE = {final_result:.6f} {output_unit}"
        )
        self.result_text.set(breakdown)
        save_record(username, img_size, final_result, output_unit, scope_name)
        messagebox.showinfo("Saved", "Calculation recorded to database.")

    def _load_history(self):
        for existing_row in self.history_tree.get_children():
            self.history_tree.delete(existing_row)
        for row in fetch_all():
            rec_id, operator, img_sz, real_val, unit, scope, ts = row
            display_real = f"{real_val:.4f} {unit}"
            self.history_tree.insert("", "end", values=(rec_id, operator, f"{img_sz} µm", display_real, scope, ts))

    def _delete_selected(self):
        selected = self.history_tree.selection()
        if not selected:
            messagebox.showinfo("Nothing Selected", "Please click on a record to select it first.")
            return
        item = self.history_tree.item(selected[0])
        record_id = item["values"][0]
        if messagebox.askyesno("Confirm Delete", f"Delete record ID {record_id}?"):
            removed = delete_by_id(record_id)
            if removed:
                self.history_tree.delete(selected[0])
                messagebox.showinfo("Deleted", "Record removed successfully.")


if __name__ == "__main__":
    app = MicroscopeApp()
    app.mainloop()