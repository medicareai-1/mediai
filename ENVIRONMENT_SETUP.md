# 🔐 Environment Variables Configuration

This document contains all environment variable configurations needed for MediScan AI.

---

## Frontend Environment Variables

Create a file named `.env` in the `frontend/` directory with the following content:

```env
# Firebase Configuration
# Get these values from Firebase Console → Project Settings → General → Your apps → Web app

VITE_FIREBASE_API_KEY=your_api_key_here
VITE_FIREBASE_AUTH_DOMAIN=your_project_id.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your_project_id
VITE_FIREBASE_STORAGE_BUCKET=your_project_id.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=your_messaging_sender_id
VITE_FIREBASE_APP_ID=your_app_id

# Backend API URL
# For local development:
VITE_API_URL=http://localhost:5000

# For production (after deploying to Render):
# VITE_API_URL=https://your-app-name.onrender.com
```

### How to Get Firebase Config Values:

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project
3. Click the gear icon (⚙️) → Project Settings
4. Scroll down to "Your apps" section
5. Click on your web app (or create one if none exists)
6. Copy each value from the `firebaseConfig` object

**Example**:
```javascript
const firebaseConfig = {
  apiKey: "AIzaSyAbc123...",                    // → VITE_FIREBASE_API_KEY
  authDomain: "mediscan-xyz.firebaseapp.com",  // → VITE_FIREBASE_AUTH_DOMAIN
  projectId: "mediscan-xyz",                   // → VITE_FIREBASE_PROJECT_ID
  storageBucket: "mediscan-xyz.appspot.com",   // → VITE_FIREBASE_STORAGE_BUCKET
  messagingSenderId: "123456789012",           // → VITE_FIREBASE_MESSAGING_SENDER_ID
  appId: "1:123456789012:web:abc123def456"    // → VITE_FIREBASE_APP_ID
};
```

---

## Backend Environment Variables

### For Local Development

Create a file named `.env` in the `backend/` directory (optional):

```env
# Flask Configuration
FLASK_ENV=development
PORT=5000

# Firebase Configuration
FIREBASE_STORAGE_BUCKET=your_project_id.appspot.com
```

**For local development**, also create `firebase-credentials.json`:

1. Go to Firebase Console → Project Settings → Service Accounts
2. Click "Generate new private key"
3. Save the downloaded JSON file as `backend/firebase-credentials.json`

**⚠️ IMPORTANT**: Add `firebase-credentials.json` to `.gitignore` - never commit this file!

---

### For Render Deployment

When deploying to Render, set these environment variables in the Render dashboard:

#### Environment Variables to Set:

1. **FIREBASE_CONFIG**
   - Value: Paste the **entire content** of your `firebase-credentials.json` file
   - This should be a single line of JSON
   - Example format:
   ```json
   {"type":"service_account","project_id":"mediscan-xyz","private_key_id":"abc123...","private_key":"-----BEGIN PRIVATE KEY-----\nMIIE...","client_email":"firebase-adminsdk@mediscan-xyz.iam.gserviceaccount.com","client_id":"123456789","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk%40mediscan-xyz.iam.gserviceaccount.com"}
   ```

2. **FIREBASE_STORAGE_BUCKET**
   - Value: `your_project_id.appspot.com`
   - Example: `mediscan-xyz.appspot.com`

3. **PORT** (Render sets this automatically)
   - Value: `5000`

4. **PYTHON_VERSION** (optional)
   - Value: `3.11.0`

#### How to Set Environment Variables on Render:

1. Go to your Render dashboard
2. Select your web service
3. Click "Environment" in the left sidebar
4. Click "Add Environment Variable"
5. Enter key and value
6. Click "Save Changes"

---

## Firebase Service Account JSON

Your `firebase-credentials.json` file should look like this:

```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "abc123...",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBA...\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-xxxxx@your-project-id.iam.gserviceaccount.com",
  "client_id": "123456789012345678901",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-xxxxx%40your-project-id.iam.gserviceaccount.com"
}
```

---

## Security Best Practices

### ✅ DO:
- Store credentials in environment variables
- Add `.env` and `firebase-credentials.json` to `.gitignore`
- Use different credentials for development and production
- Rotate credentials regularly
- Use environment-specific configs

### ❌ DON'T:
- Commit credentials to Git
- Share credentials in public channels
- Use production credentials in development
- Hardcode credentials in source code
- Upload credentials to public repositories

---

## Verifying Environment Variables

### Frontend Verification

In your browser console after starting the app:
```javascript
console.log('API URL:', import.meta.env.VITE_API_URL);
console.log('Firebase Project:', import.meta.env.VITE_FIREBASE_PROJECT_ID);
```

### Backend Verification

In `backend/app.py`, add temporary logging:
```python
import os
print('Environment:', os.environ.get('FLASK_ENV'))
print('Storage Bucket:', os.environ.get('FIREBASE_STORAGE_BUCKET'))
```

---

## Common Issues and Solutions

### Issue: "Firebase app not initialized"

**Solution**: 
- Check that frontend `.env` file exists
- Verify all VITE_ prefixed variables are set
- Restart development server after creating `.env`

### Issue: "Permission denied" in Firestore

**Solution**:
- Ensure `firebase-credentials.json` is in backend folder
- Check that service account has required permissions
- Deploy Firestore security rules

### Issue: "CORS error" when calling API

**Solution**:
- Verify `VITE_API_URL` is correct
- Check Flask-CORS is installed
- Ensure backend is running

### Issue: Render deployment fails

**Solution**:
- Verify `FIREBASE_CONFIG` is valid JSON (no line breaks)
- Check all environment variables are set
- Review Render deployment logs

---

## Environment Variable Checklist

Before running the application, ensure:

### Frontend (.env in frontend/):
- [ ] VITE_FIREBASE_API_KEY
- [ ] VITE_FIREBASE_AUTH_DOMAIN
- [ ] VITE_FIREBASE_PROJECT_ID
- [ ] VITE_FIREBASE_STORAGE_BUCKET
- [ ] VITE_FIREBASE_MESSAGING_SENDER_ID
- [ ] VITE_FIREBASE_APP_ID
- [ ] VITE_API_URL

### Backend (Local):
- [ ] firebase-credentials.json file exists in backend/
- [ ] .env file (optional)
- [ ] Virtual environment activated

### Backend (Render):
- [ ] FIREBASE_CONFIG (entire JSON as string)
- [ ] FIREBASE_STORAGE_BUCKET
- [ ] PORT (auto-set by Render)

---

## Quick Setup Commands

### Create Frontend .env
```bash
cd frontend
cat > .env << 'EOF'
VITE_FIREBASE_API_KEY=your_key
VITE_FIREBASE_AUTH_DOMAIN=your_domain
VITE_FIREBASE_PROJECT_ID=your_project
VITE_FIREBASE_STORAGE_BUCKET=your_bucket
VITE_FIREBASE_MESSAGING_SENDER_ID=your_sender
VITE_FIREBASE_APP_ID=your_app_id
VITE_API_URL=http://localhost:5000
EOF
```

### Create Backend .env
```bash
cd backend
cat > .env << 'EOF'
FLASK_ENV=development
PORT=5000
FIREBASE_STORAGE_BUCKET=your_bucket
EOF
```

### Add to .gitignore
```bash
# From project root
cat >> .gitignore << 'EOF'
# Environment variables
.env
.env.local
.env.production

# Firebase credentials
firebase-credentials.json

# Python virtual environment
venv/
__pycache__/
*.pyc

# Node modules
node_modules/
EOF
```

---

**Remember**: Never commit sensitive credentials to version control!

