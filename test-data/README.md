# 📦 Test Data for MediScan AI

## Quick Start - Generate Sample Prescriptions

### Option 1: Run the Python Script
```bash
cd test-data
python generate_sample_prescriptions.py
```

This will create 5 sample prescription images in `sample_prescriptions/` folder.

---

## Free Medical Dataset Sources

### 1. Prescriptions & Handwritten Text
- **Kaggle Medical Prescriptions**: https://www.kaggle.com/datasets/kmader/handwritten-prescriptions
- **Medical Manuscripts**: https://www.kaggle.com/datasets/andrewmvd/medical-manuscripts
- **Handwritten Text**: https://www.kaggle.com/datasets/landlord/handwriting-recognition

### 2. X-Ray Images
- **NIH Chest X-Ray**: https://www.kaggle.com/datasets/nih-chest-xrays/data (112K images)
- **COVID-19 X-Ray**: https://www.kaggle.com/datasets/tawsifurrahman/covid19-radiography-database
- **Pneumonia X-Ray**: https://www.kaggle.com/datasets/paultimothymooney/chest-xray-pneumonia

### 3. MRI Images
- **Brain MRI**: https://www.kaggle.com/datasets/navoneel/brain-mri-images-for-brain-tumor-detection
- **Brain Tumor MRI**: https://www.kaggle.com/datasets/masoudnickparvar/brain-tumor-mri-dataset

### 4. CT Scans
- **Medical Imaging**: https://www.kaggle.com/datasets/kmader/siim-medical-images

---

## How to Download from Kaggle

1. **Create Kaggle Account** (free): https://www.kaggle.com/
2. **Navigate to dataset** (links above)
3. **Click "Download"** button
4. **Extract** the ZIP file
5. **Upload to MediScan AI** through the Upload page

---

## Quick DIY Test Images

### Create Your Own Prescriptions:
1. Write on paper:
   ```
   Dr. John Smith
   Patient: Test Patient
   
   Medicines:
   1. Paracetamol 500mg - 2x daily - 5 days
   2. Amoxicillin 250mg - 3x daily - 7 days
   3. Vitamin C 1000mg - 1x daily - 30 days
   
   Signature: _____________
   ```

2. Take a photo with your phone
3. Upload to test!

---

## Recommended Test Workflow

### Step 1: Start Small
- Use the generated sample prescriptions (5 images)
- Test basic OCR and NLP functionality

### Step 2: Download Real Data
- Download 10-20 images from Kaggle datasets
- Test with variety of medical documents

### Step 3: Create Custom Data
- Write your own prescriptions
- Take photos at different angles/lighting
- Test real-world scenarios

---

## Sample Medicine Names for Testing

Common medicines to write on test prescriptions:
- Paracetamol (acetaminophen)
- Ibuprofen
- Amoxicillin
- Azithromycin
- Metformin
- Atorvastatin
- Omeprazole
- Lisinopril
- Amlodipine
- Cetirizine

---

## Image Requirements

- **Format**: PNG, JPG, JPEG
- **Size**: Up to 10MB
- **Resolution**: 800x600 minimum recommended
- **Quality**: Clear text, good lighting

---

## Testing Tips

1. **Start with clear images** - test OCR accuracy
2. **Try different handwriting styles** - test robustness
3. **Use various lighting conditions** - test preprocessing
4. **Test multiple document types** - prescriptions, X-rays, reports
5. **Upload in batches** - test real-time dashboard updates

---

## Need Help?

If you encounter issues with test data:
1. Check file size (< 10MB)
2. Ensure correct format (PNG/JPG)
3. Verify image is not corrupted
4. Try the sample generated prescriptions first

---

**Happy Testing! 🧪**

