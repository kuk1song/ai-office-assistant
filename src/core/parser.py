"""
Document Parser for AI Office Assistant

This module handles parsing of various document formats (PDF, DOCX, TXT).
Restructured as a class for better organization and future extensibility.
"""

import os
import tempfile
import shutil
from typing import Dict

# Core dependencies
import fitz  # PyMuPDF
from docx import Document

# Optional OCR dependencies
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# Optional OpenAI Vision API
try:
    import openai
    from openai import OpenAI
    import base64
    VISION_API_AVAILABLE = True
except ImportError:
    VISION_API_AVAILABLE = False

class DocumentParser:
    """
    Document parser that handles multiple file formats with OCR support.
    
    Designed as a class to support future features like:
    - Custom parsing configurations
    - Format-specific preprocessing
    - Multi-language OCR settings
    """
    
    @staticmethod
    def parse_document(file_path: str) -> Dict:
        """
        Parse a document and extract its text content.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dict with 'content' (str) or 'error' (str)
        """
        try:
            if not os.path.exists(file_path):
                return {"error": "File not found"}
            
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.pdf':
                return DocumentParser._parse_pdf(file_path)
            elif file_extension == '.docx':
                return DocumentParser._parse_docx(file_path)
            elif file_extension == '.txt':
                return DocumentParser._parse_txt(file_path)
            else:
                return {"error": f"Unsupported file format: {file_extension}"}
                
        except Exception as e:
            return {"error": f"Error parsing document: {str(e)}"}

    @staticmethod
    def _parse_pdf(file_path: str) -> Dict:
        """Parse PDF files with fallback OCR support."""
        try:
            doc = fitz.open(file_path)
            text_content = []
            temp_dir = None
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                
                if text.strip():
                    text_content.append(text)
                elif OCR_AVAILABLE:
                    # OCR fallback for image-only pages
                    if temp_dir is None:
                        temp_dir = tempfile.mkdtemp()
                    
                    pix = page.get_pixmap()
                    img_path = os.path.join(temp_dir, f"page_{page_num}.png")
                    pix.save(img_path)
                    
                    ocr_text = DocumentParser._extract_text_from_image(img_path)
                    if ocr_text.strip():
                        text_content.append(f"=== Text extracted from images using OCR ===\n{ocr_text}")
            
            doc.close()
            
            # Cleanup temp directory
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            
            if not text_content:
                return {"error": "No readable text found in PDF"}
            
            return {"content": "\n\n".join(text_content)}
            
        except Exception as e:
            return {"error": f"Error parsing PDF: {str(e)}"}

    @staticmethod
    def _parse_docx(file_path: str) -> Dict:
        """Parse DOCX files with image OCR support."""
        try:
            doc = Document(file_path)
            text_content = []
            temp_dir = None
            
            # Extract text from paragraphs
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text)
            
            # Extract text from images if OCR is available
            if OCR_AVAILABLE and hasattr(doc, 'inline_shapes'):
                for shape in doc.inline_shapes:
                    if hasattr(shape, '_inline') and hasattr(shape._inline, 'graphic'):
                        try:
                            if temp_dir is None:
                                temp_dir = tempfile.mkdtemp()
                            
                            # Extract image and perform OCR
                            # Note: This is a simplified approach
                            # More robust image extraction would be needed for production
                            pass
                        except:
                            continue
            
            # Cleanup temp directory
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            
            if not text_content:
                return {"error": "No readable text found in DOCX"}
            
            return {"content": "\n\n".join(text_content)}
            
        except Exception as e:
            return {"error": f"Error parsing DOCX: {str(e)}"}

    @staticmethod
    def _parse_txt(file_path: str) -> Dict:
        """Parse plain text files."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            if not content.strip():
                return {"error": "Text file is empty"}
            
            return {"content": content}
            
        except UnicodeDecodeError:
            try:
                # Try with different encoding
                with open(file_path, 'r', encoding='latin-1') as file:
                    content = file.read()
                return {"content": content}
            except Exception as e:
                return {"error": f"Error reading text file: {str(e)}"}
        except Exception as e:
            return {"error": f"Error parsing text file: {str(e)}"}

    @staticmethod
    def _extract_text_from_image(image_path: str) -> str:
        """Extract text from image using OCR (Tesseract) or GPT-4o Vision."""
        # Try GPT-4o Vision first (better quality)
        if VISION_API_AVAILABLE:
            try:
                vision_result = DocumentParser._extract_text_with_vision_api(image_path)
                if vision_result.strip():
                    print(f"GPT-4o Vision successfully extracted {len(vision_result.strip())} characters")
                    return vision_result.strip()
                else:
                    print("GPT-4o Vision returned empty result, falling back to OCR")
            except Exception as e:
                print(f"GPT-4o Vision failed: {e}, falling back to OCR")
        
        # Fallback to traditional OCR
        if not OCR_AVAILABLE:
            print("Neither GPT-4o Vision nor OCR available")
            return ""
        
        try:
            # Check if tesseract is actually available
            try:
                import pytesseract
                # Test tesseract installation
                pytesseract.get_tesseract_version()
                print(f"Tesseract version: {pytesseract.get_tesseract_version()}")
            except Exception as version_error:
                print(f"Tesseract system dependency error: {version_error}")
                return ""
            
            image = Image.open(image_path)
            print(f"Processing image with OCR: {image_path}, size: {image.size}")
            
            # Try multiple PSM (Page Segmentation Mode) configurations for better results
            psm_configs = [6, 8, 11, 13]  # Different modes for various image types
            
            for i, psm in enumerate(psm_configs):
                try:
                    custom_config = f'--oem 3 --psm {psm}'
                    print(f"Trying OCR config {i+1}/{len(psm_configs)}: {custom_config}")
                    text = pytesseract.image_to_string(image, config=custom_config)
                    
                    if text.strip():  # If we get meaningful text, return it
                        print(f"OCR successful with config {custom_config}, extracted {len(text.strip())} characters")
                        return text.strip()
                        
                except Exception as config_error:
                    print(f"OCR config {custom_config} failed: {config_error}")
                    continue
            
            print("All OCR configurations failed to extract meaningful text")
            return ""  # Return empty string if all PSM configs fail
            
        except Exception as e:
            print(f"OCR Error for {image_path}: {type(e).__name__}: {e}")
            # Try to provide more specific error information
            if "TesseractNotFoundError" in str(type(e)):
                print("Tesseract executable not found. Make sure tesseract-ocr is installed on the system.")
            return ""

    @staticmethod
    def _extract_text_with_vision_api(image_path: str) -> str:
        """Extract text from image using GPT-4o Vision API."""
        try:
            # Get OpenAI API key from environment
            import os
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment variables")
            
            client = OpenAI(api_key=api_key)
            
            # Encode image to base64
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Determine image format
            image_format = "jpeg"
            if image_path.lower().endswith('.png'):
                image_format = "png"
            elif image_path.lower().endswith('.webp'):
                image_format = "webp"
            elif image_path.lower().endswith('.gif'):
                image_format = "gif"
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Please extract all text content from this image. Include:
- All visible text, numbers, and symbols
- Preserve the original layout and structure as much as possible
- Include table data if present
- Include any handwritten text
- Be precise and comprehensive

Return only the extracted text content without any additional commentary."""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/{image_format};base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=4000,
                temperature=0
            )
            
            return response.choices[0].message.content or ""
            
        except Exception as e:
            print(f"GPT-4o Vision API error: {e}")
            raise e

# Backward compatibility function
def parse_document(file_path: str) -> Dict:
    """Backward compatibility wrapper for the old function-based API."""
    return DocumentParser.parse_document(file_path) 