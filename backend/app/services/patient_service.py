"""
Patient Service with Supabase REST API Integration
Fallback to SQLAlchemy for local development
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class PatientService:
    """Service for patient operations with Supabase REST API"""
    
    def __init__(self):
        # Check if we should use Supabase
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if self.supabase_url and self.supabase_key:
            try:
                from supabase import create_client, Client
                self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
                self.db_type = "supabase"
                print("✅ Using Supabase for patient data storage")
            except ImportError:
                print("⚠️ Supabase client not installed, falling back to SQLite")
                self._init_sqlite()
        else:
            print("📁 Using SQLite for patient data storage")
            self._init_sqlite()
    
    def _init_sqlite(self):
        """Initialize SQLite fallback"""
        from ..database import SessionLocal
        from ..services.database_service import DatabaseService
        self.db_type = "sqlite"
        
    async def create_patient(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new patient with only the specified fields"""
        try:
            # Extract only the fields we want to store
            clean_data = {
                "name": patient_data.get("name", "Unknown"),
                "date_of_birth": patient_data.get("date_of_birth", "1900-01-01"),
                "diagnosis": patient_data.get("diagnosis"),
                "prescription": patient_data.get("prescription"),
                "confidence_score": patient_data.get("confidence_score", 0.0),
                "raw_text": patient_data.get("raw_text", "")
            }
            
            if self.db_type == "supabase":
                return await self._create_patient_supabase(clean_data)
            else:
                return await self._create_patient_sqlite(clean_data)
                
        except Exception as e:
            logger.error(f"Error creating patient: {str(e)}")
            raise
    
    async def _create_patient_supabase(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create patient in Supabase"""
        try:
            # Add timestamp
            patient_data["created_at"] = datetime.utcnow().isoformat()
            
            result = self.supabase.table("patients").insert(patient_data).execute()
            
            if result.data and len(result.data) > 0:
                created_patient = result.data[0]
                print(f"✅ Patient created in Supabase with ID: {created_patient.get('id')}")
                return created_patient
            else:
                raise Exception("No data returned from Supabase insert")
                
        except Exception as e:
            logger.error(f"Supabase insert error: {str(e)}")
            raise
    
    async def _create_patient_sqlite(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create patient in SQLite"""
        from ..database import SessionLocal
        from ..services.database_service import DatabaseService
        
        db = SessionLocal()
        try:
            db_service = DatabaseService(db)
            
            # Convert to SQLite format
            sqlite_data = {
                "name": patient_data["name"],
                "date_of_birth": patient_data["date_of_birth"],
                "diagnosis": patient_data.get("diagnosis"),
                "prescription": patient_data.get("prescription")
            }
            
            created_patient = db_service.create_patient(sqlite_data)
            
            # Convert back to dict format
            return {
                "id": created_patient.id,
                "name": created_patient.name,
                "date_of_birth": created_patient.date_of_birth,
                "diagnosis": created_patient.diagnosis,
                "prescription": created_patient.prescription,
                "created_at": created_patient.created_at.isoformat() if created_patient.created_at else None
            }
            
        finally:
            db.close()
    
    async def get_all_patients(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all patients"""
        if self.db_type == "supabase":
            return await self._get_patients_supabase(limit)
        else:
            return await self._get_patients_sqlite(limit)
    
    async def _get_patients_supabase(self, limit: int) -> List[Dict[str, Any]]:
        """Get patients from Supabase"""
        try:
            result = self.supabase.table("patients").select("*").limit(limit).execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error fetching patients from Supabase: {str(e)}")
            return []
    
    async def _get_patients_sqlite(self, limit: int) -> List[Dict[str, Any]]:
        """Get patients from SQLite"""
        from ..database import SessionLocal
        from ..services.database_service import DatabaseService
        
        db = SessionLocal()
        try:
            db_service = DatabaseService(db)
            patients = db_service.get_all_patients()
            
            return [
                {
                    "id": p.id,
                    "name": p.name,
                    "date_of_birth": p.date_of_birth,
                    "diagnosis": p.diagnosis,
                    "prescription": p.prescription,
                    "created_at": p.created_at.isoformat() if p.created_at else None
                }
                for p in patients[:limit]
            ]
        finally:
            db.close()
    
    async def test_connection(self) -> bool:
        """Test database connection"""
        try:
            if self.db_type == "supabase":
                result = self.supabase.table("patients").select("id").limit(1).execute()
                return True
            else:
                from ..database import SessionLocal
                db = SessionLocal()
                try:
                    db.execute("SELECT 1")
                    return True
                finally:
                    db.close()
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False

# Global instance
_patient_service = None

def get_patient_service() -> PatientService:
    """Get or create patient service instance"""
    global _patient_service
    if _patient_service is None:
        _patient_service = PatientService()
    return _patient_service