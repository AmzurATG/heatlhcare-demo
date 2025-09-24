"""
Supabase REST API Service
Uses REST API instead of direct database connection (for network firewall compatibility)
"""

import os
from typing import Dict, List, Optional, Any
from supabase import create_client, Client
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SupabaseService:
    """Service for interacting with Supabase via REST API"""
    
    def __init__(self):
        # Get credentials from environment
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment")
        
        # Create Supabase client
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        print(f"✅ Supabase REST API client initialized")
        logger.info("Supabase REST API client initialized")

    async def create_patient(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new patient record"""
        try:
            # Add timestamps
            patient_data["created_at"] = datetime.now().isoformat()
            patient_data["updated_at"] = datetime.now().isoformat()
            
            # Insert via REST API
            response = self.supabase.table('patients').insert(patient_data).execute()
            
            if response.data:
                print(f"✅ Patient created: {patient_data.get('name', 'Unknown')}")
                logger.info(f"Patient created: {patient_data.get('name', 'Unknown')}")
                return response.data[0]
            else:
                raise Exception("No data returned from insert")
                
        except Exception as e:
            error_msg = f"Failed to create patient: {str(e)}"
            print(f"❌ {error_msg}")
            logger.error(error_msg)
            raise

    async def get_all_patients(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all patients with optional limit"""
        try:
            response = self.supabase.table('patients').select('*').limit(limit).order('created_at', desc=True).execute()
            
            patients = response.data or []
            print(f"📋 Retrieved {len(patients)} patients")
            logger.info(f"Retrieved {len(patients)} patients")
            return patients
            
        except Exception as e:
            error_msg = f"Failed to retrieve patients: {str(e)}"
            print(f"❌ {error_msg}")
            logger.error(error_msg)
            raise

    async def get_patient_by_id(self, patient_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific patient by ID"""
        try:
            response = self.supabase.table('patients').select('*').eq('id', patient_id).execute()
            
            if response.data:
                patient = response.data[0]
                print(f"👤 Retrieved patient: {patient.get('name', 'Unknown')}")
                logger.info(f"Retrieved patient ID {patient_id}")
                return patient
            else:
                print(f"❓ Patient not found: ID {patient_id}")
                return None
                
        except Exception as e:
            error_msg = f"Failed to retrieve patient {patient_id}: {str(e)}"
            print(f"❌ {error_msg}")
            logger.error(error_msg)
            raise

    async def update_patient(self, patient_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a patient record"""
        try:
            # Add update timestamp
            update_data["updated_at"] = datetime.now().isoformat()
            
            response = self.supabase.table('patients').update(update_data).eq('id', patient_id).execute()
            
            if response.data:
                updated_patient = response.data[0]
                print(f"✏️ Updated patient: {updated_patient.get('name', 'Unknown')}")
                logger.info(f"Updated patient ID {patient_id}")
                return updated_patient
            else:
                print(f"❓ Patient not found for update: ID {patient_id}")
                return None
                
        except Exception as e:
            error_msg = f"Failed to update patient {patient_id}: {str(e)}"
            print(f"❌ {error_msg}")
            logger.error(error_msg)
            raise

    async def delete_patient(self, patient_id: int) -> bool:
        """Delete a patient record"""
        try:
            response = self.supabase.table('patients').delete().eq('id', patient_id).execute()
            
            if response.data:
                print(f"🗑️ Deleted patient ID {patient_id}")
                logger.info(f"Deleted patient ID {patient_id}")
                return True
            else:
                print(f"❓ Patient not found for deletion: ID {patient_id}")
                return False
                
        except Exception as e:
            error_msg = f"Failed to delete patient {patient_id}: {str(e)}"
            print(f"❌ {error_msg}")
            logger.error(error_msg)
            raise

    async def search_patients(self, search_term: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search patients by name or diagnosis"""
        try:
            # Search in both name and diagnosis fields
            response = self.supabase.table('patients').select('*').or_(
                f"name.ilike.%{search_term}%,diagnosis.ilike.%{search_term}%"
            ).limit(limit).order('created_at', desc=True).execute()
            
            patients = response.data or []
            print(f"🔍 Found {len(patients)} patients matching '{search_term}'")
            logger.info(f"Search for '{search_term}' returned {len(patients)} results")
            return patients
            
        except Exception as e:
            error_msg = f"Failed to search patients: {str(e)}"
            print(f"❌ {error_msg}")
            logger.error(error_msg)
            raise

    async def get_patients_stats(self) -> Dict[str, Any]:
        """Get basic statistics about patients"""
        try:
            # Get total count
            response = self.supabase.table('patients').select('id', count='exact').execute()
            total_count = response.count or 0
            
            # Get recent patients (last 7 days)
            from datetime import datetime, timedelta
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            
            recent_response = self.supabase.table('patients').select('id', count='exact').gte('created_at', week_ago).execute()
            recent_count = recent_response.count or 0
            
            stats = {
                "total_patients": total_count,
                "recent_patients": recent_count,
                "last_updated": datetime.now().isoformat()
            }
            
            print(f"📊 Stats: {total_count} total, {recent_count} recent")
            logger.info(f"Retrieved patient stats: {stats}")
            return stats
            
        except Exception as e:
            error_msg = f"Failed to get patient stats: {str(e)}"
            print(f"❌ {error_msg}")
            logger.error(error_msg)
            raise

    async def test_connection(self) -> bool:
        """Test the Supabase REST API connection"""
        try:
            # Simple query to test connection
            response = self.supabase.table('patients').select('id').limit(1).execute()
            
            print("✅ Supabase REST API connection successful")
            logger.info("Supabase REST API connection test passed")
            return True
            
        except Exception as e:
            error_msg = f"Supabase REST API connection failed: {str(e)}"
            print(f"❌ {error_msg}")
            logger.error(error_msg)
            return False

    async def ensure_table_exists(self) -> bool:
        """Ensure the patients table exists (will be created via Supabase dashboard)"""
        try:
            # Try a simple query to check if table exists
            response = self.supabase.table('patients').select('id').limit(1).execute()
            print("✅ Patients table exists and accessible")
            return True
            
        except Exception as e:
            print(f"⚠️ Patients table may not exist: {str(e)}")
            print("Please create the table in Supabase dashboard:")
            print("https://supabase.com/dashboard → SQL Editor → Run this:")
            print("""
CREATE TABLE IF NOT EXISTS patients (
    id SERIAL PRIMARY KEY,
    name TEXT,
    date_of_birth TEXT,
    diagnosis TEXT,
    prescription TEXT,
    confidence_score FLOAT,
    raw_text TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
            """)
            return False

# Create global instance
supabase_service = None

def get_supabase_service() -> SupabaseService:
    """Get or create Supabase service instance"""
    global supabase_service
    if supabase_service is None:
        supabase_service = SupabaseService()
    return supabase_service