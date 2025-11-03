# Requirements.txt Information

## 📦 Package List (No Version Pinning)

The `requirements.txt` file includes all necessary packages **without version pinning** for maximum compatibility.

---

## ✅ Benefits of No Version Pinning

### **Advantages:**
- ✅ Always gets latest stable versions
- ✅ Easier to deploy on different platforms
- ✅ No version conflicts
- ✅ Automatic security updates
- ✅ Works with Python 3.8, 3.9, 3.10, 3.11

### **Potential Issues:**
- ⚠️ Breaking changes in major updates (rare)
- ⚠️ First deployment might be slower (downloads latest)

---

## 📋 Complete Package List

### **Web Framework (5 packages)**
```
Flask               - Web framework
flask-cors          - CORS support
flask-socketio      - Real-time features
gunicorn            - Production server
python-dotenv       - Environment variables
```

### **Firebase (1 package)**
```
firebase-admin      - Database & Auth
```

### **OCR & Vision (3 packages)**
```
easyocr             - Primary OCR engine
pytesseract         - Secondary OCR
google-generativeai - Gemini AI OCR
```

### **NLP (1 package)**
```
spacy               - Named Entity Recognition
```

### **Deep Learning (2 packages)**
```
torch               - PyTorch framework
torchvision         - Computer vision models
```

### **Image Processing (3 packages)**
```
Pillow              - Image manipulation
opencv-python       - Computer vision
scikit-image        - Image processing
```

### **PDF Processing (2 packages)**
```
pymupdf             - PDF parsing
pdf2image           - PDF to image conversion
```

### **Machine Learning (3 packages)**
```
scikit-learn        - ML algorithms
numpy               - Numerical computing
scipy               - Scientific computing
```

### **Explainability (3 packages)**
```
shap                - SHAP explanations
lime                - LIME explanations
matplotlib          - Visualization
```

### **Security (1 package)**
```
cryptography        - HIPAA/GDPR encryption
```

### **Utilities (1 package)**
```
requests            - HTTP requests
```

**Total: 25 packages**

---

## 🚀 Installation

### **Local Development:**
```bash
cd backend
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### **Production (Render/etc):**
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

---

## 🔧 If You Need Specific Versions

If deployment fails due to version conflicts, you can pin specific versions:

### **Option 1: Pin All Versions**
```bash
# After successful local install:
pip freeze > requirements-pinned.txt
```

### **Option 2: Pin Only Problematic Packages**
```
# In requirements.txt, add version to specific package:
torch==2.1.0
```

### **Option 3: Use Upper Bounds**
```
# Allow updates but set max version:
torch<3.0.0
scikit-learn<2.0.0
```

---

## 📝 Deployment Notes

### **Render.com**
- Automatically installs from requirements.txt
- Build time: ~5-10 minutes (first time)
- Python version: 3.11.0 (set in render.yaml)

### **Heroku**
- Uses requirements.txt automatically
- Needs Procfile (already configured)

### **Docker**
- Copy requirements.txt to container
- Run pip install in Dockerfile

---

## ⚠️ Known Issues & Solutions

### **Issue 1: Torch is Too Large**
**Problem:** Deployment timeout due to torch size (700MB+)

**Solution:**
```
# Use CPU-only version (smaller):
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

### **Issue 2: OpenCV Missing System Dependencies**
**Problem:** `opencv-python` needs system libraries

**Solution:** Already handled by Render/Heroku build packs

### **Issue 3: Spacy Model Not Found**
**Problem:** `en_core_web_sm` not installed

**Solution:** Build command includes:
```bash
python -m spacy download en_core_web_sm
```

---

## 🔄 Updating Packages

### **Update All:**
```bash
pip install --upgrade -r requirements.txt
```

### **Update Specific Package:**
```bash
pip install --upgrade flask
```

### **Check Outdated:**
```bash
pip list --outdated
```

---

## 💡 Best Practices

1. **Test locally first** before deploying
2. **Use virtual environment** (venv)
3. **Document any manual changes**
4. **Keep requirements.txt clean** (no comments in middle)
5. **One package per line**

---

## 📊 Estimated Installation Size

```
Small Packages (~1-10 MB each):
- Flask, numpy, requests, etc.
Total: ~50 MB

Medium Packages (~10-100 MB each):
- scikit-learn, opencv-python, etc.
Total: ~200 MB

Large Packages (~100-700 MB each):
- torch, torchvision, easyocr
Total: ~1.2 GB

Total Installation: ~1.5 GB
```

**Deployment time:** 5-10 minutes on Render free tier

---

## ✅ Deployment Checklist

Before deploying, ensure:
- [ ] requirements.txt is in backend/ folder
- [ ] No typos in package names
- [ ] All packages are on PyPI
- [ ] Build command includes spacy model download
- [ ] Python version is compatible (3.8+)

---

**All packages are production-ready and tested!** ✨

