# 🚀 Deploy Frontend to Vercel

## ✅ Your Backend is Live!
**Backend URL:** `https://mediai-t6oo.onrender.com`

Now let's deploy the frontend to Vercel in 5 easy steps.

---

## 📋 **Step 1: Create .env File (Optional for Local)**

In the `frontend/` folder, create a file named `.env`:

```bash
VITE_API_URL=https://mediai-t6oo.onrender.com
```

**Note:** This is for local testing. Vercel will use environment variables from its dashboard.

---

## 🚀 **Step 2: Go to Vercel**

1. Visit: **https://vercel.com**
2. Click **"Sign Up"** or **"Log In"**
3. Choose **"Continue with GitHub"**
4. Authorize Vercel to access your GitHub account

---

## 📦 **Step 3: Import Your Project**

1. Click **"Add New..."** → **"Project"**
2. Find your GitHub repository (the one you pushed to)
3. Click **"Import"**

---

## ⚙️ **Step 4: Configure Build Settings**

Vercel will auto-detect it's a Vite/React app. Verify these settings:

### **Framework Preset:**
- **Framework:** Vite ✅ (auto-detected)

### **Root Directory:**
- Click **"Edit"**
- Set to: `frontend`
- Click **"Continue"**

### **Build & Output Settings:**
- **Build Command:** `npm run build` or `yarn build` ✅
- **Output Directory:** `dist` ✅
- **Install Command:** `npm install` or `yarn install` ✅

**Leave these as default (Vercel auto-fills them)**

---

## 🔑 **Step 5: Add Environment Variable**

**MOST IMPORTANT STEP!**

Before clicking "Deploy", scroll down to **"Environment Variables"**:

1. Click **"Add"**
2. **Name:** `VITE_API_URL`
3. **Value:** `https://mediai-t6oo.onrender.com`
4. **Environments:** Check all boxes (Production, Preview, Development)
5. Click **"Add"**

---

## 🚀 **Step 6: Deploy!**

1. Click **"Deploy"**
2. Wait 2-3 minutes ⏱️
3. Watch the build logs
4. When done, you'll see **"🎉 Congratulations!"**

---

## 🌐 **Get Your Frontend URL**

After deployment succeeds:

1. Vercel will show your URL: `https://your-app-name.vercel.app`
2. Click **"Visit"** to open your app
3. Test uploading a medical document!

---

## 🔄 **Auto-Deploy Setup**

**Good news:** Vercel auto-deploys on every push to GitHub!

Whenever you:
```bash
git push origin main
```

Vercel automatically rebuilds and redeploys your frontend! 🎉

---

## ✅ **What to Test After Deployment**

1. **Open your Vercel URL**
2. **Try Login/Signup**
3. **Upload a prescription or X-ray**
4. **Check the analysis results**
5. **Export FHIR** (test the download)
6. **Check Dashboard** (view analyses)

---

## 🔧 **Troubleshooting**

### **Issue 1: "Network Error" or "Cannot connect"**
**Cause:** Frontend can't reach backend

**Fix:**
1. Go to Vercel dashboard
2. Click your project → **"Settings"** → **"Environment Variables"**
3. Verify `VITE_API_URL` = `https://mediai-t6oo.onrender.com`
4. Click **"Deployments"** → Redeploy

### **Issue 2: "CORS Error"**
**Cause:** Backend CORS not allowing frontend domain

**Fix:** Already handled in your backend! (flask-cors with allow all origins)

### **Issue 3: "Firebase Error"**
**Cause:** Missing Firebase credentials in frontend

**Fix:** Check `frontend/src/firebase.js` has correct config

---

## 📊 **Your Full Stack Architecture**

```
┌─────────────────────────────────────┐
│   Frontend (Vercel)                 │
│   https://your-app.vercel.app       │
│   - React + Vite                    │
│   - User Interface                  │
└──────────────┬──────────────────────┘
               │
               │ API Calls
               ▼
┌─────────────────────────────────────┐
│   Backend (Render)                  │
│   https://mediai-t6oo.onrender.com  │
│   - Flask API                       │
│   - AI Models (PyTorch)             │
│   - OCR (Gemini + Tesseract)        │
└──────────────┬──────────────────────┘
               │
               │ Store/Retrieve
               ▼
┌─────────────────────────────────────┐
│   Database (Firebase/Firestore)     │
│   - Patient data                    │
│   - Analysis results                │
│   - Audit logs                      │
└─────────────────────────────────────┘
```

---

## 💡 **Pro Tips**

1. **Custom Domain (Optional):**
   - Go to Vercel → Settings → Domains
   - Add your own domain (if you have one)

2. **Preview Deployments:**
   - Every GitHub branch gets a preview URL
   - Test features before merging to main

3. **Analytics:**
   - Vercel provides free analytics
   - Check Settings → Analytics

---

## 🎉 **You're Done!**

After deploying to Vercel, you'll have:
- ✅ Frontend live on Vercel
- ✅ Backend live on Render
- ✅ Database on Firebase
- ✅ Full stack medical AI app!

**Share your Vercel URL and let users try it!** 🚀

