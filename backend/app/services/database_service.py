from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.database import get_db, Patient as PatientDBModel
from app.models.patient import Patient, PatientCreate, PatientUpdate
from typing import List, Optional
import uuid
from datetime import datetime

class DatabaseService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_patient(self, patient_data: PatientCreate) -> Patient:
        """Create a new patient record"""
        try:
            # Generate UUID for patient
            patient_id = str(uuid.uuid4())
            
            db_patient = PatientDBModel(
                id=patient_id,
                name=patient_data.name,
                date_of_birth=patient_data.date_of_birth,
                diagnosis=patient_data.diagnosis,
                prescription=patient_data.prescription
            )
            
            self.db.add(db_patient)
            self.db.commit()
            self.db.refresh(db_patient)
            
            return Patient(
                id=db_patient.id,
                name=db_patient.name,
                date_of_birth=db_patient.date_of_birth,
                diagnosis=db_patient.diagnosis,
                prescription=db_patient.prescription,
                created_at=db_patient.created_at,
                updated_at=db_patient.updated_at
            )
        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error: {str(e)}")
    
    def get_all_patients(self) -> List[Patient]:
        """Get all patient records"""
        try:
            db_patients = self.db.query(PatientDBModel).order_by(PatientDBModel.created_at.desc()).all()
            
            return [
                Patient(
                    id=patient.id,
                    name=patient.name,
                    date_of_birth=patient.date_of_birth,
                    diagnosis=patient.diagnosis,
                    prescription=patient.prescription,
                    created_at=patient.created_at,
                    updated_at=patient.updated_at
                )
                for patient in db_patients
            ]
        except SQLAlchemyError as e:
            raise Exception(f"Database error: {str(e)}")
    
    def get_patient_by_id(self, patient_id: str) -> Optional[Patient]:
        """Get a patient by ID"""
        try:
            db_patient = self.db.query(PatientDBModel).filter(PatientDBModel.id == patient_id).first()
            
            if not db_patient:
                return None
                
            return Patient(
                id=db_patient.id,
                name=db_patient.name,
                date_of_birth=db_patient.date_of_birth,
                diagnosis=db_patient.diagnosis,
                prescription=db_patient.prescription,
                created_at=db_patient.created_at,
                updated_at=db_patient.updated_at
            )
        except SQLAlchemyError as e:
            raise Exception(f"Database error: {str(e)}")
    
    def update_patient(self, patient_id: str, patient_data: PatientUpdate) -> Optional[Patient]:
        """Update a patient record"""
        try:
            db_patient = self.db.query(PatientDBModel).filter(PatientDBModel.id == patient_id).first()
            
            if not db_patient:
                return None
            
            # Update fields that are not None
            update_data = {}
            if patient_data.name is not None:
                update_data['name'] = patient_data.name
            if patient_data.date_of_birth is not None:
                update_data['date_of_birth'] = patient_data.date_of_birth
            if patient_data.diagnosis is not None:
                update_data['diagnosis'] = patient_data.diagnosis
            if patient_data.prescription is not None:
                update_data['prescription'] = patient_data.prescription
            
            update_data['updated_at'] = datetime.utcnow()
            
            self.db.query(PatientDBModel).filter(PatientDBModel.id == patient_id).update(update_data)
            self.db.commit()
            self.db.refresh(db_patient)
            
            return Patient(
                id=db_patient.id,
                name=db_patient.name,
                date_of_birth=db_patient.date_of_birth,
                diagnosis=db_patient.diagnosis,
                prescription=db_patient.prescription,
                created_at=db_patient.created_at,
                updated_at=db_patient.updated_at
            )
        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error: {str(e)}")
    
    def delete_patient(self, patient_id: str) -> bool:
        """Delete a patient record"""
        try:
            db_patient = self.db.query(PatientDBModel).filter(PatientDBModel.id == patient_id).first()
            
            if not db_patient:
                return False
            
            self.db.delete(db_patient)
            self.db.commit()
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Database error: {str(e)}")

# Dependency to get database service
def get_database_service(db: Session) -> DatabaseService:
    return DatabaseService(db)
