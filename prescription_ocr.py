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
        """Extract text from PDF using multiple methods"""
        if not OCR_AVAILABLE:
            raise ValueError("OCR dependencies not available")
        
        extracted_text = ""
        
        # Method 1: Try PyPDF2 for text-based PDFs (faster)
        if "pypdf2" in PDF_PROCESSORS:
            try:
                logger.info("Trying PyPDF2 text extraction...")
                import io
                import PyPDF2
                
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
                text_content = ""
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            text_content += f"\n--- Page {page_num + 1} ---\n{page_text}"
                    except Exception as e:
                        logger.warning(f"PyPDF2 failed on page {page_num + 1}: {e}")
                
                if text_content.strip():
                    logger.info("Successfully extracted text using PyPDF2")
                    return text_content.strip()
                else:
                    logger.info("PyPDF2 found no text content, trying OCR method...")
                    
            except Exception as e:
                logger.warning(f"PyPDF2 method failed: {e}")
        
        # Method 2: OCR-based extraction (slower but works on image-based PDFs)
        if "pdf2image" in PDF_PROCESSORS:
            try:
                logger.info("Trying OCR-based PDF processing...")
                import asyncio
                import concurrent.futures
                
                def convert_and_ocr():
                    """Convert PDF pages and run OCR with timeout"""
                    try:
                        # Convert PDF to images with lower DPI for speed
                        images = convert_from_bytes(pdf_content, dpi=120, fmt='jpeg')
                        logger.info(f"Converted PDF to {len(images)} images")
                        
                        ocr_text = ""
                        for i, image in enumerate(images):
                            if i >= 3:  # Limit to first 3 pages for speed
                                logger.info(f"Limiting processing to first {i} pages for performance")
                                break
                                
                            try:
                                page_text = pytesseract.image_to_string(image, config='--psm 6')
                                ocr_text += f"\n--- Page {i+1} ---\n{page_text}"
                            except Exception as ocr_error:
                                logger.error(f"OCR failed for page {i+1}: {ocr_error}")
                                ocr_text += f"\n--- Page {i+1} (OCR Error) ---\n[Could not read text]"
                        
                        return ocr_text
                        
                    except Exception as e:
                        logger.error(f"PDF to image conversion failed: {e}")
                        raise ValueError("PDF processing failed - please try uploading as an image instead")
                
                # Run with shorter timeout
                loop = asyncio.get_event_loop()
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    try:
                        extracted_text = await asyncio.wait_for(
                            loop.run_in_executor(executor, convert_and_ocr),
                            timeout=20.0  # Reduced to 20 seconds
                        )
                        
                        if extracted_text.strip():
                            logger.info("Successfully extracted text using OCR")
                            return extracted_text.strip()
                            
                    except asyncio.TimeoutError:
                        logger.error("OCR processing timed out")
                        raise ValueError("PDF processing timed out. Please try uploading as an image (JPG/PNG) instead.")
                        
            except Exception as e:
                logger.error(f"OCR method failed: {e}")
                raise ValueError(f"PDF processing failed: {str(e)}. Please try uploading as an image (JPG/PNG) instead.")
        
        # If we get here, no methods worked
        raise ValueError("Unable to process PDF. Please convert to an image format (JPG/PNG) and try again.")
    
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
You are a medical AI assistant specialized in extracting medicine names from prescription text.

PRESCRIPTION TEXT:
{text}

TASK: Extract all medicine names from this prescription text.

REQUIREMENTS:
1. Look for medicine names, drug names, and pharmaceutical products
2. Include brand names and generic names
3. Exclude dosage information, instructions, and non-medicine text
4. Clean up the names (remove dosage, mg, ml, etc.)
5. Return only the core medicine names

COMMON PATTERNS TO LOOK FOR:
- Brand names (e.g., Crocin, Dolo, Paracetamol)
- Generic names 
- Tablets, capsules, syrups mentioned
- Rx: or prescription lines
- Medicine lists or numbered items

Return a JSON array of medicine names only:
["medicine1", "medicine2", "medicine3"]

EXAMPLE:
For text "1. Paracetamol 650mg - Take twice daily\n2. Ibuprofen 400mg - As needed"
Return: ["Paracetamol", "Ibuprofen"]
"""

            response = await self.groq_client.llm.ainvoke([
                {"role": "system", "content": "You are a medical AI assistant that extracts medicine names from prescription text. Always respond with a valid JSON array."},
                {"role": "user", "content": prompt}
            ])
            
            # Parse the AI response
            import json
            try:
                medicines = json.loads(response.content)
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
        # Remove dosage patterns
        name = re.sub(r'\d+\s*(?:mg|ml|g|mcg|units?)\b', '', name, flags=re.IGNORECASE)
        
        # Remove common instruction words
        name = re.sub(r'\b(?:tablet|capsule|syrup|injection|drops?|cream|ointment)\b', '', name, flags=re.IGNORECASE)
        
        # Remove extra whitespace and special characters
        name = re.sub(r'[^\w\s]', ' ', name)
        name = ' '.join(name.split())
        
        return name.strip()
    
    def _extract_medicines_with_regex(self, text: str) -> List[str]:
        """
        Fallback method to extract medicines using regex patterns
        """
        medicines = []
        
        # Common patterns for prescription medicines
        patterns = [
            r'(?:^|\n)\s*\d+\.\s*([A-Za-z][A-Za-z\s]+?)(?:\s+\d+|\s*-|\s*$)',  # Numbered lists
            r'(?:Rx:?|Tab:?|Cap:?|Syp:?)\s*([A-Za-z][A-Za-z\s]+?)(?:\s+\d+|\s*$)',  # Rx patterns
            r'\b([A-Z][a-z]+(?:\s+[A-Z]?[a-z]+)*)\s+\d+\s*(?:mg|ml|g)\b',  # Medicine + dosage
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                cleaned = self._clean_medicine_name(match)
                if cleaned and len(cleaned) > 2 and cleaned not in medicines:
                    medicines.append(cleaned)
        
        # Also look for common medicine name patterns
        common_medicine_words = ['paracetamol', 'ibuprofen', 'aspirin', 'crocin', 'dolo', 'azithromycin', 'amoxicillin']
        words = text.lower().split()
        for word in words:
            for med_word in common_medicine_words:
                if med_word in word:
                    medicines.append(med_word.title())
                    break
        
        # Remove duplicates while preserving order
        unique_medicines = []
        for med in medicines:
            if med not in unique_medicines:
                unique_medicines.append(med)
        
        logger.info(f"Regex extraction found {len(unique_medicines)} medicines: {unique_medicines}")
        return unique_medicines[:10]  # Limit to 10 medicines max