-- SQLite Schema for Patient Document Management System
-- This file is for reference only - tables are created automatically by SQLAlchemy

-- Create the patients table
CREATE TABLE IF NOT EXISTS patients (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    date_of_birth TEXT NOT NULL,
    diagnosis TEXT,
    prescription TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_patients_name ON patients(name);
CREATE INDEX IF NOT EXISTS idx_patients_dob ON patients(date_of_birth);
CREATE INDEX IF NOT EXISTS idx_patients_created_at ON patients(created_at DESC);

-- Example queries:

-- Insert a patient
-- INSERT INTO patients (id, name, date_of_birth, diagnosis, prescription) 
-- VALUES ('uuid-here', 'John Doe', '1990-01-15', 'Hypertension', 'Lisinopril 10mg daily');

-- Get all patients
-- SELECT * FROM patients ORDER BY created_at DESC;

-- Get patients by name (partial match)
-- SELECT * FROM patients WHERE name LIKE '%John%';

-- Get patients by age range (approximate)
-- SELECT * FROM patients WHERE date_of_birth BETWEEN '1980-01-01' AND '2000-12-31';
