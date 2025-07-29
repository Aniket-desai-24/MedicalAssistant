"""
SQLAlchemy models for the medical AI assistant
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Date, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Patient(Base):
    __tablename__ = "patients"
    
    patient_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date)
    ssn = Column(String(11))
    phone = Column(String(15))
    address = Column(Text)
    insurance_id = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    allergies = relationship("PatientAllergy", back_populates="patient")
    prescriptions = relationship("Prescription", back_populates="patient")

class Drug(Base):
    __tablename__ = "drugs"
    
    drug_id = Column(Integer, primary_key=True, index=True)
    drug_name = Column(String(200), nullable=False, index=True)
    generic_name = Column(String(200))
    active_ingredient = Column(String(200))
    strength = Column(String(50))
    dosage_form = Column(String(50))  # tablet, capsule, liquid, injection
    route = Column(String(50))  # oral, IV, topical, etc.
    manufacturer = Column(String(200))
    ndc_number = Column(String(20))  # National Drug Code
    approved = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    prescriptions = relationship("Prescription", back_populates="drug")
    allergen_mappings = relationship("DrugAllergenMapping", back_populates="drug")

class DrugAllergen(Base):
    __tablename__ = "drug_allergens"
    
    allergen_id = Column(Integer, primary_key=True, index=True)
    allergen_name = Column(String(200), nullable=False, index=True)
    allergen_type = Column(String(50))  # drug_class, active_ingredient, inactive_ingredient
    cross_sensitivity_group = Column(String(100))  # penicillins, sulfonamides, etc.
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    patient_allergies = relationship("PatientAllergy", back_populates="allergen")
    drug_mappings = relationship("DrugAllergenMapping", back_populates="allergen")

class DrugAllergenMapping(Base):
    __tablename__ = "drug_allergen_mapping"
    
    drug_id = Column(Integer, ForeignKey("drugs.drug_id"), primary_key=True)
    allergen_id = Column(Integer, ForeignKey("drug_allergens.allergen_id"), primary_key=True)
    
    # Relationships
    drug = relationship("Drug", back_populates="allergen_mappings")
    allergen = relationship("DrugAllergen", back_populates="drug_mappings")

class PatientAllergy(Base):
    __tablename__ = "patient_allergies"
    
    allergy_id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.patient_id"), nullable=False)
    allergen_id = Column(Integer, ForeignKey("drug_allergens.allergen_id"), nullable=False)
    allergy_type = Column(String(50))  # drug, food, environmental
    severity = Column(String(20))  # mild, moderate, severe, life_threatening
    reaction_description = Column(Text)
    onset_date = Column(Date)
    status = Column(String(20), default='active')  # active, inactive, resolved
    entered_by = Column(Integer)  # physician_id
    entry_date = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    patient = relationship("Patient", back_populates="allergies")
    allergen = relationship("DrugAllergen", back_populates="patient_allergies")

class Physician(Base):
    __tablename__ = "physicians"
    
    physician_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    license_number = Column(String(50), unique=True)
    specialty = Column(String(100))
    dea_number = Column(String(20))
    phone = Column(String(15))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    prescriptions = relationship("Prescription", back_populates="physician")

class Prescription(Base):
    __tablename__ = "prescriptions"
    
    prescription_id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.patient_id"), nullable=False)
    physician_id = Column(Integer, ForeignKey("physicians.physician_id"), nullable=False)
    drug_id = Column(Integer, ForeignKey("drugs.drug_id"), nullable=False)
    quantity = Column(DECIMAL(10, 2))
    quantity_unit = Column(String(20))  # tablets, ml, mg
    dosage_instructions = Column(Text)
    refills_allowed = Column(Integer, default=0)
    days_supply = Column(Integer)
    prescribed_date = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(20), default='active')  # active, filled, cancelled
    allergy_checked = Column(Boolean, default=False)
    interaction_checked = Column(Boolean, default=False)
    
    # Relationships
    patient = relationship("Patient", back_populates="prescriptions")
    physician = relationship("Physician", back_populates="prescriptions")
    drug = relationship("Drug", back_populates="prescriptions")
    alerts = relationship("AllergyAlert", back_populates="prescription")

class AllergyAlert(Base):
    __tablename__ = "allergy_alerts"
    
    alert_id = Column(Integer, primary_key=True, index=True)
    prescription_id = Column(Integer, ForeignKey("prescriptions.prescription_id"))
    patient_id = Column(Integer, ForeignKey("patients.patient_id"), nullable=False)
    allergen_id = Column(Integer, ForeignKey("drug_allergens.allergen_id"))
    alert_level = Column(String(20))  # warning, contraindication, caution
    alert_message = Column(Text)
    override_reason = Column(Text)
    overridden_by = Column(Integer)  # physician_id
    override_timestamp = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    prescription = relationship("Prescription", back_populates="alerts")
    patient = relationship("Patient")
    allergen = relationship("DrugAllergen")

class CrossSensitivityGroup(Base):
    __tablename__ = "cross_sensitivity_groups"
    
    group_id = Column(Integer, primary_key=True, index=True)
    group_name = Column(String(100), nullable=False)  # beta_lactams, sulfonamides, etc.
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AllergenCrossSensitivity(Base):
    __tablename__ = "allergen_cross_sensitivity"
    
    allergen_id = Column(Integer, ForeignKey("drug_allergens.allergen_id"), primary_key=True)
    group_id = Column(Integer, ForeignKey("cross_sensitivity_groups.group_id"), primary_key=True)
