"""
Sample data population for testing and demonstration
"""

from sqlalchemy.orm import Session
from models import (
    Patient, Drug, DrugAllergen, DrugAllergenMapping, 
    PatientAllergy, Physician, CrossSensitivityGroup
)
from datetime import date, datetime
import logging

logger = logging.getLogger(__name__)

def populate_sample_data(db: Session):
    """
    Populate the database with realistic medical sample data
    """
    try:
        logger.info("Starting sample data population...")
        
        # Create physicians
        physicians = [
            Physician(
                first_name="Dr. Sarah",
                last_name="Johnson",
                license_number="MD123456",
                specialty="Internal Medicine",
                dea_number="BJ1234567",
                phone="555-0101"
            ),
            Physician(
                first_name="Dr. Michael",
                last_name="Chen",
                license_number="MD789012",
                specialty="Cardiology",
                dea_number="BC7890123",
                phone="555-0102"
            ),
            Physician(
                first_name="Dr. Emily",
                last_name="Rodriguez",
                license_number="MD345678",
                specialty="Family Medicine",
                dea_number="BR3456789",
                phone="555-0103"
            )
        ]
        
        for physician in physicians:
            db.add(physician)
        db.commit()
        
        # Create cross-sensitivity groups
        cross_sensitivity_groups = [
            CrossSensitivityGroup(
                group_name="beta_lactams",
                description="Beta-lactam antibiotics including penicillins, cephalosporins, and carbapenems"
            ),
            CrossSensitivityGroup(
                group_name="sulfonamides",
                description="Sulfonamide-containing medications"
            ),
            CrossSensitivityGroup(
                group_name="nsaids",
                description="Non-steroidal anti-inflammatory drugs"
            ),
            CrossSensitivityGroup(
                group_name="opioids",
                description="Opioid pain medications"
            ),
            CrossSensitivityGroup(
                group_name="macrolides",
                description="Macrolide antibiotics"
            )
        ]
        
        for group in cross_sensitivity_groups:
            db.add(group)
        db.commit()
        
        # Create drug allergens
        drug_allergens = [
            DrugAllergen(
                allergen_name="Penicillin",
                allergen_type="active_ingredient",
                cross_sensitivity_group="beta_lactams",
                description="Beta-lactam antibiotic allergen"
            ),
            DrugAllergen(
                allergen_name="Amoxicillin",
                allergen_type="active_ingredient",
                cross_sensitivity_group="beta_lactams",
                description="Penicillin-type antibiotic"
            ),
            DrugAllergen(
                allergen_name="Cephalexin",
                allergen_type="active_ingredient",
                cross_sensitivity_group="beta_lactams",
                description="First-generation cephalosporin"
            ),
            DrugAllergen(
                allergen_name="Sulfonamides",
                allergen_type="drug_class",
                cross_sensitivity_group="sulfonamides",
                description="Sulfonamide antibiotics"
            ),
            DrugAllergen(
                allergen_name="Aspirin",
                allergen_type="active_ingredient",
                cross_sensitivity_group="nsaids",
                description="Salicylate NSAID"
            ),
            DrugAllergen(
                allergen_name="Ibuprofen",
                allergen_type="active_ingredient",
                cross_sensitivity_group="nsaids",
                description="Propionic acid NSAID"
            ),
            DrugAllergen(
                allergen_name="Morphine",
                allergen_type="active_ingredient",
                cross_sensitivity_group="opioids",
                description="Opioid analgesic"
            ),
            DrugAllergen(
                allergen_name="Codeine",
                allergen_type="active_ingredient",
                cross_sensitivity_group="opioids",
                description="Opioid analgesic"
            ),
            DrugAllergen(
                allergen_name="Erythromycin",
                allergen_type="active_ingredient",
                cross_sensitivity_group="macrolides",
                description="Macrolide antibiotic"
            ),
            DrugAllergen(
                allergen_name="Latex",
                allergen_type="inactive_ingredient",
                cross_sensitivity_group=None,
                description="Natural rubber latex"
            )
        ]
        
        for allergen in drug_allergens:
            db.add(allergen)
        db.commit()
        
        # Create drugs
        drugs = [
            Drug(
                drug_name="Amoxicillin 500mg",
                generic_name="Amoxicillin",
                active_ingredient="Amoxicillin",
                strength="500mg",
                dosage_form="capsule",
                route="oral",
                manufacturer="Generic Pharma",
                ndc_number="12345-678-90"
            ),
            Drug(
                drug_name="Penicillin V 250mg",
                generic_name="Penicillin V",
                active_ingredient="Penicillin V",
                strength="250mg",
                dosage_form="tablet",
                route="oral",
                manufacturer="Beta Pharma",
                ndc_number="23456-789-01"
            ),
            Drug(
                drug_name="Cephalexin 500mg",
                generic_name="Cephalexin",
                active_ingredient="Cephalexin",
                strength="500mg",
                dosage_form="capsule",
                route="oral",
                manufacturer="Ceph Pharma",
                ndc_number="34567-890-12"
            ),
            Drug(
                drug_name="Bactrim DS",
                generic_name="Sulfamethoxazole/Trimethoprim",
                active_ingredient="Sulfamethoxazole",
                strength="800mg/160mg",
                dosage_form="tablet",
                route="oral",
                manufacturer="Sulfa Pharma",
                ndc_number="45678-901-23"
            ),
            Drug(
                drug_name="Aspirin 325mg",
                generic_name="Aspirin",
                active_ingredient="Acetylsalicylic acid",
                strength="325mg",
                dosage_form="tablet",
                route="oral",
                manufacturer="Pain Relief Inc",
                ndc_number="56789-012-34"
            ),
            Drug(
                drug_name="Ibuprofen 200mg",
                generic_name="Ibuprofen",
                active_ingredient="Ibuprofen",
                strength="200mg",
                dosage_form="tablet",
                route="oral",
                manufacturer="NSAID Corp",
                ndc_number="67890-123-45"
            ),
            Drug(
                drug_name="Morphine 10mg",
                generic_name="Morphine Sulfate",
                active_ingredient="Morphine",
                strength="10mg",
                dosage_form="tablet",
                route="oral",
                manufacturer="Opioid Pharma",
                ndc_number="78901-234-56"
            ),
            Drug(
                drug_name="Tylenol with Codeine #3",
                generic_name="Acetaminophen/Codeine",
                active_ingredient="Codeine",
                strength="30mg/300mg",
                dosage_form="tablet",
                route="oral",
                manufacturer="Pain Solutions",
                ndc_number="89012-345-67"
            ),
            Drug(
                drug_name="Erythromycin 250mg",
                generic_name="Erythromycin",
                active_ingredient="Erythromycin",
                strength="250mg",
                dosage_form="tablet",
                route="oral",
                manufacturer="Macro Pharma",
                ndc_number="90123-456-78"
            ),
            Drug(
                drug_name="Lisinopril 10mg",
                generic_name="Lisinopril",
                active_ingredient="Lisinopril",
                strength="10mg",
                dosage_form="tablet",
                route="oral",
                manufacturer="ACE Pharma",
                ndc_number="01234-567-89"
            ),
            # Add common Indian medicines
            Drug(
                drug_name="Dolo 650",
                generic_name="Paracetamol",
                active_ingredient="Paracetamol",
                strength="650mg",
                dosage_form="tablet",
                route="oral",
                manufacturer="Micro Labs",
                ndc_number="DOLO-650-01"
            ),
            Drug(
                drug_name="Paracetamol 500mg",
                generic_name="Paracetamol",
                active_ingredient="Paracetamol",
                strength="500mg",
                dosage_form="tablet",
                route="oral",
                manufacturer="Generic Pharma",
                ndc_number="PARA-500-01"
            ),
            Drug(
                drug_name="Crocin 650",
                generic_name="Paracetamol",
                active_ingredient="Paracetamol",
                strength="650mg",
                dosage_form="tablet",
                route="oral",
                manufacturer="GSK",
                ndc_number="CROC-650-01"
            ),
            Drug(
                drug_name="Azithromycin 500mg",
                generic_name="Azithromycin",
                active_ingredient="Azithromycin",
                strength="500mg",
                dosage_form="tablet",
                route="oral",
                manufacturer="Macrolide Pharma",
                ndc_number="AZITH-500-01"
            ),
            Drug(
                drug_name="Ciprofloxacin 500mg",
                generic_name="Ciprofloxacin",
                active_ingredient="Ciprofloxacin",
                strength="500mg",
                dosage_form="tablet",
                route="oral",
                manufacturer="Quinolone Pharma",
                ndc_number="CIPRO-500-01"
            ),
            # Add more common medicines
            Drug(
                drug_name="Aspirin 325mg",
                generic_name="Aspirin",
                active_ingredient="Acetylsalicylic acid",
                strength="325mg",
                dosage_form="tablet",
                route="oral",
                manufacturer="Generic Pharma",
                ndc_number="ASP-325-01"
            ),
            Drug(
                drug_name="Ibuprofen 400mg",
                generic_name="Ibuprofen",
                active_ingredient="Ibuprofen",
                strength="400mg",
                dosage_form="tablet",
                route="oral",
                manufacturer="NSAID Pharma",
                ndc_number="IBU-400-01"
            ),
            Drug(
                drug_name="Metformin 500mg",
                generic_name="Metformin",
                active_ingredient="Metformin hydrochloride",
                strength="500mg",
                dosage_form="tablet",
                route="oral",
                manufacturer="Diabetes Care",
                ndc_number="MET-500-01"
            ),
            Drug(
                drug_name="Omeprazole 20mg",
                generic_name="Omeprazole",
                active_ingredient="Omeprazole",
                strength="20mg",
                dosage_form="capsule",
                route="oral",
                manufacturer="PPI Pharma",
                ndc_number="OME-20-01"
            )
        ]
        
        for drug in drugs:
            db.add(drug)
        db.commit()
        
        # Create drug-allergen mappings
        drug_allergen_mappings = [
            # Amoxicillin maps to both Amoxicillin and Penicillin allergens
            (1, 1),  # Amoxicillin -> Penicillin
            (1, 2),  # Amoxicillin -> Amoxicillin
            # Penicillin V maps to Penicillin allergen
            (2, 1),  # Penicillin V -> Penicillin
            # Cephalexin maps to Cephalexin allergen
            (3, 3),  # Cephalexin -> Cephalexin
            # Bactrim maps to Sulfonamides
            (4, 4),  # Bactrim -> Sulfonamides
            # Aspirin maps to Aspirin allergen
            (5, 5),  # Aspirin -> Aspirin
            # Ibuprofen maps to Ibuprofen allergen
            (6, 6),  # Ibuprofen -> Ibuprofen
            # Morphine maps to Morphine allergen
            (7, 7),  # Morphine -> Morphine
            # Tylenol with Codeine maps to Codeine allergen
            (8, 8),  # Tylenol with Codeine -> Codeine
            # Erythromycin maps to Erythromycin allergen
            (9, 9),  # Erythromycin -> Erythromycin
        ]
        
        for drug_id, allergen_id in drug_allergen_mappings:
            mapping = DrugAllergenMapping(drug_id=drug_id, allergen_id=allergen_id)
            db.add(mapping)
        db.commit()
        
        # Create patients
        patients = [
            Patient(
                first_name="John",
                last_name="Smith",
                date_of_birth=date(1980, 5, 15),
                ssn="123-45-6789",
                phone="555-1234",
                address="123 Main St, Anytown, USA",
                insurance_id="INS123456"
            ),
            Patient(
                first_name="Mary",
                last_name="Johnson",
                date_of_birth=date(1975, 8, 22),
                ssn="234-56-7890",
                phone="555-2345",
                address="456 Oak Ave, Somewhere, USA",
                insurance_id="INS234567"
            ),
            Patient(
                first_name="Robert",
                last_name="Davis",
                date_of_birth=date(1990, 12, 3),
                ssn="345-67-8901",
                phone="555-3456",
                address="789 Pine Rd, Elsewhere, USA",
                insurance_id="INS345678"
            ),
            Patient(
                first_name="Lisa",
                last_name="Wilson",
                date_of_birth=date(1985, 3, 18),
                ssn="456-78-9012",
                phone="555-4567",
                address="321 Elm St, Nowhere, USA",
                insurance_id="INS456789"
            ),
            Patient(
                first_name="David",
                last_name="Brown",
                date_of_birth=date(1972, 9, 7),
                ssn="567-89-0123",
                phone="555-5678",
                address="654 Maple Dr, Anywhere, USA",
                insurance_id="INS567890"
            )
        ]
        
        for patient in patients:
            db.add(patient)
        db.commit()
        
        # Create patient allergies
        patient_allergies = [
            # John Smith - Penicillin allergy (severe)
            PatientAllergy(
                patient_id=1,
                allergen_id=1,  # Penicillin
                allergy_type="drug",
                severity="severe",
                reaction_description="Severe rash, difficulty breathing",
                onset_date=date(2010, 6, 15),
                status="active",
                entered_by=1
            ),
            # Mary Johnson - Aspirin allergy (moderate)
            PatientAllergy(
                patient_id=2,
                allergen_id=5,  # Aspirin
                allergy_type="drug",
                severity="moderate",
                reaction_description="Stomach upset, nausea",
                onset_date=date(2015, 3, 22),
                status="active",
                entered_by=1
            ),
            # Robert Davis - Sulfonamide allergy (mild)
            PatientAllergy(
                patient_id=3,
                allergen_id=4,  # Sulfonamides
                allergy_type="drug",
                severity="mild",
                reaction_description="Skin rash",
                onset_date=date(2020, 8, 10),
                status="active",
                entered_by=2
            ),
            # Lisa Wilson - Morphine allergy (severe)
            PatientAllergy(
                patient_id=4,
                allergen_id=7,  # Morphine
                allergy_type="drug",
                severity="severe",
                reaction_description="Respiratory depression, hives",
                onset_date=date(2018, 11, 5),
                status="active",
                entered_by=3
            ),
            # David Brown - Latex allergy (moderate)
            PatientAllergy(
                patient_id=5,
                allergen_id=10,  # Latex
                allergy_type="environmental",
                severity="moderate",
                reaction_description="Contact dermatitis, itching",
                onset_date=date(2012, 4, 18),
                status="active",
                entered_by=1
            )
        ]
        
        for allergy in patient_allergies:
            db.add(allergy)
        db.commit()
        
        logger.info("Sample data population completed successfully!")
        logger.info(f"Created {len(physicians)} physicians")
        logger.info(f"Created {len(cross_sensitivity_groups)} cross-sensitivity groups")
        logger.info(f"Created {len(drug_allergens)} drug allergens")
        logger.info(f"Created {len(drugs)} drugs")
        logger.info(f"Created {len(drug_allergen_mappings)} drug-allergen mappings")
        logger.info(f"Created {len(patients)} patients")
        logger.info(f"Created {len(patient_allergies)} patient allergies")
        
    except Exception as e:
        logger.error(f"Error populating sample data: {str(e)}")
        db.rollback()
        raise e
