import google.generativeai as genai
from google import genai as google_client
import os
from typing import Dict, Any, Optional, List
import json
import logging
from PIL import Image
import io
import base64
import mimetypes
import tempfile
import shutil
import re

logger = logging.getLogger(__name__)

# Configure logger to ensure it outputs to console
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = True

class GeminiService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY must be set in environment variables")
        
        genai.configure(api_key=api_key)  # type: ignore[attr-defined]
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')  # type: ignore[attr-defined]
        # Use the google.genai client for file uploads (like in main.py)
        self.client = google_client.Client(api_key=api_key)
    
    async def extract_patient_data(self, file_content: bytes, file_type: str) -> Dict[str, Any]:
        """Extract patient data from uploaded document"""
        try:
            print(f"🔍 Processing document of type: {file_type}, size: {len(file_content)} bytes")
            logger.info(f"Processing document of type: {file_type}, size: {len(file_content)} bytes")
            
            prompt = """
            You are a medical document processor. Extract patient information from the provided document(s).
            
            The uploaded documents may include:
            1. Patient ID documents (Aadhaar card, PAN card, or other government IDs)
            2. Medical prescriptions
            3. Medical reports or diagnoses
            
            Please extract the following information and return it in JSON format:
            {
                "name": "Patient's full name",
                "date_of_birth": "Date in YYYY-MM-DD format",
                "diagnosis": "Medical diagnosis or condition",
                "prescription": "Prescribed medications and instructions",
                "confidence_score": 0.95,
                "raw_text": "All extracted text from the document"
            }
            
            IMPORTANT EXTRACTION RULES:
            1. **Patient Identity**: If you see an Aadhaar card, PAN card, or any government ID document, extract the person's name and date of birth from these documents as they are the most reliable source for patient identity.
            
            2. **Name Extraction**: 
               - **CRITICAL**: Always return names in English/Latin script ONLY
               - If you see both Devanagari (Hindi) and English versions of a name, ALWAYS use the English version
               - For example: If you see "गीताशिष जतिन शर्मा" and "Geetashish Jatin Sharma", use "Geetashish Jatin Sharma"
               - Prioritize name from ID documents (Aadhaar, PAN card) but use the English transliteration
               - If only Devanagari script is available, transliterate to English using standard transliteration rules
               - **NEVER return names in Devanagari, Arabic, or any non-Latin scripts**
               - Use the full name as it appears in English on the official document
            
            3. **Date of Birth**: 
               - Extract DOB from ID documents first (Aadhaar cards show DOB, PAN cards show it in some cases)
               - If not available on ID, look for age or DOB mentioned in medical documents
               - Convert any date format to YYYY-MM-DD format
               - If only age is mentioned, estimate DOB based on current date
            
            4. **Diagnosis Intelligence**:
               - If diagnosis is explicitly mentioned in the document, extract it directly
               - If diagnosis is NOT clearly stated but prescription is available, analyze the prescribed medications to reverse-engineer the likely diagnosis
               - Use your medical knowledge to infer conditions from medication patterns:
                 * Antibiotics (Amoxicillin, Azithromycin) → Bacterial infections
                 * Bronchodilators (Salbutamol, Levolin) → Respiratory conditions like Asthma/COPD
                 * Antacids (Pantoprazole, Omeprazole) → Gastric issues/GERD
                 * Antidiabetic drugs (Metformin, Insulin) → Diabetes
                 * Antihypertensives (Amlodipine, Enalapril) → Hypertension
                 * Pain medications + anti-inflammatory → Musculoskeletal conditions
               - Provide the most likely diagnosis based on medication analysis
            
            5. **Prescription Processing**:
               - Extract all medications with dosage, frequency, and duration
               - Include both generic and brand names if available
               - Note any special instructions or precautions
               - **CRITICAL FORMATTING**: Return prescription as clean, readable text - NOT as a list or array
               - **Example Format**: 
                 "Tab. Cefixime XP 325 - 1 OD (once daily)
                  Tab. Dolo 650 - 1 TID (three times daily) 
                  Tab. Montair 10 - 1 OD (once daily)
                  Betadine gargle 2-3 times daily
                  Rest at home"
               - **DO NOT use square brackets, quotes, or list formatting**
               - Use line breaks or semicolons to separate medications
               - Make it human-readable and professional
            
            6. **Quality Assurance**:
               - If information is not clearly available, use null for that field
               - Confidence score should reflect how certain you are about the extraction (0-1)
               - Include all visible text in raw_text field for reference
               - Higher confidence for information extracted from official ID documents
            
            STRICT OUTPUT REQUIREMENTS:
            - Respond with a single JSON object only.
            - Do not include markdown or code fences.
            - Use standard ASCII quotes for JSON keys and string values.
            
            Document to process:
            """
            
            if file_type.startswith('image/'):
                # Process image file
                print("📷 Processing as image document")
                logger.info("Processing as image document")
                image = Image.open(io.BytesIO(file_content))
                response = self._generate_content_with_image(prompt, image)
            elif file_type == 'application/pdf':
                # Process PDF file - use Gemini file upload API for better PDF handling
                print("📄 Processing as PDF document using file upload API")
                logger.info("Processing as PDF document using file upload API")
                
                # Create temp file for PDF
                temp_dir = tempfile.mkdtemp()
                try:
                    pdf_path = os.path.join(temp_dir, 'document.pdf')
                    with open(pdf_path, 'wb') as f:
                        f.write(file_content)
                    
                    # Upload to Gemini - use 'file' parameter instead of 'path'
                    uploaded_file = self.client.files.upload(
                        file=pdf_path,
                        config={"mime_type": "application/pdf"}
                    )
                    
                    # Generate content using uploaded file with proper message structure
                    resp_obj = self.client.models.generate_content(
                        model="gemini-2.0-flash-exp",
                        contents=[
                            {"role": "user", "parts": [
                                {"file_data": {"mime_type": uploaded_file.mime_type, "file_uri": uploaded_file.uri}},
                                {"text": prompt}
                            ]}
                        ]
                    )
                    response = resp_obj.text or ""
                    
                finally:
                    # Clean up temp file
                    import shutil
                    if os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir)
            else:
                # Process text file (assuming it's readable text)
                print("📄 Processing as text document")
                logger.info("Processing as text document")
                try:
                    text_content = file_content.decode('utf-8', errors='ignore')
                except UnicodeDecodeError:
                    # If UTF-8 fails, try other common encodings
                    try:
                        text_content = file_content.decode('latin-1', errors='ignore')
                    except:
                        text_content = str(file_content, errors='ignore')
                
                full_prompt = f"{prompt}\n\n{text_content}"
                print(f"📝 Text content length: {len(text_content)} characters")
                logger.info(f"Text content length: {len(text_content)} characters")
                response = self._generate_content_with_text(full_prompt)
            
            print("=== 🤖 FULL LLM RESPONSE ===")
            print(response)
            print("=== 🏁 END LLM RESPONSE ===")
            logger.info("=== FULL LLM RESPONSE ===")
            logger.info(response)
            logger.info("=== END LLM RESPONSE ===")
            
            parsed_data = self._parse_response(response)
            print(f"✅ Parsed patient data: {parsed_data}")
            logger.info(f"Parsed patient data: {parsed_data}")
            
            return parsed_data
            
        except Exception as e:
            print(f"❌ Error processing document: {str(e)}")
            logger.error(f"Error processing document: {str(e)}")
            return {
                "name": None,
                "date_of_birth": None,
                "diagnosis": None,
                "prescription": None,
                "confidence_score": 0.0,
                "raw_text": f"Error processing document: {str(e)}"
            }

    async def extract_patient_data_from_multiple_files(self, files_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract patient data from multiple uploaded documents using Gemini file upload API"""
        print(f"📁 Processing {len(files_data)} documents using Gemini file upload API")
        logger.info(f"Processing {len(files_data)} documents using Gemini file upload API")
        
        # Create temporary directory for files
        temp_dir = tempfile.mkdtemp()
        uploaded_files = []
        
        try:
            # Save files to temp directory and upload to Gemini
            for i, file_data in enumerate(files_data):
                print(f"📄 Processing document {i+1}/{len(files_data)}")
                
                file_content = file_data['content']
                file_name = file_data.get('name', f'document_{i+1}')
                file_type = file_data.get('type', 'application/octet-stream')
                
                # Determine proper MIME type
                if file_name.lower().endswith('.pdf'):
                    mime_type = 'application/pdf'
                elif file_name.lower().endswith(('.jpg', '.jpeg')):
                    mime_type = 'image/jpeg'
                elif file_name.lower().endswith('.png'):
                    mime_type = 'image/png'
                elif file_name.lower().endswith('.tiff'):
                    mime_type = 'image/tiff'
                else:
                    # Try to guess from provided file_type
                    mime_type = file_type if file_type != 'application/octet-stream' else 'application/pdf'
                
                print(f" File: {file_name}, MIME type: {mime_type}")
                
                # Save file temporarily
                file_path = os.path.join(temp_dir, file_name)
                with open(file_path, 'wb') as f:
                    f.write(file_content)
                
                # Upload to Gemini
                print(f"🔄 Uploading {file_name} to Gemini...")
                try:
                    uploaded_file = self.client.files.upload(
                        file=file_path, 
                        config={"mime_type": mime_type}
                    )
                    uploaded_files.append(uploaded_file)
                    print(f"✅ Successfully uploaded {file_name}")
                except Exception as upload_error:
                    print(f"❌ Error uploading {file_name}: {str(upload_error)}")
                    logger.error(f"Error uploading {file_name}: {str(upload_error)}")
            
            if not uploaded_files:
                raise Exception("No files were successfully uploaded to Gemini")
            
            # Create comprehensive prompt for medical document processing
            prompt = """
            You are a medical document processor. Extract patient information from the provided document(s).
            
            The uploaded documents may include:
            1. Patient ID documents (Aadhaar card, PAN card, or other government IDs)
            2. Medical prescriptions
            3. Medical reports or diagnoses
            4. Medical test results
            5. Insurance documents
            
            Please extract the following information and return it in JSON format:
            {
                "name": "Patient's full name",
                "date_of_birth": "Date in YYYY-MM-DD format",
                "diagnosis": "Medical diagnosis or condition",
                "prescription": "Prescribed medications and instructions",
                "confidence_score": 0.95,
                "raw_text": "All extracted text from all documents combined",
                "document_types": ["list of document types identified"],
                "medical_history": "Any relevant medical history mentioned",
                "doctor_name": "Name of prescribing doctor if available",
                "hospital_clinic": "Name of hospital or clinic if available"
            }
            
            IMPORTANT EXTRACTION RULES:
            1. **Patient Identity**: If you see an Aadhaar card, PAN card, or any government ID document, extract the person's name and date of birth from these documents as they are the most reliable source for patient identity.
            
            2. **Name Extraction**: 
               - **CRITICAL RULE**: Always return names in English/Latin script ONLY
               - **Example**: If you see both "गीताशिष जतिन शर्मा" and "Geetashish Jatin Sharma", use "Geetashish Jatin Sharma"
               - **Priority**: ID documents (Aadhaar shows both Hindi and English - USE ENGLISH VERSION)
               - If only Devanagari script is available, transliterate to English:
                 * गीताशिष जतिन शर्मा → "Geetashish Jatin Sharma" 
                 * राम शर्मा → "Ram Sharma"
                 * सुनीता देवी → "Sunita Devi"
               - **NEVER return names in Devanagari, Arabic, Tamil, or any non-Latin scripts**
               - Use the full name as it appears in English on the official document
            
            3. **Date of Birth**: 
               - Extract DOB from ID documents first (Aadhaar cards show DOB, PAN cards show it in some cases)
               - If not available on ID, look for age or DOB mentioned in medical documents
               - Convert any date format to YYYY-MM-DD format
               - If only age is mentioned, estimate DOB based on current date
            
            4. **Cross-Document Verification**:
               - If multiple documents contain the same information, use the most reliable source
               - ID documents are more reliable than medical documents for personal information
               - Medical documents are more reliable for medical information
            
            5. **Diagnosis Intelligence**:
               - If diagnosis is explicitly mentioned in any document, extract it directly
               - If diagnosis is NOT clearly stated but prescription is available, analyze the prescribed medications to reverse-engineer the likely diagnosis
               - Use your medical knowledge to infer conditions from medication patterns:
                 * Antibiotics (Amoxicillin, Azithromycin) → Bacterial infections
                 * Bronchodilators (Salbutamol, Levolin) → Respiratory conditions like Asthma/COPD
                 * Antacids (Pantoprazole, Omeprazole) → Gastric issues/GERD
                 * Antidiabetic drugs (Metformin, Insulin) → Diabetes
                 * Antihypertensives (Amlodipine, Enalapril) → Hypertension
                 * Pain medications + anti-inflammatory → Musculoskeletal conditions
               - Provide the most likely diagnosis based on medication analysis
            
            6. **Prescription Processing**:
               - Extract all medications with dosage, frequency, and duration from all documents
               - Include both generic and brand names if available
               - Note any special instructions or precautions
               - Combine prescriptions from multiple documents if present
               - **CRITICAL FORMATTING**: Return prescription as clean, readable text - NOT as a list or array
               - **Example Format**: 
                 "Tab. Cefixime XP 325 - 1 OD (once daily)
                  Tab. Dolo 650 - 1 TID (three times daily) 
                  Tab. Montair 10 - 1 OD (once daily)
                  Betadine gargle 2-3 times daily
                  Rest at home"
               - **DO NOT use square brackets, quotes, or list formatting**
               - Use line breaks or semicolons to separate medications
               - Make it human-readable and professional
            
            7. **Quality Assurance**:
               - If information is not clearly available, use null for that field
               - Confidence score should reflect how certain you are about the extraction (0-1)
               - Include all visible text from all documents in raw_text field for reference
               - Higher confidence for information extracted from official ID documents
            
            Process ALL the provided documents comprehensively and extract information from each one.
            
            STRICT OUTPUT REQUIREMENTS:
            - Respond with a single JSON object only.
            - Do not include markdown or code fences.
            - Use standard ASCII quotes for JSON keys and string values.
            """
            
            print("=== 🤖 SENDING MULTIPLE FILES TO LLM ===")
            print(f"Number of files uploaded: {len(uploaded_files)}")
            logger.info(f"Sending {len(uploaded_files)} files to Gemini for processing")
            
            # Generate content using all uploaded files with proper message structure
            user_parts = []
            for uploaded_file in uploaded_files:
                user_parts.append({
                    "file_data": {
                        "mime_type": uploaded_file.mime_type, 
                        "file_uri": uploaded_file.uri
                    }
                })
            user_parts.append({"text": prompt})
            
            resp_obj = self.client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=[
                    {"role": "user", "parts": user_parts}
                ]
            )
            
            response_text = resp_obj.text or ""
            print("=== 🤖 FULL LLM RESPONSE ===")
            print(response_text)
            print("=== 🏁 END LLM RESPONSE ===")
            logger.info("=== FULL LLM RESPONSE ===")
            logger.info(response_text)
            logger.info("=== END LLM RESPONSE ===")
            
            parsed_data = self._parse_response(response_text)
            parsed_data["documents_processed"] = len(files_data)
            parsed_data["processing_method"] = "gemini_file_upload_api"
            
            print(f"✅ Parsed patient data from {len(files_data)} documents: {parsed_data}")
            logger.info(f"Parsed patient data from {len(files_data)} documents")
            
            return parsed_data
            
        except Exception as e:
            print(f"❌ Error processing multiple documents: {str(e)}")
            logger.error(f"Error processing multiple documents: {str(e)}")
            return {
                "name": None,
                "date_of_birth": None,
                "diagnosis": None,
                "prescription": None,
                "confidence_score": 0.0,
                "raw_text": f"Error processing documents: {str(e)}",
                "documents_processed": len(files_data),
                "processing_method": "gemini_file_upload_api"
            }
        finally:
            # Clean up temporary files
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def _generate_content_with_image(self, prompt: str, image: Image.Image) -> str:
        """Generate content from image using Gemini"""
        try:
            print("=== 🤖 SENDING TO LLM (IMAGE) ===")
            print(f"Image size: {image.size}")
            print("=== 📨 END PROMPT ===")
            logger.info("=== SENDING TO LLM (IMAGE) ===")
            logger.info(f"Image size: {image.size}")
            logger.info("=== END PROMPT ===")
            
            response = self.model.generate_content([prompt, image])  # type: ignore[attr-defined]
            print(f"🤖 Raw Gemini response from image: {response.text}")
            logger.info(f"Raw Gemini response from image: {response.text}")
            return response.text or ""
        except Exception as e:
            print(f"❌ Error generating content from image: {str(e)}")
            logger.error(f"Error generating content from image: {str(e)}")
            raise
    
    def _generate_content_with_text(self, prompt: str) -> str:
        """Generate content from text using Gemini"""
        try:
            print("=== 🤖 SENDING TO LLM (TEXT) ===")
            print(f"Prompt length: {len(prompt)} characters")
            print("=== 📨 END PROMPT ===")
            logger.info("=== SENDING TO LLM (TEXT) ===")
            logger.info(f"Full prompt: {prompt}")
            logger.info("=== END PROMPT ===")
            
            response = self.model.generate_content(prompt)  # type: ignore[attr-defined]
            print(f"🤖 Raw Gemini response from text: {response.text}")
            logger.info(f"Raw Gemini response from text: {response.text}")
            return response.text or ""
        except Exception as e:
            print(f"❌ Error generating content from text: {str(e)}")
            logger.error(f"Error generating content from text: {str(e)}")
            raise
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse Gemini response to extract JSON data"""
        def _clean_json_text(text: str) -> str:
            # Strip surrounding code fences if present
            fenced = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
            if fenced:
                text = fenced.group(1)
            # Extract the first {...} block if still mixed content
            brace_match = re.search(r"\{[\s\S]*\}", text)
            if brace_match:
                text = brace_match.group(0)
            # Normalize smart quotes to ASCII
            replacements = {
                '\u201c': '"', '\u201d': '"', '\u201e': '"', '\u201f': '"',
                '\u2018': "'", '\u2019': "'", '\u2032': "'", '\u2033': '"'
            }
            for src, dst in replacements.items():
                text = text.replace(src, dst)
            # Remove trailing commas before } or ]
            text = re.sub(r",\s*(\}|\])", r"\1", text)
            # Remove non-printable control chars except tab/newline/carriage-return
            text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
            return text.strip()

        def _transliterate_name(name: str) -> str:
            """Transliterate Devanagari names to English"""
            if not name:
                return name
            
            # Check if name contains Devanagari characters
            devanagari_range = range(0x0900, 0x097F)
            has_devanagari = any(ord(char) in devanagari_range for char in name)
            
            if not has_devanagari:
                return name  # Already in English
            
            # Simple transliteration map for common characters
            transliteration_map = {
                'गीताशिष': 'Geetashish',
                'जतिन': 'Jatin', 
                'शर्मा': 'Sharma',
                'राम': 'Ram',
                'सुनीता': 'Sunita',
                'देवी': 'Devi',
                'कुमार': 'Kumar',
                'सिंह': 'Singh',
                'अग्रवाल': 'Agarwal',
                'गुप्ता': 'Gupta',
                'वर्मा': 'Verma',
                'मिश्रा': 'Mishra'
            }
            
            # Try direct replacement first
            for hindi, english in transliteration_map.items():
                name = name.replace(hindi, english)
            
            # If still contains Devanagari, try phonetic transliteration
            if any(ord(char) in devanagari_range for char in name):
                # Basic character-by-character transliteration
                char_map = {
                    'अ': 'a', 'आ': 'aa', 'इ': 'i', 'ई': 'ee', 'उ': 'u', 'ऊ': 'oo',
                    'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au',
                    'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'च': 'ch', 'छ': 'chh',
                    'ज': 'j', 'झ': 'jh', 'ट': 't', 'ठ': 'th', 'ड': 'd', 'ढ': 'dh',
                    'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n', 'प': 'p',
                    'फ': 'ph', 'ब': 'b', 'भ': 'bh', 'म': 'm', 'य': 'y', 'र': 'r',
                    'ल': 'l', 'व': 'w', 'श': 'sh', 'ष': 'sh', 'स': 's', 'ह': 'h',
                    '्': '', 'ं': 'n', 'ः': 'h', 'ा': 'aa', 'ि': 'i', 'ी': 'ee',
                    'ु': 'u', 'ू': 'oo', 'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au',
                    ' ': ' '
                }
                
                transliterated = ''
                for char in name:
                    if char in char_map:
                        transliterated += char_map[char]
                    elif ord(char) not in devanagari_range:
                        transliterated += char
                    else:
                        transliterated += char  # Keep unknown characters as-is
                
                # Clean up the result
                transliterated = re.sub(r'([a-z])\1+', r'\1', transliterated)  # Remove repeated chars
                transliterated = ' '.join(word.capitalize() for word in transliterated.split())
                
                return transliterated
            
            return name

        def _clean_prescription_format(prescription: str) -> str:
            """Clean up prescription formatting to remove list-like syntax"""
            if not prescription:
                return prescription
            
            # Remove square brackets
            prescription = re.sub(r'^\[|\]$', '', prescription.strip())
            
            # Remove quotes around individual items
            prescription = re.sub(r"'([^']*)'", r'\1', prescription)
            prescription = re.sub(r'"([^"]*)"', r'\1', prescription)
            
            # Convert comma-separated items to line breaks
            if ', ' in prescription and not '\n' in prescription:
                prescription = prescription.replace(', ', '\n')
            
            # Clean up any remaining formatting issues
            prescription = re.sub(r',\s*\n', '\n', prescription)
            prescription = re.sub(r'\n\s*\n', '\n', prescription)
            
            return prescription.strip()

        def _normalize(parsed: Dict[str, Any]) -> Dict[str, Any]:
            # Map common key typos
            if 'datee_of_birth' in parsed and 'date_of_birth' not in parsed:
                parsed['date_of_birth'] = parsed.pop('datee_of_birth')
            
            # Ensure keys exist and coerce to string when applicable
            name = parsed.get('name')
            dob = parsed.get('date_of_birth')
            diagnosis = parsed.get('diagnosis')
            prescription = parsed.get('prescription')
            conf = parsed.get('confidence_score', 0.5)
            raw_text = parsed.get('raw_text', '')
            
            # CRITICAL: Clean up prescription formatting
            if prescription and isinstance(prescription, str):
                prescription = _clean_prescription_format(prescription)
                print(f"💊 Prescription after cleaning: {prescription}")
                logger.info(f"Prescription after cleaning: {prescription}")
            
            # CRITICAL: Transliterate name to English if needed
            if name and isinstance(name, str):
                name = _transliterate_name(name)
                print(f"🔤 Name after transliteration: {name}")
                logger.info(f"Name after transliteration: {name}")
            
            return {
                'name': None if name is None else str(name),
                'date_of_birth': None if dob is None else str(dob),
                'diagnosis': None if diagnosis is None else str(diagnosis),
                'prescription': None if prescription is None else str(prescription),
                'confidence_score': float(conf) if isinstance(conf, (int, float, str)) and str(conf).replace('.', '', 1).isdigit() else 0.5,
                'raw_text': str(raw_text)
            }

        # Try multiple parsing strategies
        candidates: List[str] = []
        cleaned = _clean_json_text(response)
        candidates.append(cleaned)
        # If the response begins with a fence, also try raw without cleaning braces
        if response.strip().startswith("```"):
            candidates.append(response.strip().strip("`"))
        # Last resort: simple substring between first and last brace without other cleaning
        start_idx = response.find('{')
        end_idx = response.rfind('}') + 1
        if start_idx != -1 and end_idx > start_idx:
            candidates.append(response[start_idx:end_idx])

        for candidate in candidates:
            try:
                parsed = json.loads(candidate)
                return _normalize(parsed)
            except Exception:
                continue

        # Regex-based fallback extraction from the cleaned text
        try:
            text = cleaned
            def rx(key: str) -> Optional[str]:
                m = re.search(rf'"{key}"\s*:\s*"([\s\S]*?)"\s*(,|\}})', text)
                return m.group(1) if m else None
            name = rx('name')
            dob = rx('date_of_birth') or rx('datee_of_birth')
            diagnosis = rx('diagnosis')
            prescription = rx('prescription')
            conf_match = re.search(r'"confidence_score"\s*:\s*([0-9\.]+)', text)
            confidence = float(conf_match.group(1)) if conf_match else 0.5
            raw_block = rx('raw_text')
            
            # Apply transliteration to name
            if name:
                name = _transliterate_name(name)
                print(f"🔤 Name after regex fallback transliteration: {name}")
                logger.info(f"Name after regex fallback transliteration: {name}")
            
            # Apply prescription cleaning
            if prescription:
                prescription = _clean_prescription_format(prescription)
                print(f"💊 Prescription after regex fallback cleaning: {prescription}")
                logger.info(f"Prescription after regex fallback cleaning: {prescription}")
            
            return {
                'name': None if name is None else str(name),
                'date_of_birth': None if dob is None else str(dob),
                'diagnosis': None if diagnosis is None else str(diagnosis),
                'prescription': None if prescription is None else str(prescription),
                'confidence_score': confidence,
                'raw_text': str(raw_block) if raw_block is not None else response
            }
        except Exception:
            pass

        logger.warning("Could not parse JSON from Gemini response")
        return {
            "name": None,
            "date_of_birth": None,
            "diagnosis": None,
            "prescription": None,
            "confidence_score": 0.3,
            "raw_text": response
        }
    
    async def generate_chat_response(self, query: str, context: str, attached_files: Optional[List[Dict[str, Any]]] = None) -> str:
        """Generate chat response based on query, context, and optional attached files"""
        # Process attached files if any
        file_context = ""
        if attached_files:
            file_context = await self._process_attached_files(attached_files)
        
        # Combine all contexts
        full_context = f"{context}\n\n{file_context}" if file_context else context
        
        prompt = f"""
        You are a helpful medical assistant with access to patient data and any uploaded documents.
        
        Context (Patient Data and Documents):
        {full_context}
        
        User Question: {query}
        
        Please provide a helpful, accurate response based on the information provided in the context.
        If you're analyzing tabular data from uploaded files, provide insights, trends, and relevant medical observations.
        If the context doesn't contain enough information to answer the question, please say so.
        """
        
        try:
            response = self.model.generate_content(prompt)  # type: ignore[attr-defined]
            return (response.text or "")
        except Exception as e:
            logger.error(f"Error generating chat response: {str(e)}")
            return "I'm sorry, I encountered an error while processing your request."

    async def generate_chat_response_with_files(self, query: str, context: str, attached_files: Optional[List[Dict[str, Any]]] = None) -> str:
        """Generate chat response based on query, context, and optional attached files - OPTIMIZED"""
        # Process attached files if any (with caching)
        file_context = ""
        if attached_files:
            try:
                import pandas as pd
            except ImportError:
                logger.error("pandas not available for file processing")
                return "I'm sorry, pandas is not available for file processing. Please install pandas to use file attachments."
                
            file_context = await self._process_attached_files_optimized(attached_files)
        
        # Use optimized context (smaller, more focused)
        prompt = f"""
        You are a helpful medical assistant with access to patient data and any uploaded documents.
        
        Context: {context[:1500]}  
        
        File Data: {file_context[:2000]}
        
        User Question: {query}
        
        Please provide a concise, helpful response. Use bullet points and formatting where appropriate.
        Keep responses focused and under 500 words unless specifically asked for detailed analysis.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text or ""
        except Exception as e:
            logger.error(f"Error generating chat response: {str(e)}")
            return "I'm sorry, I encountered an error while processing your request."

    async def _process_attached_files_optimized(self, files: List[Dict[str, Any]]) -> str:
        """Process attached files with optimization and caching"""
        from .chat_context_service import chat_context_service
        
        context_parts = []
        
        for file_data in files:
            try:
                file_id = file_data.get('file_id', str(hash(file_data.get('name', ''))))
                
                # Check if we already processed this file
                cached_summary = chat_context_service.get_cached_file_summary(file_id)
                if cached_summary:
                    context_parts.append(cached_summary)
                    continue
                
                file_content = file_data.get('content')
                file_name = file_data.get('name', 'unknown_file')
                file_type = file_data.get('type', 'application/octet-stream')
                
                print(f"📎 Processing attached file: {file_name} ({file_type})")
                logger.info(f"Processing attached file: {file_name} ({file_type})")
                
                # Handle different file types with optimization
                if file_type in ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'] or file_name.lower().endswith(('.xls', '.xlsx')):
                    content = await self._process_excel_file_optimized(file_content, file_name)
                elif file_type == 'text/csv' or file_name.lower().endswith('.csv'):
                    content = await self._process_csv_file_optimized(file_content, file_name)
                elif file_type.startswith('image/') or file_name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.tiff')):
                    content = await self._process_image_file_optimized(file_content, file_name, file_type)
                elif file_type == 'application/pdf' or file_name.lower().endswith('.pdf'):
                    content = await self._process_pdf_file_optimized(file_content, file_name)
                elif file_type.startswith('text/') or file_name.lower().endswith('.txt'):
                    content = await self._process_text_file_optimized(file_content, file_name)
                else:
                    content = f"File '{file_name}' - {file_type} - Processing available on request."
                
                # Cache the processed content
                chat_context_service.cache_file_summary(file_id, content)
                context_parts.append(content)
                
            except Exception as e:
                logger.error(f"Error processing file {file_name}: {str(e)}")
                context_parts.append(f"Error processing file '{file_name}': {str(e)}")
        
        return "\n\n".join(context_parts)

    async def _process_excel_file_optimized(self, file_content: bytes, file_name: str) -> str:
        """Process Excel file with optimization - return summary only"""
        try:
            import pandas as pd
            import tempfile
            import os
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                tmp_file.write(file_content)
                tmp_file_path = tmp_file.name
            
            # Read only first 1000 rows for faster processing
            try:
                df = pd.read_excel(tmp_file_path, nrows=1000)
            except Exception:
                try:
                    df = pd.read_excel(tmp_file_path, engine='openpyxl', nrows=1000)
                except Exception:
                    df = pd.read_excel(tmp_file_path, engine='xlrd', nrows=1000)
            
            # Clean up temp file
            os.unlink(tmp_file_path)
            
            # Generate CONCISE summary
            summary = f"📊 {file_name}: {df.shape[0]} rows, {df.shape[1]} cols\n"
            summary += f"Columns: {', '.join(df.columns.astype(str).tolist()[:10])}{'...' if len(df.columns) > 10 else ''}\n"
            
            # Add basic statistics for numeric columns (limit to top 3)
            numeric_cols = df.select_dtypes(include=['number']).columns[:3]
            if len(numeric_cols) > 0:
                summary += "Key stats: "
                stats = []
                for col in numeric_cols:
                    if df[col].notna().any():
                        stats.append(f"{col}: avg={df[col].mean():.1f}")
                summary += ", ".join(stats) + "\n"
            
            # Show only first 3 rows
            summary += f"Sample:\n{df.head(3).to_string(index=False, max_cols=5)}"
            
            return summary
            
        except Exception as e:
            return f"Excel file '{file_name}': Error - {str(e)}"

    async def _process_csv_file_optimized(self, file_content: bytes, file_name: str) -> str:
        """Process CSV file with optimization"""
        try:
            import pandas as pd
            from io import StringIO
            
            # Decode content
            content_str = file_content.decode('utf-8', errors='ignore')
            
            # Read only first 1000 rows
            df = pd.read_csv(StringIO(content_str), nrows=1000)
            
            # Generate CONCISE summary
            summary = f"📋 {file_name}: {df.shape[0]} rows, {df.shape[1]} cols\n"
            summary += f"Columns: {', '.join(df.columns.astype(str).tolist()[:10])}{'...' if len(df.columns) > 10 else ''}\n"
            
            # Add basic statistics for numeric columns (limit to top 3)
            numeric_cols = df.select_dtypes(include=['number']).columns[:3]
            if len(numeric_cols) > 0:
                summary += "Key stats: "
                stats = []
                for col in numeric_cols:
                    if df[col].notna().any():
                        stats.append(f"{col}: avg={df[col].mean():.1f}")
                summary += ", ".join(stats) + "\n"
            
            # Show only first 3 rows
            summary += f"Sample:\n{df.head(3).to_string(index=False, max_cols=5)}"
            
            return summary
            
        except Exception as e:
            return f"CSV file '{file_name}': Error - {str(e)}"

    async def _process_image_file_optimized(self, file_content: bytes, file_name: str, file_type: str) -> str:
        """Process image file with optimization for chat context"""
        try:
            image = Image.open(io.BytesIO(file_content))
            
            prompt = f"""
            Analyze this image file '{file_name}' quickly and provide a concise summary.
            If it contains medical information, charts, tables, or any healthcare-related data, 
            extract the key information in 2-3 sentences maximum.
            Focus on the most important textual information and data values.
            """
            
            response = self._generate_content_with_image(prompt, image)
            # Truncate for optimization
            if len(response) > 500:
                response = response[:500] + "... [truncated for performance]"
            return f"🖼️ {file_name}: {response}"
            
        except Exception as e:
            return f"Image file '{file_name}': Error - {str(e)}"

    async def _process_pdf_file_optimized(self, file_content: bytes, file_name: str) -> str:
        """Process PDF file with optimization for chat context"""
        try:
            # Create temp file for PDF
            temp_dir = tempfile.mkdtemp()
            pdf_path = os.path.join(temp_dir, file_name)
            
            with open(pdf_path, 'wb') as f:
                f.write(file_content)
            
            # Upload to Gemini
            uploaded_file = self.client.files.upload(
                file=pdf_path,
                config={"mime_type": "application/pdf"}
            )
            
            prompt = f"""
            Analyze this PDF document '{file_name}' and provide a concise summary in 2-3 sentences.
            If it contains medical data, patient information, or healthcare records,
            extract only the most important key points and data values.
            Keep the response under 300 words for performance.
            """
            
            # Generate content using uploaded file
            resp_obj = self.client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=[
                    {"role": "user", "parts": [
                        {"file_data": {"mime_type": uploaded_file.mime_type, "file_uri": uploaded_file.uri}},
                        {"text": prompt}
                    ]}
                ]
            )
            
            response = resp_obj.text or ""
            
            # Clean up
            shutil.rmtree(temp_dir)
            
            # Truncate for optimization
            if len(response) > 500:
                response = response[:500] + "... [truncated for performance]"
            
            return f"📄 {file_name}: {response}"
            
        except Exception as e:
            return f"PDF file '{file_name}': Error - {str(e)}"

    async def _process_text_file_optimized(self, file_content: bytes, file_name: str) -> str:
        """Process text file with optimization"""
        try:
            content_str = file_content.decode('utf-8', errors='ignore')
            # Limit to first 1000 characters for faster processing
            if len(content_str) > 1000:
                content_str = content_str[:1000] + "... [truncated for performance]"
            return f"📝 {file_name}:\n{content_str}"
        except Exception as e:
            return f"Text file '{file_name}': Error - {str(e)}"

    async def _process_attached_files(self, files: List[Dict[str, Any]]) -> str:
        """Process attached files and return their content as context"""
        context_parts = []
        
        for file_data in files:
            try:
                file_content = file_data.get('content')
                file_name = file_data.get('name', 'unknown_file')
                file_type = file_data.get('type', 'application/octet-stream')
                
                print(f"📎 Processing attached file: {file_name} ({file_type})")
                logger.info(f"Processing attached file: {file_name} ({file_type})")
                
                # Handle different file types
                if file_type in ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'] or file_name.lower().endswith(('.xls', '.xlsx')):
                    # Excel files
                    content = await self._process_excel_file(file_content, file_name)
                elif file_type == 'text/csv' or file_name.lower().endswith('.csv'):
                    # CSV files
                    content = await self._process_csv_file(file_content, file_name)
                elif file_type.startswith('image/'):
                    # Image files
                    content = await self._process_image_file(file_content, file_name, file_type)
                elif file_type == 'application/pdf' or file_name.lower().endswith('.pdf'):
                    # PDF files
                    content = await self._process_pdf_file(file_content, file_name)
                elif file_type.startswith('text/') or file_name.lower().endswith('.txt'):
                    # Text files
                    content = await self._process_text_file(file_content, file_name)
                else:
                    content = f"File '{file_name}' (type: {file_type}) - Unable to process this file type."
                
                context_parts.append(content)
                
            except Exception as e:
                logger.error(f"Error processing file {file_name}: {str(e)}")
                context_parts.append(f"Error processing file '{file_name}': {str(e)}")
        
        return "\n\n".join(context_parts)

    async def _process_excel_file(self, file_content: bytes, file_name: str) -> str:
        """Process Excel file and return summary"""
        try:
            import pandas as pd
            import tempfile
            import os
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                tmp_file.write(file_content)
                tmp_file_path = tmp_file.name
            
            # Read Excel file with pandas
            try:
                df = pd.read_excel(tmp_file_path)
            except Exception:
                # Try reading with different engine
                try:
                    df = pd.read_excel(tmp_file_path, engine='openpyxl')
                except Exception:
                    df = pd.read_excel(tmp_file_path, engine='xlrd')
            
            # Clean up temp file
            os.unlink(tmp_file_path)
            
            # Generate summary
            summary = f"📊 Excel File: {file_name}\n"
            summary += f"Shape: {df.shape[0]} rows, {df.shape[1]} columns\n"
            summary += f"Columns: {', '.join(df.columns.astype(str).tolist())}\n\n"
            
            # Add basic statistics for numeric columns
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                summary += "📈 Numeric Data Summary:\n"
                for col in numeric_cols:
                    if df[col].notna().any():
                        summary += f"  {col}: mean={df[col].mean():.2f}, std={df[col].std():.2f}, range=({df[col].min():.2f}, {df[col].max():.2f})\n"
                summary += "\n"
            
            # Add sample data (first few rows)
            summary += "🔍 Sample Data (first 5 rows):\n"
            summary += df.head().to_string(index=False)
            summary += f"\n\nFull dataset contains {len(df)} records with the above structure."
            
            return summary
            
        except Exception as e:
            return f"Error processing Excel file '{file_name}': {str(e)}"

    async def _process_csv_file(self, file_content: bytes, file_name: str) -> str:
        """Process CSV file and return summary"""
        try:
            import pandas as pd
            from io import StringIO
            
            # Decode content
            content_str = file_content.decode('utf-8', errors='ignore')
            
            # Create DataFrame
            df = pd.read_csv(StringIO(content_str))
            
            # Generate summary
            summary = f"📋 CSV File: {file_name}\n"
            summary += f"Shape: {df.shape[0]} rows, {df.shape[1]} columns\n"
            summary += f"Columns: {', '.join(df.columns.astype(str).tolist())}\n\n"
            
            # Add basic statistics for numeric columns
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                summary += "📈 Numeric Data Summary:\n"
                for col in numeric_cols:
                    if df[col].notna().any():
                        summary += f"  {col}: mean={df[col].mean():.2f}, std={df[col].std():.2f}, range=({df[col].min():.2f}, {df[col].max():.2f})\n"
                summary += "\n"
            
            # Add sample data
            summary += "🔍 Sample Data (first 5 rows):\n"
            summary += df.head().to_string(index=False)
            summary += f"\n\nFull dataset contains {len(df)} records with the above structure."
            
            return summary
            
        except Exception as e:
            return f"Error processing CSV file '{file_name}': {str(e)}"

    async def _process_image_file(self, file_content: bytes, file_name: str, file_type: str) -> str:
        """Process image file using Gemini Vision"""
        try:
            image = Image.open(io.BytesIO(file_content))
            
            prompt = f"""
            Analyze this image file '{file_name}' and describe its contents in detail.
            If it contains medical information, charts, tables, or any healthcare-related data, 
            please extract and summarize that information.
            """
            
            response = self._generate_content_with_image(prompt, image)
            return f"🖼️ Image File: {file_name}\nAnalysis: {response}"
            
        except Exception as e:
            return f"Error processing image file '{file_name}': {str(e)}"

    async def _process_pdf_file(self, file_content: bytes, file_name: str) -> str:
        """Process PDF file using Gemini"""
        try:
            # Create temp file for PDF
            temp_dir = tempfile.mkdtemp()
            pdf_path = os.path.join(temp_dir, file_name)
            
            with open(pdf_path, 'wb') as f:
                f.write(file_content)
            
            # Upload to Gemini
            uploaded_file = self.client.files.upload(
                file=pdf_path,
                config={"mime_type": "application/pdf"}
            )
            
            prompt = f"""
            Analyze this PDF document '{file_name}' and extract all relevant information.
            If it contains medical data, patient information, test results, or healthcare records,
            please summarize the key findings and data points.
            """
            
            # Generate content using uploaded file
            resp_obj = self.client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=[
                    {"role": "user", "parts": [
                        {"file_data": {"mime_type": uploaded_file.mime_type, "file_uri": uploaded_file.uri}},
                        {"text": prompt}
                    ]}
                ]
            )
            
            response = resp_obj.text or ""
            
            # Clean up
            shutil.rmtree(temp_dir)
            
            return f"📄 PDF File: {file_name}\nContent: {response}"
            
        except Exception as e:
            return f"Error processing PDF file '{file_name}': {str(e)}"

    async def _process_text_file(self, file_content: bytes, file_name: str) -> str:
        """Process text file"""
        try:
            content_str = file_content.decode('utf-8', errors='ignore')
            return f"📝 Text File: {file_name}\nContent:\n{content_str}"
        except Exception as e:
            return f"Error processing text file '{file_name}': {str(e)}"
    
    async def _process_image_file_chat(self, file_content: bytes, file_name: str, file_type: str) -> str:
        """Process image file using Gemini Vision for chat context"""
        try:
            image = Image.open(io.BytesIO(file_content))
            
            prompt = f"""
            Analyze this image file '{file_name}' and describe its contents in detail.
            If it contains medical information, charts, tables, or any healthcare-related data, 
            please extract and summarize that information clearly and concisely.
            Focus on extracting any textual information, data values, or medical observations.
            """
            
            response = self._generate_content_with_image(prompt, image)
            return f"🖼️ Image File: {file_name}\nAnalysis: {response}"
            
        except Exception as e:
            return f"Error processing image file '{file_name}': {str(e)}"

    async def _process_pdf_file_chat(self, file_content: bytes, file_name: str) -> str:
        """Process PDF file using Gemini for chat context"""
        try:
            # Create temp file for PDF
            temp_dir = tempfile.mkdtemp()
            pdf_path = os.path.join(temp_dir, file_name)
            
            with open(pdf_path, 'wb') as f:
                f.write(file_content)
            
            # Upload to Gemini
            uploaded_file = self.client.files.upload(
                file=pdf_path,
                config={"mime_type": "application/pdf"}
            )
            
            prompt = f"""
            Analyze this PDF document '{file_name}' and extract all relevant information.
            If it contains medical data, patient information, test results, or healthcare records,
            please summarize the key findings and data points in a clear and organized manner.
            """
            
            # Generate content using uploaded file
            resp_obj = self.client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=[
                    {"role": "user", "parts": [
                        {"file_data": {"mime_type": uploaded_file.mime_type, "file_uri": uploaded_file.uri}},
                        {"text": prompt}
                    ]}
                ]
            )
            
            response = resp_obj.text or ""
            
            # Clean up
            shutil.rmtree(temp_dir)
            
            return f"📄 PDF File: {file_name}\nContent: {response}"
            
        except Exception as e:
            return f"Error processing PDF file '{file_name}': {str(e)}"

    async def _process_text_file_chat(self, file_content: bytes, file_name: str) -> str:
        """Process text file for chat context"""
        try:
            content_str = file_content.decode('utf-8', errors='ignore')
            # Limit text length for context
            if len(content_str) > 5000:
                content_str = content_str[:5000] + "... [truncated]"
            return f"📝 Text File: {file_name}\nContent:\n{content_str}"
        except Exception as e:
            return f"Error processing text file '{file_name}': {str(e)}"
