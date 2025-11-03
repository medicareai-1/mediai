import axios from 'axios';

// Backend API URL - Production: Render, Development: localhost
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://mediai-t6oo.onrender.com';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API endpoints
export const apiService = {
  // Health check
  healthCheck: async () => {
    const response = await api.get('/api/health');
    return response.data;
  },

  // Process document
  processDocument: async (data) => {
    const response = await api.post('/api/process', data);
    return response.data;
  },

  // Process PDF with auto-page routing
  processPdfAuto: async (data) => {
    const response = await api.post('/api/process-pdf-auto', data);
    return response.data;
  },

  // Process multiple documents in one request
  processBatch: async (data) => {
    // data: { file_urls: string[], patient_id: string, user_id: string, document_type: string }
    const response = await api.post('/api/process-batch', data);
    return response.data;
  },

  // Delete an analysis by id (also cleans up patient subcollection)
  deleteAnalysis: async (analysisId) => {
    const response = await api.delete(`/api/analyses/${analysisId}`);
    return response.data;
  },

  // Process prescription
  processPrescription: async (fileUrl, patientId, userId) => {
    const response = await api.post('/api/process-prescription', {
      file_url: fileUrl,
      patient_id: patientId,
      user_id: userId
    });
    return response.data;
  },

  // Analyze image
  analyzeImage: async (fileUrl, patientId) => {
    const response = await api.post('/api/analyze-image', {
      file_url: fileUrl,
      patient_id: patientId
    });
    return response.data;
  },

  // Patient management
  getPatients: async () => {
    const response = await api.get('/api/patients');
    return response.data;
  },

  createPatient: async (patientData) => {
    const response = await api.post('/api/patients', patientData);
    return response.data;
  },

  // Analytics
  getAnalytics: async () => {
    const response = await api.get('/api/analytics');
    return response.data;
  },

  // FHIR Export
  exportFHIR: async (analysisId) => {
    const response = await api.post('/api/export-fhir', {
      analysis_id: analysisId
    });
    return response.data;
  },
};

export default api;

