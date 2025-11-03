import { useState, useEffect, useRef } from 'react';
import { apiService } from '../services/api';
import { collection, query, orderBy, limit, onSnapshot, doc, getDoc } from 'firebase/firestore';
import { db } from '../services/firebase';
import { useAuth } from '../contexts/AuthContext';
import { 
  FileText, 
  Users, 
  Activity, 
  TrendingUp,
  Clock,
  CheckCircle,
  AlertCircle,
  ChevronDown,
  X,
  Image as ImageIcon,
  Trash2,
  Download
} from 'lucide-react';

function Dashboard() {
  const { currentUser } = useAuth();
  const [recentAnalyses, setRecentAnalyses] = useState([]);
  const [stats, setStats] = useState({
    totalAnalyses: 0,
    totalPatients: 0,
    todayAnalyses: 0
  });
  const [loading, setLoading] = useState(true);
  const [patients, setPatients] = useState([]);
  const [patientAnalyses, setPatientAnalyses] = useState({}); // id -> []
  const [expanded, setExpanded] = useState({});
  const [selectedAnalysis, setSelectedAnalysis] = useState(null);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  const analysisUnsubsRef = useRef({});
  const [pdfPageIndex, setPdfPageIndex] = useState(0);
  const [exportingFHIR, setExportingFHIR] = useState(false);

  // Reset pdf pagination when a new analysis opens
  useEffect(() => {
    setPdfPageIndex(0);
  }, [selectedAnalysis?.id]);

  useEffect(() => {
    // Real-time listener for recent analyses
    const analysesQuery = query(
      collection(db, 'analyses'),
      orderBy('timestamp', 'desc'),
      limit(10)
    );

    const unsubscribe = onSnapshot(analysesQuery, (snapshot) => {
      const analyses = [];
      snapshot.forEach((doc) => {
        analyses.push({ id: doc.id, ...doc.data() });
      });
      setRecentAnalyses(analyses);
      setLoading(false);
    }, (error) => {
      console.error('Error fetching analyses:', error);
      setLoading(false);
    });

    // Fetch real analytics stats
    fetchStats();

    // Patients real-time
    const unsubPatients = onSnapshot(collection(db, 'patients'), (snap) => {
      const list = [];
      snap.forEach((d) => list.push({ id: d.id, ...d.data() }));
      setPatients(list);
      // For each patient, subscribe to their analyses subcollection if not already
      list.forEach((p) => {
        if (!analysisUnsubsRef.current[p.id]) {
          const q = query(
            collection(db, 'patients', p.id, 'analyses'),
            orderBy('timestamp', 'desc'),
            limit(50)
          );
          analysisUnsubsRef.current[p.id] = onSnapshot(q, async (asnap) => {
            // Read subcollection docs then filter out any that don't exist
            // in the flat 'analyses' collection (covers manual deletions).
            const raw = [];
            asnap.forEach((d) => raw.push({ id: d.id, ...d.data() }));
            try {
              const filtered = [];
              await Promise.all(raw.map(async (item) => {
                try {
                  const flat = await getDoc(doc(db, 'analyses', item.id));
                  if (flat.exists()) {
                    filtered.push(item);
                  }
                } catch (_) {}
              }));
              setPatientAnalyses((prev) => ({ ...prev, [p.id]: filtered }));
            } catch (_) {
              setPatientAnalyses((prev) => ({ ...prev, [p.id]: raw }));
            }
          });
        }
      });
    });

    return () => {
      unsubscribe();
      unsubPatients();
      // Cleanup per-patient listeners
      Object.values(analysisUnsubsRef.current).forEach((fn) => {
        try { fn(); } catch (_) {}
      });
      analysisUnsubsRef.current = {};
    };
  }, []);

  const fetchStats = async () => {
    try {
      const [analytics, patientsRes] = await Promise.all([
        apiService.getAnalytics(),
        apiService.getPatients().catch(() => ({ patients: [] }))
      ]);
      const totalAnalyses = analytics?.total_analyses || 0;
      const recent = Array.isArray(analytics?.recent_analyses) ? analytics.recent_analyses : [];
      const totalPatients = Array.isArray(patientsRes?.patients) ? patientsRes.patients.length : 0;
      const today = recent.filter(r => {
        const t = r.timestamp ? new Date(r.timestamp) : null;
        if (!t) return false;
        const now = new Date();
        return t.toDateString() === now.toDateString();
      }).length;
      setStats({
        totalAnalyses,
        totalPatients,
        todayAnalyses: today,
        accuracy: 0
      });
    } catch (e) {
      console.error('Failed to load analytics', e);
    }
  };

  const handleExportFHIR = async (analysisId) => {
    try {
      setExportingFHIR(true);
      const result = await apiService.exportFHIR(analysisId);
      
      // Download the FHIR bundle as JSON file
      const blob = new Blob([JSON.stringify(result.fhir_bundle, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `fhir-export-${analysisId}-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      
      alert('✅ FHIR export downloaded successfully!');
    } catch (error) {
      console.error('FHIR export failed:', error);
      alert('❌ Failed to export FHIR data. Please try again.');
    } finally {
      setExportingFHIR(false);
    }
  };

  const StatCard = ({ icon: Icon, title, value, change, color }) => (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">{value}</p>
          {change && (
            <p className={`text-sm mt-2 flex items-center ${change > 0 ? 'text-green-600' : 'text-red-600'}`}>
              <TrendingUp className="w-4 h-4 mr-1" />
              {change > 0 ? '+' : ''}{change}% from last month
            </p>
          )}
        </div>
        <div className={`p-3 rounded-full ${color}`}>
          <Icon className="w-8 h-8 text-white" />
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3 mb-2">
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <div className="flex items-center gap-1 bg-green-100 px-2 py-1 rounded-full">
            <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-xs font-semibold text-green-700">Live</span>
          </div>
        </div>
        <p className="text-gray-600">Welcome back, {currentUser?.email}</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          icon={FileText}
          title="Total Analyses"
          value={stats.totalAnalyses.toLocaleString()}
          change={12.5}
          color="bg-blue-500"
        />
        <StatCard
          icon={Users}
          title="Total Patients"
          value={stats.totalPatients.toLocaleString()}
          change={8.2}
          color="bg-green-500"
        />
        <StatCard
          icon={Activity}
          title="Today's Analyses"
          value={stats.todayAnalyses}
          color="bg-purple-500"
        />
        <StatCard
          icon={CheckCircle}
          title="Model Accuracy"
          value={`${stats.accuracy}%`}
          change={1.2}
          color="bg-indigo-500"
        />
      </div>

      {/* Patients with Analyses */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Patients</h2>
          <p className="text-sm text-gray-600 mt-1">Click a patient to view their analyses</p>
        </div>

        {patients.length === 0 ? (
          <div className="p-8 text-center">
            <AlertCircle className="w-12 h-12 text-gray-400 mx-auto" />
            <p className="mt-4 text-gray-600">No patients yet. Create a patient first.</p>
          </div>
        ) : (
          <div className="divide-y">
            {patients.map((p) => {
              const analyses = patientAnalyses[p.id] || [];
              const createdAt = p.created_at ? new Date(p.created_at) : null;
              const open = !!expanded[p.id];
              return (
                <div key={p.id}>
                  <button
                    className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50"
                    onClick={() => setExpanded((prev) => ({ ...prev, [p.id]: !prev[p.id] }))}
                  >
                    <div className="text-left">
                      <div className="text-base font-semibold text-gray-900">{p.name || p.id}</div>
                      <div className="text-xs text-gray-600 mt-0.5">ID: {p.id} {createdAt ? `• Registered ${createdAt.toLocaleString()}` : ''}</div>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 border border-blue-200">{analyses.length} analyses</span>
                      <ChevronDown className={`w-4 h-4 text-gray-600 transition-transform ${open ? 'rotate-180' : ''}`} />
                    </div>
                  </button>
                  {open && (
                    <div className="px-6 pb-4">
                      {analyses.length === 0 ? (
                        <div className="text-sm text-gray-600 py-3">No analyses for this patient yet.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Confidence</th>
                                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Timestamp</th>
                                <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                              {analyses.map((a) => (
                                <tr 
                                  key={a.id} 
                                  className="hover:bg-gray-50 cursor-pointer"
                                  onClick={async () => {
                                    setSelectedAnalysis(a);
                                    try {
                                      setLoadingAnalysis(true);
                                      const full = await getDoc(doc(db, 'analyses', a.id));
                                      if (full.exists()) {
                                        const data = full.data();
                                        setSelectedAnalysis((prev) => ({ ...(prev||{}), ...data }));
                                      }
                                    } catch (e) {
                                      console.error('Failed to fetch analysis', e);
                                    } finally {
                                      setLoadingAnalysis(false);
                                    }
                                  }}
                                >
                                  <td className="px-4 py-2 whitespace-nowrap">
                      <div className="flex items-center">
                                      <FileText className="w-4 h-4 text-blue-500 mr-2" />
                                      <span className="text-sm font-medium text-gray-900">{a.document_type || 'Unknown'}</span>
                      </div>
                    </td>
                                  <td className="px-4 py-2">
                                    <span className={`px-2 py-0.5 inline-flex text-xs leading-5 font-semibold rounded-full ${a.status === 'completed' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>{a.status || 'completed'}</span>
                    </td>
                                  <td className="px-4 py-2 text-sm text-gray-600">{a.ocr_confidence ? `${(a.ocr_confidence*100).toFixed(1)}%` : (a.cnn_confidence ? `${(a.cnn_confidence*100).toFixed(1)}%` : 'N/A')}</td>
                                  <td className="px-4 py-2 text-sm text-gray-600">
                      <div className="flex items-center">
                        <Clock className="w-4 h-4 mr-1" />
                                      {a.timestamp ? new Date(a.timestamp).toLocaleString() : 'N/A'}
                      </div>
                    </td>
                                  <td className="px-4 py-2 text-right">
                                    <button
                                      className={`p-2 rounded-lg border ${deletingId===a.id ? 'bg-red-200 text-red-900' : 'bg-red-50 text-red-700 hover:bg-red-100'} `}
                                      title="Delete analysis"
                                      onClick={async (e) => {
                                        e.stopPropagation();
                                        const ok = window.confirm('Delete this analysis? This cannot be undone.');
                                        if (!ok) return;
                                        try {
                                          setDeletingId(a.id);
                                          await apiService.deleteAnalysis(a.id);
                                        } catch (err) {
                                          console.error('Delete failed', err);
                                          alert('Failed to delete analysis');
                                        } finally {
                                          setDeletingId(null);
                                        }
                                      }}
                                    >
                                      <Trash2 className="w-4 h-4" />
                                    </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Analysis Modal */}
      {selectedAnalysis && (
        <div className="fixed inset-0 bg-black/40 z-40 flex items-center justify-center p-4" onClick={() => setSelectedAnalysis(null)}>
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-5xl overflow-hidden" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between px-5 py-3 border-b">
              <div>
                <div className="text-lg font-semibold text-gray-900">{selectedAnalysis.document_type || 'Analysis'} • {selectedAnalysis.id}</div>
                <div className="text-xs text-gray-600">{selectedAnalysis.timestamp ? new Date(selectedAnalysis.timestamp).toLocaleString() : ''}</div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  className={`px-3 py-2 text-xs font-semibold rounded-lg border ${exportingFHIR ? 'bg-blue-200 text-blue-900' : 'bg-blue-50 text-blue-700 hover:bg-blue-100'}`}
                  onClick={() => handleExportFHIR(selectedAnalysis.id)}
                  disabled={exportingFHIR}
                  title="Export analysis in FHIR R4 format for hospital systems"
                >
                  <div className="flex items-center gap-1">
                    <Download className="w-4 h-4" /> 
                    {exportingFHIR ? 'Exporting...' : 'Export FHIR'}
                  </div>
                </button>
                <button
                  className={`px-3 py-2 text-xs font-semibold rounded-lg border ${deleting ? 'bg-red-200 text-red-900' : 'bg-red-50 text-red-700 hover:bg-red-100'} `}
                  onClick={async () => {
                    if (!selectedAnalysis?.id) return;
                    const ok = window.confirm('Delete this analysis? This cannot be undone.');
                    if (!ok) return;
                    try {
                      setDeleting(true);
                      await apiService.deleteAnalysis(selectedAnalysis.id);
                      setSelectedAnalysis(null);
                    } catch (e) {
                      console.error('Delete failed', e);
                      alert('Failed to delete analysis');
                    } finally {
                      setDeleting(false);
                    }
                  }}
                >
                  <div className="flex items-center gap-1"><Trash2 className="w-4 h-4" /> Delete</div>
                </button>
                <button className="p-2 hover:bg-gray-100 rounded-lg" onClick={() => setSelectedAnalysis(null)}><X className="w-5 h-5" /></button>
              </div>
            </div>
            {(
              !!(selectedAnalysis && (
                selectedAnalysis.document_type === 'pdf_auto' ||
                (Array.isArray(selectedAnalysis.pages) && selectedAnalysis.pages.length > 0) ||
                (typeof selectedAnalysis.file_url === 'string' && selectedAnalysis.file_url.startsWith('data:application/pdf'))
              ))
            ) ? (
              (() => {
                const pages = Array.isArray(selectedAnalysis?.pages) ? selectedAnalysis.pages : [];
                const total = pages.length;
                const page = total > 0 ? pages[Math.max(0, Math.min(pdfPageIndex, total - 1))] : null;
                return (
                  <div className="p-5 space-y-4 max-h-[70vh] overflow-y-auto">
                    {selectedAnalysis.diagnosis_summary && (
                      <div className="bg-green-50 border border-green-200 rounded-xl p-3 text-sm text-green-900">{selectedAnalysis.diagnosis_summary}</div>
                    )}
                    <div className="space-y-3">
                      <div className="flex items-center gap-2">
                        <div className="text-sm font-bold text-gray-900">PDF Pages</div>
                        <div className="ml-auto flex items-center gap-2 text-xs">
                          <button className={`px-2 py-1 border rounded ${pdfPageIndex>0 ? 'bg-white hover:bg-gray-50' : 'bg-gray-100 text-gray-400 cursor-not-allowed'}`} onClick={() => pdfPageIndex>0 && setPdfPageIndex(pdfPageIndex-1)} disabled={pdfPageIndex<=0}>Prev</button>
                          <span className="font-semibold text-gray-700">{total ? (pdfPageIndex+1) : 0} / {total}</span>
                          <button className={`px-2 py-1 border rounded ${pdfPageIndex < total-1 ? 'bg-white hover:bg-gray-50' : 'bg-gray-100 text-gray-400 cursor-not-allowed'}`} onClick={() => pdfPageIndex < total-1 && setPdfPageIndex(pdfPageIndex+1)} disabled={pdfPageIndex >= total-1}>Next</button>
                        </div>
                      </div>
                      {page ? (
                        <div className="border rounded-lg p-3 bg-white space-y-3">
                          <div className="text-xs text-gray-700">Page {page.page} • {String(page.detected_type || 'unknown')}</div>

                          {/* X-RAY details */}
                          {page.cnn_class && (
                            <div className="space-y-2">
                              <div className="text-xs text-gray-800"><span className="font-semibold">Imaging:</span> {page.cnn_class} ({(((page.cnn_confidence||0)*100).toFixed(1))}%)</div>
                              {page.cnn_image_stats && (
                                <div className="grid grid-cols-2 gap-2 text-[11px]">
                                  {Object.entries(page.cnn_image_stats).map(([k,v]) => (
                                    (typeof v==='number' || typeof v==='string') && (
                                      <div key={k} className="bg-purple-50 border border-purple-100 rounded p-2">
                                        <div className="text-[10px] uppercase text-purple-700 font-bold">{k.replace(/_/g,' ')}</div>
                                        <div className="text-gray-800 font-semibold">{String(v)}</div>
                                      </div>
                                    )
                                  ))}
                                </div>
                              )}
                              {page.cnn_findings && page.cnn_findings.length>0 && (
                                <div>
                                  <div className="text-xs font-bold text-gray-900 mb-1">Key Findings</div>
                                  <ul className="list-disc pl-5 text-xs text-gray-800 space-y-1">
                                    {page.cnn_findings.map((f, idx) => (<li key={idx}>{f}</li>))}
                                  </ul>
                                </div>
                              )}
                              {page.heatmap_url && (
                                <div className="mt-2"><img alt={`heatmap-${pdfPageIndex}`} src={page.heatmap_url} className="w-full max-h-80 object-contain rounded border" /></div>
                              )}
                            </div>
                          )}

                          {/* MRI details */}
                          {page.mri_label && (
                            <div className="space-y-2">
                              <div className="text-xs text-gray-800"><span className="font-semibold">MRI:</span> {page.mri_label} ({(((page.mri_confidence||0)*100).toFixed(1))}%)</div>
                              {page.mri_body_region && (<div className="text-[11px] text-gray-700">Region: {String(page.mri_body_region)}</div>)}
                              {page.mri_stats && (
                                <div className="grid grid-cols-2 gap-2 text-[11px]">
                                  {Object.entries(page.mri_stats).map(([k,v]) => (
                                    (typeof v==='number' || typeof v==='string') && (
                                      <div key={k} className="bg-indigo-50 border border-indigo-100 rounded p-2">
                                        <div className="text-[10px] uppercase text-indigo-700 font-bold">{k.replace(/_/g,' ')}</div>
                                        <div className="text-gray-800 font-semibold">{String(v)}</div>
                                      </div>
                                    )
                                  ))}
                                </div>
                              )}
                              {page.mri_findings && page.mri_findings.length>0 && (
                                <div>
                                  <div className="text-xs font-bold text-gray-900 mb-1">Key Findings</div>
                                  <ul className="list-disc pl-5 text-xs text-gray-800 space-y-1">
                                    {page.mri_findings.map((f, idx) => (<li key={idx}>{f}</li>))}
                                  </ul>
                                </div>
                              )}
                            </div>
                          )}

                          {/* CT details */}
                          {page.ct_label && (
                            <div className="space-y-2">
                              <div className="text-xs text-gray-800"><span className="font-semibold">CT:</span> {page.ct_label} ({(((page.ct_confidence||0)*100).toFixed(1))}%)</div>
                              {page.ct_body_region && (<div className="text-[11px] text-gray-700">Region: {String(page.ct_body_region)}</div>)}
                              {page.ct_stats && (
                                <div className="grid grid-cols-2 gap-2 text-[11px]">
                                  {Object.entries(page.ct_stats).map(([k,v]) => (
                                    (typeof v==='number' || typeof v==='string') && (
                                      <div key={k} className="bg-amber-50 border border-amber-100 rounded p-2">
                                        <div className="text-[10px] uppercase text-amber-700 font-bold">{k.replace(/_/g,' ')}</div>
                                        <div className="text-gray-800 font-semibold">{String(v)}</div>
                                      </div>
                                    )
                                  ))}
                                </div>
                              )}
                              {page.ct_findings && page.ct_findings.length>0 && (
                                <div>
                                  <div className="text-xs font-bold text-gray-900 mb-1">Key Findings</div>
                                  <ul className="list-disc pl-5 text-xs text-gray-800 space-y-1">
                                    {page.ct_findings.map((f, idx) => (<li key={idx}>{f}</li>))}
                                  </ul>
                                </div>
                              )}
                            </div>
                          )}

                          {/* Document details */}
                          {page.ocr_text && (
                            <div>
                              <div className="text-xs font-bold text-gray-900 mb-1">Extracted Text</div>
                              <div className="text-[11px] text-gray-700 max-h-40 overflow-y-auto bg-gray-50 border rounded p-2">{page.ocr_text}</div>
                            </div>
                          )}
                          {page.medicines && page.medicines.length>0 && (
                            <div>
                              <div className="text-xs font-bold text-gray-900 mb-1">Medicines</div>
                              <div className="flex flex-wrap gap-2">
                                {page.medicines.map((m, i) => (<span key={i} className="px-2 py-0.5 text-[11px] rounded-full bg-gray-100 border">{m.text || String(m)}</span>))}
                              </div>
                            </div>
                          )}
                          {page.lab_values && page.lab_values.length>0 && (
                            <div>
                              <div className="text-xs font-bold text-gray-900 mb-1">Lab Values</div>
                              <div className="overflow-x-auto">
                                <table className="min-w-full bg-white rounded border">
                                  <thead>
                                    <tr className="text-[11px] uppercase text-gray-600 bg-emerald-100">
                                      <th className="px-2 py-1 text-left">Test</th>
                                      <th className="px-2 py-1 text-left">Value</th>
                                      <th className="px-2 py-1 text-left">Unit</th>
                                      <th className="px-2 py-1 text-left">Reference</th>
                                      <th className="px-2 py-1 text-left">Flag</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {page.lab_values.map((row, idx) => (
                                      <tr key={idx} className="text-[11px] border-t">
                                        <td className="px-2 py-1 font-medium text-gray-900">{row.test}</td>
                                        <td className="px-2 py-1">{row.value}</td>
                                        <td className="px-2 py-1">{row.unit || '-'}</td>
                                        <td className="px-2 py-1 text-gray-600">{row.ref_low!=null && row.ref_high!=null ? `${row.ref_low} - ${row.ref_high}` : '-'}</td>
                                        <td className="px-2 py-1">
                                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${row.flag==='High' ? 'bg-red-100 text-red-700' : row.flag==='Low' ? 'bg-yellow-100 text-yellow-700' : 'bg-emerald-100 text-emerald-700'}`}>{row.flag}</span>
                                        </td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              </div>
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="text-sm text-gray-600">No pages detected.</div>
                      )}
                    </div>
                  </div>
                );
              })()
            ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-0">
                  <div className="p-5 border-r">
                    <div className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2"><ImageIcon className="w-4 h-4" /> Preview</div>
                    <div className="rounded-xl overflow-hidden border">
                      {loadingAnalysis ? (
                        <div className="h-[420px] flex items-center justify-center text-sm text-gray-500 bg-gray-50">Loading…</div>
                      ) : typeof selectedAnalysis.file_url === 'string' && selectedAnalysis.file_url.startsWith('data:application/pdf') ? (
                        <iframe title="PDF" src={selectedAnalysis.file_url} className="w-full h-[420px]" />
                      ) : typeof selectedAnalysis.file_url === 'string' && selectedAnalysis.file_url.startsWith('data:image') ? (
                        <img alt="preview" src={selectedAnalysis.file_url} className="w-full" />
                      ) : selectedAnalysis.heatmap_url ? (
                        <img alt="heatmap" src={selectedAnalysis.heatmap_url} className="w-full" />
                      ) : (
                        <div className="h-[420px] flex items-center justify-center text-sm text-gray-500 bg-gray-50">No preview available</div>
                      )}
                    </div>
                  </div>
                  <div className="p-5 space-y-4 max-h-[70vh] overflow-y-auto">
            
            
            
                {selectedAnalysis.diagnosis_summary && (
                  <div className="bg-green-50 border border-green-200 rounded-xl p-3 text-sm text-green-900">{selectedAnalysis.diagnosis_summary}</div>
                )}

                {/* Imaging Recommendations for CT/MRI/X-ray */}
                {selectedAnalysis.imaging_recommendations && (
                  <div className="bg-gradient-to-r from-red-50 to-orange-50 rounded-lg p-4 border-2 border-red-300">
                    <div className="flex items-center gap-2 mb-3">
                      <AlertCircle className="w-5 h-5 text-red-600" />
                      <h3 className="font-bold text-gray-900 text-sm">🩺 Imaging Recommendations</h3>
                      {selectedAnalysis.imaging_recommendations.urgency_level && (
                        <span className={`ml-auto text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          selectedAnalysis.imaging_recommendations.urgency_level === 'HIGH' ? 'bg-red-600 text-white' :
                          selectedAnalysis.imaging_recommendations.urgency_level.includes('MODERATE') ? 'bg-orange-500 text-white' :
                          'bg-green-500 text-white'
                        }`}>
                          {selectedAnalysis.imaging_recommendations.urgency_level}
                        </span>
                      )}
                    </div>

                    {selectedAnalysis.imaging_recommendations.what_it_means && (
                      <div className="bg-blue-50 rounded p-3 border border-blue-200 mb-3">
                        <div className="text-[11px] font-bold text-blue-900 mb-1">📖 What It Means:</div>
                        <div className="text-[11px] text-blue-800">{selectedAnalysis.imaging_recommendations.what_it_means}</div>
                      </div>
                    )}

                    {selectedAnalysis.imaging_recommendations.specialist && (
                      <div className="bg-emerald-50 rounded p-3 border border-emerald-200 mb-3">
                        <div className="text-[11px] font-bold text-emerald-900 mb-2">👨‍⚕️ Recommended Specialist:</div>
                        <div className="space-y-1 text-[11px]">
                          <div><span className="font-semibold text-emerald-900">Specialist:</span> <span className="text-emerald-800">{selectedAnalysis.imaging_recommendations.specialist.name}</span></div>
                          <div><span className="font-semibold text-orange-900">Urgency:</span> <span className="text-orange-800">{selectedAnalysis.imaging_recommendations.specialist.urgency}</span></div>
                          <div><span className="font-semibold text-gray-700">Why:</span> <span className="text-gray-800">{selectedAnalysis.imaging_recommendations.specialist.reason}</span></div>
                        </div>
                      </div>
                    )}

                    {selectedAnalysis.imaging_recommendations.warning_signs && selectedAnalysis.imaging_recommendations.warning_signs.length > 0 && (
                      <div className="bg-red-100 rounded p-3 border-2 border-red-400 mb-3">
                        <div className="text-[11px] font-bold text-red-900 mb-2">⚠️ WARNING SIGNS:</div>
                        <ul className="space-y-1">
                          {selectedAnalysis.imaging_recommendations.warning_signs.map((sign, idx) => (
                            <li key={idx} className="text-[11px] text-red-900 flex items-start gap-1">
                              <span className="text-red-600 mt-0.5">⚠️</span>
                              <span>{sign}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {selectedAnalysis.imaging_recommendations.next_steps && selectedAnalysis.imaging_recommendations.next_steps.length > 0 && (
                      <div className="bg-purple-50 rounded p-3 border border-purple-200 mb-3">
                        <div className="text-[11px] font-bold text-purple-900 mb-2">📋 Next Steps:</div>
                        <ul className="space-y-1">
                          {selectedAnalysis.imaging_recommendations.next_steps.map((step, idx) => (
                            <li key={idx} className="text-[11px] text-purple-800 flex items-start gap-1">
                              <span className="text-purple-600">•</span>
                              <span>{step}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {selectedAnalysis.imaging_recommendations.recommendations && selectedAnalysis.imaging_recommendations.recommendations.length > 0 && (
                      <div className="bg-green-50 rounded p-3 border border-green-200 mb-2">
                        <div className="text-[11px] font-bold text-green-900 mb-2">💪 Lifestyle:</div>
                        <ul className="space-y-1">
                          {selectedAnalysis.imaging_recommendations.recommendations.map((rec, idx) => (
                            <li key={idx} className="text-[11px] text-green-800 flex items-start gap-1">
                              <span className="text-green-600">•</span>
                              <span>{rec}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}

                {/* Diagnosis Suggestions for Prescriptions */}
                {selectedAnalysis.diagnosis_suggestions && selectedAnalysis.diagnosis_suggestions.possible_conditions && selectedAnalysis.diagnosis_suggestions.possible_conditions.length > 0 && (
                  <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg p-4 border-2 border-purple-300">
                    <div className="flex items-center gap-2 mb-3">
                      <Activity className="w-5 h-5 text-purple-600" />
                      <h3 className="font-bold text-gray-900 text-sm">🩺 Diagnosis Suggestions</h3>
                    </div>

                    <div className="space-y-2 mb-3">
                      {selectedAnalysis.diagnosis_suggestions.possible_conditions.slice(0, 3).map((condition, idx) => (
                        <div key={idx} className="bg-white rounded p-3 border border-purple-200">
                          <div className="flex items-start justify-between mb-1">
                            <div className="flex-1">
                              <div className="text-sm font-bold text-purple-900">{idx + 1}. {condition.condition}</div>
                              <div className="text-[11px] text-gray-600 mt-1">
                                <span className="font-medium">Evidence:</span> {condition.supporting_medicines.join(', ')}
                              </div>
                            </div>
                            <span className={`ml-2 px-2 py-0.5 rounded-full text-[10px] font-bold ${
                              condition.confidence === 'High' ? 'bg-green-100 text-green-700 border border-green-300' :
                              condition.confidence === 'Medium' ? 'bg-yellow-100 text-yellow-700 border border-yellow-300' :
                              'bg-gray-100 text-gray-700 border border-gray-300'
                            }`}>
                              {condition.confidence}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>

                    {selectedAnalysis.diagnosis_suggestions.recommendations && selectedAnalysis.diagnosis_suggestions.recommendations.length > 0 && (
                      <div className="bg-blue-50 rounded p-3 border border-blue-200 mb-3">
                        <div className="text-[11px] font-bold text-blue-900 mb-2">📋 Recommendations:</div>
                        <ul className="space-y-1">
                          {selectedAnalysis.diagnosis_suggestions.recommendations.slice(0, 8).map((rec, idx) => (
                            <li key={idx} className="text-[11px] text-blue-800 flex items-start gap-1">
                              <span className="text-blue-600">•</span>
                              <span>{rec}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {selectedAnalysis.diagnosis_suggestions.specialists && selectedAnalysis.diagnosis_suggestions.specialists.length > 0 && (
                      <div className="bg-emerald-50 rounded p-3 border border-emerald-200">
                        <div className="text-[11px] font-bold text-emerald-900 mb-2">👨‍⚕️ Specialists:</div>
                        <div className="space-y-2">
                          {selectedAnalysis.diagnosis_suggestions.specialists.map((spec, i) => (
                            <div key={i} className="bg-white rounded p-2 border border-emerald-200">
                              {typeof spec === 'object' ? (
                                <div className="space-y-0.5 text-[11px]">
                                  <div className="font-bold text-emerald-900">{spec.specialist}</div>
                                  <div className="text-gray-700"><strong>Why:</strong> {spec.reason}</div>
                                  <div className="text-orange-700"><strong>When:</strong> {spec.when_to_schedule}</div>
                                  <div className="text-blue-700"><strong>For:</strong> {spec.condition}</div>
                                </div>
                              ) : (
                                <span className="text-sm font-bold text-emerald-800">{spec}</span>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {Array.isArray(selectedAnalysis.medicines) && selectedAnalysis.medicines.length > 0 && (
                  <div>
                    <div className="text-sm font-bold text-gray-900 mb-2">Medicines</div>
                    <div className="flex flex-wrap gap-2">
                      {selectedAnalysis.medicines.map((m, i) => (
                        <span key={i} className="px-2 py-0.5 text-xs rounded-full bg-gray-100 border">{m.text || String(m)}</span>
                      ))}
                    </div>
                  </div>
                )}
                {/* X-ray imaging summary */}
                {selectedAnalysis.cnn_class && (
                  <div className="space-y-2">
                    <div className="text-sm text-gray-800"><span className="font-semibold">Imaging:</span> {selectedAnalysis.cnn_class} ({((selectedAnalysis.cnn_confidence||0)*100).toFixed(1)}%)</div>
                    {selectedAnalysis.cnn_all_probabilities && (
                      <div className="text-xs text-gray-700">
                        {Object.entries(selectedAnalysis.cnn_all_probabilities).map(([k,v]) => (
                          <div key={k} className="flex items-center gap-2"><span className="w-28 text-gray-600">{k}</span><div className="flex-1 bg-purple-100 h-1 rounded"><div className="bg-purple-500 h-1 rounded" style={{ width: `${(v*100).toFixed(1)}%` }}></div></div><span className="w-12 text-right">{(v*100).toFixed(1)}%</span></div>
                        ))}
                      </div>
                    )}
                    {selectedAnalysis.cnn_image_stats && (
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        {Object.entries(selectedAnalysis.cnn_image_stats).map(([k,v]) => (
                          (typeof v==='number' || typeof v==='string') && (
                            <div key={k} className="bg-purple-50 border border-purple-100 rounded p-2">
                              <div className="text-[10px] uppercase text-purple-700 font-bold">{k.replace(/_/g,' ')}</div>
                              <div className="text-gray-800 font-semibold">{String(v)}</div>
                            </div>
                          )
                        ))}
                      </div>
                    )}
                    {selectedAnalysis.cnn_findings && selectedAnalysis.cnn_findings.length>0 && (
                      <div>
                        <div className="text-sm font-bold text-gray-900 mb-1">Key Findings</div>
                        <ul className="list-disc pl-5 text-sm text-gray-800 space-y-1">
                          {selectedAnalysis.cnn_findings.map((f, idx) => (<li key={idx}>{f}</li>))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
                {selectedAnalysis.ocr_text && (
                  <div>
                    <div className="text-sm font-bold text-gray-900 mb-1">Extracted Text</div>
                    <div className="text-xs text-gray-700 max-h-40 overflow-y-auto border rounded p-2 bg-gray-50">{selectedAnalysis.ocr_text}</div>
                  </div>
                )}

                {/* MRI details */}
                {selectedAnalysis.mri_label && (
                  <div className="space-y-2">
                    <div className="text-sm text-gray-800"><span className="font-semibold">MRI:</span> {selectedAnalysis.mri_label} ({(((selectedAnalysis.mri_confidence||0)*100).toFixed(1))}%)</div>
                    {selectedAnalysis.mri_body_region && (
                      <div className="text-xs text-gray-700">Region: {String(selectedAnalysis.mri_body_region)}</div>
                    )}
                    {selectedAnalysis.mri_stats && (
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        {Object.entries(selectedAnalysis.mri_stats).map(([k,v]) => (
                          (typeof v==='number' || typeof v==='string') && (
                            <div key={k} className="bg-indigo-50 border border-indigo-100 rounded p-2">
                              <div className="text-[10px] uppercase text-indigo-700 font-bold">{k.replace(/_/g,' ')}</div>
                              <div className="text-gray-800 font-semibold">{String(v)}</div>
                            </div>
                          )
                        ))}
                      </div>
                    )}
                    {selectedAnalysis.mri_findings && selectedAnalysis.mri_findings.length>0 && (
                      <div>
                        <div className="text-sm font-bold text-gray-900 mb-1">Key Findings</div>
                        <ul className="list-disc pl-5 text-sm text-gray-800 space-y-1">
                          {selectedAnalysis.mri_findings.map((f, idx) => (<li key={idx}>{f}</li>))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}

                {/* CT details */}
                {selectedAnalysis.ct_label && (
                  <div className="space-y-2">
                    <div className="text-sm text-gray-800"><span className="font-semibold">CT:</span> {selectedAnalysis.ct_label} ({(((selectedAnalysis.ct_confidence||0)*100).toFixed(1))}%)</div>
                    {selectedAnalysis.ct_body_region && (
                      <div className="text-xs text-gray-700">Region: {String(selectedAnalysis.ct_body_region)}</div>
                    )}
                    {selectedAnalysis.ct_stats && (
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        {Object.entries(selectedAnalysis.ct_stats).map(([k,v]) => (
                          (typeof v==='number' || typeof v==='string') && (
                            <div key={k} className="bg-amber-50 border border-amber-100 rounded p-2">
                              <div className="text-[10px] uppercase text-amber-700 font-bold">{k.replace(/_/g,' ')}</div>
                              <div className="text-gray-800 font-semibold">{String(v)}</div>
                            </div>
                          )
                        ))}
                      </div>
                    )}
                    {selectedAnalysis.ct_findings && selectedAnalysis.ct_findings.length>0 && (
                      <div>
                        <div className="text-sm font-bold text-gray-900 mb-1">Key Findings</div>
                        <ul className="list-disc pl-5 text-sm text-gray-800 space-y-1">
                          {selectedAnalysis.ct_findings.map((f, idx) => (<li key={idx}>{f}</li>))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}

                {/* Lab values */}
                {selectedAnalysis.lab_values && selectedAnalysis.lab_values.length>0 && (
                  <div className="text-sm">
                    <div className="text-sm font-bold text-gray-900 mb-2">Lab Values</div>
                    <div className="overflow-x-auto">
                      <table className="min-w-full bg-white rounded border">
                        <thead>
                          <tr className="text-xs uppercase text-gray-600 bg-emerald-100">
                            <th className="px-2 py-1 text-left">Test</th>
                            <th className="px-2 py-1 text-left">Value</th>
                            <th className="px-2 py-1 text-left">Unit</th>
                            <th className="px-2 py-1 text-left">Reference</th>
                            <th className="px-2 py-1 text-left">Flag</th>
                          </tr>
                        </thead>
                        <tbody>
                          {selectedAnalysis.lab_values.map((row, idx) => (
                            <tr key={idx} className="text-xs border-t">
                              <td className="px-2 py-1 font-medium text-gray-900">{row.test}</td>
                              <td className="px-2 py-1">{row.value}</td>
                              <td className="px-2 py-1">{row.unit || '-'}</td>
                              <td className="px-2 py-1 text-gray-600">{row.ref_low!=null && row.ref_high!=null ? `${row.ref_low} - ${row.ref_high}` : '-'}</td>
                              <td className="px-2 py-1">
                                <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${row.flag==='High' ? 'bg-red-100 text-red-700' : row.flag==='Low' ? 'bg-yellow-100 text-yellow-700' : 'bg-emerald-100 text-emerald-700'}`}>{row.flag}</span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* PDF Auto pages */}
                {selectedAnalysis.pages && Array.isArray(selectedAnalysis.pages) && (
                  <div className="space-y-3">
                    <div className="text-sm font-bold text-gray-900">PDF Pages</div>
                    <div className="space-y-2">
                      {selectedAnalysis.pages.map((p, i) => (
                        <div key={i} className="border rounded-lg p-3">
                          <div className="text-xs text-gray-700 mb-1">Page {p.page} • {String(p.detected_type || 'unknown')}</div>
                          {p.cnn_class && (
                            <div className="text-xs text-gray-800"><span className="font-semibold">Imaging:</span> {p.cnn_class} ({(((p.cnn_confidence||0)*100).toFixed(1))}%)</div>
                          )}
                          {p.lab_values && p.lab_values.length>0 && (
                            <div className="text-xs text-gray-800 mt-1">Lab values: {p.lab_values.length}</div>
                          )}
                          {p.medicines && p.medicines.length>0 && (
                            <div className="text-xs text-gray-800 mt-1">Medicines: {p.medicines.length}</div>
                          )}
                          {p.ocr_text && (
                            <div className="text-[11px] text-gray-700 mt-1 max-h-20 overflow-y-auto bg-gray-50 border rounded p-2">{p.ocr_text}</div>
                          )}
                          {p.heatmap_url && (
                            <div className="mt-2"><img alt={`heatmap-${i}`} src={p.heatmap_url} className="w-full rounded border" /></div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;

