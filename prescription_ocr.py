"""
Prescription OCR Module
Handles PDF and image processing to extract medicine names from prescription files
"""

import re
import logging
import tempfile
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

from groq_client import GroqClient

# Configure logger first
logger = logging.getLogger(__name__)

# Optional dependencies - graceful fallback if not available
try:
    import pytesseract
    from PIL import Image
    from pdf2image import convert_from_path, convert_from_bytes
    OCR_AVAILABLE = True
    
    # Try to import alternative PDF processors
    PDF_PROCESSORS = []
    
    # Try PyPDF2 for simple text extraction
    try:
        import PyPDF2
        PDF_PROCESSORS.append("pypdf2")
        logger.info("Added PyPDF2 for text-based PDF processing")
    except ImportError:
        logger.debug("PyPDF2 not available")
    
    # pdf2image is already imported above
    if 'convert_from_bytes' in locals():
        PDF_PROCESSORS.append("pdf2image")
        logger.info("Added pdf2image for OCR-based PDF processing")
    
    logger.info(f"Available PDF processors: {PDF_PROCESSORS}")
    
except ImportError:
    OCR_AVAILABLE = False
    PDF_PROCESSORS = []
    logger.warning("OCR dependencies not available. File upload features will be limited.")

class PrescriptionOCR:
    def __init__(self, groq_client: GroqClient):
        self.groq_client = groq_client
        
    async def extract_medicines_from_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Extract medicine names from uploaded prescription file (PDF or image)
        
        Args:
            file_content: The file content as bytes
            filename: Original filename
            
        Returns:
            Dict with extracted medicines and metadata
        """
        try:
            if not OCR_AVAILABLE:
                return {
                    "success": False,
                    "error": "OCR functionality not available. Please install pytesseract, PIL, and pdf2image dependencies.",
                    "medicines": [],
                    "file_type": "unknown", 
                    "filename": filename,
                    "fallback_available": True,
                    "message": "You can still use manual entry to input medicine names."
                }
            
            # Determine file type from filename extension
            file_extension = Path(filename).suffix.lower()
            logger.info(f"Processing file: {filename}, extension: {file_extension}")
            
            # Extract text based on file extension
            if file_extension == '.pdf':
                extracted_text = await self._extract_text_from_pdf(file_content)
                file_type = 'application/pdf'
            elif file_extension in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
                extracted_text = await self._extract_text_from_image(file_content)
                file_type = f'image/{file_extension[1:]}'
            else:
                raise ValueError(f"Unsupported file type: {file_extension}. Please upload PDF or image files.")
            
            # Extract medicine names from the text using AI
            medicines = await self._extract_medicines_with_ai(extracted_text)
            
            return {
                "success": True,
                "extracted_text": extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text,
                "medicines": medicines,
                "file_type": file_type,
                "filename": filename
            }
            
        except Exception as e:
            logger.error(f"Error processing prescription file: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "medicines": [],
                "file_type": "unknown",
                "filename": filename
            }
    
    async def _extract_text_from_pdf(self, pdf_content: bytes) -> str:
        """Extract text from PDF using robust approach"""
        if not OCR_AVAILABLE:
            raise ValueError("OCR dependencies not available")
        
        logger.info("Starting PDF processing...")
        
        try:
            import asyncio
            import concurrent.futures
            import os
            
            def process_pdf():
                """Process PDF with timeout protection"""
                try:
                    # Set environment to ensure poppler tools are found
                    env = os.environ.copy()
                    env['PATH'] = f"/nix/var/nix/profiles/default/bin:{env.get('PATH', '')}"
                    
                    # Convert PDF to images with optimized settings
                    images = convert_from_bytes(
                        pdf_content, 
                        dpi=150,  # Good balance of quality and speed
                        fmt='jpeg',
                        thread_count=2  # Limit threads for stability
                    )
                    
                    if not images:
                        raise ValueError("No pages found in PDF")
                    
                    logger.info(f"Successfully converted PDF to {len(images)} pages")
                    
                    # Extract text from each page using OCR
                    extracted_text = ""
                    max_pages = min(5, len(images))  # Limit to 5 pages for performance
                    
                    for i, image in enumerate(images[:max_pages]):
                        try:
                            # Use OCR to extract text with proper configuration
                            page_text = pytesseract.image_to_string(
                                image, 
                                config='--psm 6'
                            )
                            
                            if page_text.strip():
                                extracted_text += f"\n--- Page {i+1} ---\n{page_text}"
                            
                        except Exception as ocr_error:
                            logger.warning(f"OCR failed for page {i+1}: {ocr_error}")
                            extracted_text += f"\n--- Page {i+1} (OCR Issue) ---\n[Text extraction failed for this page]"
                    
                    return extracted_text.strip() if extracted_text.strip() else "No readable text found in PDF"
                    
                except Exception as e:
                    logger.error(f"PDF processing failed: {e}")
                    raise ValueError(f"PDF processing error: {str(e)}")
            
            # Execute with timeout
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                try:
                    result = await asyncio.wait_for(
                        loop.run_in_executor(executor, process_pdf),
                        timeout=25.0  # 25 second timeout
                    )
                    
                    logger.info("PDF processing completed successfully")
                    return result
                    
                except asyncio.TimeoutError:
                    logger.error("PDF processing timed out")
                    raise ValueError("PDF processing took too long. Please try a smaller file or convert to image format.")
                    
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            raise ValueError(f"Could not process PDF: {str(e)}. You can try converting it to an image (JPG/PNG) instead.")
    
    async def _extract_text_from_image(self, image_content: bytes) -> str:
        """Extract text from image using OCR"""
        if not OCR_AVAILABLE:
            raise ValueError("OCR dependencies not available")
            
        try:
            # Create temporary file for image processing
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                temp_file.write(image_content)
                temp_path = temp_file.name
            
            try:
                # Open and process image
                image = Image.open(temp_path)
                
                # Enhance image for better OCR
                image = image.convert('RGB')
                
                # Extract text using Tesseract
                extracted_text = pytesseract.image_to_string(image, config='--psm 6')
                
                return extracted_text.strip()
                
            finally:
                # Clean up temporary file
                os.unlink(temp_path)
                
        except Exception as e:
            logger.error(f"Error extracting text from image: {str(e)}")
            raise
    
    async def _extract_medicines_with_ai(self, text: str) -> List[str]:
        """
        Use AI to intelligently extract medicine names from prescription text
        """
        try:
            prompt = f"""
You are a medical expert specializing in reading prescriptions. Extract ONLY actual medicine names from this prescription text.

PRESCRIPTION TEXT:
{text}

CRITICAL RULES:
1. ONLY extract actual medicine/drug names (e.g., Ibuprofen, Penicillin, Aspirin, Metformin)
2. IGNORE all instructions like "take twice daily", "let every", "four times daily"
3. IGNORE dosages, frequencies, and administration instructions
4. IGNORE doctor names, clinic names, patient information
5. IGNORE words like "tablet", "capsule", "mg", "ml"

WHAT TO LOOK FOR:
- Pharmaceutical drug names (brand or generic)
- Active ingredient names
- Medicine names that appear before dosage information

WHAT TO IGNORE:
- Instructions ("take", "daily", "times", "every", "as needed")
- Dosage amounts ("200mg", "250mg") 
- Administration details ("with food", "before meals")
- Medical advice or notes
- Doctor/clinic information

EXAMPLES:
✓ CORRECT: "Ibuprofen 200mg - take every 6 hours" → Extract: "Ibuprofen"
✓ CORRECT: "Penicillin V 250mg tablet four times daily" → Extract: "Penicillin V"  
✗ WRONG: Don't extract "take every", "four times daily", "200mg"

Return ONLY a JSON array of medicine names:
["Medicine1", "Medicine2"]

If no actual medicines found, return: []
"""

            response = await self.groq_client.get_completion(prompt)
            
            # Parse the AI response
            import json
            try:
                # Clean the response to extract JSON
                response_clean = response.strip()
                if response_clean.startswith('```json'):
                    response_clean = response_clean[7:]
                if response_clean.endswith('```'):
                    response_clean = response_clean[:-3]
                response_clean = response_clean.strip()
                
                medicines = json.loads(response_clean)
                if isinstance(medicines, list):
                    # Clean and validate medicine names
                    cleaned_medicines = []
                    for med in medicines:
                        if isinstance(med, str) and med.strip():
                            # Remove common non-medicine words and clean up
                            cleaned_name = self._clean_medicine_name(med.strip())
                            if cleaned_name and len(cleaned_name) > 2:
                                cleaned_medicines.append(cleaned_name)
                    
                    logger.info(f"Extracted {len(cleaned_medicines)} medicines: {cleaned_medicines}")
                    return cleaned_medicines
                else:
                    raise ValueError("AI response is not a list")
                    
            except json.JSONDecodeError:
                logger.error("Failed to parse AI response as JSON")
                # Fallback: use regex patterns
                return self._extract_medicines_with_regex(text)
                
        except Exception as e:
            logger.error(f"Error in AI medicine extraction: {str(e)}")
            # Fallback to regex-based extraction
            return self._extract_medicines_with_regex(text)
    
    def _clean_medicine_name(self, name: str) -> str:
        """Clean medicine name by removing dosage and common suffixes"""
        if not name:
            return ""
            
        # Remove dosage patterns
        name = re.sub(r'\d+\s*(?:mg|ml|g|mcg|units?)\b', '', name, flags=re.IGNORECASE)
        
        # Remove common instruction and form words
        unwanted_words = [
            'tablet', 'capsule', 'syrup', 'injection', 'drops?', 'cream', 'ointment',
            'take', 'daily', 'times', 'every', 'hours', 'let', 'four', 'twice',
            'once', 'three', 'needed', 'pain', 'for', 'days'
        ]
        
        for word in unwanted_words:
            name = re.sub(rf'\b{word}\b', '', name, flags=re.IGNORECASE)
        
        # Remove extra whitespace and special characters
        name = re.sub(r'[^\w\s]', ' ', name)
        name = ' '.join(name.split())
        
        return name.strip()
    
    def _extract_medicines_with_regex(self, text: str) -> List[str]:
        """
        Fallback method to extract medicines using regex patterns focused on actual medicine names
        """
        medicines = []
        
        # Enhanced patterns that focus on medicine names before dosage
        patterns = [
            # Pattern: "• Medicine Name 123mg" or "1. Medicine Name 123mg"
            r'(?:^|\n)\s*[•\d]+\.?\s*([A-Z][a-z]+(?:\s+[A-Z])?)\s+\d+\s*(?:mg|ml|g)\b',
            # Pattern: "Medicine Name" followed by dosage info
            r'\b([A-Z][a-z]+(?:\s+V)?)\s+\d+\s*mg\b',
            # Pattern: Known medicine names
            r'\b(Ibuprofen|Penicillin|Aspirin|Paracetamol|Acetaminophen|Amoxicillin|Azithromycin)\b'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                cleaned = self._clean_medicine_name(match)
                # More strict validation - must be a real medicine name
                if self._is_valid_medicine_name(cleaned):
                    medicines.append(cleaned)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_medicines = []
        for med in medicines:
            if med not in seen:
                seen.add(med)
                unique_medicines.append(med)
        
        return unique_medicines
    
    def _is_valid_medicine_name(self, name: str) -> bool:
        """Check if a name is likely a valid medicine name"""
        if not name or len(name) < 3:
            return False
            
        # Filter out common instruction words
        invalid_words = {
            'let', 'take', 'daily', 'times', 'every', 'hours', 'days',
            'tablet', 'capsule', 'dose', 'with', 'food', 'water',
            'morning', 'evening', 'night', 'before', 'after',
            'four', 'twice', 'once', 'three', 'needed', 'pain',
            'for', 'and', 'the', 'of', 'in', 'to', 'as'
        }
        
        name_lower = name.lower()
        words = name_lower.split()
        
        # Reject if any word is in invalid words
        for word in words:
            if word in invalid_words:
                return False
        
        # Must start with capital letter (proper medicine names do)
        if not name[0].isupper():
            return False
            
        # Known medicine patterns
        known_medicines = {
            'ibuprofen', 'penicillin', 'aspirin', 'paracetamol', 
            'acetaminophen', 'amoxicillin', 'azithromycin'
        }
        
        # Accept if it's a known medicine
        if name_lower in known_medicines or name_lower.startswith(tuple(known_medicines)):
            return True
            
        # Accept if it looks like a proper medicine name (starts with capital, reasonable length)
        return len(name) <= 20 and all(c.isalpha() or c.isspace() for c in name)