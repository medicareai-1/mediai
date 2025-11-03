# 🚀 MediScan AI - Complete Setup Guide

This guide will walk you through setting up MediScan AI from scratch to deployment.

---

## 📋 Prerequisites Checklist

Before starting, ensure you have:

- [ ] Node.js 16+ installed ([Download](https://nodejs.org/))
- [ ] Python 3.9+ installed ([Download](https://www.python.org/))
- [ ] Git installed ([Download](https://git-scm.com/))
- [ ] A Google account (for Firebase)
- [ ] A GitHub account (for Render deployment)

---

## 🔥 Step 1: Firebase Setup

### 1.1 Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Add project"
3. Enter project name: `mediscan-ai` (or your preferred name)
4. Disable Google Analytics (optional for this project)
5. Click "Create project"

### 1.2 Enable Authentication

1. In Firebase Console, go to **Build → Authentication**
2. Click "Get started"
3. Enable **Email/Password**:
   - Click "Email/Password"
   - Toggle "Enable"
   - Click "Save"
4. Enable **Google**:
   - Click "Google"
   - Toggle "Enable"
   - Select support email
   - Click "Save"

### 1.3 Create Firestore Database

1. Go to **Build → Firestore Database**
2. Click "Create database"
3. Select "Start in test mode" (we'll add rules later)
4. Choose location (select closest to you)
5. Click "Enable"

### 1.4 ~~Enable Storage~~ (NOT NEEDED! ✅)

**SKIP THIS STEP!** 

This project uses **base64 encoding** to store images directly in Firestore, so Firebase Storage is **NOT required**! This means:
- ✅ No billing/payment method needed
- ✅ 100% free
- ✅ Simpler setup

See `NO_STORAGE_NEEDED.md` for details.

### 1.5 Get Frontend Configuration

1. Go to **Project Settings** (gear icon)
2. Scroll to "Your apps"
3. Click web icon (</>) to add a web app
4. Register app name: `mediscan-ai-web`
5. Copy the configuration object:

```javascript
const firebaseConfig = {
  apiKey: "AIza...",
  authDomain: "mediscan-ai.firebaseapp.com",
  projectId: "mediscan-ai",
  storageBucket: "mediscan-ai.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456:web:abc123"
};
```

Save this somewhere - you'll need it soon!

### 1.6 Get Backend Credentials

1. Go to **Project Settings → Service Accounts**
2. Click "Generate new private key"
3. Click "Generate key" (downloads JSON file)
4. Rename file to `firebase-credentials.json`
5. **Keep this file safe and never commit it to Git!**

---

## 💻 Step 2: Local Development Setup

### 2.1 Clone or Create Project

```bash
# If you have the code, clone it
git clone https://github.com/yourusername/mediscan-ai.git
cd mediscan-ai

# Or create the directory structure manually
# (all files are already created in this project)
```

### 2.2 Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy language model
python -m spacy download en_core_web_sm

# Copy your firebase credentials
# Place firebase-credentials.json in backend/ folder
```

**Update `backend/app.py`**:

Find line 21 where it says:
```python
'storageBucket': 'your-project-id.appspot.com'
```

Replace with your actual storage bucket name from Firebase config.

**Create `.env` file in backend folder** (optional):
```env
FLASK_ENV=development
PORT=5000
FIREBASE_STORAGE_BUCKET=mediscan-ai.appspot.com
```

**Start backend server**:
```bash
python app.py
```

Server should start on `http://localhost:5000`

### 2.3 Frontend Setup

Open a new terminal:

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Create .env file
# Create a file named .env in the frontend folder
```

**Frontend `.env` file content**:
```env
VITE_FIREBASE_API_KEY=AIza...
VITE_FIREBASE_AUTH_DOMAIN=mediscan-ai.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=mediscan-ai
VITE_FIREBASE_STORAGE_BUCKET=mediscan-ai.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=123456789
VITE_FIREBASE_APP_ID=1:123456:web:abc123
VITE_API_URL=http://localhost:5000
```

Replace all values with your Firebase config from Step 1.5!

**Update `frontend/src/services/firebase.js`**:

Replace the firebaseConfig object with your actual config:
```javascript
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID
};
```

**Start frontend**:
```bash
npm run dev
```

Frontend should start on `http://localhost:3000`

### 2.4 Test Locally

1. Open browser to `http://localhost:3000`
2. Sign up with email/password
3. Try uploading a sample medical document
4. Check dashboard for real-time updates

---

## 🌐 Step 3: Deploy Backend to Render

### 3.1 Prepare Repository

```bash
# Initialize git (if not already)
git init

# Add files
git add .

# Commit
git commit -m "Initial commit"

# Create GitHub repository and push
git remote add origin https://github.com/yourusername/mediscan-ai.git
git branch -M main
git push -u origin main
```

### 3.2 Create Render Account

1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Authorize Render to access repositories

### 3.3 Create Web Service

1. Click "New +" → "Web Service"
2. Connect your repository
3. Configure:
   - **Name**: `mediscan-ai-backend`
   - **Region**: Select closest to you
   - **Branch**: `main`
   - **Root Directory**: Leave blank
   - **Environment**: `Python 3`
   - **Build Command**:
     ```bash
     pip install -r backend/requirements.txt && python -m spacy download en_core_web_sm
     ```
   - **Start Command**:
     ```bash
     cd backend && gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120
     ```
   - **Plan**: Free

4. Click "Advanced" → Add Environment Variables:

   **FIREBASE_CONFIG**:
   ```
   Paste entire content of firebase-credentials.json as single line
   ```
   
   **FIREBASE_STORAGE_BUCKET**:
   ```
   mediscan-ai.appspot.com
   ```

5. Click "Create Web Service"

6. Wait for deployment (5-10 minutes first time)

7. Copy your Render URL: `https://mediscan-ai-backend.onrender.com`

### 3.4 Update Backend in Frontend

Edit `frontend/.env`:
```env
VITE_API_URL=https://mediscan-ai-backend.onrender.com
```

**Important Note**: Render free tier goes to sleep after 15 minutes of inactivity. First request will be slow (30 seconds) as it wakes up.

---

## 🔥 Step 4: Deploy Frontend to Firebase Hosting

### 4.1 Install Firebase CLI

```bash
npm install -g firebase-tools
```

### 4.2 Login to Firebase

```bash
firebase login
```

Follow browser prompts to login.

### 4.3 Initialize Firebase

```bash
# From project root
firebase init
```

Select:
- **Hosting**: Configure files for Firebase Hosting
- Use existing project → Select your project
- Public directory: `frontend/dist`
- Single-page app: **Yes**
- Set up automatic builds: **No**
- Don't overwrite index.html: **No**

### 4.4 Deploy Firestore Rules

```bash
firebase deploy --only firestore:rules
firebase deploy --only storage
```

### 4.5 Build and Deploy Frontend

```bash
cd frontend

# Build for production
npm run build

# Deploy to Firebase Hosting
firebase deploy --only hosting
```

Your app is now live at: `https://mediscan-ai.web.app`

---

## 🔒 Step 5: Security Configuration

### 5.1 Update Firestore Rules

Already done! The `firestore.rules` file provides:
- User authentication required
- Users can only access their own data
- Read access for authenticated users

### 5.2 Update Storage Rules

Already done! The `storage.rules` file provides:
- Users can only upload to their own folders
- Authenticated access only

### 5.3 Update Firebase Auth Domain

1. Firebase Console → Authentication → Settings
2. Add authorized domains:
   - Your Render URL: `mediscan-ai-backend.onrender.com`
   - Your Firebase Hosting URL: `mediscan-ai.web.app`

---

## ✅ Step 6: Testing Deployment

### 6.1 Test Authentication

1. Go to your Firebase Hosting URL
2. Sign up with email/password
3. Check Firebase Console → Authentication → Users (should see new user)

### 6.2 Test Upload

1. Login to your app
2. Go to "Patients" → Add a test patient
3. Go to "Upload"
4. Select document type and patient ID
5. Upload a sample image
6. Wait for processing (first time takes 30+ seconds on Render)

### 6.3 Verify Firestore

1. Firebase Console → Firestore Database
2. Should see collections: `patients`, `analyses`
3. Check that data is saved correctly

### 6.4 Verify Storage

1. Firebase Console → Storage
2. Should see folders: `documents/`, `heatmaps/`
3. Check uploaded files

---

## 🐛 Troubleshooting

### Backend Not Starting on Render

**Symptoms**: Build succeeds but service won't start

**Solutions**:
1. Check Render logs for errors
2. Ensure `requirements.txt` has all dependencies
3. Verify Firebase credentials are correct
4. Check if Python version is compatible

### Firebase Permission Errors

**Symptoms**: "Permission denied" errors in console

**Solutions**:
1. Deploy Firestore rules: `firebase deploy --only firestore:rules`
2. Deploy Storage rules: `firebase deploy --only storage`
3. Check user is authenticated
4. Verify rules in Firebase Console

### CORS Errors

**Symptoms**: "CORS policy" errors in browser

**Solutions**:
1. Verify Flask-CORS is installed
2. Check backend URL in frontend `.env`
3. Restart backend server
4. Clear browser cache

### Models Taking Too Long

**Symptoms**: Timeout errors on first request

**Solutions**:
1. Normal on Render free tier (cold start)
2. Keep service warm with uptime monitor (UptimeRobot)
3. Increase timeout in `render.yaml`

### Frontend Build Fails

**Symptoms**: `npm run build` fails

**Solutions**:
```bash
# Delete node_modules and lock file
rm -rf node_modules package-lock.json

# Reinstall
npm install

# Try build again
npm run build
```

---

## 📊 Usage Examples

### Sample Test Data

**Patient Information**:
- Name: John Doe
- Age: 45
- Gender: Male
- Contact: +1234567890

**Sample Prescription Text** (for testing OCR):
```
Dr. Sarah Johnson
City Hospital

Patient: John Doe
Date: 01/15/2024

Rx:
1. Amoxicillin 500mg - Take 1 tablet 3 times daily for 7 days
2. Ibuprofen 400mg - Take 1 tablet as needed for pain
3. Multivitamin - Take 1 tablet daily

Follow up in 2 weeks.

Dr. Sarah Johnson, MD
```

---

## 🎯 Next Steps

After successful deployment:

1. **Customize branding**: Update colors in `tailwind.config.js`
2. **Add more AI models**: Train custom models for your specific use case
3. **Implement analytics**: Add Google Analytics or custom tracking
4. **Create documentation**: Add user guide and API docs
5. **Present project**: Prepare demo and presentation slides

---

## 📞 Support

If you encounter issues:

1. Check the Troubleshooting section above
2. Review Firebase Console logs
3. Check Render deployment logs
4. Review browser console for errors
5. Create an issue on GitHub

---

## 🎓 For College Project Presentation

### Key Points to Highlight

1. **Real-time Architecture**: Firestore onSnapshot for live updates
2. **Multi-modal AI**: OCR + NLP + CNN working together
3. **Explainability**: Grad-CAM for transparent AI decisions
4. **Free Deployment**: Production app at zero cost
5. **Modern Stack**: Latest React, Flask, PyTorch
6. **Security**: Firebase Auth + rules
7. **Scalability**: Can handle multiple concurrent users

### Demo Flow

1. Show login (Email + Google OAuth)
2. Add a patient
3. Upload prescription → show OCR results
4. Upload X-ray → show CNN + Grad-CAM
5. Navigate to Analytics → show charts
6. Highlight real-time updates in Dashboard

### Technical Depth

- Explain ResNet architecture
- Discuss Grad-CAM visualization
- Show Firestore real-time sync
- Explain spaCy NER custom patterns
- Discuss deployment architecture

---

**Good luck with your project! 🚀**

