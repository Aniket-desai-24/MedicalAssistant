"""
Medical AI Assistant - FastAPI Backend
Analyzes prescriptions for allergy conflicts and ingredient cross-reactivity
"""

import os
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import json
import logging

# Import our modules
from database import engine, SessionLocal, Base
from models import Patient, Drug, PatientAllergy, Prescription, DrugAllergen, AllergyAlert
from schemas import (
    PrescriptionRequest, PrescriptionResponse, PatientCreate, DrugCreate,
    AllergyCheckResult, PrescriptionCreate, PatientAllergyCreate, WarningItem, ContraindicationItem
)
from ai_agent import MedicalAIAgent
from allergy_checker import AllergyChecker
from sample_data import populate_sample_data
from prescription_ocr import PrescriptionOCR
from groq_client import GroqClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Medical AI Assistant",
    description="AI-powered prescription analysis for allergy conflicts and cross-reactivity",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize AI agent and allergy checker
groq_client = GroqClient()
ai_agent = MedicalAIAgent()
allergy_checker = AllergyChecker()
prescription_ocr = PrescriptionOCR(groq_client)

def get_db():
    """Database dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
async def startup_event():
    """Initialize the application with sample data"""
    db = SessionLocal()
    try:
        # Check if we need to populate sample data
        patient_count = db.query(Patient).count()
        if patient_count == 0:
            logger.info("Populating database with sample data...")
            populate_sample_data(db)
            logger.info("Sample data populated successfully")
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main application page"""
    with open("static/index.html", "r") as file:
        return HTMLResponse(content=file.read())

@app.post("/check_prescription", response_model=PrescriptionResponse)
async def check_prescription(
    prescription_data: PrescriptionRequest,
    db: Session = Depends(get_db)
):
    """
    Main endpoint to check prescription for allergy conflicts and cross-reactivity
    
    Args:
        prescription_data: Contains patient name and list of medicines
        
    Returns:
        PrescriptionResponse with safety analysis and warnings
    """
    try:
        logger.info(f"Checking prescription for patient: {prescription_data.patient_name}")
        
        # Find patient by name
        patient = db.query(Patient).filter(
            Patient.first_name.ilike(f"%{prescription_data.patient_name.split()[0]}%")
        ).first()
        
        if not patient:
            raise HTTPException(
                status_code=404, 
                detail=f"Patient '{prescription_data.patient_name}' not found in database"
            )
        
        # Get patient allergies
        patient_allergies = db.query(PatientAllergy).filter(
            PatientAllergy.patient_id == patient.patient_id,
            PatientAllergy.status == 'active'
        ).all()
        
        warnings = []
        safe_medicines = []
        contraindications = []
        
        # Check each medicine
        for medicine_name in prescription_data.medicines:
            logger.info(f"Checking medicine: {medicine_name}")
            
            # Find drug in database with flexible search
            # Remove quotes if present
            clean_medicine_name = medicine_name.strip().strip('"').strip("'")
            
            # Try multiple search strategies
            drug = (
                db.query(Drug).filter(
                    Drug.drug_name.ilike(f"%{clean_medicine_name}%")
                ).first() or
                db.query(Drug).filter(
                    Drug.generic_name.ilike(f"%{clean_medicine_name}%")
                ).first() or
                db.query(Drug).filter(
                    Drug.active_ingredient.ilike(f"%{clean_medicine_name}%")
                ).first()
            )
            
            if not drug:
                # Try to find similar medicines using multiple strategies
                suggestions = []
                
                # Strategy 1: Prefix matching (first 3+ characters)
                if len(clean_medicine_name) >= 3:
                    prefix_matches = db.query(Drug).filter(
                        Drug.drug_name.ilike(f"{clean_medicine_name[:3]}%") |
                        Drug.generic_name.ilike(f"{clean_medicine_name[:3]}%")
                    ).limit(3).all()
                    suggestions.extend([d.drug_name for d in prefix_matches])
                
                # Strategy 2: Substring matching anywhere in name
                substring_matches = db.query(Drug).filter(
                    Drug.drug_name.ilike(f"%{clean_medicine_name}%") |
                    Drug.generic_name.ilike(f"%{clean_medicine_name}%") |
                    Drug.active_ingredient.ilike(f"%{clean_medicine_name}%")
                ).limit(2).all()
                suggestions.extend([d.drug_name for d in substring_matches])
                
                # Remove duplicates while preserving order
                unique_suggestions = []
                for s in suggestions:
                    if s not in unique_suggestions:
                        unique_suggestions.append(s)
                
                suggestion_text = ""
                if unique_suggestions:
                    suggestion_text = f" Did you mean: {', '.join(unique_suggestions[:3])}?"
                
                warnings.append(WarningItem(
                    medicine=medicine_name,
                    reason=f"Medicine '{medicine_name}' not found in drug database. Please verify the spelling or check if it's available under a different name.{suggestion_text}",
                    confidence="high"
                ))
                continue
            
            # Check for direct allergy matches
            direct_conflicts = allergy_checker.check_direct_allergies(
                patient_allergies, drug, db
            )
            
            # Check for cross-reactivity using AI
            cross_reactivity_result = await ai_agent.analyze_cross_reactivity(
                patient_allergies, drug, db
            )
            
            # Combine results - check for duplicates before adding
            if direct_conflicts:
                for conflict in direct_conflicts:
                    # Create unique identifier for this conflict
                    conflict_key = f"{medicine_name}_{conflict['allergen_name']}_{conflict['severity']}"
                    
                    # Check if this exact conflict already exists
                    existing_contraindications = [f"{c.medicine}_{c.allergen}_{c.severity}" for c in contraindications]
                    existing_warnings = [f"{w.medicine}_{getattr(w, 'allergen', '')}_{getattr(w, 'severity', '')}" for w in warnings]
                    
                    if conflict_key not in existing_contraindications and conflict_key not in existing_warnings:
                        if conflict['severity'] in ['life_threatening', 'severe']:
                            contraindications.append(ContraindicationItem(
                                medicine=medicine_name,
                                allergen=conflict['allergen_name'],
                                severity=conflict['severity'],
                                reason=f"Direct allergy match: {conflict['reaction_description']}"
                            ))
                        else:
                            warnings.append(WarningItem(
                                medicine=medicine_name,
                                allergen=conflict['allergen_name'],
                                severity=conflict['severity'],
                                reason=f"Known allergy: {conflict['reaction_description']}"
                            ))
            
            elif cross_reactivity_result.get('has_cross_reactivity'):
                warnings.append(WarningItem(
                    medicine=medicine_name,
                    reason=cross_reactivity_result.get('explanation', 'Potential cross-reactivity detected'),
                    confidence=cross_reactivity_result.get('confidence', 'medium')
                ))
            
            else:
                safe_medicines.append(medicine_name)
        
        # Determine overall safety
        is_safe = len(contraindications) == 0
        
        response = PrescriptionResponse(
            patient_name=prescription_data.patient_name,
            patient_id=patient.patient_id,
            is_safe=is_safe,
            warnings=warnings,
            contraindications=contraindications,
            safe_medicines=safe_medicines,
            ai_analysis=await ai_agent.generate_summary(
                patient, prescription_data.medicines, warnings, contraindications
            )
        )
        
        # Log the prescription check to database
        try:
            # Create prescription records for each medicine
            for medicine_name in prescription_data.medicines:
                drug = db.query(Drug).filter(
                    Drug.drug_name.ilike(f"%{medicine_name}%")
                ).first()
                
                if drug:  # Only log if drug exists in database
                    prescription_record = Prescription(
                        patient_id=patient.patient_id,
                        physician_id=1,  # Default physician for demo
                        drug_id=drug.drug_id,
                        dosage_instructions=f"As prescribed for {medicine_name}",
                        allergy_checked=True,
                        interaction_checked=True
                    )
                    db.add(prescription_record)
                    
                    # Log any alerts
                    for warning in warnings:
                        if hasattr(warning, 'medicine') and warning.medicine == medicine_name:
                            alert = AllergyAlert(
                                prescription_id=prescription_record.prescription_id,
                                patient_id=patient.patient_id,
                                alert_level='warning',
                                alert_message=warning.reason
                            )
                            db.add(alert)
                    
                    for contraindication in contraindications:
                        if contraindication.medicine == medicine_name:
                            alert = AllergyAlert(
                                prescription_id=prescription_record.prescription_id,
                                patient_id=patient.patient_id,
                                alert_level='contraindication',
                                alert_message=contraindication.reason
                            )
                            db.add(alert)
            
            db.commit()
            logger.info(f"Prescription records saved to database")
        except Exception as e:
            logger.error(f"Error logging prescription to database: {str(e)}")
            db.rollback()
        
        logger.info(f"Prescription check completed. Safe: {is_safe}, Warnings: {len(warnings)}, Contraindications: {len(contraindications)}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error checking prescription: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/patients", response_model=Dict[str, Any])
async def create_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    """Create a new patient"""
    try:
        db_patient = Patient(**patient.dict())
        db.add(db_patient)
        db.commit()
        db.refresh(db_patient)
        return {"message": "Patient created successfully", "patient_id": db_patient.patient_id}
    except Exception as e:
        logger.error(f"Error creating patient: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/patients/{patient_id}/allergies")
async def add_patient_allergy(
    patient_id: int, 
    allergy: PatientAllergyCreate, 
    db: Session = Depends(get_db)
):
    """Add an allergy for a patient"""
    try:
        # Check if patient exists
        patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        db_allergy = PatientAllergy(patient_id=patient_id, **allergy.dict())
        db.add(db_allergy)
        db.commit()
        db.refresh(db_allergy)
        return {"message": "Allergy added successfully", "allergy_id": db_allergy.allergy_id}
    except Exception as e:
        logger.error(f"Error adding patient allergy: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patients")
async def list_patients(db: Session = Depends(get_db)):
    """List all patients"""
    try:
        patients = db.query(Patient).all()
        return [
            {
                "patient_id": p.patient_id,
                "name": f"{p.first_name} {p.last_name}",
                "date_of_birth": p.date_of_birth.isoformat() if p.date_of_birth else None
            }
            for p in patients
        ]
    except Exception as e:
        logger.error(f"Error listing patients: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patients/{patient_id}/allergies")
async def get_patient_allergies(patient_id: int, db: Session = Depends(get_db)):
    """Get all allergies for a patient"""
    try:
        allergies = db.query(PatientAllergy).filter(
            PatientAllergy.patient_id == patient_id,
            PatientAllergy.status == 'active'
        ).all()
        
        result = []
        for allergy in allergies:
            allergen = db.query(DrugAllergen).filter(
                DrugAllergen.allergen_id == allergy.allergen_id
            ).first()
            
            result.append({
                "allergy_id": allergy.allergy_id,
                "allergen_name": allergen.allergen_name if allergen else "Unknown",
                "severity": allergy.severity,
                "reaction_description": allergy.reaction_description
            })
        
        return result
    except Exception as e:
        logger.error(f"Error getting patient allergies: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/drugs")
async def list_drugs(search: Optional[str] = None, db: Session = Depends(get_db)):
    """List all available drugs with optional search"""
    try:
        query = db.query(Drug)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                Drug.drug_name.ilike(search_term) |
                Drug.generic_name.ilike(search_term) |
                Drug.active_ingredient.ilike(search_term)
            )
        
        drugs = query.limit(50).all()  # Limit results for performance
        return [
            {
                "drug_id": d.drug_id,
                "drug_name": d.drug_name,
                "generic_name": d.generic_name,
                "active_ingredient": d.active_ingredient,
                "strength": d.strength,
                "dosage_form": d.dosage_form
            }
            for d in drugs
        ]
    except Exception as e:
        logger.error(f"Error listing drugs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload_prescription")
async def upload_prescription(
    patient_name: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload and process prescription file (PDF or image) to extract medicine names
    """
    try:
        logger.info(f"Processing prescription file upload for patient: {patient_name}")
        
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file uploaded")
        
        # Read file content
        file_content = await file.read()
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        # Process the file with OCR
        ocr_result = await prescription_ocr.extract_medicines_from_file(
            file_content, file.filename
        )
        
        if not ocr_result["success"]:
            return {
                "success": False,
                "error": ocr_result["error"],
                "extracted_text": "",
                "medicines": []
            }
        
        # If medicines were extracted, automatically check the prescription
        extracted_medicines = ocr_result["medicines"]
        
        if extracted_medicines:
            # Create prescription request with extracted medicines
            from schemas import PrescriptionRequest
            prescription_request = PrescriptionRequest(
                patient_name=patient_name,
                medicines=extracted_medicines
            )
            
            # Run the prescription check
            check_result = await check_prescription(prescription_request, db)
            
            return {
                "success": True,
                "ocr_result": ocr_result,
                "prescription_analysis": check_result,
                "extracted_medicines": extracted_medicines,
                "extracted_text_preview": ocr_result["extracted_text"][:200] + "..." if len(ocr_result["extracted_text"]) > 200 else ocr_result["extracted_text"]
            }
        else:
            return {
                "success": True,
                "ocr_result": ocr_result,
                "message": "No medicines found in the prescription. Please verify the file quality and try again.",
                "extracted_text_preview": ocr_result["extracted_text"][:200] + "..." if len(ocr_result["extracted_text"]) > 200 else ocr_result["extracted_text"]
            }
            
    except Exception as e:
        logger.error(f"Error processing prescription upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.get("/patients/{patient_id}/prescriptions")
async def get_patient_prescriptions(patient_id: int, db: Session = Depends(get_db)):
    """Get prescription history for a patient"""
    try:
        prescriptions = db.query(Prescription).filter(
            Prescription.patient_id == patient_id
        ).order_by(Prescription.prescribed_date.desc()).all()
        
        result = []
        for prescription in prescriptions:
            drug = db.query(Drug).filter(Drug.drug_id == prescription.drug_id).first()
            alerts = db.query(AllergyAlert).filter(
                AllergyAlert.prescription_id == prescription.prescription_id
            ).all()
            
            result.append({
                "prescription_id": prescription.prescription_id,
                "drug_name": drug.drug_name if drug else "Unknown",
                "dosage_instructions": prescription.dosage_instructions,
                "prescribed_date": prescription.prescribed_date.isoformat(),
                "status": prescription.status,
                "allergy_checked": prescription.allergy_checked,
                "alerts": [
                    {
                        "alert_level": alert.alert_level,
                        "alert_message": alert.alert_message
                    }
                    for alert in alerts
                ]
            })
        
        return result
    except Exception as e:
        logger.error(f"Error getting patient prescriptions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/allergy-patterns")
async def get_allergy_patterns(db: Session = Depends(get_db)):
    """Get analytics on common allergy patterns"""
    try:
        from sqlalchemy import func
        
        # Get most common allergies
        common_allergies = db.query(
            DrugAllergen.allergen_name,
            func.count(PatientAllergy.allergy_id).label('count')
        ).join(
            PatientAllergy, DrugAllergen.allergen_id == PatientAllergy.allergen_id
        ).group_by(
            DrugAllergen.allergen_name
        ).order_by(
            func.count(PatientAllergy.allergy_id).desc()
        ).limit(10).all()
        
        # Get severity distribution
        severity_dist = db.query(
            PatientAllergy.severity,
            func.count(PatientAllergy.allergy_id).label('count')
        ).group_by(PatientAllergy.severity).all()
        
        return {
            "common_allergies": [
                {"allergen": allergy.allergen_name, "patient_count": allergy.count}
                for allergy in common_allergies
            ],
            "severity_distribution": [
                {"severity": sev.severity, "count": sev.count}
                for sev in severity_dist
            ]
        }
    except Exception as e:
        logger.error(f"Error getting allergy patterns: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Medical AI Assistant"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=5000, 
        reload=True,
        log_level="info"
    )
