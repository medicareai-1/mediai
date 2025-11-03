# 🚀 Exact Commands to Deploy

Copy-paste these commands to deploy your app!

---

## 📦 Step 1: Prepare for Deployment

### Save Your Firebase Credentials
```bash
# Open this file and copy its content (you'll need it later)
notepad backend/firebase-credentials.json

# Copy everything and save it somewhere safe!
```

---

## 🔧 Step 2: Push to GitHub

```bash
# Navigate to project
cd C:\Users\bbhar\Downloads\proejct

# Initialize git (if not already)
git init

# Add all files
git add .

# Commit
git commit -m "MediScan AI - Initial deployment"

# Create a new repo on GitHub.com called "mediscan-ai"
# Then run these (replace YOUR_USERNAME):

git remote add origin https://github.com/YOUR_USERNAME/mediscan-ai.git
git branch -M main
git push -u origin main
```

**✅ Code is now on GitHub!**

---

## 🖥️ Step 3: Deploy Backend (Render)

### Go to Browser:
1. Open: **https://render.com**
2. Click **"Sign Up"** → Sign in with GitHub
3. Click **"New +"** → **"Web Service"**
4. Select **mediscan-ai** repository

### Fill in these settings:
```
Name: mediscan-ai-backend
Environment: Python 3
Region: Oregon (US West)
Branch: main
Root Directory: (leave blank)

Build Command:
pip install -r backend/requirements.txt && python -m spacy download en_core_web_sm

Start Command:
cd backend && gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120

Instance Type: FREE
```

### Add Environment Variables:
Click **"Add Environment Variable"**

**Variable 1:**
```
Key: FIREBASE_CONFIG
Value: (paste your firebase-credentials.json content here)
```

**Variable 2 (Optional - if using Gemini):**
```
Key: GEMINI_API_KEY
Value: your_gemini_api_key
```

### Deploy:
5. Click **"Create Web Service"**
6. Wait 5-10 minutes for build
7. You'll get: `https://mediscan-ai-backend-xxxx.onrender.com`

**✅ Backend is LIVE!**

---

## 🎨 Step 4: Deploy Frontend (Vercel)

### Go to Browser:
1. Open: **https://vercel.com**
2. Click **"Sign Up"** → Sign in with GitHub
3. Click **"Add New..."** → **"Project"**
4. Import **mediscan-ai** repository

### Configure Project:
```
Framework Preset: Vite
Root Directory: frontend
Build Command: npm run build
Output Directory: dist
Install Command: npm install
```

### Add Environment Variables:
Click **"Environment Variables"** → Add these:

**Get values from:** `frontend/src/services/firebase.js` or Firebase Console

```
VITE_API_URL
Value: https://mediscan-ai-backend-xxxx.onrender.com
(Use YOUR backend URL from Step 3)

VITE_FIREBASE_API_KEY
Value: your_firebase_api_key

VITE_FIREBASE_AUTH_DOMAIN
Value: your-project.firebaseapp.com

VITE_FIREBASE_PROJECT_ID
Value: your-project-id

VITE_FIREBASE_STORAGE_BUCKET
Value: your-project.appspot.com

VITE_FIREBASE_MESSAGING_SENDER_ID
Value: your_sender_id

VITE_FIREBASE_APP_ID
Value: your_app_id
```

### Deploy:
5. Click **"Deploy"**
6. Wait 2-3 minutes
7. You'll get: `https://mediscan-ai-xxxx.vercel.app`

**✅ Frontend is LIVE!**

---

## ✅ Step 5: Test Your App

### Test Backend:
Open in browser:
```
https://mediscan-ai-backend-xxxx.onrender.com/api/health
```

Should return:
```json
{"status": "healthy"}
```

### Test Frontend:
Open in browser:
```
https://mediscan-ai-xxxx.vercel.app
```

Should show your MediScan AI login page!

### Full Test:
1. Login/Signup
2. Upload a file
3. Check dashboard
4. Export FHIR

**If everything works → You're LIVE!** 🎉

---

## 🔄 Update Your App Later

Whenever you make changes:

```bash
cd C:\Users\bbhar\Downloads\proejct

# Make your code changes, then:
git add .
git commit -m "Updated feature XYZ"
git push
```

**Both Render and Vercel will auto-deploy!** ✨

No need to do anything else!

---

## 🐛 Troubleshooting

### Backend not working?
```bash
# Check Render logs:
1. Go to render.com
2. Click your service
3. Click "Logs" tab
4. Look for errors
```

### Frontend not working?
```bash
# Check browser console:
1. Open your app
2. Press F12
3. Click "Console" tab
4. Look for errors
```

### Common fixes:
- **504 Timeout:** First request after sleep takes 30 seconds (normal!)
- **CORS Error:** Backend needs `CORS(app)` in app.py
- **Firebase Error:** Check environment variables in Vercel
- **Build Failed:** Check requirements.txt dependencies

---

## 📝 Your URLs (Fill in after deployment)

**Frontend:** https://_________________________.vercel.app

**Backend:** https://_________________________.onrender.com

**Save these URLs!** Share with anyone! 🌍

---

## 💰 Cost

**Total: $0/month** ✅

Free tier limits:
- Render: 750 hours/month (enough for 24/7)
- Vercel: 100 GB bandwidth
- Firebase: 1 GB storage, 50K reads/day

---

**Done! Your app is now accessible worldwide!** 🚀🌍

