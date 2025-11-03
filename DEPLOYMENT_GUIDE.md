# 🚀 MediScan AI - FREE Deployment Guide

Complete guide to deploy MediScan AI for **100% FREE** using Render + Vercel + Firebase.

---

## 📊 Deployment Architecture

```
┌─────────────────────────────────────────────────────┐
│  USERS → https://your-app.vercel.app               │
└────────────────┬────────────────────────────────────┘
                 │
    ┌────────────┴────────────┐
    │                         │
┌───▼────────────┐    ┌──────▼──────────┐
│   FRONTEND     │    │    BACKEND      │
│   (Vercel)     │───→│   (Render.com)  │
│   React/Vite   │    │   Flask/Python  │
└────────────────┘    └──────┬──────────┘
                             │
                      ┌──────▼──────────┐
                      │   FIREBASE      │
                      │   (Firestore)   │
                      └─────────────────┘
```

**Total Cost: $0/month** ✅

---

## 🎯 Part 1: Deploy Backend (Render.com)

### Prerequisites
- ✅ GitHub account
- ✅ Firebase credentials JSON file
- ✅ Your code pushed to GitHub

### Step 1: Push Code to GitHub

```bash
# Initialize git (if not already)
cd C:\Users\bbhar\Downloads\proejct
git init

# Add all files
git add .
git commit -m "Initial commit - MediScan AI"

# Create repository on GitHub (do this first on github.com)
# Then push:
git remote add origin https://github.com/YOUR_USERNAME/mediscan-ai.git
git branch -M main
git push -u origin main
```

### Step 2: Sign Up for Render

1. Go to **https://render.com**
2. Click **"Sign Up"**
3. Sign up with **GitHub** (easiest)
4. Authorize Render to access your repos

### Step 3: Create New Web Service

1. Click **"New +"** → **"Web Service"**
2. Connect your **mediscan-ai** repository
3. Configure:
   ```
   Name: mediscan-ai-backend
   Region: Oregon (US West)
   Branch: main
   Runtime: Python 3
   Build Command: pip install -r backend/requirements.txt
   Start Command: cd backend && gunicorn app:app --bind 0.0.0.0:$PORT
   Plan: FREE
   ```

### Step 4: Add Environment Variables

In Render dashboard → Environment → Add:

```
FIREBASE_CONFIG = {paste your firebase-credentials.json content here}
GEMINI_API_KEY = your_gemini_api_key_here
PYTHON_VERSION = 3.11.0
```

**Important:** For `FIREBASE_CONFIG`:
1. Open `backend/firebase-credentials.json`
2. Copy the ENTIRE JSON content
3. Paste it as the value (keep it as JSON)

### Step 5: Deploy!

1. Click **"Create Web Service"**
2. Wait 5-10 minutes for first deployment
3. You'll get a URL like: `https://mediscan-ai-backend.onrender.com`

### Step 6: Test Backend

Open: `https://mediscan-ai-backend.onrender.com/api/health`

Should return:
```json
{
  "status": "healthy",
  "message": "MediScan AI Backend is running"
}
```

✅ **Backend deployed!**

---

## 🎨 Part 2: Deploy Frontend (Vercel)

### Step 1: Update Frontend API URL

Edit `frontend/src/services/api.js`:

```javascript
// Change this line:
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

// To use your Render URL:
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://mediscan-ai-backend.onrender.com';
```

Commit and push:
```bash
git add frontend/src/services/api.js
git commit -m "Update API URL for production"
git push
```

### Step 2: Sign Up for Vercel

1. Go to **https://vercel.com**
2. Click **"Sign Up"**
3. Sign up with **GitHub**
4. Authorize Vercel

### Step 3: Import Project

1. Click **"Add New..."** → **"Project"**
2. Import your **mediscan-ai** repository
3. Configure:
   ```
   Framework Preset: Vite
   Root Directory: frontend
   Build Command: npm run build
   Output Directory: dist
   ```

### Step 4: Add Environment Variables

In Vercel → Project Settings → Environment Variables:

```
VITE_API_URL = https://mediscan-ai-backend.onrender.com

VITE_FIREBASE_API_KEY = your_firebase_api_key
VITE_FIREBASE_AUTH_DOMAIN = your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID = your-project-id
VITE_FIREBASE_STORAGE_BUCKET = your-project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID = your_sender_id
VITE_FIREBASE_APP_ID = your_app_id
```

**Get these from:** `frontend/src/services/firebase.js`

### Step 5: Deploy!

1. Click **"Deploy"**
2. Wait 2-3 minutes
3. You'll get a URL like: `https://mediscan-ai.vercel.app`

✅ **Frontend deployed!**

---

## 🔥 Part 3: Configure Firebase (Already Setup!)

Your Firebase should already be working, but verify:

### Firestore Rules (Should be set)
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if request.auth != null;
    }
  }
}
```

### Firebase Authentication
Make sure **Email/Password** is enabled in Firebase Console.

---

## ✅ Testing Your Deployed App

### 1. Open Your App
Visit: `https://mediscan-ai.vercel.app`

### 2. Test Login
- Create account or login
- Should work without errors

### 3. Test Upload
- Upload a prescription or CT scan
- Check if analysis works

### 4. Test Dashboard
- View analyses
- Click on rows
- Export FHIR

### 5. Check Backend Logs
- Go to Render Dashboard
- Click on your service
- View **Logs** tab to debug issues

---

## 🐛 Common Issues & Fixes

### Issue 1: CORS Error
**Error:** "Access to fetch blocked by CORS policy"

**Fix:** Backend should have this in `app.py`:
```python
from flask_cors import CORS
CORS(app)
```

### Issue 2: 504 Timeout on First Request
**Cause:** Render free tier "sleeps" after 15 min inactivity

**Fix:** First request takes 30-60 seconds (normal!)

### Issue 3: Firebase Auth Not Working
**Fix:** Check Firebase config in Vercel environment variables

### Issue 4: Backend Crash
**Fix:** Check Render logs for errors
- Might be missing dependencies
- Check environment variables are set

---

## 💰 Cost Breakdown

| Service | Tier | Cost |
|---------|------|------|
| **Render** (Backend) | Free | $0/month |
| **Vercel** (Frontend) | Hobby | $0/month |
| **Firebase** (Database + Auth) | Spark | $0/month |
| **Total** | | **$0/month** ✅ |

### Free Tier Limits
- **Render:** 750 hours/month (enough for 24/7!)
- **Vercel:** 100 GB bandwidth, unlimited requests
- **Firebase:** 1 GB storage, 50K reads/day, 20K writes/day

---

## 🚀 Optional: Custom Domain

### Free Option: Use Vercel subdomain
- `https://mediscan-ai.vercel.app` (FREE)

### Paid Option: Custom domain
- Buy domain from Namecheap (~$10/year)
- Add to Vercel → Settings → Domains

---

## 📝 Deployment Checklist

### Before Deployment
- [ ] Code pushed to GitHub
- [ ] Firebase credentials ready
- [ ] Gemini API key ready
- [ ] Tested locally

### Backend (Render)
- [ ] Render account created
- [ ] Repository connected
- [ ] Environment variables set
- [ ] Service deployed
- [ ] Health endpoint working

### Frontend (Vercel)
- [ ] Vercel account created
- [ ] API URL updated
- [ ] Firebase config set
- [ ] Project deployed
- [ ] App accessible

### Testing
- [ ] Login works
- [ ] Upload works
- [ ] Dashboard loads
- [ ] FHIR export works
- [ ] All features tested

---

## 🎉 Success!

Your app is now live at:
- **Frontend:** https://mediscan-ai.vercel.app
- **Backend:** https://mediscan-ai-backend.onrender.com

**Share it with anyone in the world!** 🌍

---

## 🔄 Updating Your App

### Update Code
```bash
# Make changes to your code
git add .
git commit -m "Your update message"
git push
```

**Both Render and Vercel will auto-deploy on push!** ✨

---

## 📞 Support

**Render Issues:** https://render.com/docs  
**Vercel Issues:** https://vercel.com/docs  
**Firebase Issues:** https://firebase.google.com/support

---

**Happy Deploying!** 🚀

