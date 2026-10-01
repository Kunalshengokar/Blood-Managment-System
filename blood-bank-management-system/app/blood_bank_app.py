"""
Blood Bank Management System — Desktop Front End
==================================================
Tkinter GUI for the MySQL schema in blood_bank_management_system.sql.

Setup:
    pip install mysql-connector-python
Run:
    python blood_bank_app.py
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

import mysql.connector
from mysql.connector import Error

BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
GENDERS = ["M", "F", "O"]


# =====================================================================
# DATABASE LAYER
# =====================================================================
class DB:
    """Thin wrapper around a single mysql-connector connection."""

    def __init__(self):
        self.conn = None

    def connect(self, **kwargs):
        self.conn = mysql.connector.connect(**kwargs)

    def query(self, sql, params=None):
        cur = self.conn.cursor()
        cur.execute(sql, params or ())
        rows = cur.fetchall()
        cur.close()
        return rows

    def execute(self, sql, params=None):
        cur = self.conn.cursor()
        cur.execute(sql, params or ())
        self.conn.commit()
        cur.close()

    def call_proc(self, name, args):
        cur = self.conn.cursor()
        cur.callproc(name, args)
        results = [r.fetchall() for r in cur.stored_results()]
        self.conn.commit()
        cur.close()
        return results


db = DB()


# =====================================================================
# SMALL UI HELPERS (shared by every tab — this is what keeps tabs short)
# =====================================================================
def make_tree(parent, columns, widths):
    """Create a scrollable Treeview list."""
    tree = ttk.Treeview(parent, columns=columns, show="headings", height=12)
    for col, width in zip(columns, widths):
        tree.heading(col, text=col)
        tree.column(col, width=width, anchor="w")
    scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    tree.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")
    parent.grid_rowconfigure(0, weight=1)
    parent.grid_columnconfigure(0, weight=1)
    return tree


def fill_tree(tree, rows):
    tree.delete(*tree.get_children())
    for row in rows:
        tree.insert("", "end", values=row)


def labeled_field(parent, label, row, values=None, width=22):
    """Place a label + entry/combobox pair; return (StringVar, widget)."""
    ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=4, pady=3)
    var = tk.StringVar()
    if values is not None:
        widget = ttk.Combobox(parent, textvariable=var, values=values, width=width - 2, state="readonly")
    else:
        widget = ttk.Entry(parent, textvariable=var, width=width)
    widget.grid(row=row, column=1, sticky="w", padx=4, pady=3)
    return var, widget


def build_form(parent, fields, start_row=0):
    """fields: list of (name, label, kwargs-for-labeled_field). Returns {name: var}."""
    return {name: labeled_field(parent, label, row, **kwargs)[0]
            for row, (name, label, kwargs) in enumerate(fields, start=start_row)}


def combo_id(text):
    """Comboboxes show 'id - label'; extract the leading id."""
    return int(text.split(" - ")[0]) if text else None


def lookup(query, label_cols=(1,)):
    """Run a lookup query, return ['id - label', ...] strings for a combobox."""
    return [f"{r[0]} - {' '.join(str(r[c]) for c in label_cols)}" for r in db.query(query)]


def save_record(sql, params, success_msg, refresh):
    """Shared insert/commit/refresh/error-report pattern used by every form."""
    try:
        db.execute(sql, params)
        messagebox.showinfo("Saved", success_msg)
        refresh()
    except (Error, ValueError) as e:
        messagebox.showerror("Save failed", str(e))


# =====================================================================
# LOGIN WINDOW
# =====================================================================
class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Connect to Blood Bank Database")
        self.geometry("380x260")
        self.resizable(False, False)

        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="MySQL Connection", font=("Segoe UI", 13, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(0, 12)
        )

        self.fields = build_form(frame, [
            ("host", "Host:", {}),
            ("port", "Port:", {}),
            ("user", "User:", {}),
            ("password", "Password:", {}),
            ("database", "Database:", {}),
        ], start_row=1)
        self.fields["host"].set("localhost")
        self.fields["port"].set("3306")
        self.fields["user"].set("root")
        self.fields["database"].set("blood_bank_management")
        for w in frame.grid_slaves(row=4, column=1):
            w.configure(show="*")  # mask password

        ttk.Button(frame, text="Connect", command=self.try_connect).grid(row=6, column=0, columnspan=2, pady=16)
        self.status = ttk.Label(frame, text="", foreground="red")
        self.status.grid(row=7, column=0, columnspan=2)

    def try_connect(self):
        try:
            db.connect(
                host=self.fields["host"].get().strip(),
                port=int(self.fields["port"].get().strip() or 3306),
                user=self.fields["user"].get().strip(),
                password=self.fields["password"].get(),
                database=self.fields["database"].get().strip(),
            )
            self.destroy()
            MainApp().mainloop()
        except Error as e:
            self.status.config(text=f"Connection failed: {e}")
        except ValueError:
            self.status.config(text="Port must be a number")


# =====================================================================
# MAIN APPLICATION
# =====================================================================
class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Blood Bank Management System")
        self.geometry("1150x650")
        self.minsize(1100, 600)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)
        self.refreshers = {}  # tab frame -> callable that reloads its data

        for title, builder in [
            ("Dashboard", self.build_dashboard_tab),
            ("Donors", self.build_donor_tab),
            ("Blood Banks", self.build_bank_tab),
            ("Donations", self.build_donation_tab),
            ("Hospitals & Recipients", self.build_hospital_tab),
            ("Blood Requests", self.build_request_tab),
        ]:
            tab = ttk.Frame(self.notebook)
            self.notebook.add(tab, text=title)
            builder(tab)

        self.notebook.bind("<<NotebookTabChanged>>", lambda e: self.refresh_current_tab())
        self.refresh_current_tab()

    def refresh_current_tab(self):
        """Reload whichever tab is now visible — keeps every list and every
        FK dropdown current without needing manual 'load list' buttons."""
        tab = self.nametowidget(self.notebook.select())
        refresh = self.refreshers.get(tab)
        if refresh:
            refresh()

    # -----------------------------------------------------------
    # DASHBOARD
    # -----------------------------------------------------------
    def build_dashboard_tab(self, tab):
        bar = ttk.Frame(tab)
        bar.pack(fill="x", padx=8, pady=8)
        ttk.Label(bar, text="Stock Summary (all banks)", font=("Segoe UI", 12, "bold")).pack(side="left")

        tree_frame = ttk.Frame(tab)
        tree_frame.pack(fill="both", expand=True, padx=8, pady=4)
        cols = ("bank_name", "blood_group", "units_available", "expiry_date", "stock_flag")
        tree = make_tree(tree_frame, cols, [220, 90, 110, 110, 130])
        tree.tag_configure("LOW", background="#FBE1E1")
        tree.tag_configure("EXPIRING SOON", background="#FFF2CC")

        def refresh():
            rows = db.query(
                "SELECT bank_name, blood_group, units_available, expiry_date, stock_flag "
                "FROM vw_stock_summary ORDER BY stock_flag DESC, units_available ASC"
            )
            tree.delete(*tree.get_children())
            for row in rows:
                tree.insert("", "end", values=row, tags=(row[4] if row[4] != "OK" else "",))

        ttk.Button(bar, text="Refresh", command=refresh).pack(side="right")
        self.refreshers[tab] = refresh

    # -----------------------------------------------------------
    # DONORS
    # -----------------------------------------------------------
    def build_donor_tab(self, tab):
        left = ttk.Frame(tab)
        left.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        right = ttk.LabelFrame(tab, text="Add Donor")
        right.pack(side="right", fill="y", padx=8, pady=8)

        bar = ttk.Frame(left)
        bar.pack(fill="x")
        ttk.Label(bar, text="Blood group:").pack(side="left")
        group_filter = ttk.Combobox(bar, values=["All"] + BLOOD_GROUPS, state="readonly", width=8)
        group_filter.set("All")
        group_filter.pack(side="left", padx=6)

        tree_frame = ttk.Frame(left)
        tree_frame.pack(fill="both", expand=True, pady=6)
        cols = ("id", "name", "gender", "dob", "blood_group", "phone", "email", "last_donation")
        tree = make_tree(tree_frame, cols, [40, 130, 55, 90, 80, 100, 140, 100])

        def refresh(eligible_only=False):
            clauses, params = [], []
            if group_filter.get() not in ("", "All"):
                clauses.append("blood_group=%s")
                params.append(group_filter.get())
            if eligible_only:
                clauses.append("(last_donation_date IS NULL OR last_donation_date <= CURDATE() - INTERVAL 90 DAY)")
            where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
            fill_tree(tree, db.query(
                "SELECT donor_id, name, gender, dob, blood_group, phone, email, last_donation_date "
                f"FROM Donor{where} ORDER BY name", params
            ))

        ttk.Button(bar, text="Apply", command=lambda: refresh()).pack(side="left")
        ttk.Button(bar, text="Eligible only (90+ days)", command=lambda: refresh(True)).pack(side="left", padx=6)

        donor_fields = [
            ("name", "Name:", {}),
            ("gender", "Gender:", {"values": GENDERS}),
            ("dob", "DOB (YYYY-MM-DD):", {}),
            ("blood_group", "Blood group:", {"values": BLOOD_GROUPS}),
            ("phone", "Phone:", {}),
            ("email", "Email:", {}),
            ("address", "Address:", {}),
        ]
        vars_ = build_form(right, donor_fields)

        def save():
            save_record(
                "INSERT INTO Donor (name, gender, dob, blood_group, phone, email, address) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                tuple(vars_[name].get() for name, _, _ in donor_fields),
                "Donor added.", refresh,
            )

        ttk.Button(right, text="Save Donor", command=save).grid(row=len(donor_fields), column=0, columnspan=2, pady=10)
        self.refreshers[tab] = refresh

    # -----------------------------------------------------------
    # BLOOD BANKS  (simple list + form — same shape as Hospitals below)
    # -----------------------------------------------------------
    def build_bank_tab(self, tab):
        self._simple_list_form_tab(
            tab,
            tree_cols=("id", "name", "address", "city", "phone", "license_no"),
            tree_widths=[40, 160, 200, 100, 110, 120],
            list_sql="SELECT bank_id, name, address, city, phone, license_no FROM BloodBank ORDER BY name",
            fields=[
                ("name", "Name:", {}), ("address", "Address:", {}), ("city", "City:", {}),
                ("phone", "Phone:", {}), ("license_no", "License No:", {}),
            ],
            insert_sql="INSERT INTO BloodBank (name, address, city, phone, license_no) VALUES (%s,%s,%s,%s,%s)",
            form_title="Add Blood Bank", success_msg="Blood bank added.",
        )

    def _simple_list_form_tab(self, tab, tree_cols, tree_widths, list_sql, fields, insert_sql, form_title, success_msg):
        """Reusable 'list on the left, add-form on the right' tab (used by Banks & Hospitals)."""
        left = ttk.Frame(tab)
        left.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        right = ttk.LabelFrame(tab, text=form_title)
        right.pack(side="right", fill="y", padx=8, pady=8)

        tree_frame = ttk.Frame(left)
        tree_frame.pack(fill="both", expand=True)
        tree = make_tree(tree_frame, tree_cols, tree_widths)
        vars_ = build_form(right, fields)

        def refresh():
            fill_tree(tree, db.query(list_sql))

        def save():
            save_record(insert_sql, tuple(vars_[name].get() for name, _, _ in fields), success_msg, refresh)

        ttk.Button(right, text="Save", command=save).grid(row=len(fields), column=0, columnspan=2, pady=10)
        self.refreshers[tab] = refresh
        return tree

    # -----------------------------------------------------------
    # DONATIONS  (inserting here fires the DB trigger that updates stock)
    # -----------------------------------------------------------
    def build_donation_tab(self, tab):
        left = ttk.Frame(tab)
        left.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        right = ttk.LabelFrame(tab, text="Record Donation")
        right.pack(side="right", fill="y", padx=8, pady=8)

        tree_frame = ttk.Frame(left)
        tree_frame.pack(fill="both", expand=True)
        cols = ("id", "donor", "bank", "employee", "date", "quantity_ml", "blood_group")
        tree = make_tree(tree_frame, cols, [40, 140, 140, 140, 90, 90, 90])

        donor_var, donor_cb = labeled_field(right, "Donor:", 0, values=[], width=28)
        bank_var, bank_cb = labeled_field(right, "Bank:", 1, values=[], width=28)
        emp_var, emp_cb = labeled_field(right, "Employee:", 2, values=[], width=28)
        date_var, _ = labeled_field(right, "Date (YYYY-MM-DD):", 3)
        date_var.set(str(date.today()))
        qty_var, _ = labeled_field(right, "Quantity (ml):", 4)
        qty_var.set("450")
        group_var, _ = labeled_field(right, "Blood group:", 5, values=BLOOD_GROUPS)

        def refresh():
            fill_tree(tree, db.query(
                "SELECT d.donation_id, dn.name, bb.name, e.name, d.donation_date, d.quantity_ml, d.blood_group "
                "FROM Donation d "
                "JOIN Donor dn ON dn.donor_id = d.donor_id "
                "JOIN BloodBank bb ON bb.bank_id = d.bank_id "
                "JOIN Employee e ON e.employee_id = d.employee_id "
                "ORDER BY d.donation_date DESC"
            ))
            donor_cb["values"] = lookup("SELECT donor_id, name FROM Donor ORDER BY name")
            bank_cb["values"] = lookup("SELECT bank_id, name FROM BloodBank ORDER BY name")
            emp_cb["values"] = lookup("SELECT employee_id, name FROM Employee ORDER BY name")

        def save():
            donor_id, bank_id, employee_id = combo_id(donor_var.get()), combo_id(bank_var.get()), combo_id(emp_var.get())
            if not all([donor_id, bank_id, employee_id]):
                messagebox.showwarning("Missing info", "Pick a donor, bank, and employee from the dropdowns.")
                return
            save_record(
                "INSERT INTO Donation (donor_id, bank_id, employee_id, donation_date, quantity_ml, blood_group) "
                "VALUES (%s,%s,%s,%s,%s,%s)",
                (donor_id, bank_id, employee_id, date_var.get(), int(qty_var.get()), group_var.get()),
                "Donation recorded — inventory updated automatically by the DB trigger.", refresh,
            )

        ttk.Button(right, text="Save Donation", command=save).grid(row=6, column=0, columnspan=2, pady=10)
        self.refreshers[tab] = refresh

    # -----------------------------------------------------------
    # HOSPITALS & RECIPIENTS
    # -----------------------------------------------------------
    def build_hospital_tab(self, tab):
        hosp_frame = ttk.LabelFrame(tab, text="Hospitals")
        hosp_frame.pack(fill="both", expand=True, padx=8, pady=(8, 4))
        hosp_tree_frame = ttk.Frame(hosp_frame)
        hosp_tree_frame.pack(side="left", fill="both", expand=True, padx=6, pady=6)
        hosp_tree = make_tree(hosp_tree_frame, ("id", "name", "address", "phone"), [40, 200, 260, 110])
        hosp_form = ttk.Frame(hosp_frame)
        hosp_form.pack(side="right", fill="y", padx=6, pady=6)
        hosp_vars = build_form(hosp_form, [("name", "Name:", {}), ("address", "Address:", {}), ("phone", "Phone:", {})])

        rec_frame = ttk.LabelFrame(tab, text="Recipients")
        rec_frame.pack(fill="both", expand=True, padx=8, pady=(4, 8))
        rec_tree_frame = ttk.Frame(rec_frame)
        rec_tree_frame.pack(side="left", fill="both", expand=True, padx=6, pady=6)
        rec_tree = make_tree(rec_tree_frame, ("id", "name", "hospital", "gender", "blood_group", "phone"), [40, 140, 160, 55, 80, 100])
        rec_form = ttk.Frame(rec_frame)
        rec_form.pack(side="right", fill="y", padx=6, pady=6)
        hospital_var, hospital_cb = labeled_field(rec_form, "Hospital:", 0, values=[], width=28)
        rec_vars = {"hospital": hospital_var}
        rec_vars["name"], _ = labeled_field(rec_form, "Name:", 1)
        rec_vars["gender"], _ = labeled_field(rec_form, "Gender:", 2, values=GENDERS)
        rec_vars["blood_group"], _ = labeled_field(rec_form, "Blood group:", 3, values=BLOOD_GROUPS)
        rec_vars["phone"], _ = labeled_field(rec_form, "Phone:", 4)

        def refresh():
            fill_tree(hosp_tree, db.query("SELECT hospital_id, name, address, phone FROM Hospital ORDER BY name"))
            fill_tree(rec_tree, db.query(
                "SELECT r.recipient_id, r.name, h.name, r.gender, r.blood_group, r.phone "
                "FROM Recipient r JOIN Hospital h ON h.hospital_id = r.hospital_id ORDER BY r.name"
            ))
            hospital_cb["values"] = lookup("SELECT hospital_id, name FROM Hospital ORDER BY name")

        def save_hospital():
            save_record(
                "INSERT INTO Hospital (name, address, phone) VALUES (%s,%s,%s)",
                (hosp_vars["name"].get(), hosp_vars["address"].get(), hosp_vars["phone"].get()),
                "Hospital added.", refresh,
            )

        def save_recipient():
            hospital_id = combo_id(rec_vars["hospital"].get())
            if hospital_id is None:
                messagebox.showwarning("Missing info", "Pick a hospital from the dropdown.")
                return
            save_record(
                "INSERT INTO Recipient (hospital_id, name, gender, blood_group, phone) VALUES (%s,%s,%s,%s,%s)",
                (hospital_id, rec_vars["name"].get(), rec_vars["gender"].get(),
                 rec_vars["blood_group"].get(), rec_vars["phone"].get()),
                "Recipient added.", refresh,
            )

        ttk.Button(hosp_form, text="Save Hospital", command=save_hospital).grid(row=3, column=0, columnspan=2, pady=8)
        ttk.Button(rec_form, text="Save Recipient", command=save_recipient).grid(row=5, column=0, columnspan=2, pady=8)
        self.refreshers[tab] = refresh

    # -----------------------------------------------------------
    # BLOOD REQUESTS
    # -----------------------------------------------------------
    def build_request_tab(self, tab):
        left = ttk.Frame(tab)
        left.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        right = ttk.LabelFrame(tab, text="New Request")
        right.pack(side="right", fill="y", padx=8, pady=8)

        bar = ttk.Frame(left)
        bar.pack(fill="x")
        tree_frame = ttk.Frame(left)
        tree_frame.pack(fill="both", expand=True, pady=6)
        cols = ("id", "recipient", "hospital", "bank", "blood_group", "units", "date", "status")
        tree = make_tree(tree_frame, cols, [40, 130, 150, 130, 90, 60, 90, 90])

        def refresh():
            fill_tree(tree, db.query(
                "SELECT br.request_id, r.name, h.name, bb.name, br.blood_group, br.units_requested, "
                "br.request_date, br.status "
                "FROM BloodRequest br "
                "JOIN Recipient r ON r.recipient_id = br.recipient_id "
                "JOIN Hospital h ON h.hospital_id = r.hospital_id "
                "JOIN BloodBank bb ON bb.bank_id = br.bank_id "
                "ORDER BY br.request_date DESC"
            ))

        def fulfill_selected():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("No selection", "Select a request row first.")
                return
            request_id = tree.item(selected[0])["values"][0]
            try:
                result = db.call_proc("sp_fulfill_request", [request_id])
                messagebox.showinfo("Result", result[0][0][0] if result and result[0] else "Procedure executed.")
                refresh()
            except Error as e:
                messagebox.showerror("Procedure failed", str(e))

        ttk.Button(bar, text="Refresh", command=refresh).pack(side="left")
        ttk.Button(bar, text="Fulfill Selected", command=fulfill_selected).pack(side="left", padx=6)

        request_fields = [
            ("recipient_id", "Recipient id:", {}),
            ("bank_id", "Bank id:", {}),
            ("blood_group", "Blood group:", {"values": BLOOD_GROUPS}),
            ("units_requested", "Units requested:", {}),
            ("request_date", "Date (YYYY-MM-DD):", {}),
        ]
        vars_ = build_form(right, request_fields)
        vars_["request_date"].set(str(date.today()))
        ttk.Label(right, text="(See Donors/Banks tabs for ids)", foreground="gray").grid(
            row=len(request_fields), column=0, columnspan=2, sticky="w", padx=4
        )

        def save():
            save_record(
                "INSERT INTO BloodRequest (recipient_id, bank_id, blood_group, units_requested, request_date) "
                "VALUES (%s,%s,%s,%s,%s)",
                (
                    int(vars_["recipient_id"].get()), int(vars_["bank_id"].get()), vars_["blood_group"].get(),
                    int(vars_["units_requested"].get()), vars_["request_date"].get(),
                ),
                "Request created (status: Pending).", refresh,
            )

        ttk.Button(right, text="Save Request", command=save).grid(row=len(request_fields) + 1, column=0, columnspan=2, pady=10)
        self.refreshers[tab] = refresh


if __name__ == "__main__":
    LoginWindow().mainloop()
