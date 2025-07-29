"""
LangGraph-based AI agent for medical reasoning and prescription analysis
"""

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from typing import TypedDict, List, Dict, Any, Optional
import logging
from groq_client import GroqClient
from schemas import AIAnalysis
from models import DrugAllergen

logger = logging.getLogger(__name__)

class MedicalAnalysisState(TypedDict):
    patient_info: Dict[str, Any]
    drug_info: Dict[str, Any]
    patient_allergies: List[Dict[str, Any]]
    analysis_result: Dict[str, Any]
    messages: List[HumanMessage | AIMessage]
    current_step: str
    error: Optional[str]

class MedicalAIAgent:
    def __init__(self):
        self.groq_client = GroqClient()
        self.workflow = self._build_workflow()
        
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for medical analysis"""
        
        workflow = StateGraph(MedicalAnalysisState)
        
        # Add nodes
        workflow.add_node("initialize", self._initialize_analysis)
        workflow.add_node("analyze_direct_allergies", self._analyze_direct_allergies)
        workflow.add_node("analyze_cross_reactivity", self._analyze_cross_reactivity)
        workflow.add_node("generate_recommendations", self._generate_recommendations)
        workflow.add_node("finalize_analysis", self._finalize_analysis)
        
        # Define the flow
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "analyze_direct_allergies")
        workflow.add_edge("analyze_direct_allergies", "analyze_cross_reactivity")
        workflow.add_edge("analyze_cross_reactivity", "generate_recommendations")
        workflow.add_edge("generate_recommendations", "finalize_analysis")
        workflow.add_edge("finalize_analysis", END)
        
        return workflow.compile()
    
    async def _initialize_analysis(self, state: MedicalAnalysisState) -> MedicalAnalysisState:
        """Initialize the medical analysis process"""
        logger.info("Initializing medical analysis")
        
        state["current_step"] = "initialization"
        state["analysis_result"] = {
            "direct_allergies": [],
            "cross_reactivity": {},
            "recommendations": [],
            "risk_level": "low"
        }
        
        return state
    
    async def _analyze_direct_allergies(self, state: MedicalAnalysisState) -> MedicalAnalysisState:
        """Analyze for direct allergy matches"""
        logger.info("Analyzing direct allergies")
        
        state["current_step"] = "direct_allergy_analysis"
        
        try:
            drug_name = state["drug_info"].get("drug_name", "")
            active_ingredient = state["drug_info"].get("active_ingredient", "")
            
            direct_matches = []
            for allergy in state["patient_allergies"]:
                allergen_name = allergy.get("allergen_name", "").lower()
                
                # Check for direct matches
                if (allergen_name in drug_name.lower() or 
                    allergen_name in active_ingredient.lower()):
                    direct_matches.append({
                        "allergen": allergen_name,
                        "severity": allergy.get("severity", "unknown"),
                        "reaction": allergy.get("reaction_description", ""),
                        "match_type": "direct"
                    })
            
            state["analysis_result"]["direct_allergies"] = direct_matches
            
        except Exception as e:
            logger.error(f"Error in direct allergy analysis: {str(e)}")
            state["error"] = str(e)
        
        return state
    
    async def _analyze_cross_reactivity(self, state: MedicalAnalysisState) -> MedicalAnalysisState:
        """Analyze for cross-reactivity using AI"""
        logger.info("Analyzing cross-reactivity")
        
        state["current_step"] = "cross_reactivity_analysis"
        
        try:
            # Use Groq for sophisticated cross-reactivity analysis
            cross_reactivity_result = await self.groq_client.analyze_cross_reactivity(
                state["patient_allergies"],
                state["drug_info"]
            )
            
            state["analysis_result"]["cross_reactivity"] = cross_reactivity_result
            
            # Update risk level based on findings
            if cross_reactivity_result.get("has_cross_reactivity"):
                current_risk = state["analysis_result"]["risk_level"]
                new_risk = cross_reactivity_result.get("risk_level", "medium")
                
                # Take the higher risk level
                risk_hierarchy = {"low": 1, "medium": 2, "high": 3, "critical": 4}
                if risk_hierarchy.get(new_risk, 1) > risk_hierarchy.get(current_risk, 1):
                    state["analysis_result"]["risk_level"] = new_risk
            
        except Exception as e:
            logger.error(f"Error in cross-reactivity analysis: {str(e)}")
            state["error"] = str(e)
        
        return state
    
    async def _generate_recommendations(self, state: MedicalAnalysisState) -> MedicalAnalysisState:
        """Generate medical recommendations based on analysis"""
        logger.info("Generating recommendations")
        
        state["current_step"] = "recommendation_generation"
        
        try:
            recommendations = []
            
            # Recommendations based on direct allergies
            if state["analysis_result"]["direct_allergies"]:
                for allergy in state["analysis_result"]["direct_allergies"]:
                    if allergy["severity"] in ["severe", "life_threatening"]:
                        recommendations.append(
                            f"CONTRAINDICATION: Avoid {state['drug_info']['drug_name']} due to {allergy['severity']} allergy to {allergy['allergen']}"
                        )
                    else:
                        recommendations.append(
                            f"CAUTION: Monitor patient for allergic reactions to {allergy['allergen']}"
                        )
            
            # Recommendations based on cross-reactivity
            cross_reactivity = state["analysis_result"]["cross_reactivity"]
            if cross_reactivity.get("has_cross_reactivity"):
                recommendations.extend(cross_reactivity.get("recommendations", []))
            
            # General recommendations
            if not recommendations:
                recommendations.append("No specific allergy concerns identified. Monitor patient for any adverse reactions.")
            
            state["analysis_result"]["recommendations"] = recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            state["error"] = str(e)
        
        return state
    
    async def _finalize_analysis(self, state: MedicalAnalysisState) -> MedicalAnalysisState:
        """Finalize the analysis and prepare results"""
        logger.info("Finalizing analysis")
        
        state["current_step"] = "finalization"
        
        # Ensure we have a complete analysis
        if "analysis_result" not in state:
            state["analysis_result"] = {
                "direct_allergies": [],
                "cross_reactivity": {"has_cross_reactivity": False},
                "recommendations": ["Analysis incomplete - manual review required"],
                "risk_level": "medium"
            }
        
        return state
    
    async def analyze_cross_reactivity(self, patient_allergies: List, drug, db) -> Dict[str, Any]:
        """
        Public method to analyze cross-reactivity for a specific drug
        """
        try:
            # Prepare allergy data
            allergy_data = []
            for allergy in patient_allergies:
                allergen = db.query(DrugAllergen).filter(
                    DrugAllergen.allergen_id == allergy.allergen_id
                ).first()
                
                if allergen:
                    allergy_data.append({
                        "allergen_name": allergen.allergen_name,
                        "severity": allergy.severity,
                        "reaction_description": allergy.reaction_description,
                        "cross_sensitivity_group": allergen.cross_sensitivity_group
                    })
            
            # Prepare drug data
            drug_data = {
                "drug_name": drug.drug_name,
                "generic_name": drug.generic_name,
                "active_ingredient": drug.active_ingredient,
                "drug_class": getattr(drug, 'drug_class', 'Unknown')
            }
            
            # Initialize state for analysis
            initial_state = MedicalAnalysisState(
                patient_info={},
                drug_info=drug_data,
                patient_allergies=allergy_data,
                analysis_result={},
                messages=[],
                current_step="",
                error=None
            )
            
            # Run the workflow
            result = await self.workflow.ainvoke(initial_state)
            
            return result.get("analysis_result", {}).get("cross_reactivity", {
                "has_cross_reactivity": False,
                "confidence": "low",
                "explanation": "Analysis could not be completed"
            })
            
        except Exception as e:
            logger.error(f"Error in analyze_cross_reactivity: {str(e)}")
            return {
                "has_cross_reactivity": False,
                "confidence": "low",
                "explanation": f"Error during analysis: {str(e)}"
            }
    
    async def generate_summary(
        self, 
        patient, 
        medicines: List[str], 
        warnings: List, 
        contraindications: List
    ) -> AIAnalysis:
        """
        Generate a comprehensive summary using Groq AI
        """
        try:
            patient_info = {
                "name": f"{patient.first_name} {patient.last_name}",
                "patient_id": patient.patient_id
            }
            
            logger.info(f"Generating AI summary for {len(medicines)} medicines, {len(warnings)} warnings, {len(contraindications)} contraindications")
            
            summary_result = await self.groq_client.generate_prescription_summary(
                patient_info, medicines, warnings, contraindications
            )
            
            # Ensure we always return a meaningful analysis
            summary = summary_result.get("summary")
            if not summary or len(summary.strip()) < 10:
                if len(contraindications) > 0:
                    summary = f"Critical allergy conflicts detected for {len(contraindications)} medicine(s). Immediate review required."
                elif len(warnings) > 0:
                    summary = f"Prescription contains {len(warnings)} warning(s) that require attention. Overall assessment suggests caution."
                else:
                    summary = f"All {len(medicines)} prescribed medicine(s) appear safe for this patient based on known allergy profile."
            
            recommendations = summary_result.get("recommendations", [])
            if not recommendations:
                if len(contraindications) > 0:
                    recommendations = ["DO NOT ADMINISTER contraindicated medicines", "Find alternative medications", "Consult with allergist"]
                elif len(warnings) > 0:
                    recommendations = ["Monitor patient closely", "Consider alternative medications if available", "Have emergency protocols ready"]
                else:
                    recommendations = ["Proceed with prescription as planned", "Monitor for any unexpected reactions"]
            
            return AIAnalysis(
                summary=summary,
                recommendations=recommendations,
                risk_level=summary_result.get("risk_level", "low" if len(contraindications) == 0 and len(warnings) == 0 else "medium")
            )
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return AIAnalysis(
                summary=f"Analysis completed with errors: {str(e)}",
                recommendations=["Manual review recommended due to system error"],
                risk_level="medium"
            )
