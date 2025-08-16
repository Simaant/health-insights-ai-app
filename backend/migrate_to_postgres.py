#!/usr/bin/env python3
"""
Database Migration Script: SQLite to PostgreSQL
This script helps migrate data from SQLite to PostgreSQL for production deployment.
"""

import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_sqlite_connection():
    """Connect to SQLite database"""
    return sqlite3.connect('health_insights.db')

def get_postgres_connection():
    """Connect to PostgreSQL database"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    return psycopg2.connect(database_url)

def create_postgres_tables(conn):
    """Create tables in PostgreSQL"""
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Create chat_sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id VARCHAR(255) PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            title VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Create chat_messages table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id VARCHAR(255) PRIMARY KEY,
            session_id VARCHAR(255) REFERENCES chat_sessions(id) ON DELETE CASCADE,
            content TEXT NOT NULL,
            role VARCHAR(50) NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Create health_reports table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS health_reports (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            filename VARCHAR(255) NOT NULL,
            file_path VARCHAR(500) NOT NULL,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            extracted_text TEXT,
            health_markers JSONB
        );
    """)
    
    # Create wearable_data table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wearable_data (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            date DATE NOT NULL,
            steps INTEGER DEFAULT 0,
            heart_rate INTEGER,
            sleep_hours DECIMAL(4,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    conn.commit()
    cursor.close()

def migrate_data():
    """Migrate data from SQLite to PostgreSQL"""
    sqlite_conn = get_sqlite_connection()
    postgres_conn = get_postgres_connection()
    
    try:
        # Create tables in PostgreSQL
        create_postgres_tables(postgres_conn)
        
        # Migrate users
        sqlite_cursor = sqlite_conn.cursor()
        postgres_cursor = postgres_conn.cursor()
        
        sqlite_cursor.execute("SELECT * FROM users")
        users = sqlite_cursor.fetchall()
        
        for user in users:
            postgres_cursor.execute("""
                INSERT INTO users (id, email, password_hash, first_name, last_name, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, user)
        
        # Migrate chat_sessions
        sqlite_cursor.execute("SELECT * FROM chat_sessions")
        sessions = sqlite_cursor.fetchall()
        
        for session in sessions:
            postgres_cursor.execute("""
                INSERT INTO chat_sessions (id, user_id, title, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, session)
        
        # Migrate chat_messages
        sqlite_cursor.execute("SELECT * FROM chat_messages")
        messages = sqlite_cursor.fetchall()
        
        for message in messages:
            postgres_cursor.execute("""
                INSERT INTO chat_messages (id, session_id, content, role, timestamp)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, message)
        
        # Migrate health_reports
        sqlite_cursor.execute("SELECT * FROM health_reports")
        reports = sqlite_cursor.fetchall()
        
        for report in reports:
            postgres_cursor.execute("""
                INSERT INTO health_reports (id, user_id, filename, file_path, upload_date, extracted_text, health_markers)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, report)
        
        # Migrate wearable_data
        sqlite_cursor.execute("SELECT * FROM wearable_data")
        wearable_data = sqlite_cursor.fetchall()
        
        for data in wearable_data:
            postgres_cursor.execute("""
                INSERT INTO wearable_data (id, user_id, date, steps, heart_rate, sleep_hours, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, data)
        
        postgres_conn.commit()
        print("✅ Data migration completed successfully!")
        
    except Exception as e:
        postgres_conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        sqlite_conn.close()
        postgres_conn.close()

if __name__ == "__main__":
    print("🚀 Starting database migration from SQLite to PostgreSQL...")
    migrate_data()
    print("🎉 Migration completed!")
