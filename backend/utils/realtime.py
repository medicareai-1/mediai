"""
Real-time Dashboard Module
Provides WebSocket support for live updates and real-time analytics
"""

from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime
import threading
import time

class RealtimeManager:
    """Manages real-time updates via WebSocket"""
    
    def __init__(self, app=None, db=None):
        self.db = db
        self.socketio = None
        self.active_users = {}
        self.stats_cache = {}
        self.update_interval = 5  # seconds
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize SocketIO with Flask app"""
        self.socketio = SocketIO(
            app, 
            cors_allowed_origins="*",
            async_mode='threading',
            logger=False,
            engineio_logger=False
        )
        
        # Register event handlers
        self._register_handlers()
        
        # Start background stats updater
        self._start_background_updater()
    
    def _register_handlers(self):
        """Register WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            print(f"Client connected: {request.sid}")
            emit('connection_status', {'status': 'connected', 'timestamp': datetime.now().isoformat()})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print(f"Client disconnected: {request.sid}")
            # Remove from active users
            from flask import request
            if request.sid in self.active_users:
                del self.active_users[request.sid]
        
        @self.socketio.on('join_dashboard')
        def handle_join_dashboard(data):
            """Client joins dashboard room for real-time updates"""
            from flask import request
            user_id = data.get('user_id')
            self.active_users[request.sid] = user_id
            join_room('dashboard')
            print(f"User {user_id} joined dashboard room")
            
            # Send initial stats
            stats = self._get_dashboard_stats()
            emit('dashboard_update', stats)
        
        @self.socketio.on('leave_dashboard')
        def handle_leave_dashboard():
            """Client leaves dashboard room"""
            from flask import request
            leave_room('dashboard')
            if request.sid in self.active_users:
                del self.active_users[request.sid]
        
        @self.socketio.on('request_stats')
        def handle_stats_request():
            """Client requests current statistics"""
            stats = self._get_dashboard_stats()
            emit('dashboard_update', stats)
    
    def _start_background_updater(self):
        """Start background thread for periodic updates"""
        def update_loop():
            while True:
                time.sleep(self.update_interval)
                if self.active_users:
                    stats = self._get_dashboard_stats()
                    self.socketio.emit('dashboard_update', stats, room='dashboard')
        
        thread = threading.Thread(target=update_loop, daemon=True)
        thread.start()
    
    def _get_dashboard_stats(self):
        """Get current dashboard statistics"""
        try:
            if not self.db:
                return self._get_mock_stats()
            
            # Check cache (60 second TTL)
            cache_key = 'dashboard_stats'
            if cache_key in self.stats_cache:
                cached_time, cached_data = self.stats_cache[cache_key]
                if (time.time() - cached_time) < 60:
                    return cached_data
            
            # Fetch fresh data
            stats = {
                'timestamp': datetime.now().isoformat(),
                'total_patients': self._count_collection('patients'),
                'total_analyses': self._count_collection('analyses'),
                'analyses_today': self._count_today('analyses'),
                'active_users': len(self.active_users),
                'recent_activities': self._get_recent_activities(),
                'medicine_trends': self._get_medicine_trends(),
                'diagnosis_distribution': self._get_diagnosis_distribution()
            }
            
            # Update cache
            self.stats_cache[cache_key] = (time.time(), stats)
            
            return stats
            
        except Exception as e:
            print(f"Stats retrieval error: {e}")
            return self._get_mock_stats()
    
    def _count_collection(self, collection_name):
        """Count documents in a collection"""
        try:
            # Note: Firestore doesn't have efficient count, using query limit
            docs = list(self.db.collection(collection_name).limit(10000).stream())
            return len(docs)
        except Exception:
            return 0
    
    def _count_today(self, collection_name):
        """Count documents created today"""
        try:
            from datetime import datetime, timedelta
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            docs = self.db.collection(collection_name)\
                .where('timestamp', '>=', today_start.isoformat())\
                .stream()
            
            return len(list(docs))
        except Exception:
            return 0
    
    def _get_recent_activities(self, limit=10):
        """Get recent analysis activities"""
        try:
            activities = []
            docs = self.db.collection('analyses')\
                .order_by('timestamp', direction='DESCENDING')\
                .limit(limit)\
                .stream()
            
            for doc in docs:
                data = doc.to_dict()
                activities.append({
                    'id': doc.id,
                    'patient_id': data.get('patient_id'),
                    'type': data.get('document_type'),
                    'timestamp': data.get('timestamp'),
                    'status': data.get('status', 'completed')
                })
            
            return activities
        except Exception:
            return []
    
    def _get_medicine_trends(self, limit=10):
        """Get top prescribed medicines"""
        try:
            medicine_counts = {}
            
            # Get recent prescriptions
            docs = self.db.collection('analyses')\
                .where('document_type', '==', 'prescription')\
                .limit(500)\
                .stream()
            
            for doc in docs:
                data = doc.to_dict()
                medicines = data.get('medicines', [])
                
                for med in medicines:
                    med_name = med.get('text', '') if isinstance(med, dict) else str(med)
                    if med_name:
                        medicine_counts[med_name] = medicine_counts.get(med_name, 0) + 1
            
            # Sort and return top medicines
            sorted_meds = sorted(medicine_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
            
            return [{'name': name, 'count': count} for name, count in sorted_meds]
            
        except Exception:
            return []
    
    def _get_diagnosis_distribution(self):
        """Get distribution of diagnoses from X-ray analyses"""
        try:
            diagnosis_counts = {}
            
            docs = self.db.collection('analyses')\
                .where('document_type', '==', 'xray')\
                .limit(500)\
                .stream()
            
            for doc in docs:
                data = doc.to_dict()
                diagnosis = data.get('cnn_class', 'Unknown')
                diagnosis_counts[diagnosis] = diagnosis_counts.get(diagnosis, 0) + 1
            
            # Convert to list format
            distribution = [
                {'label': label, 'count': count}
                for label, count in diagnosis_counts.items()
            ]
            
            return sorted(distribution, key=lambda x: x['count'], reverse=True)
            
        except Exception:
            return []
    
    def _get_mock_stats(self):
        """Return mock stats when DB unavailable"""
        return {
            'timestamp': datetime.now().isoformat(),
            'total_patients': 0,
            'total_analyses': 0,
            'analyses_today': 0,
            'active_users': len(self.active_users),
            'recent_activities': [],
            'medicine_trends': [],
            'diagnosis_distribution': [],
            'mock_data': True
        }
    
    # ===== NOTIFICATION METHODS =====
    
    def notify_analysis_complete(self, analysis_data):
        """Notify dashboard when new analysis completes"""
        try:
            notification = {
                'type': 'analysis_complete',
                'timestamp': datetime.now().isoformat(),
                'patient_id': analysis_data.get('patient_id'),
                'document_type': analysis_data.get('document_type'),
                'analysis_id': analysis_data.get('document_id'),
                'status': 'success'
            }
            
            self.socketio.emit('notification', notification, room='dashboard')
            
        except Exception as e:
            print(f"Notification error: {e}")
    
    def notify_new_patient(self, patient_data):
        """Notify dashboard when new patient is added"""
        try:
            notification = {
                'type': 'new_patient',
                'timestamp': datetime.now().isoformat(),
                'patient_id': patient_data.get('id'),
                'patient_name': patient_data.get('name'),
                'status': 'success'
            }
            
            self.socketio.emit('notification', notification, room='dashboard')
            
        except Exception as e:
            print(f"Notification error: {e}")
    
    def notify_alert(self, alert_type, message, severity='info'):
        """Send alert to dashboard"""
        try:
            alert = {
                'type': 'alert',
                'alert_type': alert_type,
                'message': message,
                'severity': severity,
                'timestamp': datetime.now().isoformat()
            }
            
            self.socketio.emit('alert', alert, room='dashboard')
            
        except Exception as e:
            print(f"Alert error: {e}")


# Global instance (will be initialized in app.py)
realtime_manager = None

