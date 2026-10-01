# Blood Bank Management System

A mini DBMS project: a relational database for blood bank operations (donors,
inventory, hospitals, recipients, requests, donation camps), paired with a
Python/Tkinter desktop front end.

## Features

- Donor registration and 90-day donation-eligibility checks
- Live blood inventory with low-stock / expiring-soon alerts (`vw_stock_summary` view)
- Recording a donation automatically restocks inventory via a database **trigger**
- Fulfilling a request safely deducts stock via a **stored procedure**
  (`sp_fulfill_request`) — stock can never go negative
- Hospitals, recipients, and blood requests with status tracking
- Desktop GUI (Tkinter) with auto-refreshing tabs for every entity

## Tech Stack

| Layer          | Technology                        |
|----------------|------------------------------------|
| Database       | MySQL 8.x / MariaDB 10.x           |
| Backend        | Python 3                           |
| GUI            | Tkinter (ttk)                      |
| DB Connector   | mysql-connector-python             |
| ER Diagram     | Graphviz                           |

## Project Structure

```
blood-bank-management-system/
├── app/
│   └── blood_bank_app.py        # Tkinter desktop application
├── database/
│   └── blood_bank_management_system.sql   # schema, sample data, view, trigger, procedure
├── docs/
│   └── Blood_Bank_Management_System_Report.docx   # full project report
├── requirements.txt
├── setup.sh                     # one-shot setup script (Linux)
└── README.md
```

## Setup

### Option 1 — automated (Linux)

```bash
bash setup.sh
```

This installs MariaDB, Tkinter, and pip dependencies; creates a dedicated
database user; imports the schema; and prints the login details to use in
the app.

### Option 2 — manual

1. Create the database:
   ```bash
   mysql -u root -p < database/blood_bank_management_system.sql
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   python app/blood_bank_app.py
   ```
4. On the login screen, enter your MySQL host, port, user, password, and
   `blood_bank_management` as the database name.

## Database Design

- 9 tables normalized to **3NF**: `BloodBank`, `Employee`, `Donor`, `Donation`,
  `BloodInventory`, `Hospital`, `Recipient`, `BloodRequest`, `BloodCamp`
- A **view** (`vw_stock_summary`) flags stock as `OK`, `LOW`, or `EXPIRING SOON`
- A **trigger** (`trg_after_donation_insert`) updates inventory on every new donation
- A **stored procedure** (`sp_fulfill_request`) safely fulfills a blood request

Full schema, ER diagram, and normalization notes are in
[`docs/Blood_Bank_Management_System_Report.docx`](docs/Blood_Bank_Management_System_Report.docx).

## License

MIT — see [LICENSE](LICENSE).
