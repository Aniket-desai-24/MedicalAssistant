"""
Groq API client for fast LLM inference
"""

import os
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Dict, Any, List
import json
import logging

logger = logging.getLogger(__name__)


class GroqClient:

    def __init__(self):
        self.api_key = os.getenv(
            "GROQ_API_KEY",
            "your_groq_api_key_here"  # Replace with your actual Groq API key
        )  # Replace with your actual Groq API key
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.1,  # Low temperature for medical accuracy
            max_tokens=2048,
            groq_api_key=self.api_key)

    async def analyze_cross_reactivity(self,
                                       patient_allergies: List[Dict],
                                       drug_info: Dict,
                                       context: str = "") -> Dict[str, Any]:
        """
        Analyze potential cross-reactivity between patient allergies and prescribed drug
        """
        try:
            system_prompt = """You are a medical AI assistant specializing in drug allergy analysis and cross-reactivity detection.

Your task is to analyze potential cross-reactivity between a patient's known allergies and a prescribed medication.

Key principles:
1. Beta-lactam antibiotics (penicillins, cephalosporins, carbapenems) have cross-reactivity
2. Sulfonamide antibiotics may cross-react with sulfonamide diuretics
3. NSAIDs may have cross-reactivity within the class
4. Consider chemical structure similarities
5. Evaluate severity levels carefully

Respond in JSON format with:
{
    "has_cross_reactivity": boolean,
    "confidence": "low|medium|high",
    "explanation": "detailed explanation",
    "risk_level": "low|medium|high|critical",
    "recommendations": ["list of recommendations"]
}"""

            allergy_info = []
            for allergy in patient_allergies:
                allergy_info.append({
                    "allergen":
                    allergy.get('allergen_name', 'Unknown'),
                    "severity":
                    allergy.get('severity', 'Unknown'),
                    "reaction":
                    allergy.get('reaction_description', 'Not specified')
                })

            human_prompt = f"""
Patient Allergies:
{json.dumps(allergy_info, indent=2)}

Prescribed Drug:
- Name: {drug_info.get('drug_name', 'Unknown')}
- Generic: {drug_info.get('generic_name', 'Unknown')}
- Active Ingredient: {drug_info.get('active_ingredient', 'Unknown')}
- Drug Class: {drug_info.get('drug_class', 'Unknown')}

Additional Context: {context}

Analyze for potential cross-reactivity and provide your assessment."""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ]

            response = await self.llm.ainvoke(messages)

            # Parse JSON response
            try:
                result = json.loads(response.content)
                return result
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    "has_cross_reactivity": False,
                    "confidence": "low",
                    "explanation": "Unable to parse AI response",
                    "risk_level": "low",
                    "recommendations": ["Manual review recommended"]
                }

        except Exception as e:
            logger.error(f"Error in cross-reactivity analysis: {str(e)}")
            return {
                "has_cross_reactivity": False,
                "confidence": "low",
                "explanation": f"Analysis error: {str(e)}",
                "risk_level": "low",
                "recommendations":
                ["Manual review required due to system error"]
            }

    async def generate_prescription_summary(
            self, patient_info: Dict, medicines: List[str],
            warnings: List[Dict],
            contraindications: List[Dict]) -> Dict[str, Any]:
        """
        Generate a comprehensive summary and recommendations for the prescription
        """
        try:
            system_prompt = """You are a medical AI assistant providing prescription safety summaries.

Generate a comprehensive analysis including:
1. Overall risk assessment
2. Specific recommendations for each concern
3. Alternative medication suggestions if needed
4. Monitoring recommendations

Respond in JSON format with:
{
    "summary": "comprehensive summary",
    "recommendations": ["list of specific recommendations"],
    "risk_level": "low|medium|high|critical"
}"""

            # Convert warning and contraindication objects to dictionaries
            warnings_data = []
            if warnings:
                for w in warnings:
                    if hasattr(w, '__dict__'):
                        warnings_data.append(w.__dict__)
                    else:
                        warnings_data.append(w)

            contraindications_data = []
            if contraindications:
                for c in contraindications:
                    if hasattr(c, '__dict__'):
                        contraindications_data.append(c.__dict__)
                    else:
                        contraindications_data.append(c)

            # Create better formatted context
            medicines_list = '\n'.join([f"• {med}" for med in medicines])

            warnings_text = "None identified"
            if warnings_data:
                warnings_text = '\n'.join([
                    f"• {w.get('medicine', 'Medicine')}: {w.get('reason', 'Warning detected')}"
                    for w in warnings_data
                ])

            contraindications_text = "None identified"
            if contraindications_data:
                contraindications_text = '\n'.join([
                    f"• {c.get('medicine', 'Medicine')}: {c.get('reason', 'Contraindication detected')}"
                    for c in contraindications_data
                ])

            human_prompt = f"""
PATIENT: {patient_info.get('name', 'Unknown Patient')}

PRESCRIBED MEDICINES:
{medicines_list}

SAFETY ANALYSIS RESULTS:
Warnings ({len(warnings_data)}):
{warnings_text}

Contraindications ({len(contraindications_data)}):
{contraindications_text}

REQUIREMENTS:
• Always mention each prescribed medicine by name in the summary
• Provide specific details about each medicine's safety profile and use
• Give practical, actionable recommendations
• Set appropriate risk level: low (no issues), medium (warnings), high (contraindications)
• Even with no issues, provide substantive medical guidance about the medicines

Provide comprehensive analysis in the specified JSON format."""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ]

            response = await self.llm.ainvoke(messages)

            try:
                result = json.loads(response.content)
                return result
            except json.JSONDecodeError:
                # Create a more informative fallback based on actual data
                fallback_summary = f"Analysis completed for {len(medicines)} medicine(s): {', '.join(medicines)}. "
                if contraindications_data:
                    fallback_summary += "Critical contraindications found - immediate review required."
                    risk_level = "high"
                    recommendations = [
                        "DO NOT ADMINISTER contraindicated medicines",
                        "Find alternative medications", "Consult specialist"
                    ]
                elif warnings_data:
                    fallback_summary += "Warnings detected - careful monitoring recommended."
                    risk_level = "medium"
                    recommendations = [
                        "Monitor patient closely",
                        "Watch for adverse reactions",
                        "Consider alternatives if issues arise"
                    ]
                else:
                    fallback_summary += "No critical issues detected based on available allergy information."
                    risk_level = "low"
                    recommendations = [
                        "Proceed as prescribed",
                        "Monitor for unexpected reactions",
                        "Follow standard dosing guidelines"
                    ]

                return {
                    "summary": fallback_summary,
                    "recommendations": recommendations,
                    "risk_level": risk_level
                }

        except Exception as e:
            logger.error(f"Error generating prescription summary: {str(e)}")
            return {
                "summary": f"Analysis error: {str(e)}",
                "recommendations":
                ["Manual review required due to system error"],
                "risk_level": "medium"
            }

    async def analyze_drug_ingredients(
            self,
            drug_name: str,
            active_ingredient: str = None) -> Dict[str, Any]:
        """
        Analyze drug ingredients and classify the medication
        """
        try:
            system_prompt = """You are a pharmaceutical expert AI. Analyze the given drug and provide detailed information about its ingredients, drug class, and potential allergens.

Respond in JSON format with:
{
    "drug_class": "primary drug classification",
    "active_ingredients": ["list of active ingredients"],
    "inactive_ingredients": ["common inactive ingredients if known"],
    "allergen_potential": ["potential allergens"],
    "cross_sensitivity_groups": ["groups this drug belongs to"]
}"""

            human_prompt = f"""
Drug Name: {drug_name}
Active Ingredient: {active_ingredient or 'Not specified'}

Provide detailed ingredient analysis and classification."""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ]

            response = await self.llm.ainvoke(messages)

            try:
                result = json.loads(response.content)
                return result
            except json.JSONDecodeError:
                return {
                    "drug_class":
                    "Unknown",
                    "active_ingredients":
                    [active_ingredient] if active_ingredient else [],
                    "inactive_ingredients": [],
                    "allergen_potential": [],
                    "cross_sensitivity_groups": []
                }

        except Exception as e:
            logger.error(f"Error analyzing drug ingredients: {str(e)}")
            return {
                "drug_class": "Unknown",
                "active_ingredients": [],
                "inactive_ingredients": [],
                "allergen_potential": [],
                "cross_sensitivity_groups": []
            }
