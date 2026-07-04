-- CREATE DATABASE IF NOT EXISTS society_management;
-- USE society_management;

-- 1. Roles table
CREATE TABLE IF NOT EXISTS roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    role_id INT NOT NULL,
    status VARCHAR(20) DEFAULT 'Active', -- Active, Inactive, Pending
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Buildings table
CREATE TABLE IF NOT EXISTS buildings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255),
    floors_count INT DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Flats table
CREATE TABLE IF NOT EXISTS flats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    building_id INT NOT NULL,
    flat_number VARCHAR(20) NOT NULL,
    floor_number INT NOT NULL,
    flat_type VARCHAR(50) DEFAULT '2BHK', -- 1BHK, 2BHK, 3BHK, Penthouse, etc.
    occupancy_status VARCHAR(50) DEFAULT 'Vacant', -- Vacant, Owner-Occupied, Tenant-Occupied
    FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE,
    UNIQUE KEY uq_building_flat (building_id, flat_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Residents table
CREATE TABLE IF NOT EXISTS residents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE,
    flat_id INT NULL,
    resident_type VARCHAR(50) NOT NULL DEFAULT 'Tenant', -- Owner, Tenant
    emergency_contact VARCHAR(100),
    move_in_date DATE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (flat_id) REFERENCES flats(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Visitors table
CREATE TABLE IF NOT EXISTS visitors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    purpose VARCHAR(255) NOT NULL,
    flat_id INT NOT NULL,
    check_in_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    check_out_time TIMESTAMP NULL DEFAULT NULL,
    vehicle_number VARCHAR(20),
    status VARCHAR(50) DEFAULT 'Checked-In', -- Checked-In, Checked-Out
    checked_in_by INT, -- user_id of the Security Guard
    FOREIGN KEY (flat_id) REFERENCES flats(id) ON DELETE CASCADE,
    FOREIGN KEY (checked_in_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. Staff table
CREATE TABLE IF NOT EXISTS staff (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE,
    staff_type VARCHAR(50) NOT NULL, -- Security, Maintenance, Admin, Other
    designation VARCHAR(100),
    salary DECIMAL(10, 2),
    joining_date DATE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. Complaints table
CREATE TABLE IF NOT EXISTS complaints (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50) NOT NULL, -- Plumbing, Electrical, Security, Cleaning, Other
    flat_id INT NOT NULL,
    created_by_user_id INT NOT NULL,
    assigned_to_staff_id INT NULL,
    status VARCHAR(50) DEFAULT 'Pending', -- Pending, In Progress, Resolved
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    resolution_notes TEXT,
    FOREIGN KEY (flat_id) REFERENCES flats(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_to_staff_id) REFERENCES staff(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. Maintenance table
CREATE TABLE IF NOT EXISTS maintenance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    flat_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    due_date DATE NOT NULL,
    bill_date DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'Unpaid', -- Unpaid, Paid, Overdue
    FOREIGN KEY (flat_id) REFERENCES flats(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 10. Payments table
CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    maintenance_id INT NOT NULL,
    amount_paid DECIMAL(10, 2) NOT NULL,
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payment_method VARCHAR(50) NOT NULL, -- Card, Cash, UPI, NetBanking
    transaction_id VARCHAR(100) UNIQUE,
    status VARCHAR(50) DEFAULT 'Success', -- Success, Failed, Pending
    FOREIGN KEY (maintenance_id) REFERENCES maintenance(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 11. Notices table
CREATE TABLE IF NOT EXISTS notices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    content TEXT NOT NULL,
    created_by_user_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expiry_date DATE NULL,
    attachment_path VARCHAR(255) NULL,
    FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 12. Events table
CREATE TABLE IF NOT EXISTS events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    event_date DATETIME NOT NULL,
    venue VARCHAR(150) NOT NULL,
    created_by_user_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 13. Vehicles table
CREATE TABLE IF NOT EXISTS vehicles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    flat_id INT NOT NULL,
    vehicle_type VARCHAR(50) NOT NULL, -- 2 Wheeler, 4 Wheeler
    vehicle_number VARCHAR(50) NOT NULL UNIQUE,
    owner_name VARCHAR(100) NOT NULL,
    FOREIGN KEY (flat_id) REFERENCES flats(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
