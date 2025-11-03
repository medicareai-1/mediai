#!/usr/bin/env python3
"""
Generate Sample Prescription Images for Testing
Run: python generate_sample_prescriptions.py
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_prescription(filename, patient_name, medicines):
    """Create a sample prescription image"""
    # Create a white image
    width, height = 800, 600
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a default font (works on most systems)
    try:
        font_title = ImageFont.truetype("arial.ttf", 32)
        font_text = ImageFont.truetype("arial.ttf", 24)
    except:
        font_title = ImageFont.load_default()
        font_text = ImageFont.load_default()
    
    # Draw header
    draw.text((50, 30), "Medical Prescription", fill='black', font=font_title)
    draw.text((50, 80), f"Patient: {patient_name}", fill='black', font=font_text)
    draw.line([(50, 120), (750, 120)], fill='black', width=2)
    
    # Draw medicines
    y_position = 150
    draw.text((50, y_position), "Prescribed Medicines:", fill='black', font=font_text)
    y_position += 50
    
    for i, med in enumerate(medicines, 1):
        text = f"{i}. {med}"
        draw.text((70, y_position), text, fill='black', font=font_text)
        y_position += 40
    
    # Draw footer
    y_position += 30
    draw.line([(50, y_position), (750, y_position)], fill='black', width=2)
    draw.text((50, y_position + 20), "Dr. John Smith", fill='black', font=font_text)
    draw.text((50, y_position + 50), "License: MD-12345", fill='black', font=font_text)
    
    # Save
    img.save(filename)
    print(f"✓ Created: {filename}")

def main():
    # Create output directory
    os.makedirs('sample_prescriptions', exist_ok=True)
    
    # Sample prescriptions
    prescriptions = [
        {
            'filename': 'sample_prescriptions/prescription_1.png',
            'patient': 'John Doe',
            'medicines': [
                'Paracetamol 500mg - Take 2 times daily - 5 days',
                'Amoxicillin 250mg - Take 3 times daily - 7 days',
                'Vitamin C 1000mg - Take once daily - 30 days'
            ]
        },
        {
            'filename': 'sample_prescriptions/prescription_2.png',
            'patient': 'Jane Smith',
            'medicines': [
                'Ibuprofen 400mg - Take as needed - 10 days',
                'Cetirizine 10mg - Take once at night - 14 days',
                'Omeprazole 20mg - Take before breakfast - 30 days'
            ]
        },
        {
            'filename': 'sample_prescriptions/prescription_3.png',
            'patient': 'Robert Johnson',
            'medicines': [
                'Metformin 500mg - Take twice daily - 90 days',
                'Aspirin 75mg - Take once daily - Ongoing',
                'Atorvastatin 10mg - Take at bedtime - 90 days'
            ]
        },
        {
            'filename': 'sample_prescriptions/prescription_4.png',
            'patient': 'Emily Davis',
            'medicines': [
                'Azithromycin 500mg - Take once daily - 3 days',
                'Dextromethorphan 10mg - Take every 6 hours - 7 days',
                'Loratadine 10mg - Take once daily - 14 days'
            ]
        },
        {
            'filename': 'sample_prescriptions/prescription_5.png',
            'patient': 'Michael Brown',
            'medicines': [
                'Lisinopril 10mg - Take once daily - 90 days',
                'Amlodipine 5mg - Take once daily - 90 days',
                'Clopidogrel 75mg - Take once daily - Ongoing'
            ]
        }
    ]
    
    print("\n🏥 Generating Sample Prescription Images...\n")
    
    for prescription in prescriptions:
        create_prescription(
            prescription['filename'],
            prescription['patient'],
            prescription['medicines']
        )
    
    print(f"\n✅ Created {len(prescriptions)} sample prescriptions!")
    print(f"📁 Location: ./sample_prescriptions/")
    print(f"\n💡 You can now upload these to test your MediScan AI application!\n")

if __name__ == '__main__':
    main()

