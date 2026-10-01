#!/bin/bash
# Blood Bank Management System — full setup (Linux, MariaDB/MySQL)
# Run from the folder containing blood_bank_management_system.sql:
#   bash setup.sh
set -e

echo "== 1/5: Installing MariaDB, Tkinter, pip =="
sudo apt update
sudo apt install -y mariadb-server python3-tk python3-pip

echo "== 2/5: Starting MariaDB =="
sudo systemctl start mariadb
sudo systemctl enable mariadb

echo "== 3/5: Creating dedicated DB user 'bloodbank' =="
sudo mysql <<'SQL'
CREATE USER IF NOT EXISTS 'bloodbank'@'localhost' IDENTIFIED BY 'Test1234';
GRANT ALL PRIVILEGES ON blood_bank_management.* TO 'bloodbank'@'localhost';
FLUSH PRIVILEGES;
SQL

echo "== 4/5: Importing schema, sample data, view, trigger, procedure =="
sudo mysql < blood_bank_management_system.sql

echo "== 5/5: Installing Python MySQL driver =="
pip3 install mysql-connector-python

echo ""
echo "Setup complete. Run the app with:"
echo "    python3 blood_bank_app.py"
echo ""
echo "Login screen values:"
echo "    Host:     localhost"
echo "    Port:     3306"
echo "    User:     bloodbank"
echo "    Password: Test1234   (change this — see note below)"
echo "    Database: blood_bank_management"
echo ""
echo "NOTE: Test1234 is a placeholder. To use your own password, edit the"
echo "'IDENTIFIED BY' line above before running this script, or change it"
echo "later with: sudo mysql -e \"ALTER USER 'bloodbank'@'localhost' IDENTIFIED BY 'yournewpassword';\""
