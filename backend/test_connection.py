#!/usr/bin/env python3
"""
Supabase Connection Test Script
Tests different connection methods to troubleshoot connectivity
"""

import os
from dotenv import load_dotenv
import requests
import socket
from sqlalchemy import create_engine, text

load_dotenv()

def test_basic_connectivity():
    """Test basic network connectivity"""
    host = "duisrvekhqlmkvreswyp.supabase.co"
    ports = [5432, 6543, 443]  # Direct DB, Connection Pooler, HTTPS
    
    print("🌐 Testing basic network connectivity...")
    
    for port in ports:
        try:
            sock = socket.create_connection((host, port), timeout=10)
            sock.close()
            print(f"✅ Port {port}: Connected successfully")
        except Exception as e:
            print(f"❌ Port {port}: {str(e)}")

def test_https_connection():
    """Test HTTPS connection to Supabase"""
    print("\n🔗 Testing HTTPS connection to Supabase...")
    
    try:
        response = requests.get("https://duisrvekhqlmkvreswyp.supabase.co", timeout=10)
        print(f"✅ HTTPS: Status {response.status_code}")
    except Exception as e:
        print(f"❌ HTTPS: {str(e)}")

def test_database_connections():
    """Test different database connection methods"""
    print("\n🗄️ Testing database connections...")
    
    # Test direct connection (port 5432)
    direct_url = "postgresql://postgres:kmvf945nse43@duisrvekhqlmkvreswyp.supabase.co:5432/postgres"
    test_db_connection("Direct DB (5432)", direct_url)
    
    # Test connection pooler (port 6543)  
    pooler_url = "postgresql://postgres:kmvf945nse43@duisrvekhqlmkvreswyp.supabase.co:6543/postgres"
    test_db_connection("Connection Pooler (6543)", pooler_url)

def test_db_connection(name, url):
    """Test a specific database connection"""
    try:
        engine = create_engine(url, connect_args={"connect_timeout": 10})
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print(f"✅ {name}: Connected successfully")
    except Exception as e:
        print(f"❌ {name}: {str(e)}")

def suggest_fixes():
    """Suggest potential fixes"""
    print("""
🔧 POTENTIAL FIXES:

1. **Check Firewall:**
   - Windows Defender may be blocking port 5432/6543
   - Add Python to Windows Firewall exceptions

2. **Try VPN/Mobile Hotspot:**
   - Your ISP might block database ports
   - Try connecting through mobile data or VPN

3. **Use Connection Pooler:**
   - Port 6543 is often less restricted than 5432
   - Already updated your .env file to use port 6543

4. **Check Corporate Network:**
   - If on work/school network, database ports may be blocked
   - Contact network administrator

5. **Supabase Project Status:**
   - Check if project is "Paused" or "Starting"
   - Go to supabase.com dashboard to verify status
""")

if __name__ == "__main__":
    print("🏥 PatientDB - Supabase Connection Diagnostics")
    print("=" * 50)
    
    test_basic_connectivity()
    test_https_connection()
    test_database_connections()
    suggest_fixes()
    
    print("\n🎯 Try running migration again with port 6543!")
    print("python migrate_db.py")