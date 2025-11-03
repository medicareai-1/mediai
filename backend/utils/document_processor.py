"""
Document Processing Utilities
Handles PDF, DICOM, and multiple file formats
"""

from PIL import Image
import io
import numpy as np
import os

def process_pdf(pdf_file):
    """Convert PDF to images for OCR processing"""
    try:
        from pdf2image import convert_from_bytes
        
        # Convert PDF to list of PIL images
        images = convert_from_bytes(pdf_file.read())
        print(f"✓ Converted PDF to {len(images)} page(s)")
        
        return images
    except Exception as e:
        print(f"PDF processing error: {e}")
        # Fallback: treat as regular image
        pdf_file.seek(0)
        return [Image.open(pdf_file)]


def process_pdf_bytes(pdf_bytes):
    """Convert PDF bytes to list of PIL images using PyMuPDF fallback.

    Tries PyMuPDF (no external deps). If unavailable, tries pdf2image with
    optional POPPLER_PATH.
    """
    # 1) Try PyMuPDF (fitz)
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        images = []
        for page in doc:
            pix = page.get_pixmap(dpi=200)
            mode = "RGBA" if pix.alpha else "RGB"
            img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
            if mode == "RGBA":
                img = img.convert("RGB")
            images.append(img)
        if images:
            print(f"✓ Converted PDF via PyMuPDF to {len(images)} page(s)")
            return images
    except Exception as e:
        print(f"PyMuPDF fallback failed: {e}")

    # 2) Try pdf2image with Poppler (optional)
    try:
        from pdf2image import convert_from_bytes
        poppler_path = os.getenv('POPPLER_PATH', None)
        images = convert_from_bytes(pdf_bytes, poppler_path=poppler_path)
        print(f"✓ Converted PDF via pdf2image to {len(images)} page(s)")
        return images
    except Exception as e:
        print(f"pdf2image fallback failed: {e}")
        raise


def process_dicom(dicom_file):
    """Convert DICOM medical imaging format to PIL Image"""
    try:
        import pydicom
        
        # Read DICOM file
        dcm = pydicom.dcmread(dicom_file)
        
        # Get pixel array
        pixel_array = dcm.pixel_array
        
        # Normalize to 0-255
        pixel_array = pixel_array.astype(np.float32)
        pixel_array = (pixel_array - pixel_array.min()) / (pixel_array.max() - pixel_array.min()) * 255
        pixel_array = pixel_array.astype(np.uint8)
        
        # Convert to PIL Image
        if len(pixel_array.shape) == 2:  # Grayscale
            image = Image.fromarray(pixel_array, mode='L')
        else:  # RGB
            image = Image.fromarray(pixel_array)
        
        print(f"✓ Converted DICOM to image ({image.size})")
        print(f"  Patient: {getattr(dcm, 'PatientName', 'Unknown')}")
        print(f"  Study: {getattr(dcm, 'StudyDescription', 'Unknown')}")
        
        return [image], {
            "patient_name": str(getattr(dcm, 'PatientName', '')),
            "study_date": str(getattr(dcm, 'StudyDate', '')),
            "modality": str(getattr(dcm, 'Modality', '')),
            "study_description": str(getattr(dcm, 'StudyDescription', ''))
        }
    except Exception as e:
        print(f"DICOM processing error: {e}")
        # Fallback: treat as regular image
        dicom_file.seek(0)
        return [Image.open(dicom_file)], {}


def detect_file_type(filename, file_content):
    """Detect file type from extension and content"""
    filename_lower = filename.lower()
    
    if filename_lower.endswith('.pdf'):
        return 'pdf'
    elif filename_lower.endswith('.dcm') or filename_lower.endswith('.dicom'):
        return 'dicom'
    elif filename_lower.endswith(('.nii', '.nii.gz')):
        return 'nifti'
    elif filename_lower.endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff')):
        return 'image'
    else:
        # Try to detect from content
        file_content.seek(0)
        header = file_content.read(4)
        file_content.seek(0)
        
        if header[:2] == b'%P':  # PDF magic number
            return 'pdf'
        elif b'DICM' in file_content.read(132):  # DICOM magic
            file_content.seek(0)
            return 'dicom'
        else:
            return 'image'


def process_document_file(file):
    """
    Process any document file type and return list of images
    Returns: (images_list, metadata_dict)
    """
    try:
        file_type = detect_file_type(file.filename, file)
        print(f"Processing file: {file.filename} (Type: {file_type})")
        
        if file_type == 'pdf':
            images = process_pdf(file)
            metadata = {"pages": len(images), "type": "pdf"}
            return images, metadata
            
        elif file_type == 'dicom':
            images, dicom_metadata = process_dicom(file)
            metadata = {"type": "dicom", **dicom_metadata}
            return images, metadata
            
        else:  # Regular image
            file.seek(0)
            image = Image.open(file)
            return [image], {"type": "image"}
            
    except Exception as e:
        print(f"Document processing error: {e}")
        # Last resort fallback
        file.seek(0)
        try:
            image = Image.open(file)
            return [image], {"type": "image", "warning": "Fallback processing"}
        except:
            raise Exception(f"Could not process file: {file.filename}")

