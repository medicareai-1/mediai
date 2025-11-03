# ⚡ MediScan AI - Quick Start Guide

Get up and running in 10 minutes!

---

## 🚀 Prerequisites

1. Install [Python 3.9+](https://www.python.org/downloads/)
2. Install [Node.js 16+](https://nodejs.org/)
3. Create [Firebase Account](https://console.firebase.google.com/)

---

## 🔥 Firebase Setup (5 minutes)

### 1. Create Project
```
Go to Firebase Console → Add project → Name it "mediscan-ai" → Create
```

### 2. Enable Services
```
Authentication → Get Started → Enable Email/Password + Google
Firestore Database → Create database → Test mode → Enable
Storage → SKIP THIS! (Not needed - we use base64!)
```

### 3. Get Credentials

**Frontend Config:**
```
Project Settings → Your apps → Web app → Copy config
```

**Backend Credentials:**
```
Project Settings → Service Accounts → Generate new private key
Save as backend/firebase-credentials.json
```

---

## 💻 Local Setup (5 minutes)

### 1. Clone/Download Project
```bash
cd Downloads/proejct
```

### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Place your firebase-credentials.json in backend/ folder

# Start server
python app.py
```

✅ Backend running on `http://localhost:5000`

### 3. Frontend Setup (New Terminal)
```bash
cd frontend

# Install dependencies
npm install

# Create .env file
# Copy content from ENVIRONMENT_SETUP.md
# Add your Firebase config

# Start dev server
npm run dev
```

✅ Frontend running on `http://localhost:3000`

---

## 🎯 Test It Out

1. **Open**: http://localhost:3000
2. **Sign Up**: Create account with email/password
3. **Add Patient**: Go to Patients → Add Patient
4. **Upload**: Go to Upload → Select document type → Upload image
5. **View Results**: See OCR, NLP, CNN results
6. **Dashboard**: Check real-time updates

---

## 📁 Required Files

Before starting, ensure these files exist:

### Backend
```
backend/
├── firebase-credentials.json  ← Download from Firebase
└── requirements.txt           ← Already exists
```

### Frontend
```
frontend/
├── .env                       ← Create this (see ENVIRONMENT_SETUP.md)
└── package.json              ← Already exists
```

---

## 🐛 Quick Troubleshooting

### Backend won't start
```bash
# Ensure virtual environment is activated
# You should see (venv) in terminal

# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Frontend won't start
```bash
# Delete and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Firebase errors
```
1. Check firebase-credentials.json is in backend/ folder
2. Verify .env has correct Firebase config
3. Ensure Firestore and Storage are enabled in Firebase Console
```

---

## 📝 Minimal .env for Frontend

Create `frontend/.env`:
```env
VITE_FIREBASE_API_KEY=AIza...
VITE_FIREBASE_AUTH_DOMAIN=mediscan-xyz.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=mediscan-xyz
VITE_FIREBASE_STORAGE_BUCKET=mediscan-xyz.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=123456
VITE_FIREBASE_APP_ID=1:123456:web:abc123
VITE_API_URL=http://localhost:5000
```

Replace all values with your actual Firebase config!

---

## 🌐 Deploy (Optional - Later)

Once local setup works, follow these guides:

1. **Backend**: See `SETUP_GUIDE.md` → Step 3 (Deploy to Render)
2. **Frontend**: See `SETUP_GUIDE.md` → Step 4 (Deploy to Firebase Hosting)

---

## ✅ Success Checklist

- [ ] Python and Node.js installed
- [ ] Firebase project created
- [ ] Backend running on port 5000
- [ ] Frontend running on port 3000
- [ ] Can login to app
- [ ] Can upload document
- [ ] Results appear in dashboard

---

## 📞 Need Help?

- Review `SETUP_GUIDE.md` for detailed instructions
- Check `ENVIRONMENT_SETUP.md` for configuration details
- See `DEPLOYMENT_CHECKLIST.md` for comprehensive checklist

---

**That's it! You're ready to go! 🎉**

Now you can:
- Upload medical documents
- See AI analysis results
- View real-time dashboard
- Explore analytics
- Manage patients

Happy coding! 💻🏥

