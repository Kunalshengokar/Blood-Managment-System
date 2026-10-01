-- =====================================================================
-- BLOOD BANK MANAGEMENT SYSTEM
-- Mini DBMS Project — Full SQL Script
-- Tested on MySQL 8.0 (works with minor syntax tweaks on other RDBMS)
-- =====================================================================

DROP DATABASE IF EXISTS blood_bank_management;
CREATE DATABASE blood_bank_management;
USE blood_bank_management;

-- =====================================================================
-- SECTION 1: TABLE CREATION (DDL)
-- =====================================================================

-- 1. BLOOD BANK
CREATE TABLE BloodBank (
    bank_id      INT AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(100) NOT NULL,
    address      VARCHAR(200) NOT NULL,
    city         VARCHAR(50)  NOT NULL,
    phone        VARCHAR(15)  NOT NULL,
    license_no   VARCHAR(30)  NOT NULL UNIQUE
);

-- 2. EMPLOYEE
CREATE TABLE Employee (
    employee_id  INT AUTO_INCREMENT PRIMARY KEY,
    bank_id      INT NOT NULL,
    name         VARCHAR(100) NOT NULL,
    role         VARCHAR(50)  NOT NULL,
    phone        VARCHAR(15),
    hire_date    DATE NOT NULL,
    FOREIGN KEY (bank_id) REFERENCES BloodBank(bank_id) ON DELETE CASCADE
);

-- 3. DONOR
CREATE TABLE Donor (
    donor_id            INT AUTO_INCREMENT PRIMARY KEY,
    name                VARCHAR(100) NOT NULL,
    gender              CHAR(1) CHECK (gender IN ('M','F','O')),
    dob                 DATE NOT NULL,
    blood_group         VARCHAR(3) NOT NULL
                         CHECK (blood_group IN ('A+','A-','B+','B-','AB+','AB-','O+','O-')),
    phone               VARCHAR(15) NOT NULL,
    email               VARCHAR(100),
    address             VARCHAR(200),
    last_donation_date  DATE
);

-- 4. DONATION
CREATE TABLE Donation (
    donation_id    INT AUTO_INCREMENT PRIMARY KEY,
    donor_id       INT NOT NULL,
    bank_id        INT NOT NULL,
    employee_id    INT NOT NULL,
    donation_date  DATE NOT NULL,
    quantity_ml    INT NOT NULL CHECK (quantity_ml BETWEEN 200 AND 500),
    blood_group    VARCHAR(3) NOT NULL,
    FOREIGN KEY (donor_id) REFERENCES Donor(donor_id) ON DELETE CASCADE,
    FOREIGN KEY (bank_id) REFERENCES BloodBank(bank_id) ON DELETE CASCADE,
    FOREIGN KEY (employee_id) REFERENCES Employee(employee_id)
);

-- 5. BLOOD INVENTORY
CREATE TABLE BloodInventory (
    inventory_id     INT AUTO_INCREMENT PRIMARY KEY,
    bank_id          INT NOT NULL,
    blood_group      VARCHAR(3) NOT NULL
                      CHECK (blood_group IN ('A+','A-','B+','B-','AB+','AB-','O+','O-')),
    units_available  INT NOT NULL DEFAULT 0 CHECK (units_available >= 0),
    expiry_date      DATE NOT NULL,
    FOREIGN KEY (bank_id) REFERENCES BloodBank(bank_id) ON DELETE CASCADE,
    UNIQUE (bank_id, blood_group, expiry_date)
);

-- 6. HOSPITAL
CREATE TABLE Hospital (
    hospital_id  INT AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(100) NOT NULL,
    address      VARCHAR(200) NOT NULL,
    phone        VARCHAR(15)  NOT NULL
);

-- 7. RECIPIENT
CREATE TABLE Recipient (
    recipient_id  INT AUTO_INCREMENT PRIMARY KEY,
    hospital_id   INT NOT NULL,
    name          VARCHAR(100) NOT NULL,
    gender        CHAR(1) CHECK (gender IN ('M','F','O')),
    blood_group   VARCHAR(3) NOT NULL
                  CHECK (blood_group IN ('A+','A-','B+','B-','AB+','AB-','O+','O-')),
    phone         VARCHAR(15),
    FOREIGN KEY (hospital_id) REFERENCES Hospital(hospital_id) ON DELETE CASCADE
);

-- 8. BLOOD REQUEST
CREATE TABLE BloodRequest (
    request_id       INT AUTO_INCREMENT PRIMARY KEY,
    recipient_id     INT NOT NULL,
    bank_id          INT NOT NULL,
    blood_group      VARCHAR(3) NOT NULL,
    units_requested  INT NOT NULL CHECK (units_requested > 0),
    request_date     DATE NOT NULL,
    status           VARCHAR(20) NOT NULL DEFAULT 'Pending'
                     CHECK (status IN ('Pending','Approved','Fulfilled','Rejected')),
    FOREIGN KEY (recipient_id) REFERENCES Recipient(recipient_id) ON DELETE CASCADE,
    FOREIGN KEY (bank_id) REFERENCES BloodBank(bank_id) ON DELETE CASCADE
);

-- 9. BLOOD CAMP
CREATE TABLE BloodCamp (
    camp_id       INT AUTO_INCREMENT PRIMARY KEY,
    bank_id       INT NOT NULL,
    location      VARCHAR(150) NOT NULL,
    camp_date     DATE NOT NULL,
    organizer     VARCHAR(100),
    target_units  INT,
    FOREIGN KEY (bank_id) REFERENCES BloodBank(bank_id) ON DELETE CASCADE
);

-- =====================================================================
-- SECTION 2: SAMPLE DATA (DML)
-- =====================================================================

INSERT INTO BloodBank (name, address, city, phone, license_no) VALUES
('LifeLine Blood Bank', '12 MG Road', 'Pune', '9822011111', 'LIC-PN-001'),
('RedCross Central Bank', '45 Park Street', 'Kolkata', '9832022222', 'LIC-KO-002'),
('City Hope Blood Bank', '78 Anna Salai', 'Chennai', '9884033333', 'LIC-CH-003');

INSERT INTO Employee (bank_id, name, role, phone, hire_date) VALUES
(1, 'Rajesh Kumar', 'Lab Technician', '9900011111', '2021-03-15'),
(1, 'Sunita Rao', 'Manager', '9900022222', '2019-06-01'),
(2, 'Arindam Sen', 'Lab Technician', '9900033333', '2020-01-10'),
(3, 'Priya Menon', 'Manager', '9900044444', '2018-11-20');

INSERT INTO Donor (name, gender, dob, blood_group, phone, email, address, last_donation_date) VALUES
('Amit Sharma', 'M', '1995-04-12', 'O+', '9811111111', 'amit@example.com', 'Pune', '2026-06-01'),
('Neha Verma', 'F', '1998-09-23', 'A+', '9822222222', 'neha@example.com', 'Pune', '2026-05-15'),
('Ravi Iyer', 'M', '1990-01-05', 'B+', '9833333333', 'ravi@example.com', 'Chennai', '2026-04-20'),
('Sara Khan', 'F', '2000-07-30', 'AB-', '9844444444', 'sara@example.com', 'Kolkata', NULL),
('Vikram Das', 'M', '1985-11-18', 'O-', '9855555555', 'vikram@example.com', 'Kolkata', '2026-07-02'),
('Anjali Nair', 'F', '1993-03-09', 'B-', '9866666666', 'anjali@example.com', 'Chennai', NULL);

INSERT INTO Donation (donor_id, bank_id, employee_id, donation_date, quantity_ml, blood_group) VALUES
(1, 1, 1, '2026-06-01', 450, 'O+'),
(2, 1, 1, '2026-05-15', 400, 'A+'),
(3, 3, 4, '2026-04-20', 450, 'B+'),
(5, 2, 3, '2026-07-02', 400, 'O-'),
(1, 1, 2, '2026-01-05', 450, 'O+');

INSERT INTO BloodInventory (bank_id, blood_group, units_available, expiry_date) VALUES
(1, 'O+', 12, '2026-11-01'),
(1, 'A+', 8,  '2026-10-20'),
(1, 'B+', 3,  '2026-09-25'),
(2, 'O-', 5,  '2026-10-10'),
(2, 'AB-', 2, '2026-09-30'),
(3, 'B+', 10, '2026-11-15'),
(3, 'O+', 6,  '2026-10-05');

INSERT INTO Hospital (name, address, phone) VALUES
('Apollo Hospital', '10 Bund Garden Road, Pune', '02066011111'),
('AMRI Hospital', '5 JC Bose Road, Kolkata', '03340022222'),
('Global Health Hospital', '22 GST Road, Chennai', '04430033333');

INSERT INTO Recipient (hospital_id, name, gender, blood_group, phone) VALUES
(1, 'Manoj Tiwari', 'M', 'O+', '9700011111'),
(2, 'Fatima Sheikh', 'F', 'AB-', '9700022222'),
(3, 'Karthik Subramaniam', 'M', 'B+', '9700033333');

INSERT INTO BloodRequest (recipient_id, bank_id, blood_group, units_requested, request_date, status) VALUES
(1, 1, 'O+', 2, '2026-09-01', 'Fulfilled'),
(2, 2, 'AB-', 1, '2026-09-05', 'Pending'),
(3, 3, 'B+', 4, '2026-09-10', 'Approved');

INSERT INTO BloodCamp (bank_id, location, camp_date, organizer, target_units) VALUES
(1, 'Pune Community Hall', '2026-08-15', 'Lions Club Pune', 100),
(2, 'Kolkata Town Square', '2026-08-20', 'Rotary Club Kolkata', 150),
(3, 'Chennai Tech Park', '2026-09-05', 'IT Employees Association', 80);

-- =====================================================================
-- SECTION 3: CORE QUERIES
-- =====================================================================

-- 3.1 List all donors of a given blood group, eligible to donate again
--     (last donation more than 90 days ago, or never donated)
SELECT donor_id, name, phone, blood_group, last_donation_date
FROM Donor
WHERE blood_group = 'O+'
  AND (last_donation_date IS NULL OR last_donation_date <= CURDATE() - INTERVAL 90 DAY);

-- 3.2 Total units available per blood group, across all banks
SELECT blood_group, SUM(units_available) AS total_units
FROM BloodInventory
GROUP BY blood_group
ORDER BY total_units DESC;

-- 3.3 Blood banks running low (< 5 units) on any blood group — shortage alert
SELECT bb.name AS bank_name, bi.blood_group, bi.units_available
FROM BloodInventory bi
JOIN BloodBank bb ON bb.bank_id = bi.bank_id
WHERE bi.units_available < 5
ORDER BY bi.units_available ASC;

-- 3.4 Units expiring within the next 30 days (wastage prevention)
SELECT bb.name AS bank_name, bi.blood_group, bi.units_available, bi.expiry_date
FROM BloodInventory bi
JOIN BloodBank bb ON bb.bank_id = bi.bank_id
WHERE bi.expiry_date <= CURDATE() + INTERVAL 30 DAY
ORDER BY bi.expiry_date;

-- 3.5 Pending / approved blood requests with recipient and hospital details
SELECT br.request_id, r.name AS recipient_name, h.name AS hospital_name,
       br.blood_group, br.units_requested, br.status, br.request_date
FROM BloodRequest br
JOIN Recipient r ON r.recipient_id = br.recipient_id
JOIN Hospital h ON h.hospital_id = r.hospital_id
WHERE br.status IN ('Pending','Approved')
ORDER BY br.request_date;

-- 3.6 Donation history of a specific donor
SELECT d.donation_date, d.quantity_ml, bb.name AS bank_name, e.name AS collected_by
FROM Donation d
JOIN BloodBank bb ON bb.bank_id = d.bank_id
JOIN Employee e ON e.employee_id = d.employee_id
WHERE d.donor_id = 1
ORDER BY d.donation_date DESC;

-- 3.7 Top donors by number of donations (leaderboard)
SELECT dn.donor_id, dn.name, COUNT(*) AS total_donations, SUM(dn2.quantity_ml) AS total_ml
FROM Donor dn
JOIN Donation dn2 ON dn2.donor_id = dn.donor_id
GROUP BY dn.donor_id, dn.name
ORDER BY total_donations DESC, total_ml DESC;

-- 3.8 Blood banks and the number of camps they have organized
SELECT bb.name, COUNT(bc.camp_id) AS camps_organized, SUM(bc.target_units) AS total_target_units
FROM BloodBank bb
LEFT JOIN BloodCamp bc ON bc.bank_id = bb.bank_id
GROUP BY bb.bank_id, bb.name;

-- =====================================================================
-- SECTION 4: VIEW
-- =====================================================================

-- A consolidated, read-only summary of stock across every bank
CREATE OR REPLACE VIEW vw_stock_summary AS
SELECT bb.bank_id, bb.name AS bank_name, bi.blood_group,
       bi.units_available, bi.expiry_date,
       CASE
           WHEN bi.units_available < 5 THEN 'LOW'
           WHEN bi.expiry_date <= CURDATE() + INTERVAL 15 DAY THEN 'EXPIRING SOON'
           ELSE 'OK'
       END AS stock_flag
FROM BloodInventory bi
JOIN BloodBank bb ON bb.bank_id = bi.bank_id;

-- Usage: SELECT * FROM vw_stock_summary WHERE stock_flag <> 'OK';

-- =====================================================================
-- SECTION 5: TRIGGER
-- =====================================================================

-- Automatically add donated blood into inventory the moment a donation
-- is recorded (adds a fresh inventory row valid for 42 days, the
-- standard shelf life of whole blood).
DELIMITER $$

CREATE TRIGGER trg_after_donation_insert
AFTER INSERT ON Donation
FOR EACH ROW
BEGIN
    INSERT INTO BloodInventory (bank_id, blood_group, units_available, expiry_date)
    VALUES (NEW.bank_id, NEW.blood_group, 1, DATE_ADD(NEW.donation_date, INTERVAL 42 DAY))
    ON DUPLICATE KEY UPDATE units_available = units_available + 1;
END$$

DELIMITER ;

-- =====================================================================
-- SECTION 6: STORED PROCEDURE
-- =====================================================================

-- Fulfils a blood request: checks stock, deducts units, and updates
-- the request status in one atomic transaction.
DELIMITER $$

CREATE PROCEDURE sp_fulfill_request(IN p_request_id INT)
BEGIN
    DECLARE v_bank_id INT;
    DECLARE v_group VARCHAR(3);
    DECLARE v_units INT;
    DECLARE v_available INT DEFAULT 0;

    SELECT bank_id, blood_group, units_requested
    INTO v_bank_id, v_group, v_units
    FROM BloodRequest
    WHERE request_id = p_request_id;

    SELECT COALESCE(SUM(units_available), 0) INTO v_available
    FROM BloodInventory
    WHERE bank_id = v_bank_id AND blood_group = v_group;

    IF v_available >= v_units THEN
        UPDATE BloodInventory
        SET units_available = units_available - v_units
        WHERE bank_id = v_bank_id AND blood_group = v_group
        ORDER BY expiry_date ASC
        LIMIT 1;

        UPDATE BloodRequest
        SET status = 'Fulfilled'
        WHERE request_id = p_request_id;

        SELECT 'Request fulfilled successfully' AS message;
    ELSE
        UPDATE BloodRequest SET status = 'Pending' WHERE request_id = p_request_id;
        SELECT 'Insufficient stock — request kept pending' AS message;
    END IF;
END$$

DELIMITER ;

-- Usage: CALL sp_fulfill_request(2);

-- =====================================================================
-- END OF SCRIPT
-- =====================================================================
