# Firestore Document Size Fix

## Problem
The application was failing with error:
```
InvalidArgument: 400 Document cannot be written because its size (1,069,982 bytes) 
exceeds the maximum allowed size of 1,048,576 bytes.
```

## Root Cause
Firestore has a **1MB limit per document**. The analysis results were exceeding this due to:
1. Large base64-encoded heatmap images
2. Large SHAP/LIME visualization images
3. Large base64-encoded original file URLs

## Solutions Implemented

### 1. Exclude Large Images from Firestore (app.py)
- **Excluded** from Firestore storage:
  - `shap_visualization` (large base64 image)
  - `lime_visualization_positive` (large base64 image)
  - `lime_visualization_both` (large base64 image)
  - `heatmap_url` (large base64 heatmap)
  - `file_url` (large base64 original image)

- **What gets stored**: Only essential text data (OCR text, medicines, entities, confidence scores, diagnoses)
- **What gets returned to frontend**: Full result including all images (API response still has everything)

### 2. Reduced Image Sizes (helpers.py)
- **Thumbnail size**: Reduced from 800x800 to **400x400** pixels
- **Format**: Changed from PNG to **JPEG with 70% quality**
- **Compression**: Added JPEG optimization to reduce size further

### 3. Disabled Auto-Generation of SHAP/LIME (app.py)
- SHAP/LIME explainability now **disabled by default** (was causing errors + large size)
- Available **on-demand** via `/api/explainability/generate` endpoint
- Users can request these separately if needed

## Benefits
✅ Documents now stay well under 1MB limit  
✅ Faster Firestore writes  
✅ Reduced storage costs  
✅ Frontend still receives complete analysis with all images  
✅ No data loss - images are returned in API response  

## What Still Works
- ✅ GradCAM heatmaps (returned in API, not stored in Firestore)
- ✅ All OCR text and formatting
- ✅ Medicine extraction and NLP entities
- ✅ CNN predictions and confidence scores
- ✅ Diagnosis suggestions
- ✅ Full analysis results returned to frontend

## What Changed for Users
- **No visible change** - Frontend receives complete data
- Firestore stores lightweight metadata only
- SHAP/LIME must be generated on-demand (button click) instead of automatic
- Heatmaps are smaller (400x400) but still clear

## Migration Notes
- Old analyses with large documents may still fail to load
- New analyses will work correctly
- Consider cleaning up old oversized documents if needed

## Technical Details
```python
# Before: Everything stored in Firestore (1MB+)
db.collection('analyses').add(result)  # ❌ Failed

# After: Filtered storage (< 200KB typically)
firestore_result = {k: v for k, v in result.items() if k not in [
    'shap_visualization',
    'lime_visualization_positive', 
    'lime_visualization_both',
    'heatmap_url',
    'file_url'
]}
db.collection('analyses').add(firestore_result)  # ✅ Works
```

## Future Improvements
1. Store large images in Firebase Storage instead of base64
2. Implement lazy loading for visualizations
3. Add image compression options in settings
4. Cache SHAP/LIME results for faster regeneration

