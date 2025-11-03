# 🚀 Quick Start: New Features

## Installation

```bash
# Backend
cd backend
pip install shap lime scikit-image scikit-learn matplotlib cryptography flask-socketio scipy

# Frontend (no new dependencies)
cd frontend
npm install
```

## 1. Using SHAP/LIME Explainability

### Backend (Automatic)
SHAP and LIME are automatically generated for X-ray analyses:

```python
# In app.py - already integrated
if document_type == 'xray':
    # ... CNN analysis ...
    
    # SHAP (automatic)
    shap_result = shap_explainer.explain(image, cnn.model, prediction_class)
    result["shap_visualization"] = shap_result.get("visualization")
    
    # LIME (automatic)
    lime_result = lime_explainer.explain(image, cnn.model, prediction_class)
    result["lime_visualization_positive"] = lime_result.get("visualization_positive")
```

### Frontend
```jsx
import ExplainabilityViewer from './components/ExplainabilityViewer';

// In your analysis result page
<ExplainabilityViewer 
  analysisData={analysisResult} 
  analysisId={analysisId} 
/>
```

### API Usage
```javascript
// Generate on-demand
const response = await fetch('/api/explainability/generate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    analysis_id: 'abc123',
    type: 'all',  // 'shap', 'lime', or 'all'
    user_id: 'user_001'
  })
});
```

## 2. Compliance Features

### Audit Logging
```python
# Automatically logs all data access
compliance_manager.log_access(
    action='view',
    user_id='user_001',
    patient_id='patient_123',
    resource_type='analysis',
    ip_address=request.remote_addr
)
```

### PHI Encryption
```python
# Encrypt patient data
encrypted_patient = compliance_manager.encrypt_phi(patient_data)

# Decrypt when needed
decrypted_patient = compliance_manager.decrypt_phi(encrypted_patient)
```

### GDPR Export
```javascript
// Frontend
const exportData = async (patientId) => {
  const response = await fetch('/api/compliance/export-patient-data', {
    method: 'POST',
    body: JSON.stringify({ patient_id: patientId, user_id: 'user_001' })
  });
  
  const data = await response.json();
  // Download as JSON
  const blob = new Blob([JSON.stringify(data, null, 2)]);
  // ... download logic
};
```

### GDPR Deletion
```javascript
// Frontend
const deleteData = async (patientId) => {
  await fetch('/api/compliance/delete-patient-data', {
    method: 'POST',
    body: JSON.stringify({ patient_id: patientId, user_id: 'user_001' })
  });
};
```

## 3. Real-time Dashboard

### Backend Setup
```python
# Already initialized in app.py
realtime_manager = RealtimeManager(app=app, db=db)

# Send notifications
realtime_manager.notify_analysis_complete(analysis_data)
realtime_manager.notify_new_patient(patient_data)
```

### Frontend WebSocket
```javascript
import io from 'socket.io-client';

const socket = io('http://localhost:5000');

// Join dashboard room
socket.emit('join_dashboard', { user_id: 'user_001' });

// Listen for updates
socket.on('dashboard_update', (stats) => {
  console.log('Real-time stats:', stats);
  // Update UI with stats
});

// Listen for notifications
socket.on('notification', (notification) => {
  console.log('New notification:', notification);
  // Show notification
});
```

## 4. Enhanced Lab Reports

### Using Enhanced Parser
```python
from utils.lab_parser import parse as parse_lab

# Parse with age/gender for specific ranges
lab_result = parse_lab(
    ocr_text, 
    age=45, 
    gender='M'
)

# Returns:
{
    "values": [...],              # All parsed values
    "abnormal_count": 3,          # Count of abnormals
    "critical_flags": [...],      # Critical alerts
    "insights": [...],            # Clinical insights
    "recommendations": [...],     # Action items
    "total_tests": 12
}
```

### Display Insights
```jsx
{labResult.insights?.map(insight => (
  <div key={insight} className="bg-blue-50 p-3 rounded">
    {insight}
  </div>
))}

{labResult.recommendations?.map(rec => (
  <div key={rec} className="bg-green-50 p-3 rounded">
    {rec}
  </div>
))}
```

## 5. Testing Checklist

### Test SHAP/LIME
- [ ] Upload X-ray image
- [ ] Wait for analysis completion
- [ ] Open ExplainabilityViewer
- [ ] Check Grad-CAM, SHAP, LIME tabs
- [ ] Verify visualizations load
- [ ] Test on-demand generation

### Test Compliance
- [ ] Navigate to /compliance
- [ ] Export patient data (check JSON download)
- [ ] View audit logs
- [ ] Test anomaly detection
- [ ] Verify encryption (check database)

### Test Real-time
- [ ] Open dashboard in 2+ tabs
- [ ] Upload new document in one tab
- [ ] Verify update in other tabs
- [ ] Check WebSocket connection in DevTools

### Test Lab Reports
- [ ] Upload lab report image
- [ ] Verify insights appear
- [ ] Check recommendations
- [ ] Verify critical flags show

## 6. Common Issues & Solutions

### SHAP/LIME Not Showing
```bash
# Check dependencies
pip install shap lime scikit-image matplotlib

# Check model compatibility
# Ensure CNN model outputs correct prediction format
```

### WebSocket Connection Failed
```bash
# Install flask-socketio
pip install flask-socketio

# Check CORS settings
# Verify client URL matches server URL
```

### Encryption Key Missing
```bash
# First run generates encryption.key automatically
# If missing, delete and restart server
rm encryption.key
python app.py
```

### Audit Logs Empty
```bash
# Ensure Firebase is initialized
# Check db connection
# Verify compliance_manager is initialized with db
```

## 7. Configuration

### Environment Variables
```bash
# .env file
FIREBASE_CONFIG=<firebase-credentials-json>
PORT=5000
ENCRYPTION_KEY_PATH=./encryption.key  # Optional
```

### Customization
```python
# Update intervals
realtime_manager.update_interval = 10  # seconds

# SHAP samples (speed vs accuracy)
shap_explainer.explain(image, model, pred, num_samples=50)  # faster
shap_explainer.explain(image, model, pred, num_samples=200) # more accurate

# Anomaly threshold
compliance_manager.detect_anomaly(user_id, action_count_threshold=100)
```

## 8. Production Deployment

### Run with SocketIO
```bash
# Use eventlet worker
gunicorn --worker-class eventlet -w 1 app:app --bind 0.0.0.0:5000
```

### Nginx Config
```nginx
location /socket.io/ {
    proxy_pass http://localhost:5000/socket.io/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "Upgrade";
}
```

### Security
```bash
# Secure encryption key
chmod 600 encryption.key
chown www-data:www-data encryption.key

# Add to .gitignore
echo "encryption.key" >> .gitignore
```

## 9. API Quick Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/explainability/generate` | POST | Generate SHAP/LIME |
| `/api/compliance/audit-logs` | GET | Get audit logs |
| `/api/compliance/export-patient-data` | POST | GDPR export |
| `/api/compliance/delete-patient-data` | POST | GDPR deletion |
| `/api/compliance/anonymize-patient` | POST | Anonymize data |
| `/api/compliance/detect-anomaly` | POST | Check anomalies |
| `/api/realtime/stats` | GET | Real-time stats |

## 10. Resources

- [SHAP Documentation](https://shap.readthedocs.io/)
- [LIME Tutorial](https://github.com/marcotcr/lime)
- [Flask-SocketIO Docs](https://flask-socketio.readthedocs.io/)
- [HIPAA Compliance Guide](https://www.hhs.gov/hipaa/)
- [GDPR Official Site](https://gdpr.eu/)

---

**Status:** ✅ All Features Ready  
**Last Updated:** November 2, 2025

