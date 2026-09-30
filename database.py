"""
Database initialization and access layer for Smart Healthcare Appointment System
SQLite database with full transactional support
"""

import os
import shutil
import sqlite3
import datetime
import json

IS_VERCEL = bool(os.environ.get("VERCEL"))
if IS_VERCEL:
    DB_PATH = os.path.join("/tmp", "healthcare.db")
else:
    DB_PATH = os.path.join(os.path.dirname(__file__), "healthcare.db")

def get_db():
    if IS_VERCEL and not os.path.exists(DB_PATH):
        bundled_db = os.path.join(os.path.dirname(__file__), "healthcare.db")
        if os.path.exists(bundled_db):
            shutil.copyfile(bundled_db, DB_PATH)
        else:
            init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Doctors table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS doctors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        specialization TEXT NOT NULL,
        department TEXT NOT NULL,
        room_no TEXT NOT NULL,
        avg_consultation_time INTEGER DEFAULT 15,
        experience_years INTEGER DEFAULT 10,
        is_available BOOLEAN DEFAULT 1,
        photo_url TEXT,
        rating REAL DEFAULT 4.8,
        contact_phone TEXT
    );
    """)

    # Patients / Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        phone TEXT,
        age INTEGER,
        gender TEXT,
        blood_group TEXT,
        medical_notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Appointments & Queue table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        doctor_id INTEGER NOT NULL,
        appointment_date TEXT NOT NULL,
        appointment_time TEXT NOT NULL,
        reason TEXT NOT NULL,
        priority TEXT DEFAULT 'Routine', -- 'Routine', 'Priority', 'Emergency'
        status TEXT DEFAULT 'WAITING',  -- 'WAITING', 'IN_CONSULTATION', 'COMPLETED', 'CANCELLED', 'DELAYED'
        queue_number INTEGER DEFAULT 1,
        predicted_wait_mins REAL DEFAULT 15.0,
        actual_wait_mins REAL DEFAULT NULL,
        delay_reason TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(id),
        FOREIGN KEY (doctor_id) REFERENCES doctors(id)
    );
    """)

    # Notifications table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        doctor_id INTEGER,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        channel TEXT DEFAULT 'IN_APP', -- 'IN_APP', 'SMS', 'EMAIL'
        is_read BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Check if doctors are already seeded
    cursor.execute("SELECT COUNT(*) as count FROM doctors")
    if cursor.fetchone()["count"] == 0:
        seed_data(cursor)

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

def seed_data(cursor):
    # Seed top doctors
    doctors = [
        ("Dr. Sarah Chen, MD", "Cardiologist", "Cardiology", "Room 301", 20, 14, 1, "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=150&auto=format&fit=crop&q=80", 4.9, "+1 (555) 234-5678"),
        ("Dr. Marcus Vance, MD", "Neurologist", "Neurology", "Room 412", 25, 18, 1, "https://images.unsplash.com/photo-1622253692010-333f2da6031d?w=150&auto=format&fit=crop&q=80", 4.8, "+1 (555) 345-6789"),
        ("Dr. Elena Rostova, MD", "Pediatric Specialist", "Pediatrics", "Room 105", 15, 11, 1, "https://images.unsplash.com/photo-1594824813575-f5b248a0429f?w=150&auto=format&fit=crop&q=80", 4.9, "+1 (555) 456-7890"),
        ("Dr. James Wilson, MD", "Orthopedic Surgeon", "Orthopedics", "Room 210", 20, 16, 1, "https://images.unsplash.com/photo-1537368910025-700350fe46c7?w=150&auto=format&fit=crop&q=80", 4.7, "+1 (555) 567-8901"),
        ("Dr. Priya Sharma, MBBS", "Consultant Physician", "General Medicine", "Room 102", 15, 9, 1, "https://images.unsplash.com/photo-1651008376811-b90baee60c1f?w=150&auto=format&fit=crop&q=80", 4.8, "+1 (555) 678-9012"),
        ("Dr. Robert Sterling, MD", "Dermatology Specialist", "Dermatology", "Room 205", 15, 12, 1, "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=150&auto=format&fit=crop&q=80", 4.8, "+1 (555) 789-0123")
    ]
    cursor.executemany("""
    INSERT INTO doctors (name, specialization, department, room_no, avg_consultation_time, experience_years, is_available, photo_url, rating, contact_phone)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, doctors)

    # Seed Patients
    patients = [
        ("Johnathan Davis", "john.davis@example.com", "+1 555-0101", 42, "Male", "O+", "Mild hypertension, penicillin allergy"),
        ("Sophia Patel", "sophia.patel@example.com", "+1 555-0102", 29, "Female", "A+", "Asthma history"),
        ("Arthur Morgan", "arthur.m@example.com", "+1 555-0103", 56, "Male", "B+", "Chronic lower back stiffness"),
        ("Chloe Zhang", "chloe.z@example.com", "+1 555-0104", 8, "Female", "AB-", "Seasonal allergic rhinitis"),
        ("Michael Bennett", "michael.b@example.com", "+1 555-0105", 34, "Male", "O-", "Post-viral fatigue and elevated pulse"),
        ("Emma Watson", "emma.w@example.com", "+1 555-0106", 62, "Female", "A-", "Type 2 Diabetes, routine monitoring"),
        ("David Miller", "david.m@example.com", "+1 555-0107", 45, "Male", "B-", "Severe chest discomfort, referred for ECG")
    ]
    cursor.executemany("""
    INSERT INTO patients (name, email, phone, age, gender, blood_group, medical_notes)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, patients)

    today = datetime.date.today().isoformat()

    # Seed today's active appointments & live queue
    # Dr. Sarah Chen (Doctor ID 1 - Cardiology)
    # Dr. Priya Sharma (Doctor ID 5 - General Medicine)
    appointments = [
        # (patient_id, doctor_id, date, time, reason, priority, status, queue_number, predicted_wait, actual_wait)
        (1, 1, today, "09:30", "Follow-up on Blood Pressure Medication", "Routine", "IN_CONSULTATION", 1, 0, 12),
        (7, 1, today, "10:00", "Acute chest pain radiating to left shoulder", "Emergency", "WAITING", 2, 4, None),
        (5, 1, today, "10:30", "Arrhythmia checkup after exercise", "Priority", "WAITING", 3, 19, None),
        (6, 1, today, "11:15", "Routine ECG review and lipid panel", "Routine", "WAITING", 4, 38, None),
        (2, 5, today, "09:45", "Persistent dry cough and wheezing", "Priority", "IN_CONSULTATION", 1, 0, 8),
        (3, 4, today, "10:30", "Knee joint swelling and limited mobility", "Routine", "WAITING", 1, 14, None),
        (4, 3, today, "11:00", "Pediatric wellness exam and immunization", "Routine", "WAITING", 1, 10, None)
    ]
    cursor.executemany("""
    INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, reason, priority, status, queue_number, predicted_wait_mins, actual_wait_mins)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, appointments)

    # Initial notifications
    notifications = [
        (1, 1, "Appointment Now Active", "Dr. Sarah Chen has called you into Consultation Room 301.", "IN_APP"),
        (7, 1, "Emergency Priority Granted", "Your queue position has been elevated to Priority #2 due to acute cardiac symptoms.", "SMS"),
        (5, 1, "Queue Update Alert", "Estimated consultation at 10:24 AM (approx. 19 mins). Please remain seated in Zone B.", "IN_APP"),
        (6, 1, "Doctor Delay Notice", "Dr. Sarah Chen is attending to a prioritized emergency case. Your appointment is rescheduled for ~11:35 AM.", "SMS")
    ]
    cursor.executemany("""
    INSERT INTO notifications (patient_id, doctor_id, title, message, channel)
    VALUES (?, ?, ?, ?, ?)
    """, notifications)
