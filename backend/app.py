"""
MediScan AI - Backend Flask Application
Real-time multimodal medical document analyzer
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
from datetime import datetime
import traceback
from dotenv import load_dotenv
import numpy as np

# Load environment variables from .env file
load_dotenv()

# Import custom model modules
from models.ocr_model import OCRModel
from models.nlp_model import NLPModel
from models.cnn_model import CNNModel
from models.mri_model import MRIModel
from models.ct_model import CTModel
from explainability.gradcam import GradCAM
from utils.helpers import download_image, upload_to_storage, create_thumbnail

# Import new utilities
from utils.document_processor import process_document_file
from utils.diagnosis_suggestor import diagnosis_suggestor
from utils.imaging_recommendations import imaging_recommendations
from utils.fhir_export import fhir_exporter
from utils.lab_parser import parse as parse_lab
from utils.pdf_utils import pdf_bytes_to_images
import base64
from io import BytesIO

# Import NEW features - Compliance, Real-time
from utils.compliance import ComplianceManager
from utils.realtime import RealtimeManager

# Advanced explainability (SHAP/LIME) - DISABLED for Render free tier
# These require scipy which needs Fortran compiler (not available on free tier)
# Grad-CAM provides excellent visualization and works perfectly!
EXPLAINABILITY_ADVANCED = False
shap_explainer = None
lime_explainer = None
print("ℹ️ Using Grad-CAM for explainability (SHAP/LIME disabled - requires scipy/Fortran)")
print("  Grad-CAM provides excellent heatmap visualizations! ✅")

# Configure Tesseract OCR path for Windows
try:
    import pytesseract
    if os.name == 'nt':  # Windows
        tesseract_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            r'C:\Tesseract-OCR\tesseract.exe'
        ]
        for path in tesseract_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                print(f"✓ Tesseract OCR found at: {path}")
                break
        else:
            print("⚠ Tesseract not found in standard locations")
except ImportError:
    print("⚠ pytesseract not installed")

app = Flask(__name__)
CORS(app)

# Initialize Firebase Admin SDK (No Storage needed - using base64)
try:
    # For local development - use service account key
    if os.path.exists('firebase-credentials.json'):
        cred = credentials.Certificate('firebase-credentials.json')
        firebase_admin.initialize_app(cred)
    else:
        # For Render deployment - use environment variable
        firebase_config = os.environ.get('FIREBASE_CONFIG')
        if firebase_config:
            cred = credentials.Certificate(json.loads(firebase_config))
            firebase_admin.initialize_app(cred)
except Exception as e:
    print(f"Firebase initialization warning: {e}")

db = firestore.client() if firebase_admin._apps else None

# Initialize Compliance Manager
compliance_manager = ComplianceManager(db=db)

# Initialize Real-time Manager (WebSocket support)
realtime_manager = RealtimeManager(app=app, db=db)

# Initialize AI Models (lazy loading for faster startup)
ocr_model = None
nlp_model = None
cnn_model = None
mri_model = None
ct_model = None
gradcam = None

def get_ocr_model():
    global ocr_model
    if ocr_model is None:
        ocr_model = OCRModel()
    return ocr_model

def get_nlp_model():
    global nlp_model
    if nlp_model is None:
        nlp_model = NLPModel()
    return nlp_model

def get_cnn_model():
    global cnn_model
    if cnn_model is None:
        cnn_model = CNNModel()
    return cnn_model

def get_mri_model():
    global mri_model
    if mri_model is None:
        mri_model = MRIModel()
    return mri_model

def get_ct_model():
    global ct_model
    if ct_model is None:
        ct_model = CTModel()
    return ct_model

def get_gradcam():
    global gradcam
    if gradcam is None:
        gradcam = GradCAM()
    return gradcam


def _patient_exists(patient_id: str) -> bool:
    """Check if a patient document exists in Firestore."""
    try:
        if not db or not patient_id:
            return False
        doc = db.collection('patients').document(str(patient_id)).get()
        return doc.exists
    except Exception:
        return False


@app.route('/')
def home():
    """Health check endpoint"""
    return jsonify({
        "status": "online",
        "service": "MediScan AI Backend",
        "version": "1.0.0"
    })


@app.route('/api/health', methods=['GET'])
def health():
    """Detailed health check"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "models": {
            "ocr": "ready",
            "nlp": "ready",
            "cnn": "ready"
        }
    })


@app.route('/api/process', methods=['POST'])
def process_document():
    """
    Main endpoint to process medical documents
    Accepts: file_url, document_type, patient_id, user_id
    Returns: OCR text, NLP entities, CNN results, heatmap URL
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        file_url = data.get('file_url')
        document_type = data.get('document_type', 'prescription')
        patient_id = data.get('patient_id')
        user_id = data.get('user_id')
        
        if not file_url:
            return jsonify({"error": "file_url is required"}), 400

        # Enforce patient existence before analysis (when DB is available)
        if db and patient_id:
            if not _patient_exists(patient_id):
                return jsonify({
                    "error": "Unknown patient_id. Create the patient first, then run analysis.",
                    "patient_id": patient_id
                }), 400
        
        # Handle base64 PDF (first page) or image
        image = None
        if isinstance(file_url, str) and file_url.startswith('data:application/pdf'):
            try:
                b64 = file_url.split(',', 1)[1]
                pdf_bytes = base64.b64decode(b64)
                pages = pdf_bytes_to_images(pdf_bytes)
                if not pages:
                    return jsonify({"error": "PDF parsed but no pages found"}), 400
                image = pages[0]
                print(f"✓ Loaded first PDF page as image: {image.size}")
            except Exception as e:
                return jsonify({"error": f"PDF processing failed: {e}"}), 500
        else:
            # Download image from URL or base64
            image = download_image(file_url)
        
        # Initialize result object
        result = {
            "patient_id": patient_id,
            "user_id": user_id,
            "document_type": document_type,
            "file_url": file_url,
            "timestamp": datetime.now().isoformat(),
            "status": "processing"
        }
        
        # Quick modality guess to help warnings and routing
        def _edge_score(arr):
            try:
                gx = np.abs(np.diff(arr.astype(np.float32), axis=1))
                gy = np.abs(np.diff(arr.astype(np.float32), axis=0))
                return float((gx.mean() + gy.mean()) / 2.0)
            except Exception:
                return 20.0

        img_arr = np.array(image.convert('L'))
        H, W = img_arr.shape
        # Use center crop for heuristics to avoid PDF white margins
        y0, y1 = int(H * 0.1), int(H * 0.9)
        x0, x1 = int(W * 0.1), int(W * 0.9)
        core = img_arr[y0:y1, x0:x1] if y1 > y0 and x1 > x0 else img_arr
        brightness_guess = float(core.mean())
        contrast_guess = float(core.std())
        edge_guess = _edge_score(core)
        # Dental panoramic heuristic: wide aspect + stronger edges in lower band
        aspect_guess = float(W) / float(H) if H else 1.0
        try:
            gx = np.abs(np.diff(img_arr.astype(np.float32), axis=1))
            gy = np.abs(np.diff(img_arr.astype(np.float32), axis=0))
            emap = (gx[:-1, :] + gy[:, :-1])
            split_y = int(0.6 * emap.shape[0])
            upper_e = float(np.mean(emap[:split_y, :]))
            lower_e = float(np.mean(emap[split_y:, :]))
            lower_upper_ratio = (lower_e + 1e-6) / (upper_e + 1e-6)
        except Exception:
            lower_upper_ratio = 1.0
        dental_like = (aspect_guess > 1.6 and lower_upper_ratio > 1.5)
        looks_like_xray = ((brightness_guess < 170 and contrast_guess > 30 and edge_guess > 18) or dental_like)
        # Gemini Vision assist for modality gate (helps with PDFs with big margins)
        try:
            from models.gemini_vision import gemini_vision as _GV
            if _GV and _GV.is_available():
                g = _GV.analyze(image)
                if g and g.get('modality') in ['chest-xray', 'non-chest-xray'] and float(g.get('confidence', 0.8)) > 0.75:
                    looks_like_xray = True
        except Exception:
            pass
        looks_like_document = (brightness_guess > 185 and contrast_guess < 55)

        # Imaging types (skip OCR/NLP): lab reports are textual → should NOT be here
        xray_types = ['xray', 'mri', 'ct_scan']

        # Step 1: OCR - only for non-imaging documents
        if document_type not in xray_types:
            # Hard gate: if the file strongly looks like an imaging scan, skip OCR entirely
            if looks_like_xray:
                result["ocr_skipped"] = True
                result["status"] = "mismatch"
                result["type_mismatch_warning"] = "The uploaded image appears to be a medical scan (e.g., X-ray). Analysis for prescriptions was skipped. Please re-upload using the correct type."
                result["recommended_type"] = "xray"
                # Save and return early (no OCR/NLP performed)
                if db:
                    doc_ref = db.collection('analyses').add(result)
                    result["document_id"] = doc_ref[1].id
                return jsonify(result), 200

            print("Running OCR...")
            ocr = get_ocr_model()
            ocr_result = ocr.extract_text(image)

            # Format the text into organized sections (prefer Gemini structured)
            formatted_text = None
            if isinstance(ocr_result, dict):
                if ocr_result.get("ocr_text_formatted"):
                    formatted_text = ocr_result["ocr_text_formatted"]
                elif ocr_result.get("gemini_structured"):
                    gs = ocr_result["gemini_structured"]
                    formatted_text = {
                        "header": gs.get("header", ""),
                        "patient_info": gs.get("patient_info", ""),
                        "medications": gs.get("medications", []) or [],
                        "doctor_info": gs.get("doctor_info", ""),
                        "full_text": ocr_result.get("text", "")
                    }
            if formatted_text is None:
                formatted_text = format_prescription_text(ocr_result["text"]) 

            result["ocr_text"] = ocr_result["text"]
            result["ocr_text_formatted"] = formatted_text
            result["ocr_confidence"] = ocr_result["confidence"]
            result["is_handwritten"] = ocr_result.get("is_handwritten", False)

            if "warning" in ocr_result:
                result["ocr_warning"] = ocr_result["warning"]
            if "info" in ocr_result:
                result["ocr_info"] = ocr_result["info"]
            # Warn if the content appears to be an X-ray while type is prescription
            if looks_like_xray:
                result["type_mismatch_warning"] = "The uploaded image looks like an X-ray, but 'Prescription' was selected. Please re-upload using the X-ray type for correct analysis."
                result["recommended_type"] = "xray"
        else:
            result["ocr_skipped"] = True
            if looks_like_document:
                result["type_mismatch_warning"] = "The uploaded image looks like a document, but 'X-ray' was selected. Please re-upload with the correct type for best results."
                result["recommended_type"] = "prescription"
        
        # Step 2: NLP/Lab parsing
        if document_type == 'lab_report' and result.get("ocr_text"):
            print("Parsing lab report...")
            lab = parse_lab(result["ocr_text"])
            result["lab_values"] = lab.get("values", [])
            result["lab_abnormal_count"] = lab.get("abnormal_count", 0)
            if lab.get("critical_flags"):
                result["lab_critical_flags"] = lab["critical_flags"]
        elif document_type not in xray_types and result.get("ocr_text"):
            print("Running NLP...")
            nlp = get_nlp_model()
            nlp_result = nlp.extract_entities(result["ocr_text"])
            result["entities"] = nlp_result["entities"]
            result["medicines"] = nlp_result["medicines"]
            result["dosages"] = nlp_result["dosages"]
            result["durations"] = nlp_result["durations"]
            # Pair medicines with nearest dosage/duration for frontend convenience
            result["medication_items"] = pair_medications(
                result.get("medicines", []),
                result.get("dosages", []),
                result.get("durations", [])
            )

        # If Gemini provided structured medications, merge them into medicines list for UI
        try:
            structured_meds = []
            if result.get("ocr_text_formatted") and result["ocr_text_formatted"].get("medications"):
                structured_meds = result["ocr_text_formatted"]["medications"]
            if structured_meds:
                existing = {m.get("text", "").strip().lower() for m in result["medicines"] if isinstance(m, dict)}
                for sm in structured_meds:
                    label = sm.get("name") if isinstance(sm, dict) else str(sm)
                    label_norm = label.strip().lower()
                    if label and label_norm not in existing:
                        result["medicines"].append({"text": label})
                        existing.add(label_norm)
        except Exception:
            pass
        
        # Step 3: Imaging Analysis (X-ray only here; MRI/CT handled below)
        if document_type in ['xray']:
            print("Running CNN analysis...")
            cnn = get_cnn_model()
            cnn_result = cnn.analyze_image(image)
            result["cnn_prediction"] = cnn_result["prediction"]
            result["cnn_confidence"] = cnn_result["confidence"]
            result["cnn_class"] = cnn_result["class_name"]
            # New: pass through detailed stats for richer UI
            if isinstance(cnn_result, dict):
                if cnn_result.get("all_probabilities"):
                    result["cnn_all_probabilities"] = cnn_result.get("all_probabilities")
                if cnn_result.get("image_stats"):
                    result["cnn_image_stats"] = cnn_result.get("image_stats")
                if cnn_result.get("findings"):
                    result["cnn_findings"] = cnn_result.get("findings")

            # Grad-CAM for 2D models
            print("Generating Grad-CAM...")
            gradcam_processor = get_gradcam()
            heatmap = gradcam_processor.generate_heatmap(image, cnn.model, cnn_result["prediction"])
            heatmap_url = upload_to_storage(heatmap, f"heatmaps/{patient_id}_{datetime.now().timestamp()}.png")
            result["heatmap_url"] = heatmap_url
            # Create small thumbnail for database storage
            result["heatmap_thumbnail"] = create_thumbnail(heatmap, size=(200, 200), quality=50)
            
            # Structured explainability metadata
            # Note: SHAP/LIME disabled for now due to document size limits (can generate on-demand)
            result["explainability"] = {
                "gradcam_url": heatmap_url,
                "shap_supported": False,  # Available on-demand via /api/explainability/generate
                "lime_supported": False   # Available on-demand via /api/explainability/generate
            }
            
            # Generate imaging recommendations for X-ray
            print("Generating imaging recommendations...")
            imaging_recs = imaging_recommendations.generate_recommendations(result, document_type='xray')
            result["imaging_recommendations"] = imaging_recs

        elif document_type == 'mri':
            print("Running MRI analysis...")
            mri = get_mri_model()
            mri_result = mri.analyze_image(image)
            # Return MRI-specific keys
            if isinstance(mri_result, dict):
                result.update({
                    "mri_label": mri_result.get("mri_label"),
                    "mri_confidence": mri_result.get("mri_confidence"),
                    "mri_body_region": mri_result.get("mri_body_region"),
                    "mri_findings": mri_result.get("mri_findings"),
                    "mri_stats": mri_result.get("mri_stats"),
                    "mri_backend": mri_result.get("used_backend")
                })
                
                # Generate imaging recommendations for MRI
                print("Generating imaging recommendations...")
                imaging_recs = imaging_recommendations.generate_recommendations(result, document_type='mri')
                result["imaging_recommendations"] = imaging_recs
        elif document_type == 'ct_scan':
            print("Running CT analysis...")
            ct = get_ct_model()
            ct_result = ct.analyze_image(image)
            if isinstance(ct_result, dict):
                result.update({
                    "ct_label": ct_result.get("ct_label"),
                    "ct_confidence": ct_result.get("ct_confidence"),
                    "ct_body_region": ct_result.get("ct_body_region"),
                    "ct_findings": ct_result.get("ct_findings"),
                    "ct_stats": ct_result.get("ct_stats"),
                    "ct_backend": ct_result.get("used_backend")
                })
                
                # Generate imaging recommendations for CT
                print("Generating imaging recommendations...")
                imaging_recs = imaging_recommendations.generate_recommendations(result, document_type='ct_scan')
                result["imaging_recommendations"] = imaging_recs
        
        # Step 5: Generate AI-assisted diagnosis suggestions
        if result.get("medicines"):
            print("Generating diagnosis suggestions...")
            cnn_results = None
            if result.get("cnn_class"):
                cnn_results = {
                    "class_name": result.get("cnn_class"),
                    "confidence": result.get("cnn_confidence")
                }
            
            diagnosis_suggestions = diagnosis_suggestor.suggest_diagnosis(
                result["medicines"],
                result.get("ocr_text", ""),
                cnn_results
            )
            result["diagnosis_suggestions"] = diagnosis_suggestions
            print(f"  ✓ Suggested {len(diagnosis_suggestions.get('possible_conditions', []))} possible conditions")
        
        # Step 6: Generate diagnosis summary
        result["diagnosis_summary"] = generate_diagnosis_summary(result)
        result["status"] = "completed"
        
        # Step 6: Save to Firestore (exclude large base64 images to stay under 1MB limit)
        if db:
            # Create a cleaned copy without large base64 visualizations
            firestore_result = {k: v for k, v in result.items() if k not in [
                'shap_visualization',  # Exclude large SHAP image
                'lime_visualization_positive',  # Exclude large LIME images
                'lime_visualization_both',
                'heatmap_url',  # Exclude full heatmap (too large)
                'heatmap_thumbnail',  # Will be stored as heatmap_url instead
                'file_url'  # Exclude original file (too large if base64)
            ]}
            
            # Store thumbnail version of heatmap (small enough for Firestore)
            if result.get('heatmap_thumbnail'):
                firestore_result['heatmap_url'] = result['heatmap_thumbnail']  # Store thumbnail as heatmap_url
            
            # Create and store thumbnail of original image if it's base64
            if result.get('file_url'):
                if isinstance(result['file_url'], str) and result['file_url'].startswith('data:image'):
                    try:
                        # Create thumbnail for database
                        img_for_thumb = download_image(result['file_url'])
                        firestore_result['file_thumbnail'] = create_thumbnail(img_for_thumb, size=(200, 200), quality=50)
                    except Exception:
                        firestore_result['has_file_url'] = True  # Just a flag if thumbnail fails
                elif isinstance(result['file_url'], str) and not result['file_url'].startswith('data:'):
                    firestore_result['file_url'] = result['file_url']  # Store URL if it's not base64
            
            # Keep explainability metadata (small)
            if 'explainability' in result:
                firestore_result['explainability'] = {
                    'gradcam_available': True,
                    'shap_supported': False,  # On-demand only
                    'lime_supported': False   # On-demand only
                }
            
            try:
                doc_ref = db.collection('analyses').add(firestore_result)
                result["document_id"] = doc_ref[1].id
                
                # Save minimal metadata to patient subcollection
                if patient_id:
                    db.collection('patients').document(str(patient_id))\
                        .collection('analyses').document(result["document_id"]).set({
                            "analysis_id": result["document_id"],
                            "timestamp": result.get("timestamp"),
                            "document_type": result.get("document_type"),
                            "diagnosis_summary": result.get("diagnosis_summary"),
                            "cnn_class": result.get("cnn_class"),
                            "ocr_confidence": result.get("ocr_confidence")
                        })
            except Exception as e:
                print(f"Firestore save error: {e}")
                # Still continue and return the result to the user
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"Error processing document: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@app.route('/api/process-prescription', methods=['POST'])
def process_prescription():
    """Specialized endpoint for prescription processing"""
    try:
        data = request.get_json()
        file_url = data.get('file_url')
        
        if not file_url:
            return jsonify({"error": "file_url is required"}), 400
        
        image = download_image(file_url)
        
        # OCR extraction
        ocr = get_ocr_model()
        ocr_result = ocr.extract_text(image)
        
        # NLP parsing for medicines
        nlp = get_nlp_model()
        nlp_result = nlp.extract_entities(ocr_result["text"])
        
        result = {
            "text": ocr_result["text"],
            "medicines": nlp_result["medicines"],
            "dosages": nlp_result["dosages"],
            "durations": nlp_result["durations"],
            "entities": nlp_result["entities"],
            "timestamp": datetime.now().isoformat()
        }
        
        if db:
            db.collection('prescriptions').add(result)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/process-batch', methods=['POST'])
def process_batch():
    """Process multiple documents at once (PDF pages, multiple images, DICOM)"""
    try:
        data = request.get_json()
        file_urls = data.get('file_urls', [])  # List of file URLs
        patient_id = data.get('patient_id', '01')
        user_id = data.get('user_id', 'user_001')
        document_type = data.get('document_type', 'prescription')
        
        if not file_urls:
            return jsonify({"error": "file_urls array is required"}), 400
        
        # Enforce patient existence before analysis (when DB is available)
        if db and patient_id:
            if not _patient_exists(patient_id):
                return jsonify({
                    "error": "Unknown patient_id. Create the patient first, then run analysis.",
                    "patient_id": patient_id
                }), 400
        
        print(f"\n=== Batch Processing {len(file_urls)} files ===")
        
        results = []
        
        # Process each file (supports images and base64 PDFs)
        for idx, file_url in enumerate(file_urls):
            print(f"\nProcessing file {idx+1}/{len(file_urls)}")
            try:
                if isinstance(file_url, str) and file_url.startswith('data:application/pdf'):
                    # Base64 PDF: split into pages
                    try:
                        b64 = file_url.split(',', 1)[1]
                        pdf_bytes = base64.b64decode(b64)
                        pages = pdf_bytes_to_images(pdf_bytes)
                    except Exception as e:
                        raise RuntimeError(f"PDF decode failed: {e}")

                    for p_idx, page_img in enumerate(pages, start=1):
                        page_res = {
                            "file_number": idx + 1,
                            "page": p_idx,
                            "file_url": f"{file_url[:40]}...",
                            "patient_id": patient_id,
                            "user_id": user_id,
                            "document_type": document_type,
                            "timestamp": datetime.now().isoformat()
                        }
                        # OCR + NLP pairing
                        ocr = get_ocr_model()
                        ocr_result = ocr.extract_text(page_img)
                        formatted_text = format_prescription_text(ocr_result.get("text", ""))
                        page_res.update({
                            "ocr_text": ocr_result.get("text", ""),
                            "ocr_text_formatted": formatted_text,
                            "ocr_confidence": ocr_result.get("confidence", 0.0),
                            "is_handwritten": ocr_result.get("is_handwritten", False)
                        })
                        nlp = get_nlp_model()
                        nlp_result = nlp.extract_entities(ocr_result.get("text", ""))
                        page_res.update({
                            "medicines": nlp_result.get("medicines", []),
                            "dosages": nlp_result.get("dosages", []),
                            "durations": nlp_result.get("durations", []),
                            "medication_items": pair_medications(
                                nlp_result.get("medicines", []),
                                nlp_result.get("dosages", []),
                                nlp_result.get("durations", [])
                            )
                        })
                        # Save each page result if DB available
                        if db:
                            try:
                                doc_ref = db.collection('analyses').add(page_res)
                                page_res["document_id"] = doc_ref[1].id
                                db.collection('patients').document(str(patient_id))\
                                    .collection('analyses').document(page_res["document_id"]).set({
                                        "analysis_id": page_res["document_id"],
                                        "timestamp": page_res.get("timestamp"),
                                        "document_type": f"{document_type}-pdf-page",
                                        "cnn_class": page_res.get("cnn_class"),
                                        "ocr_confidence": page_res.get("ocr_confidence")
                                    })
                            except Exception:
                                pass
                        results.append(page_res)
                else:
                    # Process single image or URL
                    image = download_image(file_url)
                    result = {
                        "file_number": idx + 1,
                        "file_url": file_url,
                        "patient_id": patient_id,
                        "user_id": user_id,
                        "document_type": document_type,
                        "timestamp": datetime.now().isoformat()
                    }

                    if document_type not in ['xray', 'mri', 'ct_scan']:
                        # OCR + NLP for textual documents
                        ocr = get_ocr_model()
                        ocr_result = ocr.extract_text(image)
                        formatted_text = format_prescription_text(ocr_result.get("text", ""))
                        result.update({
                            "ocr_text": ocr_result.get("text", ""),
                            "ocr_text_formatted": formatted_text,
                            "ocr_confidence": ocr_result.get("confidence", 0.0),
                            "is_handwritten": ocr_result.get("is_handwritten", False)
                        })
                        nlp = get_nlp_model()
                        nlp_result = nlp.extract_entities(ocr_result.get("text", ""))
                        result.update({
                            "medicines": nlp_result.get("medicines", []),
                            "dosages": nlp_result.get("dosages", []),
                            "durations": nlp_result.get("durations", []),
                            "medication_items": pair_medications(
                                nlp_result.get("medicines", []),
                                nlp_result.get("dosages", []),
                                nlp_result.get("durations", [])
                            )
                        })
                    else:
                        # Imaging analysis
                        cnn = get_cnn_model()
                        cnn_result = cnn.analyze_image(image)
                        result.update({
                            "cnn_class": cnn_result.get("class_name"),
                            "cnn_confidence": cnn_result.get("confidence")
                        })
                        if isinstance(cnn_result, dict):
                            if cnn_result.get("all_probabilities"):
                                result["cnn_all_probabilities"] = cnn_result.get("all_probabilities")
                            if cnn_result.get("image_stats"):
                                result["cnn_image_stats"] = cnn_result.get("image_stats")
                            if cnn_result.get("findings"):
                                result["cnn_findings"] = cnn_result.get("findings")
                            # Grad-CAM for explainability
                            try:
                                heatmap = get_gradcam().generate_heatmap(image, cnn.model, cnn_result["prediction"]) 
                                heatmap_url = upload_to_storage(heatmap, f"heatmaps/{patient_id}_{datetime.now().timestamp()}.png")
                                result["heatmap_url"] = heatmap_url
                                result["explainability"] = {
                                    "gradcam_url": heatmap_url,
                                    "shap_supported": False,
                                    "lime_supported": False
                                }
                            except Exception:
                                pass

                    # Save item if DB available
                    if db:
                        try:
                            dref = db.collection('analyses').add(result)
                            result["document_id"] = dref[1].id
                            db.collection('patients').document(str(patient_id))\
                                .collection('analyses').document(result["document_id"]).set({
                                    "analysis_id": result["document_id"],
                                    "timestamp": result.get("timestamp"),
                                    "document_type": result.get("document_type"),
                                    "cnn_class": result.get("cnn_class"),
                                    "ocr_confidence": result.get("ocr_confidence")
                                })
                        except Exception:
                            pass
                    results.append(result)
                
            except Exception as e:
                print(f"Error processing file {idx+1}: {e}")
                results.append({
                    "file_number": idx + 1,
                    "file_url": file_url,
                    "error": str(e)
                })
        
        # Generate combined diagnosis if prescriptions
        if document_type == 'prescription':
            all_medicines = []
            for r in results:
                if "medicines" in r:
                    all_medicines.extend(r["medicines"])
            
            if all_medicines:
                combined_diagnosis = diagnosis_suggestor.suggest_diagnosis(all_medicines, "")
                return jsonify({
                    "batch_results": results,
                    "combined_diagnosis": combined_diagnosis,
                    "total_files": len(file_urls),
                    "successful": len([r for r in results if "error" not in r])
                }), 200
        
        return jsonify({
            "batch_results": results,
            "total_files": len(file_urls),
            "successful": len([r for r in results if "error" not in r])
        }), 200
        
    except Exception as e:
        print(f"Batch processing error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/export-fhir', methods=['POST'])
def export_fhir():
    """Export analysis results in FHIR format for hospital integration"""
    try:
        data = request.get_json()
        analysis_id = data.get('analysis_id')
        
        if not analysis_id:
            return jsonify({"error": "analysis_id is required"}), 400
        
        # Get analysis from Firestore
        if db:
            doc_ref = db.collection('analyses').document(analysis_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return jsonify({"error": "Analysis not found"}), 404
            
            analysis_data = doc.to_dict()
            
            # Export as FHIR bundle
            fhir_bundle = fhir_exporter.export_bundle(analysis_data)
            
            return jsonify({
                "fhir_bundle": fhir_bundle,
                "format": "FHIR R4",
                "analysis_id": analysis_id
            }), 200
        else:
            return jsonify({"error": "Database not available"}), 500
            
    except Exception as e:
        print(f"FHIR export error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/analyze-image', methods=['POST'])
def analyze_image():
    """Specialized endpoint for medical image analysis (X-ray, MRI, CT)"""
    try:
        data = request.get_json()
        file_url = data.get('file_url')
        patient_id = data.get('patient_id')
        
        if not file_url:
            return jsonify({"error": "file_url is required"}), 400
        
        image = download_image(file_url)
        
        # CNN analysis
        cnn = get_cnn_model()
        cnn_result = cnn.analyze_image(image)
        
        # Grad-CAM
        gradcam_processor = get_gradcam()
        heatmap = gradcam_processor.generate_heatmap(image, cnn.model, cnn_result["prediction"])
        
        # Upload heatmap
        heatmap_url = upload_to_storage(
            heatmap, 
            f"heatmaps/{patient_id}_{datetime.now().timestamp()}.png"
        )
        
        result = {
            "prediction": cnn_result["prediction"],
            "confidence": cnn_result["confidence"],
            "class_name": cnn_result["class_name"],
            "heatmap_url": heatmap_url,
            "timestamp": datetime.now().isoformat()
        }
        
        if db:
            db.collection('image_analyses').add(result)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/patients', methods=['GET', 'POST'])
def patients():
    """CRUD endpoint for patient management"""
    try:
        if request.method == 'GET':
            # Fetch all patients
            if not db:
                return jsonify({"patients": []}), 200
            
            patients_ref = db.collection('patients')
            patients_list = []
            
            for doc in patients_ref.stream():
                patient_data = doc.to_dict()
                patient_data['id'] = doc.id
                patients_list.append(patient_data)
            
            return jsonify({"patients": patients_list}), 200
        
        elif request.method == 'POST':
            # Create new patient (allow custom ID)
            data = request.get_json()
            
            if not db:
                return jsonify({"error": "Database not initialized"}), 500
            
            custom_id = (data.get('id') or '').strip()
            patient_data = {
                "name": data.get('name'),
                "age": data.get('age'),
                "gender": data.get('gender'),
                "contact": data.get('contact'),
                "email": data.get('email'),
                "medical_history": data.get('medical_history', ''),
                "created_at": datetime.now().isoformat(),
                "user_id": data.get('user_id')
            }
            
            if custom_id:
                if _patient_exists(custom_id):
                    return jsonify({"error": "Patient ID already exists", "id": custom_id}), 409
                db.collection('patients').document(custom_id).set(patient_data)
                patient_data['id'] = custom_id
            else:
                doc_ref = db.collection('patients').add(patient_data)
                patient_data['id'] = doc_ref[1].id
            
            return jsonify(patient_data), 201
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/patients/<patient_id>', methods=['GET'])
def get_patient(patient_id):
    """Fetch a single patient by ID"""
    try:
        if not db:
            return jsonify({"error": "Database not initialized"}), 500
        doc = db.collection('patients').document(str(patient_id)).get()
        if not doc.exists:
            return jsonify({"error": "Not found"}), 404
        data = doc.to_dict()
        data['id'] = doc.id
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/analytics', methods=['GET'])
def analytics():
    """Get analytics data for dashboard"""
    try:
        if not db:
            return jsonify({"error": "Database not initialized"}), 500
        
        # Fetch recent analyses
        analyses_ref = db.collection('analyses').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(100)
        analyses = [doc.to_dict() for doc in analyses_ref.stream()]
        
        # Calculate statistics
        total_analyses = len(analyses)
        medicine_frequency = {}
        diagnosis_patterns = {}
        
        for analysis in analyses:
            # Count medicines
            for medicine in analysis.get('medicines', []):
                med_name = medicine.get('text', '')
                medicine_frequency[med_name] = medicine_frequency.get(med_name, 0) + 1
            
            # Count diagnoses
            diagnosis = analysis.get('cnn_class', 'Unknown')
            diagnosis_patterns[diagnosis] = diagnosis_patterns.get(diagnosis, 0) + 1
        
        return jsonify({
            "total_analyses": total_analyses,
            "medicine_frequency": medicine_frequency,
            "diagnosis_patterns": diagnosis_patterns,
            "recent_analyses": analyses[:10]
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/patients-with-analyses', methods=['GET'])
def patients_with_analyses():
    """Return patients with aggregate info and latest analysis timestamp.

    Response: [{ id, name, created_at, analysis_count, last_analysis_ts }]
    """
    try:
        if not db:
            return jsonify({"patients": []}), 200

        items = []
        for doc in db.collection('patients').stream():
            p = doc.to_dict() or {}
            pid = doc.id
            # Count analyses via flat 'analyses' collection for performance
            count = 0
            last_ts = None
            try:
                q = db.collection('analyses').where('patient_id', '==', pid).order_by('timestamp', direction=firestore.Query.DESCENDING).limit(50)
                results = list(q.stream())
                count = len(results)
                if results:
                    last_ts = results[0].to_dict().get('timestamp')
            except Exception:
                # Fallback: try patient subcollection (may be fewer docs returned depending on limit)
                try:
                    q2 = db.collection('patients').document(pid).collection('analyses').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(50)
                    results2 = list(q2.stream())
                    count = len(results2)
                    if results2:
                        last_ts = results2[0].to_dict().get('timestamp')
                except Exception:
                    pass

            items.append({
                "id": pid,
                "name": p.get('name'),
                "created_at": p.get('created_at'),
                "analysis_count": count,
                "last_analysis_ts": last_ts
            })

        # Sort by last analysis time desc
        items.sort(key=lambda x: x.get('last_analysis_ts') or '', reverse=True)
        return jsonify({"patients": items}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/patients/<patient_id>/analyses', methods=['GET'])
def get_patient_analyses(patient_id):
    """List analyses for a patient (from subcollection, falls back to flat).

    Query params: limit (default 50)
    """
    try:
        if not db:
            return jsonify({"analyses": []}), 200

        try:
            limit_param = int(request.args.get('limit', '50'))
        except Exception:
            limit_param = 50

        analyses = []
        try:
            q = db.collection('patients').document(str(patient_id)).collection('analyses')\
                .order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit_param)
            for d in q.stream():
                a = d.to_dict() or {}
                a['id'] = d.id
                analyses.append(a)
        except Exception:
            # Fallback to flat collection
            q2 = db.collection('analyses').where('patient_id', '==', str(patient_id))\
                .order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit_param)
            for d in q2.stream():
                a = d.to_dict() or {}
                a['id'] = d.id
                analyses.append(a)

        return jsonify({"analyses": analyses}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/analyses/<analysis_id>', methods=['GET'])
def get_analysis(analysis_id):
    """Return an analysis document from the flat collection by id."""
    try:
        if not db:
            return jsonify({"error": "Database not initialized"}), 500
        doc = db.collection('analyses').document(str(analysis_id)).get()
        if not doc.exists:
            return jsonify({"error": "Not found"}), 404
        data = doc.to_dict() or {}
        data['id'] = doc.id
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/analyses/<analysis_id>', methods=['DELETE'])
def delete_analysis(analysis_id):
    """Delete an analysis from flat collection and patient subcollection if present."""
    try:
        if not db:
            return jsonify({"error": "Database not initialized"}), 500
        # Fetch to get patient_id
        doc_ref = db.collection('analyses').document(str(analysis_id))
        doc = doc_ref.get()
        if not doc.exists:
            return jsonify({"error": "Not found"}), 404
        data = doc.to_dict() or {}
        patient_id = data.get('patient_id')

        # Delete flat analysis
        doc_ref.delete()

        # Delete from patient subcollection (best-effort)
        try:
            if patient_id:
                db.collection('patients').document(str(patient_id))\
                  .collection('analyses').document(str(analysis_id)).delete()
        except Exception:
            pass

        return jsonify({"deleted": True, "analysis_id": analysis_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route('/api/process-pdf-auto', methods=['POST'])
def process_pdf_auto():
    """Auto-split a PDF and route each page to the correct analyzer.

    Accepts: file_url (data:application/pdf;base64,...), patient_id, user_id
    Returns: pages[] with per-page results and detected types.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        file_url = data.get('file_url')
        patient_id = data.get('patient_id', '01')
        user_id = data.get('user_id', 'user_001')
        if not file_url or not file_url.startswith('data:application/pdf'):
            return jsonify({"error": "Provide base64 PDF in file_url"}), 400

        # Enforce patient existence before analysis (when DB is available)
        if db and patient_id:
            if not _patient_exists(patient_id):
                return jsonify({
                    "error": "Unknown patient_id. Create the patient first, then run analysis.",
                    "patient_id": patient_id
                }), 400

        # Decode PDF
        b64 = file_url.split(',', 1)[1]
        pdf_bytes = base64.b64decode(b64)

        pages = pdf_bytes_to_images(pdf_bytes)
        results = []

        # Optional Gemini Vision for modality detection
        gem = None
        try:
            from models.gemini_vision import gemini_vision as gem
            if not gem.is_available():
                gem = None
        except Exception:
            gem = None

        for idx, img in enumerate(pages, start=1):
            page_res = {"page": idx}
            # Heuristic modality hints
            arr = np.array(img.convert('L'))
            def _edge_score(arr_):
                try:
                    gx = np.abs(np.diff(arr_.astype(np.float32), axis=1))
                    gy = np.abs(np.diff(arr_.astype(np.float32), axis=0))
                    return float((gx.mean() + gy.mean()) / 2.0)
                except Exception:
                    return 20.0
            brightness = float(arr.mean())
            contrast = float(arr.std())
            edges = _edge_score(arr)
            looks_like_xray = (brightness < 170 and contrast > 30 and edges > 18)
            looks_like_document = (brightness > 185 and contrast < 55)

            gem_mod = None
            gem_region = None
            if gem:
                try:
                    g = gem.analyze(img)
                    if g:
                        gem_mod = g.get('modality')
                        gem_region = g.get('body_region')
                except Exception:
                    pass

            detected = 'prescription'
            if (gem_mod in ['chest-xray', 'non-chest-xray'] or looks_like_xray) and looks_like_document:
                detected = 'mixed'
            elif gem_mod in ['chest-xray', 'non-chest-xray'] or looks_like_xray:
                detected = 'xray'
            elif gem_mod == 'mri':
                detected = 'mri'
            elif gem_mod and 'ct' in gem_mod:
                detected = 'ct_scan'
            else:
                # document – decide prescription vs lab after OCR
                detected = 'document'

            if detected == 'xray':
                cnn = get_cnn_model()
                cnn_result = cnn.analyze_image(img)
                heatmap = get_gradcam().generate_heatmap(img, cnn.model, cnn_result["prediction"]) 
                heatmap_url = upload_to_storage(heatmap, f"heatmaps/{patient_id}_{datetime.now().timestamp()}.png")
                page_res.update({
                    "detected_type": "xray",
                    "cnn_class": cnn_result.get("class_name"),
                    "cnn_confidence": cnn_result.get("confidence"),
                    "cnn_image_stats": cnn_result.get("image_stats"),
                    "cnn_findings": cnn_result.get("findings"),
                    "heatmap_url": heatmap_url,
                    "explainability": {
                        "gradcam_url": heatmap_url,
                        "shap_supported": False,
                        "lime_supported": False
                    }
                })

            elif detected == 'mri':
                mri = get_mri_model()
                mri_result = mri.analyze_image(img)
                page_res.update({"detected_type": "mri", **mri_result})

            elif detected == 'ct_scan':
                ct = get_ct_model()
                ct_result = ct.analyze_image(img)
                page_res.update({"detected_type": "ct_scan", **ct_result})

            elif detected == 'mixed':
                # Run both OCR (lab or prescription) and X-ray
                ocr = get_ocr_model()
                ocr_result = ocr.extract_text(img)
                text = ocr_result.get('text', '')
                lab = parse_lab(text)
                is_lab = lab and len(lab.get('values', [])) >= 2
                cnn = get_cnn_model()
                cnn_result = cnn.analyze_image(img)
                heatmap = get_gradcam().generate_heatmap(img, cnn.model, cnn_result["prediction"]) 
                heatmap_url = upload_to_storage(heatmap, f"heatmaps/{patient_id}_{datetime.now().timestamp()}.png")
                page_res.update({
                    "detected_type": "mixed",
                    "ocr_text": text,
                    "lab_values": lab.get('values', []) if is_lab else [],
                    "lab_abnormal_count": lab.get('abnormal_count', 0) if is_lab else 0,
                    "medicines": [] if is_lab else get_nlp_model().extract_entities(text).get('medicines', []),
                    "cnn_class": cnn_result.get("class_name"),
                    "cnn_confidence": cnn_result.get("confidence"),
                    "cnn_image_stats": cnn_result.get("image_stats"),
                    "cnn_findings": cnn_result.get("findings"),
                    "heatmap_url": heatmap_url,
                    "explainability": {
                        "gradcam_url": heatmap_url,
                        "shap_supported": False,
                        "lime_supported": False
                    }
                })
                if not is_lab:
                    try:
                        nlp_tmp = get_nlp_model().extract_entities(text)
                        page_res["dosages"] = nlp_tmp.get('dosages', [])
                        page_res["durations"] = nlp_tmp.get('durations', [])
                        page_res["medication_items"] = pair_medications(
                            page_res.get('medicines', []),
                            page_res.get('dosages', []),
                            page_res.get('durations', [])
                        )
                    except Exception:
                        pass

            else:
                # Document: OCR then lab/prescription decision
                ocr = get_ocr_model()
                ocr_result = ocr.extract_text(img)
                text = ocr_result.get('text', '')
                lab = parse_lab(text)
                is_lab = lab and len(lab.get('values', [])) >= 2
                if is_lab:
                    page_res.update({
                        "detected_type": "lab_report",
                        "ocr_text": text,
                        "lab_values": lab.get('values', []),
                        "lab_abnormal_count": lab.get('abnormal_count', 0),
                        "lab_critical_flags": lab.get('critical_flags', [])
                    })
                else:
                    nlp = get_nlp_model()
                    nlp_result = nlp.extract_entities(text)
                    page_res.update({
                        "detected_type": "prescription",
                        "ocr_text": text,
                        "medicines": nlp_result.get('medicines', []),
                        "dosages": nlp_result.get('dosages', []),
                        "durations": nlp_result.get('durations', []),
                        "medication_items": pair_medications(
                            nlp_result.get('medicines', []),
                            nlp_result.get('dosages', []),
                            nlp_result.get('durations', [])
                        )
                    })

            results.append(page_res)

        response_obj = {
            "total_pages": len(pages),
            "pages": results
        }
        # Save combined analysis doc for PDF (optional)
        if db:
            try:
                combined = {
                    "patient_id": patient_id,
                    "user_id": user_id,
                    "document_type": "pdf_auto",
                    "timestamp": datetime.now().isoformat(),
                    "pages": results,
                    "total_pages": len(pages)
                }
                cref = db.collection('analyses').add(combined)
                response_obj["document_id"] = cref[1].id
                if patient_id:
                    db.collection('patients').document(str(patient_id))\
                        .collection('analyses').document(response_obj["document_id"]).set({
                            "analysis_id": response_obj["document_id"],
                            "timestamp": combined.get("timestamp"),
                            "document_type": "pdf_auto"
                        })
            except Exception:
                pass
        return jsonify(response_obj), 200

    except Exception as e:
        print(f"PDF auto process error: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


def format_prescription_text(raw_text):
    """Format OCR text into organized sections for better readability"""
    try:
        lines = raw_text.split()
        formatted = {
            "header": "",
            "patient_info": "",
            "medications": [],
            "doctor_info": "",
            "full_text": raw_text
        }
        
        # Detect header (medical center, address)
        header_keywords = ["MEDICAL", "CENTRE", "CENTER", "HOSPITAL", "CLINIC", "Street", "NY", "USA"]
        header_parts = []
        patient_parts = []
        med_parts = []
        doctor_parts = []
        
        # Simple section detection
        in_meds = False
        in_patient = False
        
        for i, word in enumerate(lines):
            # Header detection
            if any(kw in word.upper() for kw in header_keywords) and not in_meds:
                header_parts.append(word)
            
            # Patient info detection
            elif any(kw in word.upper() for kw in ["NAME", "AGE", "ADDRESS", "DATE"]):
                in_patient = True
                in_meds = False
                patient_parts.append(word)
            
            # Medication detection
            elif any(kw in word for kw in ["mg", "ml", "tab", "BID", "TID", "QD", "QID"]) or word.endswith("mg") or word.endswith("ml"):
                in_meds = True
                in_patient = False
                med_parts.append(word)
            
            # Doctor/signature detection
            elif any(kw in word for kw in ["Dr.", "Dr", "signature", "LABEL", "REFILL"]):
                in_meds = False
                doctor_parts.append(word)
            
            # Continue current section
            elif in_patient:
                patient_parts.append(word)
            elif in_meds:
                med_parts.append(word)
        
        # Format sections
        formatted["header"] = " ".join(header_parts[:15]) if header_parts else ""
        formatted["patient_info"] = " ".join(patient_parts[:20]) if patient_parts else ""
        formatted["doctor_info"] = " ".join(doctor_parts[:10]) if doctor_parts else ""
        
        # Format medications as separate lines
        med_text = " ".join(med_parts)
        # Try to split by common patterns
        med_lines = []
        current_med = []
        for word in med_parts:
            current_med.append(word)
            # New medicine starts with capital letter or after dosage instruction
            if word.upper() in ["BID", "TID", "QD", "QID"] or (word[0].isupper() and len(current_med) > 3):
                if len(current_med) > 1:
                    med_lines.append(" ".join(current_med[:-1]))
                    current_med = [word]
        
        if current_med:
            med_lines.append(" ".join(current_med))
        
        formatted["medications"] = med_lines if med_lines else [med_text]
        
        return formatted
    
    except Exception as e:
        print(f"Text formatting error: {e}")
        return {
            "header": "",
            "patient_info": "",
            "medications": [],
            "doctor_info": "",
            "full_text": raw_text
        }


def pair_medications(medicines, dosages, durations):
    """Pair medicines with nearest dosage and duration by start offsets.
    Returns a list of dicts: { name, dosage, duration }.
    """
    try:
        meds = medicines or []
        dsg = dosages or []
        dur = durations or []

        def nearest(source_start, arr):
            best = None
            best_dist = 10**9
            for x in arr:
                s = x.get('start') if isinstance(x, dict) else None
                if isinstance(s, int) and isinstance(source_start, int) and source_start >= 0:
                    dist = abs(s - source_start)
                    if dist < best_dist:
                        best = x
                        best_dist = dist
            return best

        paired = []
        for m in meds:
            name = m.get('text') if isinstance(m, dict) else str(m)
            m_start = m.get('start') if isinstance(m, dict) else None
            nd = nearest(m_start if isinstance(m_start, int) else -1, dsg)
            ndr = nearest(m_start if isinstance(m_start, int) else -1, dur)
            paired.append({
                "name": name,
                "dosage": nd.get('text') if isinstance(nd, dict) else None,
                "duration": ndr.get('text') if isinstance(ndr, dict) else None
            })
        return paired
    except Exception:
        try:
            return [{"name": (m.get('text') if isinstance(m, dict) else str(m))} for m in (medicines or [])]
        except Exception:
            return []


def generate_diagnosis_summary(result):
    """Generate REAL, honest diagnosis summary based on actual analysis"""
    summary_parts = []

    # OCR quality assessment with REAL feedback
    ocr_conf = result.get('ocr_confidence', 0)
    is_handwritten = result.get('is_handwritten', False)
    word_count = len(result.get('ocr_text', '').split())
    
    if is_handwritten:
        summary_parts.append(f"⚠️ Handwritten prescription detected (OCR: {int(ocr_conf * 100)}% confidence).")
    elif ocr_conf > 0.80:
        summary_parts.append(f"✓ High-quality text extraction ({int(ocr_conf * 100)}% confidence, {word_count} words).")
    elif ocr_conf > 0.60:
        summary_parts.append(f"Text extracted with {int(ocr_conf * 100)}% confidence ({word_count} words).")
    elif ocr_conf > 0.40:
        summary_parts.append(f"⚠️ Low-quality text ({int(ocr_conf * 100)}% confidence). Results may be incomplete.")
    else:
        summary_parts.append(f"⚠️ Very poor OCR quality ({int(ocr_conf * 100)}% confidence). Text extraction unreliable.")
    
    # Medicine extraction with context
    medicines = result.get('medicines', [])
    if medicines:
        summary_parts.append(f"Found {len(medicines)} medicine(s).")
    elif is_handwritten:
        summary_parts.append("No medicines reliably extracted (handwriting limitation).")
    else:
        summary_parts.append("No medicines identified.")

    # Lab summary
    if result.get('lab_values'):
        abn = int(result.get('lab_abnormal_count', 0))
        if abn > 0:
            summary_parts.append(f"{abn} lab value(s) outside reference range.")
        else:
            summary_parts.append("All parsed lab values within reference range.")
    
    # Image classification
    if result.get('cnn_class'):
        cnn_conf = result.get('cnn_confidence', 0)
        summary_parts.append(f"Image: {result['cnn_class']} ({int(cnn_conf * 100)}%).")
    
    return " ".join(summary_parts)


@app.route('/api/compliance/audit-logs', methods=['GET'])
def get_audit_logs():
    """Get audit logs for compliance tracking"""
    try:
        user_id = request.args.get('user_id')
        patient_id = request.args.get('patient_id')
        limit = int(request.args.get('limit', 100))
        
        logs = compliance_manager.get_audit_logs(
            user_id=user_id,
            patient_id=patient_id,
            limit=limit
        )
        
        return jsonify({
            'audit_logs': logs,
            'count': len(logs),
            'compliant': True
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/compliance/export-patient-data', methods=['POST'])
def export_patient_data():
    """Export all patient data (GDPR Right to Data Portability)"""
    try:
        data = request.get_json()
        patient_id = data.get('patient_id')
        
        if not patient_id:
            return jsonify({'error': 'patient_id is required'}), 400
        
        # Log the export request
        compliance_manager.log_access(
            action='gdpr_export',
            user_id=data.get('user_id', 'system'),
            patient_id=patient_id,
            resource_type='patient_data_export',
            ip_address=request.remote_addr
        )
        
        export_data = compliance_manager.export_user_data(patient_id)
        
        if not export_data:
            return jsonify({'error': 'Patient not found'}), 404
        
        return jsonify(export_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/compliance/delete-patient-data', methods=['POST'])
def delete_patient_data_gdpr():
    """Delete all patient data (GDPR Right to Erasure)"""
    try:
        data = request.get_json()
        patient_id = data.get('patient_id')
        user_id = data.get('user_id')
        
        if not patient_id or not user_id:
            return jsonify({'error': 'patient_id and user_id are required'}), 400
        
        # Verify user has permission (in production, add proper auth)
        success = compliance_manager.delete_user_data(patient_id, user_id)
        
        if success:
            return jsonify({
                'deleted': True,
                'patient_id': patient_id,
                'gdpr_compliant': True,
                'timestamp': datetime.now().isoformat()
            }), 200
        else:
            return jsonify({'error': 'Deletion failed'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/compliance/anonymize-patient', methods=['POST'])
def anonymize_patient_endpoint():
    """Anonymize patient data for research/analytics"""
    try:
        data = request.get_json()
        patient_id = data.get('patient_id')
        
        if not patient_id:
            return jsonify({'error': 'patient_id is required'}), 400
        
        if not db:
            return jsonify({'error': 'Database not available'}), 500
        
        # Get patient data
        patient_doc = db.collection('patients').document(str(patient_id)).get()
        if not patient_doc.exists:
            return jsonify({'error': 'Patient not found'}), 404
        
        patient_data = patient_doc.to_dict()
        patient_data['id'] = patient_doc.id
        
        # Anonymize
        anonymized = compliance_manager.anonymize_patient(patient_data)
        
        # Log the anonymization
        compliance_manager.log_access(
            action='anonymize',
            user_id=data.get('user_id', 'system'),
            patient_id=patient_id,
            resource_type='patient',
            ip_address=request.remote_addr
        )
        
        return jsonify(anonymized), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/compliance/detect-anomaly', methods=['POST'])
def detect_anomaly_endpoint():
    """Detect unusual access patterns (data breach detection)"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400
        
        anomaly_report = compliance_manager.detect_anomaly(user_id)
        
        return jsonify(anomaly_report), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/realtime/stats', methods=['GET'])
def get_realtime_stats():
    """Get real-time dashboard statistics"""
    try:
        stats = realtime_manager._get_dashboard_stats()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/explainability/generate', methods=['POST'])
def generate_explainability():
    """
    Generate SHAP and LIME explanations for a previously analyzed image
    """
    try:
        data = request.get_json()
        analysis_id = data.get('analysis_id')
        explainability_type = data.get('type', 'all')  # 'shap', 'lime', or 'all'
        
        if not analysis_id:
            return jsonify({'error': 'analysis_id is required'}), 400
        
        if not db:
            return jsonify({'error': 'Database not available'}), 500
        
        # Get analysis
        analysis_doc = db.collection('analyses').document(analysis_id).get()
        if not analysis_doc.exists:
            return jsonify({'error': 'Analysis not found'}), 404
        
        analysis_data = analysis_doc.to_dict()
        file_url = analysis_data.get('file_url')
        
        if not file_url:
            return jsonify({'error': 'No image found for this analysis'}), 400
        
        # Download image
        image = download_image(file_url)
        
        # Load CNN model
        cnn = get_cnn_model()
        cnn_result = cnn.analyze_image(image)
        prediction_class = cnn_result['prediction']
        
        result = {}
        
        # Generate SHAP (only if available)
        if explainability_type in ['shap', 'all'] and EXPLAINABILITY_ADVANCED and shap_explainer:
            print("Generating SHAP...")
            shap_result = shap_explainer.explain(image, cnn.model, prediction_class, num_samples=100)
            result['shap'] = {
                'visualization': shap_result.get('visualization'),
                'importance_scores': shap_result.get('importance_scores'),
                'method': shap_result.get('method')
            }
        elif explainability_type in ['shap', 'all']:
            print("⚠️ SHAP not available (missing dependencies)")
            result['shap'] = {'error': 'SHAP not available - install shap and matplotlib'}
        
        # Generate LIME (only if available)
        if explainability_type in ['lime', 'all'] and EXPLAINABILITY_ADVANCED and lime_explainer:
            print("Generating LIME...")
            lime_result = lime_explainer.explain(image, cnn.model, prediction_class, num_samples=200, num_features=10)
            result['lime'] = {
                'visualization_positive': lime_result.get('visualization_positive'),
                'visualization_both': lime_result.get('visualization_both'),
                'feature_weights': lime_result.get('feature_weights'),
                'method': lime_result.get('method')
            }
        elif explainability_type in ['lime', 'all']:
            print("⚠️ LIME not available (missing dependencies)")
            result['lime'] = {'error': 'LIME not available - install lime, scikit-image and matplotlib'}
        
        # Log the explainability generation
        if compliance_manager:
            compliance_manager.log_access(
                action='generate_explainability',
                user_id=data.get('user_id', 'system'),
                patient_id=analysis_data.get('patient_id'),
                resource_type='explainability',
                resource_id=analysis_id,
                ip_address=request.remote_addr
            )
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"Explainability generation error: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    
    # Use SocketIO run instead of app.run for WebSocket support
    if realtime_manager and realtime_manager.socketio:
        print("Starting with WebSocket support...")
        realtime_manager.socketio.run(app, host='0.0.0.0', port=port, debug=True)
    else:
        print("Starting without WebSocket support...")
        app.run(host='0.0.0.0', port=port, debug=True)

