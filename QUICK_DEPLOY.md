# ⚡ Quick Deploy Guide (5 Minutes)

The **fastest way** to get MediScan AI live!

---

## 🚀 Step 1: Push to GitHub (2 min)

```bash
cd C:\Users\bbhar\Downloads\proejct

# Create .gitignore (prevents uploading secrets)
# Already created - check .gitignore file

# Initialize git
git init
git add .
git commit -m "MediScan AI - Ready for deployment"

# Create repo on GitHub.com first, then:
git remote add origin https://github.com/YOUR_USERNAME/mediscan-ai.git
git branch -M main
git push -u origin main
```

**⚠️ Important:** Before pushing, copy your `firebase-credentials.json` content somewhere safe! You'll need it for environment variables.

---

## 🔧 Step 2: Deploy Backend to Render (2 min)

1. Go to **https://render.com** → Sign up with GitHub
2. Click **"New +"** → **"Web Service"**
3. Select your **mediscan-ai** repo
4. Fill in:
   ```
   Name: mediscan-ai-backend
   Root Directory: (leave empty)
   Environment: Python 3
   Build Command: pip install -r backend/requirements.txt
   Start Command: cd backend && gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120
   Plan: FREE
   ```

5. **Add Environment Variable:**
   - Key: `FIREBASE_CONFIG`
   - Value: (paste your `firebase-credentials.json` content)

6. Click **"Create Web Service"**

7. Wait 5-10 minutes, you'll get: `https://mediscan-ai-backend.onrender.com`

---

## 🎨 Step 3: Deploy Frontend to Vercel (1 min)

1. Go to **https://vercel.com** → Sign up with GitHub
2. Click **"Add New..."** → **"Project"**
3. Import **mediscan-ai** repo
4. Configure:
   ```
   Framework: Vite
   Root Directory: frontend
   Build Command: npm run build
   Output Directory: dist
   ```

5. **Add Environment Variables:** (from your firebase.js)
   ```
   VITE_API_URL = https://mediscan-ai-backend.onrender.com
   VITE_FIREBASE_API_KEY = your_key
   VITE_FIREBASE_AUTH_DOMAIN = your_domain
   VITE_FIREBASE_PROJECT_ID = your_project
   VITE_FIREBASE_STORAGE_BUCKET = your_bucket
   VITE_FIREBASE_MESSAGING_SENDER_ID = your_id
   VITE_FIREBASE_APP_ID = your_app_id
   ```

6. Click **"Deploy"**

7. Done! You get: `https://mediscan-ai.vercel.app`

---

## ✅ Step 4: Test (30 seconds)

1. Visit your Vercel URL
2. Create account / Login
3. Upload a file
4. Check dashboard

**If it works → You're LIVE!** 🎉

---

## 🐛 If Something Breaks

### Backend Issues
- Check Render logs: Dashboard → Your Service → Logs tab
- Most common: Missing environment variable

### Frontend Issues
- Check browser console (F12)
- Most common: Wrong API URL or Firebase config

### Quick Fix
- Redeploy: Render/Vercel → Manual Deploy → Deploy

---

## 🔄 Update Your App Later

```bash
# Make changes to code
git add .
git commit -m "Updated feature X"
git push
```

**Auto-deploys on both Render and Vercel!** ✨

---

**Total Time: 5 minutes**  
**Total Cost: $0/month**

Done! 🚀

