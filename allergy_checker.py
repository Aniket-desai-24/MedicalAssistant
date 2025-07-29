"""
Direct allergy checking and database utilities
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from models import DrugAllergen, DrugAllergenMapping, PatientAllergy
import logging

logger = logging.getLogger(__name__)

class AllergyChecker:
    def __init__(self):
        pass
    
    def check_direct_allergies(
        self, 
        patient_allergies: List[PatientAllergy], 
        drug, 
        db: Session
    ) -> List[Dict[str, Any]]:
        """
        Check for direct allergy conflicts between patient allergies and prescribed drug
        
        Args:
            patient_allergies: List of PatientAllergy objects
            drug: Drug object to check against
            db: Database session
            
        Returns:
            List of direct allergy conflicts
        """
        conflicts = []
        
        try:
            # Get all allergens associated with this drug
            drug_allergens = db.query(DrugAllergenMapping).filter(
                DrugAllergenMapping.drug_id == drug.drug_id
            ).all()
            
            drug_allergen_ids = [mapping.allergen_id for mapping in drug_allergens]
            
            # Check each patient allergy against drug allergens
            for patient_allergy in patient_allergies:
                if patient_allergy.allergen_id in drug_allergen_ids:
                    # Direct match found
                    allergen = db.query(DrugAllergen).filter(
                        DrugAllergen.allergen_id == patient_allergy.allergen_id
                    ).first()
                    
                    if allergen:
                        conflicts.append({
                            "allergen_id": allergen.allergen_id,
                            "allergen_name": allergen.allergen_name,
                            "allergen_type": allergen.allergen_type,
                            "severity": patient_allergy.severity,
                            "reaction_description": patient_allergy.reaction_description,
                            "conflict_type": "direct",
                            "cross_sensitivity_group": allergen.cross_sensitivity_group
                        })
            
            # Check for cross-sensitivity within groups
            cross_sensitivity_conflicts = self._check_cross_sensitivity(
                patient_allergies, drug_allergen_ids, db
            )
            conflicts.extend(cross_sensitivity_conflicts)
            
            logger.info(f"Found {len(conflicts)} direct allergy conflicts for drug {drug.drug_name}")
            
        except Exception as e:
            logger.error(f"Error checking direct allergies: {str(e)}")
        
        return conflicts
    
    def _check_cross_sensitivity(
        self, 
        patient_allergies: List[PatientAllergy], 
        drug_allergen_ids: List[int], 
        db: Session
    ) -> List[Dict[str, Any]]:
        """
        Check for cross-sensitivity conflicts based on allergen groups
        """
        conflicts = []
        
        try:
            # Get cross-sensitivity groups for patient allergies
            patient_groups = set()
            for allergy in patient_allergies:
                allergen = db.query(DrugAllergen).filter(
                    DrugAllergen.allergen_id == allergy.allergen_id
                ).first()
                
                if allergen and allergen.cross_sensitivity_group:
                    patient_groups.add(allergen.cross_sensitivity_group)
            
            # Get cross-sensitivity groups for drug allergens
            drug_groups = set()
            for allergen_id in drug_allergen_ids:
                allergen = db.query(DrugAllergen).filter(
                    DrugAllergen.allergen_id == allergen_id
                ).first()
                
                if allergen and allergen.cross_sensitivity_group:
                    drug_groups.add(allergen.cross_sensitivity_group)
            
            # Find overlapping groups
            overlapping_groups = patient_groups.intersection(drug_groups)
            
            for group in overlapping_groups:
                # Find the specific allergens in this group
                for allergy in patient_allergies:
                    allergen = db.query(DrugAllergen).filter(
                        DrugAllergen.allergen_id == allergy.allergen_id
                    ).first()
                    
                    if allergen and allergen.cross_sensitivity_group == group:
                        conflicts.append({
                            "allergen_id": allergen.allergen_id,
                            "allergen_name": allergen.allergen_name,
                            "allergen_type": allergen.allergen_type,
                            "severity": allergy.severity,
                            "reaction_description": allergy.reaction_description,
                            "conflict_type": "cross_sensitivity",
                            "cross_sensitivity_group": group
                        })
            
        except Exception as e:
            logger.error(f"Error checking cross-sensitivity: {str(e)}")
        
        return conflicts
    
    def get_allergen_by_name(self, allergen_name: str, db: Session) -> DrugAllergen:
        """
        Find allergen by name (case-insensitive)
        """
        return db.query(DrugAllergen).filter(
            DrugAllergen.allergen_name.ilike(f"%{allergen_name}%")
        ).first()
    
    def create_allergen_if_not_exists(
        self, 
        allergen_name: str, 
        allergen_type: str = "drug", 
        cross_sensitivity_group: str = None,
        db: Session = None
    ) -> DrugAllergen:
        """
        Create a new allergen if it doesn't exist
        """
        existing = self.get_allergen_by_name(allergen_name, db)
        if existing:
            return existing
        
        new_allergen = DrugAllergen(
            allergen_name=allergen_name,
            allergen_type=allergen_type,
            cross_sensitivity_group=cross_sensitivity_group
        )
        
        db.add(new_allergen)
        db.commit()
        db.refresh(new_allergen)
        
        return new_allergen
    
    def map_drug_to_allergen(self, drug_id: int, allergen_id: int, db: Session):
        """
        Create mapping between drug and allergen
        """
        existing_mapping = db.query(DrugAllergenMapping).filter(
            DrugAllergenMapping.drug_id == drug_id,
            DrugAllergenMapping.allergen_id == allergen_id
        ).first()
        
        if not existing_mapping:
            mapping = DrugAllergenMapping(
                drug_id=drug_id,
                allergen_id=allergen_id
            )
            db.add(mapping)
            db.commit()
