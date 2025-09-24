#!/usr/bin/env python3
"""
Simple Supabase Setup for PatientDB
Creates tables and tests connection (no data migration needed)
"""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def setup_supabase():
    """Create tables in Supabase and test connection"""
    
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found in .env file")
        return False
    
    print("🚀 Setting up PatientDB with Supabase...")
    print(f"🔗 Connecting to Supabase...")
    
    try:
        # Create engine
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        
        # Test connection first
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Connection to Supabase successful!")
        
        # Create tables
        create_tables(engine)
        
        # Verify tables were created
        verify_setup(engine)
        
        print("\n🎉 Supabase setup completed successfully!")
        print("🚀 You can now run your FastAPI application:")
        print("   cd backend")
        print("   uvicorn main:app --reload")
        
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {str(e)}")
        print("\n💡 Troubleshooting tips:")
        print("1. Check if your Supabase project is active")
        print("2. Verify your DATABASE_URL in .env file")
        print("3. Try running: python test_connection.py")
        return False

def create_tables(engine):
    """Create the patients table and indexes"""
    
    print("📋 Creating database tables...")
    
    # SQL to create patients table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS patients (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255),
        date_of_birth VARCHAR(50),
        diagnosis TEXT,
        prescription TEXT,
        confidence_score FLOAT,
        raw_text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Create indexes for better performance
    CREATE INDEX IF NOT EXISTS idx_patients_name ON patients(name);
    CREATE INDEX IF NOT EXISTS idx_patients_created_at ON patients(created_at);
    CREATE INDEX IF NOT EXISTS idx_patients_diagnosis ON patients(diagnosis);
    """
    
    with engine.connect() as conn:
        conn.execute(text(create_table_sql))
        conn.commit()
    
    print("✅ Database tables created successfully")

def verify_setup(engine):
    """Verify that tables were created correctly"""
    
    print("🔍 Verifying table creation...")
    
    with engine.connect() as conn:
        # Check if patients table exists
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'patients'
        """))
        
        if result.fetchone():
            print("✅ 'patients' table created successfully")
            
            # Check table structure
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'patients' AND table_schema = 'public'
                ORDER BY ordinal_position
            """))
            
            columns = result.fetchall()
            print("📋 Table structure:")
            for col in columns:
                print(f"   - {col[0]}: {col[1]}")
        else:
            print("❌ 'patients' table not found")

def show_next_steps():
    """Show what to do next"""
    print("""
🎯 NEXT STEPS:

1. ✅ Supabase is now configured and ready!

2. 🚀 Start your FastAPI application:
   cd backend
   uvicorn main:app --reload

3. 🌐 Open your frontend:
   cd frontend
   npm start

4. 📝 Your app will now:
   - Store patient data in Supabase PostgreSQL
   - Work in production environment
   - Scale automatically
   - Have automatic backups

5. 🔧 For deployment:
   - Frontend: Deploy to Vercel
   - Backend: Deploy to Railway/Render
   - Database: Already on Supabase ✅

Your application is production-ready! 🎉
""")

if __name__ == "__main__":
    print("🏥 PatientDB - Supabase Setup")
    print("=" * 40)
    
    if setup_supabase():
        show_next_steps()
    else:
        print("\n❌ Setup failed. Please check your connection and try again.")
        print("💡 You can run 'python test_connection.py' to diagnose issues.")