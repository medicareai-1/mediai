# 📂 MediScan AI - Project Structure

Complete file organization and description.

---

## 📁 Root Directory

```
mediscan-ai/
├── backend/                          # Flask backend application
├── frontend/                         # React frontend application
├── firebase.json                     # Firebase hosting configuration
├── firestore.rules                   # Firestore security rules
├── firestore.indexes.json            # Firestore indexes
├── storage.rules                     # Firebase Storage security rules
├── render.yaml                       # Render deployment configuration
├── .gitignore                        # Git ignore patterns
├── LICENSE                           # MIT License
├── README.md                         # Main project documentation
├── SETUP_GUIDE.md                    # Detailed setup instructions
├── QUICKSTART.md                     # Quick start guide
├── ENVIRONMENT_SETUP.md              # Environment variables guide
└── DEPLOYMENT_CHECKLIST.md           # Deployment checklist
```

---

## 🐍 Backend Structure

```
backend/
├── app.py                            # Main Flask application
│   ├── Flask routes & endpoints
│   ├── Firebase initialization
│   ├── CORS configuration
│   └── API endpoints
│
├── models/                           # AI Models
│   ├── __init__.py
│   ├── ocr_model.py                 # EasyOCR implementation
│   │   ├── OCRModel class
│   │   ├── Text extraction
│   │   └── Image preprocessing
│   ├── nlp_model.py                 # spaCy NLP model
│   │   ├── NLPModel class
│   │   ├── Entity extraction
│   │   ├── Medicine identification
│   │   └── Custom patterns
│   └── cnn_model.py                 # PyTorch CNN model
│       ├── CNNModel class
│       ├── ResNet18 architecture
│       └── Image classification
│
├── explainability/                   # Explainability modules
│   ├── __init__.py
│   └── gradcam.py                   # Grad-CAM implementation
│       ├── GradCAM class
│       ├── Heatmap generation
│       └── Visualization
│
├── utils/                            # Utility functions
│   ├── __init__.py
│   └── helpers.py                   # Helper functions
│       ├── download_image()
│       ├── upload_to_storage()
│       ├── resize_image()
│       └── normalize_image()
│
├── requirements.txt                  # Python dependencies
├── firebase-credentials.json         # Firebase service account (DON'T COMMIT!)
└── .env                              # Environment variables (DON'T COMMIT!)
```

### Backend Key Files Description

#### `app.py`
Main Flask application with API endpoints:
- `/` - Health check
- `/api/health` - Detailed health status
- `/api/process` - Process any medical document
- `/api/process-prescription` - Process prescription specifically
- `/api/analyze-image` - Analyze medical images
- `/api/patients` - Patient CRUD operations
- `/api/analytics` - Analytics data

#### Models

**`ocr_model.py`** - OCR Engine
- Uses EasyOCR for text extraction
- Preprocesses images (grayscale, denoise, threshold)
- Returns text with confidence scores

**`nlp_model.py`** - NLP Parser
- Uses spaCy en_core_web_sm
- Custom entity recognition (MEDICINE, DOSAGE, DURATION)
- Pattern matching with regex
- Medicine name extraction with heuristics

**`cnn_model.py`** - Image Classifier
- PyTorch ResNet18 pretrained on ImageNet
- Fine-tuned for medical image classification
- 4 classes: Normal, Pneumonia, Tumor, Fracture
- Returns prediction with confidence

**`gradcam.py`** - Explainability
- Implements Grad-CAM algorithm
- Generates heatmap overlays
- Shows which image regions influenced decision
- Supports multiple class visualization

---

## ⚛️ Frontend Structure

```
frontend/
├── public/                          # Static assets
│   └── mediscan-icon.svg           # App icon (optional)
│
├── src/                            # Source code
│   ├── components/                 # Reusable components
│   │   └── Layout.jsx             # Main layout with navigation
│   │
│   ├── pages/                     # Page components
│   │   ├── Login.jsx              # Authentication page
│   │   ├── Dashboard.jsx          # Main dashboard
│   │   ├── Upload.jsx             # Document upload page
│   │   ├── Patients.jsx           # Patient management
│   │   └── Analytics.jsx          # Analytics dashboard
│   │
│   ├── contexts/                  # React contexts
│   │   └── AuthContext.jsx        # Authentication state
│   │
│   ├── services/                  # External services
│   │   ├── firebase.js            # Firebase configuration
│   │   └── api.js                 # Backend API client
│   │
│   ├── App.jsx                    # Root component
│   ├── main.jsx                   # Entry point
│   └── index.css                  # Global styles (Tailwind)
│
├── dist/                           # Production build (generated)
├── node_modules/                   # Dependencies (generated)
├── index.html                      # HTML template
├── package.json                    # Node dependencies
├── package-lock.json               # Locked dependencies
├── vite.config.js                  # Vite configuration
├── tailwind.config.js              # Tailwind CSS config
├── postcss.config.js               # PostCSS config
└── .env                            # Environment variables (DON'T COMMIT!)
```

### Frontend Key Files Description

#### Pages

**`Login.jsx`** - Authentication
- Email/password login
- Google OAuth
- Sign up functionality
- Form validation
- Beautiful gradient background

**`Dashboard.jsx`** - Main Dashboard
- Real-time analyses table (Firestore onSnapshot)
- Stat cards (total analyses, patients, etc.)
- Recent activity
- Live updates

**`Upload.jsx`** - Document Upload
- Document type selection
- Patient ID input
- File upload with preview
- Processing status
- Results display (OCR, NLP, CNN, Grad-CAM)

**`Patients.jsx`** - Patient Management
- Patient list with search
- Add new patient modal
- Real-time updates
- Patient cards with details

**`Analytics.jsx`** - Analytics Dashboard
- Chart.js visualizations
- Medicine frequency bar chart
- Diagnosis distribution pie chart
- Daily analyses trend line chart
- Model performance metrics

#### Components

**`Layout.jsx`** - Main Layout
- Navigation bar
- User menu
- Logout functionality
- Mobile responsive menu
- Route-based active highlighting

#### Services

**`firebase.js`** - Firebase Setup
- Firebase initialization
- Auth, Firestore, Storage exports
- Configuration from environment variables

**`api.js`** - API Client
- Axios instance
- Backend API endpoints
- Request/response handling
- Error handling

#### Contexts

**`AuthContext.jsx`** - Auth State Management
- Current user state
- Login/logout functions
- Sign up function
- Google OAuth
- Session persistence

---

## 🔥 Firebase Configuration Files

### `firebase.json`
Firebase hosting configuration:
- Public directory: `frontend/dist`
- Rewrites for single-page app
- Caching headers
- References to rules and indexes

### `firestore.rules`
Firestore security rules:
- Authentication required
- User-based access control
- Collection-specific rules
- Read/write permissions

### `firestore.indexes.json`
Firestore composite indexes:
- Timestamp descending index
- User + timestamp compound index
- Query optimization

### `storage.rules`
Storage security rules:
- User-specific folders
- Authentication required
- Read/write permissions
- Path-based security

---

## 🚀 Deployment Configuration

### `render.yaml`
Render deployment configuration:
- Service type: Web
- Environment: Python
- Build command
- Start command
- Environment variables
- Plan: Free

---

## 📚 Documentation Files

### `README.md`
Main project documentation:
- Overview and features
- Architecture diagram
- Tech stack
- Setup instructions
- Deployment guide
- API documentation
- Screenshots
- Troubleshooting

### `SETUP_GUIDE.md`
Detailed setup instructions:
- Step-by-step Firebase setup
- Local development setup
- Deployment to Render
- Deployment to Firebase Hosting
- Configuration details
- Testing procedures

### `QUICKSTART.md`
Quick start guide:
- Minimal setup steps
- Essential commands
- Quick troubleshooting
- Success checklist

### `ENVIRONMENT_SETUP.md`
Environment variables guide:
- Frontend .env variables
- Backend .env variables
- Firebase credentials
- Security best practices
- Troubleshooting

### `DEPLOYMENT_CHECKLIST.md`
Comprehensive deployment checklist:
- Firebase setup checklist
- Backend deployment checklist
- Frontend deployment checklist
- Security checklist
- Testing checklist
- Success criteria

---

## 🔒 Security Files

### `.gitignore`
Prevents committing sensitive files:
- `.env` files
- `firebase-credentials.json`
- `node_modules/`
- `venv/`
- Build artifacts
- IDE files

---

## 📦 Dependency Files

### `backend/requirements.txt`
Python dependencies:
- Flask (web framework)
- flask-cors (CORS support)
- firebase-admin (Firebase SDK)
- easyocr (OCR engine)
- spacy (NLP library)
- torch (PyTorch)
- torchvision (computer vision)
- opencv-python (image processing)
- gunicorn (production server)

### `frontend/package.json`
Node dependencies:
- react (UI framework)
- react-router-dom (routing)
- firebase (Firebase SDK)
- chart.js (charts)
- axios (HTTP client)
- tailwindcss (CSS framework)
- vite (build tool)
- lucide-react (icons)

---

## 🎯 File Size Estimates

```
Total Project Size: ~150-200 MB (with dependencies)

Backend:
├── Code: ~50 KB
├── Dependencies: ~800 MB (virtual environment)
└── Models (downloaded at runtime): ~200 MB

Frontend:
├── Code: ~100 KB
├── Dependencies: ~300 MB (node_modules)
└── Build output: ~500 KB

Firebase:
├── Credentials: ~2 KB
└── Rules: ~2 KB

Documentation:
└── All .md files: ~100 KB
```

---

## 📊 Code Statistics

```
Backend:
- Python files: 6
- Total lines: ~1,500
- Functions: ~30
- Classes: 4

Frontend:
- JSX/JS files: 12
- Total lines: ~2,500
- Components: 10
- Pages: 5

Configuration:
- Config files: 10
- Documentation: 7
- Total files: ~35
```

---

## 🔄 Data Flow Through Structure

```
User uploads document
    ↓
frontend/src/pages/Upload.jsx
    ↓
frontend/src/services/firebase.js (Upload to Storage)
    ↓
frontend/src/services/api.js (Call backend)
    ↓
backend/app.py (/api/process endpoint)
    ↓
backend/models/ocr_model.py (Extract text)
    ↓
backend/models/nlp_model.py (Extract entities)
    ↓
backend/models/cnn_model.py (Classify image)
    ↓
backend/explainability/gradcam.py (Generate heatmap)
    ↓
backend/utils/helpers.py (Upload heatmap)
    ↓
Firebase Firestore (Save results)
    ↓
frontend/src/pages/Dashboard.jsx (Real-time update)
```

---

## 🎨 UI Component Hierarchy

```
App.jsx
├── AuthContext (Wraps everything)
└── Router
    ├── /login → Login.jsx
    └── / → Layout.jsx
        ├── Navigation
        ├── Outlet (Page content)
        │   ├── / → Dashboard.jsx
        │   ├── /upload → Upload.jsx
        │   ├── /patients → Patients.jsx
        │   └── /analytics → Analytics.jsx
        └── User menu
```

---

This structure is designed for:
✅ **Scalability** - Easy to add new features
✅ **Maintainability** - Clear separation of concerns
✅ **Readability** - Logical organization
✅ **Deployment** - Ready for production
✅ **Collaboration** - Easy for teams to work on

---

**Understanding this structure is key to successfully working with and presenting MediScan AI!**

