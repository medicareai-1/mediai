"""
Quick test script for Gemini Vision OCR
Run this to verify Gemini is working correctly
"""

from PIL import Image
import os
import sys

# Add models directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'models'))

from gemini_ocr import gemini_ocr

def test_gemini():
    """Test Gemini OCR with a sample image"""
    
    print("\n" + "="*60)
    print("🧪 TESTING GEMINI VISION OCR")
    print("="*60 + "\n")
    
    # Check if Gemini is available
    if not gemini_ocr.is_available():
        print("❌ Gemini is NOT available!")
        print("\nPossible reasons:")
        print("1. GEMINI_API_KEY not set in .env file")
        print("2. Invalid API key")
        print("3. Network connection issue")
        print("\nGet your FREE API key: https://aistudio.google.com/app/apikey")
        return
    
    print("✅ Gemini is available!\n")
    
    # Look for test images
    test_image_paths = [
        "../test-data/sample_prescriptions/prescription_1.png",
        "../test-data/sample_prescriptions/prescription_2.png",
        "../test-data/sample_prescriptions/prescription_3.png",
        "prescription.jpg",
        "test.png"
    ]
    
    test_image = None
    for path in test_image_paths:
        if os.path.exists(path):
            test_image = path
            break
    
    if not test_image:
        print("⚠️  No test image found!")
        print(f"Looked in: {test_image_paths}")
        print("\nCreate a test by placing an image in one of these paths.")
        return
    
    print(f"📷 Testing with: {test_image}\n")
    print("-" * 60)
    
    # Load and test
    try:
        img = Image.open(test_image)
        print(f"Image loaded: {img.size[0]}x{img.size[1]} pixels\n")
        
        print("🌟 Running Gemini Vision OCR...\n")
        result = gemini_ocr.extract_text(img)
        
        if result:
            print("\n" + "="*60)
            print("✅ GEMINI OCR RESULT:")
            print("="*60 + "\n")
            
            print(f"Method: {result.get('method', 'unknown')}")
            print(f"Confidence: {result.get('confidence', 0)*100:.1f}%")
            print(f"Word Count: {result.get('word_count', 0)}")
            print(f"Is Handwritten: {result.get('is_handwritten', False)}")
            
            if result.get('info'):
                print(f"\nInfo: {result['info']}")
            
            print(f"\n{'─'*60}")
            print("EXTRACTED TEXT:")
            print('─'*60)
            print(result.get('text', 'No text extracted'))
            
            # Show structured data if available
            if 'gemini_structured' in result:
                structured = result['gemini_structured']
                
                if structured.get('medications'):
                    print(f"\n{'─'*60}")
                    print("MEDICATIONS DETECTED:")
                    print('─'*60)
                    for i, med in enumerate(structured['medications'], 1):
                        print(f"{i}. {med}")
                
                if structured.get('patient_info'):
                    print(f"\n{'─'*60}")
                    print("PATIENT INFO:")
                    print('─'*60)
                    print(structured['patient_info'])
            
            print(f"\n{'='*60}")
            print("✅ TEST PASSED!")
            print("="*60 + "\n")
            
        else:
            print("\n❌ Gemini returned None (failed)")
            print("Check backend logs for error details.")
    
    except FileNotFoundError:
        print(f"❌ Image file not found: {test_image}")
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ .env file loaded\n")
    except:
        print("⚠️  python-dotenv not available, using system environment only\n")
    
    test_gemini()

