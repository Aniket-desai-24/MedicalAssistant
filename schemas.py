"""
Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date, datetime

class PrescriptionRequest(BaseModel):
    patient_name: str = Field(..., description="Full name of the patient")
    medicines: List[str] = Field(..., description="List of prescribed medicine names")

class WarningItem(BaseModel):
    medicine: Optional[str] = None
    allergen: Optional[str] = None
    severity: Optional[str] = None
    reason: str
    confidence: Optional[str] = None

class ContraindicationItem(BaseModel):
    medicine: str
    allergen: str
    severity: str
    reason: str

class AIAnalysis(BaseModel):
    summary: str
    recommendations: List[str]
    risk_level: str  # low, medium, high, critical

class PrescriptionResponse(BaseModel):
    patient_name: str
    patient_id: int
    is_safe: bool
    warnings: List[WarningItem]
    contraindications: List[ContraindicationItem]
    safe_medicines: List[str]
    ai_analysis: AIAnalysis

class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    ssn: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    insurance_id: Optional[str] = None

class DrugCreate(BaseModel):
    drug_name: str
    generic_name: Optional[str] = None
    active_ingredient: Optional[str] = None
    strength: Optional[str] = None
    dosage_form: Optional[str] = None
    route: Optional[str] = None
    manufacturer: Optional[str] = None
    ndc_number: Optional[str] = None

class PatientAllergyCreate(BaseModel):
    allergen_id: int
    allergy_type: str = "drug"
    severity: str  # mild, moderate, severe, life_threatening
    reaction_description: Optional[str] = None
    onset_date: Optional[date] = None

class PrescriptionCreate(BaseModel):
    patient_id: int
    physician_id: int
    drug_id: int
    quantity: Optional[float] = None
    quantity_unit: Optional[str] = None
    dosage_instructions: Optional[str] = None
    refills_allowed: int = 0
    days_supply: Optional[int] = None

class AllergyCheckResult(BaseModel):
    has_conflict: bool
    conflict_type: str  # direct, cross_reactive, none
    allergen_name: Optional[str] = None
    severity: Optional[str] = None
    explanation: str
    confidence: str  # low, medium, high
