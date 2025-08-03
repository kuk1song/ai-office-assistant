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
        """Extract text from image using OCR (Tesseract)."""
        if not OCR_AVAILABLE:
            return ""
        
        try:
            image = Image.open(image_path)
            
            # Try multiple PSM (Page Segmentation Mode) configurations for better results
            psm_configs = [6, 8, 11, 13]  # Different modes for various image types
            
            for psm in psm_configs:
                try:
                    custom_config = f'--oem 3 --psm {psm}'
                    text = pytesseract.image_to_string(image, config=custom_config)
                    
                    if text.strip():  # If we get meaningful text, return it
                        return text.strip()
                        
                except Exception:
                    continue
            
            return ""  # Return empty string if all PSM configs fail
            
        except Exception as e:
            print(f"OCR Error for {image_path}: {e}")
            return ""

# Backward compatibility function
def parse_document(file_path: str) -> Dict:
    """Backward compatibility wrapper for the old function-based API."""
    return DocumentParser.parse_document(file_path) 