"""
HIPAA/GDPR Compliance Module
Provides encryption, audit logging, data anonymization, and access control
"""

from cryptography.fernet import Fernet
import base64
import hashlib
import json
import os
from datetime import datetime
from functools import wraps
from flask import request, jsonify

class ComplianceManager:
    """Manages HIPAA/GDPR compliance features"""
    
    def __init__(self, db=None):
        self.db = db
        self.encryption_key = self._get_or_create_key()
        self.cipher = Fernet(self.encryption_key)
    
    def _get_or_create_key(self):
        """Get or create encryption key"""
        key_file = 'encryption.key'
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    # ===== ENCRYPTION =====
    
    def encrypt_data(self, data):
        """Encrypt sensitive data (PHI/PII)"""
        try:
            if isinstance(data, dict):
                data = json.dumps(data)
            elif not isinstance(data, (str, bytes)):
                data = str(data)
            
            if isinstance(data, str):
                data = data.encode()
            
            encrypted = self.cipher.encrypt(data)
            return base64.b64encode(encrypted).decode()
            
        except Exception as e:
            print(f"Encryption error: {e}")
            return None
    
    def decrypt_data(self, encrypted_data):
        """Decrypt sensitive data"""
        try:
            if isinstance(encrypted_data, str):
                encrypted_data = base64.b64decode(encrypted_data)
            
            decrypted = self.cipher.decrypt(encrypted_data)
            return decrypted.decode()
            
        except Exception as e:
            print(f"Decryption error: {e}")
            return None
    
    def encrypt_phi(self, patient_data):
        """
        Encrypt Protected Health Information (PHI)
        Encrypts: name, contact, email, address, medical_history
        """
        try:
            encrypted_data = patient_data.copy()
            
            phi_fields = ['name', 'contact', 'email', 'address', 'medical_history']
            
            for field in phi_fields:
                if field in encrypted_data and encrypted_data[field]:
                    encrypted_data[field] = self.encrypt_data(encrypted_data[field])
                    encrypted_data[f'{field}_encrypted'] = True
            
            return encrypted_data
            
        except Exception as e:
            print(f"PHI encryption error: {e}")
            return patient_data
    
    def decrypt_phi(self, encrypted_patient_data):
        """Decrypt Protected Health Information"""
        try:
            decrypted_data = encrypted_patient_data.copy()
            
            phi_fields = ['name', 'contact', 'email', 'address', 'medical_history']
            
            for field in phi_fields:
                if f'{field}_encrypted' in decrypted_data and decrypted_data.get(f'{field}_encrypted'):
                    decrypted_data[field] = self.decrypt_data(decrypted_data[field])
                    del decrypted_data[f'{field}_encrypted']
            
            return decrypted_data
            
        except Exception as e:
            print(f"PHI decryption error: {e}")
            return encrypted_patient_data
    
    # ===== ANONYMIZATION =====
    
    def anonymize_patient(self, patient_data):
        """Anonymize patient data for analytics/research"""
        try:
            anonymized = {
                'patient_id_hash': self._hash_id(patient_data.get('id', '')),
                'age': patient_data.get('age'),
                'gender': patient_data.get('gender'),
                'created_at': patient_data.get('created_at'),
                'anonymized': True,
                'anonymized_at': datetime.now().isoformat()
            }
            
            # Remove all PHI
            return anonymized
            
        except Exception as e:
            print(f"Anonymization error: {e}")
            return None
    
    def _hash_id(self, patient_id):
        """Hash patient ID for anonymized tracking"""
        if not patient_id:
            return None
        return hashlib.sha256(str(patient_id).encode()).hexdigest()[:16]
    
    # ===== AUDIT LOGGING =====
    
    def log_access(self, action, user_id, patient_id=None, resource_type=None, 
                    resource_id=None, details=None, ip_address=None):
        """
        Log all access to PHI for HIPAA compliance
        
        Args:
            action: 'view', 'create', 'update', 'delete', 'export'
            user_id: ID of user performing action
            patient_id: ID of patient whose data was accessed
            resource_type: 'patient', 'analysis', 'prescription', etc.
            resource_id: ID of specific resource
            details: Additional details
            ip_address: IP address of request
        """
        try:
            if not self.db:
                print("⚠️ Database not available for audit logging")
                return None
            
            audit_log = {
                'timestamp': datetime.now().isoformat(),
                'action': action,
                'user_id': user_id,
                'patient_id': patient_id,
                'resource_type': resource_type,
                'resource_id': resource_id,
                'details': details,
                'ip_address': ip_address,
                'compliant': True
            }
            
            # Save to audit_logs collection
            doc_ref = self.db.collection('audit_logs').add(audit_log)
            audit_log['id'] = doc_ref[1].id
            
            return audit_log
            
        except Exception as e:
            print(f"Audit logging error: {e}")
            return None
    
    def get_audit_logs(self, user_id=None, patient_id=None, limit=100):
        """Retrieve audit logs"""
        try:
            if not self.db:
                return []
            
            query = self.db.collection('audit_logs')
            
            if user_id:
                query = query.where('user_id', '==', user_id)
            if patient_id:
                query = query.where('patient_id', '==', patient_id)
            
            query = query.order_by('timestamp', direction='DESCENDING').limit(limit)
            
            logs = []
            for doc in query.stream():
                log_data = doc.to_dict()
                log_data['id'] = doc.id
                logs.append(log_data)
            
            return logs
            
        except Exception as e:
            print(f"Audit log retrieval error: {e}")
            return []
    
    # ===== DATA RETENTION =====
    
    def check_retention_policy(self, data_timestamp, retention_days=2555):
        """
        Check if data exceeds retention policy (default: 7 years for HIPAA)
        
        Args:
            data_timestamp: ISO format timestamp string
            retention_days: Number of days to retain (default 2555 = ~7 years)
            
        Returns:
            bool: True if data should be retained, False if should be deleted
        """
        try:
            from datetime import datetime, timedelta
            
            if not data_timestamp:
                return True
            
            data_date = datetime.fromisoformat(data_timestamp.replace('Z', '+00:00'))
            retention_date = datetime.now() - timedelta(days=retention_days)
            
            return data_date > retention_date
            
        except Exception as e:
            print(f"Retention check error: {e}")
            return True  # Default to retain if error
    
    # ===== ACCESS CONTROL =====
    
    def require_auth(self, f):
        """Decorator to require authentication for endpoints"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get user_id from request
            user_id = request.headers.get('X-User-ID') or request.json.get('user_id') if request.json else None
            
            if not user_id:
                return jsonify({'error': 'Authentication required', 'compliant': False}), 401
            
            # Log the access
            self.log_access(
                action='api_access',
                user_id=user_id,
                resource_type=request.endpoint,
                ip_address=request.remote_addr,
                details=f"Accessed {request.method} {request.path}"
            )
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    def check_user_permission(self, user_id, action, resource_type):
        """
        Check if user has permission for action
        
        Args:
            user_id: User ID
            action: 'view', 'create', 'update', 'delete', 'export'
            resource_type: 'patient', 'analysis', etc.
            
        Returns:
            bool: True if permitted, False otherwise
        """
        # TODO: Implement role-based access control (RBAC)
        # For now, allow all authenticated users
        return user_id is not None
    
    # ===== DATA BREACH DETECTION =====
    
    def detect_anomaly(self, user_id, action_count_threshold=50):
        """
        Detect potential data breach or unusual access patterns
        
        Args:
            user_id: User ID to check
            action_count_threshold: Max actions per hour
            
        Returns:
            dict: Anomaly report
        """
        try:
            if not self.db:
                return {'anomaly_detected': False}
            
            from datetime import datetime, timedelta
            
            # Get logs from last hour
            one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
            
            logs = self.db.collection('audit_logs')\
                .where('user_id', '==', user_id)\
                .where('timestamp', '>=', one_hour_ago)\
                .stream()
            
            log_count = len(list(logs))
            
            anomaly_detected = log_count > action_count_threshold
            
            if anomaly_detected:
                # Log the security event
                self.log_access(
                    action='security_alert',
                    user_id=user_id,
                    details=f"Anomalous activity detected: {log_count} actions in 1 hour",
                    resource_type='security'
                )
            
            return {
                'anomaly_detected': anomaly_detected,
                'action_count': log_count,
                'threshold': action_count_threshold,
                'time_window': '1 hour'
            }
            
        except Exception as e:
            print(f"Anomaly detection error: {e}")
            return {'anomaly_detected': False, 'error': str(e)}
    
    # ===== GDPR RIGHTS =====
    
    def export_user_data(self, patient_id):
        """Export all data for a patient (GDPR Right to Data Portability)"""
        try:
            if not self.db:
                return None
            
            # Get patient data
            patient_doc = self.db.collection('patients').document(str(patient_id)).get()
            if not patient_doc.exists:
                return None
            
            patient_data = patient_doc.to_dict()
            patient_data['id'] = patient_doc.id
            
            # Decrypt PHI
            patient_data = self.decrypt_phi(patient_data)
            
            # Get all analyses
            analyses = []
            analyses_ref = self.db.collection('analyses').where('patient_id', '==', str(patient_id)).stream()
            for doc in analyses_ref:
                analysis = doc.to_dict()
                analysis['id'] = doc.id
                analyses.append(analysis)
            
            export_data = {
                'patient': patient_data,
                'analyses': analyses,
                'export_date': datetime.now().isoformat(),
                'format': 'JSON',
                'gdpr_compliant': True
            }
            
            # Log the export
            self.log_access(
                action='export',
                user_id='patient_request',
                patient_id=patient_id,
                resource_type='full_data_export',
                details='GDPR data portability request'
            )
            
            return export_data
            
        except Exception as e:
            print(f"Data export error: {e}")
            return None
    
    def delete_user_data(self, patient_id, user_id):
        """Delete all data for a patient (GDPR Right to Erasure)"""
        try:
            if not self.db:
                return False
            
            # Log before deletion (for legal compliance)
            self.log_access(
                action='delete',
                user_id=user_id,
                patient_id=patient_id,
                resource_type='full_data_deletion',
                details='GDPR right to erasure request'
            )
            
            # Delete all analyses
            analyses_ref = self.db.collection('analyses').where('patient_id', '==', str(patient_id)).stream()
            for doc in analyses_ref:
                doc.reference.delete()
            
            # Delete patient subcollection analyses
            subcoll_ref = self.db.collection('patients').document(str(patient_id)).collection('analyses').stream()
            for doc in subcoll_ref:
                doc.reference.delete()
            
            # Delete patient record
            self.db.collection('patients').document(str(patient_id)).delete()
            
            return True
            
        except Exception as e:
            print(f"Data deletion error: {e}")
            return False


# Global instance (will be initialized with db in app.py)
compliance_manager = None

