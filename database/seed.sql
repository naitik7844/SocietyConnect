-- Seed data for roles
INSERT INTO roles (id, name, description) VALUES
(1, 'Admin', 'Overall administrator with full system privileges'),
(2, 'Owner', 'Society flat owner'),
(3, 'Resident', 'Resident of a flat (could be owner or tenant)'),
(4, 'Security', 'Security guard for visitor log tracking'),
(5, 'Staff', 'Authorized society maintenance and operations staff')
ON DUPLICATE KEY UPDATE name=VALUES(name), description=VALUES(description);
