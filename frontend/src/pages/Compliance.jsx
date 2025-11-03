import React, { useState, useEffect } from 'react';
import { Shield, Download, Trash2, Eye, AlertTriangle, Clock, User, Activity } from 'lucide-react';

const Compliance = () => {
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedPatient, setSelectedPatient] = useState('');
  const [anomalyReport, setAnomalyReport] = useState(null);

  useEffect(() => {
    fetchAuditLogs();
  }, [selectedPatient]);

  const fetchAuditLogs = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (selectedPatient) params.append('patient_id', selectedPatient);
      params.append('limit', '100');

      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'https://mediai-t6oo.onrender.com'}/api/compliance/audit-logs?${params}`
      );
      const data = await response.json();
      setAuditLogs(data.audit_logs || []);
    } catch (error) {
      console.error('Failed to fetch audit logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const exportPatientData = async (patientId) => {
    if (!patientId) {
      alert('Please enter a patient ID');
      return;
    }

    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'https://mediai-t6oo.onrender.com'}/api/compliance/export-patient-data`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            patient_id: patientId,
            user_id: 'user_001' // TODO: Get from auth
          }),
        }
      );

      if (!response.ok) {
        throw new Error('Export failed');
      }

      const data = await response.json();
      
      // Download as JSON file
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `patient_${patientId}_export_${new Date().toISOString()}.json`;
      a.click();
      URL.revokeObjectURL(url);

      alert('✅ Patient data exported successfully (GDPR compliant)');
    } catch (error) {
      alert('❌ Export failed: ' + error.message);
    }
  };

  const deletePatientData = async (patientId) => {
    if (!patientId) {
      alert('Please enter a patient ID');
      return;
    }

    const confirmed = confirm(
      `⚠️ GDPR Right to Erasure\n\nThis will permanently delete ALL data for patient ${patientId}.\n\nThis action cannot be undone. Continue?`
    );

    if (!confirmed) return;

    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'https://mediai-t6oo.onrender.com'}/api/compliance/delete-patient-data`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            patient_id: patientId,
            user_id: 'user_001' // TODO: Get from auth
          }),
        }
      );

      if (!response.ok) {
        throw new Error('Deletion failed');
      }

      alert('✅ Patient data deleted successfully (GDPR Right to Erasure executed)');
      fetchAuditLogs();
    } catch (error) {
      alert('❌ Deletion failed: ' + error.message);
    }
  };

  const checkAnomaly = async (userId) => {
    if (!userId) {
      alert('Please enter a user ID');
      return;
    }

    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'https://mediai-t6oo.onrender.com'}/api/compliance/detect-anomaly`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: userId }),
        }
      );

      const data = await response.json();
      setAnomalyReport(data);
    } catch (error) {
      alert('❌ Anomaly check failed: ' + error.message);
    }
  };

  const getActionIcon = (action) => {
    const icons = {
      view: <Eye className="w-4 h-4" />,
      create: <Activity className="w-4 h-4" />,
      update: <Activity className="w-4 h-4" />,
      delete: <Trash2 className="w-4 h-4" />,
      export: <Download className="w-4 h-4" />,
      gdpr_export: <Download className="w-4 h-4" />,
    };
    return icons[action] || <Activity className="w-4 h-4" />;
  };

  const getActionColor = (action) => {
    const colors = {
      view: 'text-blue-600',
      create: 'text-green-600',
      update: 'text-yellow-600',
      delete: 'text-red-600',
      export: 'text-purple-600',
      gdpr_export: 'text-purple-600',
    };
    return colors[action] || 'text-gray-600';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white rounded-lg shadow-lg p-8">
        <div className="flex items-center gap-3 mb-2">
          <Shield className="w-8 h-8" />
          <h1 className="text-3xl font-bold">HIPAA/GDPR Compliance Dashboard</h1>
        </div>
        <p className="text-blue-100">
          Audit logs, data protection, and regulatory compliance management
        </p>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Export Patient Data (GDPR) */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center gap-3 mb-4">
            <Download className="w-6 h-6 text-blue-600" />
            <h3 className="text-lg font-semibold text-gray-900">Export Patient Data</h3>
          </div>
          <p className="text-sm text-gray-600 mb-4">GDPR Right to Data Portability</p>
          <input
            type="text"
            placeholder="Patient ID"
            id="export-patient-id"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg mb-3"
          />
          <button
            onClick={() => exportPatientData(document.getElementById('export-patient-id').value)}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center justify-center gap-2"
          >
            <Download className="w-4 h-4" />
            Export Data (JSON)
          </button>
        </div>

        {/* Delete Patient Data (GDPR) */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center gap-3 mb-4">
            <Trash2 className="w-6 h-6 text-red-600" />
            <h3 className="text-lg font-semibold text-gray-900">Delete Patient Data</h3>
          </div>
          <p className="text-sm text-gray-600 mb-4">GDPR Right to Erasure</p>
          <input
            type="text"
            placeholder="Patient ID"
            id="delete-patient-id"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg mb-3"
          />
          <button
            onClick={() => deletePatientData(document.getElementById('delete-patient-id').value)}
            className="w-full px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center justify-center gap-2"
          >
            <Trash2 className="w-4 h-4" />
            Delete All Data
          </button>
        </div>

        {/* Anomaly Detection */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center gap-3 mb-4">
            <AlertTriangle className="w-6 h-6 text-orange-600" />
            <h3 className="text-lg font-semibold text-gray-900">Anomaly Detection</h3>
          </div>
          <p className="text-sm text-gray-600 mb-4">Data breach monitoring</p>
          <input
            type="text"
            placeholder="User ID"
            id="anomaly-user-id"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg mb-3"
          />
          <button
            onClick={() => checkAnomaly(document.getElementById('anomaly-user-id').value)}
            className="w-full px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 flex items-center justify-center gap-2"
          >
            <AlertTriangle className="w-4 h-4" />
            Check Activity
          </button>
        </div>
      </div>

      {/* Anomaly Report */}
      {anomalyReport && (
          <div
            className={`rounded-lg shadow-md p-6 ${
              anomalyReport.anomaly_detected
                ? 'bg-red-50 border-2 border-red-300'
                : 'bg-green-50 border-2 border-green-300'
            }`}
          >
            <div className="flex items-center gap-3 mb-3">
              <AlertTriangle
                className={`w-6 h-6 ${
                  anomalyReport.anomaly_detected ? 'text-red-600' : 'text-green-600'
                }`}
              />
              <h3 className="text-lg font-semibold">
                {anomalyReport.anomaly_detected ? '⚠️ ANOMALY DETECTED' : '✅ No Anomalies'}
              </h3>
            </div>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <div className="text-gray-600">Actions (1 hour)</div>
                <div className="text-2xl font-bold">{anomalyReport.action_count}</div>
              </div>
              <div>
                <div className="text-gray-600">Threshold</div>
                <div className="text-2xl font-bold">{anomalyReport.threshold}</div>
              </div>
              <div>
                <div className="text-gray-600">Status</div>
                <div className="text-2xl font-bold">
                  {anomalyReport.anomaly_detected ? '🚨 Alert' : '✅ Normal'}
                </div>
              </div>
            </div>
          </div>
      )}

      {/* Audit Logs */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <Clock className="w-6 h-6 text-blue-600" />
            <h2 className="text-xl font-bold text-gray-900">Audit Logs</h2>
          </div>
          <div className="flex items-center gap-3">
            <input
              type="text"
              placeholder="Filter by Patient ID"
              value={selectedPatient}
              onChange={(e) => setSelectedPatient(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg"
            />
            <button
              onClick={fetchAuditLogs}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Refresh
            </button>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-gray-600 mt-2">Loading audit logs...</p>
          </div>
        ) : auditLogs.length === 0 ? (
          <div className="text-center py-8 text-gray-600">No audit logs found</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase">
                    Timestamp
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase">
                    Action
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase">
                    User ID
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase">
                    Patient ID
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase">
                    Resource
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase">
                    IP Address
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {auditLogs.map((log, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="px-4 py-3">
                      <div className={`flex items-center gap-2 ${getActionColor(log.action)}`}>
                        {getActionIcon(log.action)}
                        <span className="text-sm font-medium">{log.action}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">{log.user_id}</td>
                    <td className="px-4 py-3 text-sm text-gray-900">{log.patient_id || '-'}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{log.resource_type || '-'}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{log.ip_address || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Compliance Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="font-semibold text-blue-900 mb-3">✅ Compliance Features Active</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-blue-600" />
            <span>AES-256 PHI Encryption</span>
          </div>
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-blue-600" />
            <span>Complete Audit Trail (HIPAA)</span>
          </div>
          <div className="flex items-center gap-2">
            <Download className="w-4 h-4 text-blue-600" />
            <span>GDPR Data Portability</span>
          </div>
          <div className="flex items-center gap-2">
            <Trash2 className="w-4 h-4 text-blue-600" />
            <span>GDPR Right to Erasure</span>
          </div>
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-blue-600" />
            <span>Anomaly Detection</span>
          </div>
          <div className="flex items-center gap-2">
            <User className="w-4 h-4 text-blue-600" />
            <span>Data Anonymization</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Compliance;

