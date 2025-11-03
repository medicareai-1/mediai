import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { apiService } from '../services/api';
import { 
  Upload as UploadIcon, 
  FileText, 
  Image as ImageIcon,
  CheckCircle,
  AlertCircle,
  Loader,
  Activity,
  ChevronDown,
  Search,
  User as UserIcon
} from 'lucide-react';

function Upload() {
  const { currentUser } = useAuth();
  const [file, setFile] = useState(null); // keep for single-file backward compat
  const [files, setFiles] = useState([]); // multi-file queue
  const [documentType, setDocumentType] = useState('prescription');
  const [patientId, setPatientId] = useState('');
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [preview, setPreview] = useState(null);
  // Pagination for Auto (PDF) results
  const [autoPage, setAutoPage] = useState(0); // 0-based index of page groups

  // Patients dropdown
  const [patients, setPatients] = useState([]);
  const [loadingPatients, setLoadingPatients] = useState(true);
  const [patientMenuOpen, setPatientMenuOpen] = useState(false);
  const [patientQuery, setPatientQuery] = useState('');
  const patientMenuRef = useRef(null);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const data = await apiService.getPatients();
        const list = Array.isArray(data?.patients) ? data.patients : (Array.isArray(data) ? data : []);
        if (mounted) {
          setPatients(list);
        }
      } catch (e) {
        console.error('Failed to load patients', e);
      } finally {
        if (mounted) setLoadingPatients(false);
      }
    })();
    return () => { mounted = false; };
  }, []);

  // Close patient dropdown on outside click
  useEffect(() => {
    function handleClickOutside(e) {
      if (patientMenuRef.current && !patientMenuRef.current.contains(e.target)) {
        setPatientMenuOpen(false);
      }
    }
    if (patientMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [patientMenuOpen]);

  const documentTypes = [
    { value: 'prescription', label: 'Prescription', icon: FileText },
    { value: 'xray', label: 'X-Ray', icon: ImageIcon },
    { value: 'mri', label: 'MRI Scan', icon: ImageIcon },
    { value: 'ct_scan', label: 'CT Scan', icon: ImageIcon },
    // UI-only rename: use the PDF auto route but show as Lab Report
    { value: 'auto', label: 'Lab Report (PDF)', icon: FileText },
  ];

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files || []);
    if (selectedFiles.length > 0) {
      setFiles(selectedFiles);
      setFile(selectedFiles[0] || null);
      setError('');
      // Create preview from first file only
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result);
      };
      reader.readAsDataURL(selectedFiles[0]);
    }
  };

  const fileToDataUrl = (f) => new Promise((resolve, reject) => {
    try {
      const reader = new FileReader();
      reader.onloadend = () => resolve(reader.result);
      reader.onerror = () => reject(new Error('Failed to read file'));
      reader.readAsDataURL(f);
    } catch (err) {
      reject(err);
    }
  });

  const handleUploadAndProcess = async () => {
    if (!file && files.length === 0) {
      setError('Please select a file');
      return;
    }

    if (!patientId.trim()) {
      setError('Please enter a patient ID');
      return;
    }

    setUploading(true);
    setError('');

    try {
      const selectedFiles = files.length > 0 ? files : (file ? [file] : []);
      const hasMultiple = selectedFiles.length > 1;

      // If multiple files, only images will be sent to batch endpoint
      if (hasMultiple) {
        // Convert all selected files to base64
        const dataUrls = await Promise.all(selectedFiles.map(fileToDataUrl));
        const imageDataUrls = [];
        let skipped = 0;
        dataUrls.forEach((u) => {
          if (typeof u === 'string' && u.startsWith('data:image')) {
            imageDataUrls.push(u);
          } else {
            skipped += 1;
          }
        });

        if (imageDataUrls.length === 0) {
          setUploading(false);
          setError('Only images are supported in multi-file mode. For PDFs, upload one at a time.');
          return;
        }

        setUploading(false);
        setProcessing(true);
        try {
          const response = await apiService.processBatch({
            file_urls: imageDataUrls,
            patient_id: patientId,
            user_id: currentUser.uid,
            document_type: documentType,
          });
          if (skipped > 0) {
            response.skipped = skipped;
          }
          setResult(response);
          setProcessing(false);
        } catch (err) {
          console.error('Batch processing error:', err);
          setError(err.message || 'Failed to process batch');
          setProcessing(false);
        }
        return;
      }

      // Single-file flow (supports PDF auto-route)
      const base64String = await fileToDataUrl(selectedFiles[0]);
        setUploading(false);
        setProcessing(true);

        try {
          let response;
          // Auto route for PDFs
          if (documentType === 'auto' && typeof base64String === 'string' && base64String.startsWith('data:application/pdf')) {
            response = await apiService.processPdfAuto({
              file_url: base64String,
              patient_id: patientId,
              user_id: currentUser.uid
            });
            // Reset pagination to the first group when a new Auto PDF is analyzed
            setAutoPage(0);
          } else {
            // Send base64 to backend for AI processing
            response = await apiService.processDocument({
              file_url: base64String,
              document_type: documentType,
              patient_id: patientId,
              user_id: currentUser.uid
            });
          }

          setResult(response);
          setProcessing(false);
        } catch (err) {
          console.error('Processing error:', err);
          setError(err.message || 'Failed to process document');
          setProcessing(false);
        }

    } catch (err) {
      console.error('Error:', err);
      setError(err.message || 'Failed to process document');
      setUploading(false);
      setProcessing(false);
    }
  };

  const resetForm = () => {
    setFile(null);
    setFiles([]);
    setPreview(null);
    setPatientId('');
    setResult(null);
    setError('');
    setAutoPage(0);
  };

  const pairMeds = (medicines = [], dosages = [], durations = []) => {
    try {
      const dsg = Array.isArray(dosages) ? dosages : [];
      const dur = Array.isArray(durations) ? durations : [];
      return (Array.isArray(medicines) ? medicines : []).map((m) => {
        const mStart = typeof m.start === 'number' ? m.start : -1;
        // Find nearest dosage/duration by absolute start distance
        const nearest = (arr) => {
          let best = null; let bestDist = Infinity;
          arr.forEach((x) => {
            const s = typeof x.start === 'number' ? x.start : null;
            if (s != null && mStart >= 0) {
              const dist = Math.abs(s - mStart);
              if (dist < bestDist) { best = x; bestDist = dist; }
            }
          });
          return best;
        };
        const nd = nearest(dsg);
        const ndr = nearest(dur);
        return {
          name: m.text || String(m),
          dosage: nd ? nd.text : null,
          duration: ndr ? ndr.text : null,
        };
      });
    } catch (_) {
      return (medicines || []).map((m) => ({ name: m.text || String(m) }));
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header with gradient */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-8 text-white shadow-xl">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-white bg-opacity-20 rounded-xl backdrop-blur-sm">
            <UploadIcon className="w-8 h-8" />
          </div>
          <div>
            <h1 className="text-4xl font-bold">📄 Upload & Analyze</h1>
            <p className="text-blue-100 text-lg mt-1">Real-time OCR and Imaging AI</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upload Form */}
        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-blue-100 rounded-lg">
              <FileText className="w-5 h-5 text-blue-600" />
            </div>
            <h2 className="text-xl font-bold text-gray-900">Document Details</h2>
          </div>

          {/* Document Type Selection */}
          <div className="mb-6">
            <label className="block text-sm font-semibold text-gray-700 mb-3">
              📋 Document Type
            </label>
            <div className="grid grid-cols-2 gap-3">
              {documentTypes.map((type) => {
                const Icon = type.icon;
                return (
                  <button
                    key={type.value}
                    onClick={() => setDocumentType(type.value)}
                    className={`flex items-center justify-center p-4 border-2 rounded-xl transition-all transform hover:scale-105 ${
                      documentType === type.value
                        ? 'border-blue-500 bg-gradient-to-br from-blue-50 to-blue-100 text-blue-700 shadow-md'
                        : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    <Icon className="w-5 h-5 mr-2" />
                    <span className="text-sm font-semibold">{type.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Patient Selection */}
          <div className="mb-6" ref={patientMenuRef}>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              <span className="inline-flex items-center gap-2"><UserIcon className="w-4 h-4 text-gray-600" /> Patient</span>
            </label>
            {loadingPatients ? (
              <div className="w-full px-4 py-3.5 border-2 border-gray-200 rounded-xl bg-gray-50 text-sm text-gray-500">Loading patients…</div>
            ) : patients.length > 0 ? (
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setPatientMenuOpen((v) => !v)}
                  className="w-full flex items-center justify-between px-4 py-3.5 border-2 border-gray-200 rounded-xl bg-gray-50 hover:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                >
                  <span className={`text-sm ${patientId ? 'text-gray-900' : 'text-gray-500'}`}>
                    {patientId ? (() => { const p = patients.find(x => x.id === patientId); return p ? `${p.name || p.id}${p.age ? ` • ${p.age}` : ''}${p.gender ? ` • ${p.gender}` : ''}` : 'Select a patient…'; })() : 'Select a patient…'}
                  </span>
                  <ChevronDown className="w-4 h-4 text-gray-600" />
                </button>

                {patientMenuOpen && (
                  <div className="absolute z-20 mt-2 w-full bg-white border-2 border-gray-200 rounded-xl shadow-lg">
                    <div className="p-2 border-b bg-gray-50 rounded-t-xl">
                      <div className="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-white border">
                        <Search className="w-4 h-4 text-gray-500" />
            <input
              type="text"
                          value={patientQuery}
                          onChange={(e) => setPatientQuery(e.target.value)}
                          placeholder="Search name, id…"
                          className="w-full text-sm outline-none placeholder:text-gray-400"
                        />
                      </div>
                    </div>
                    <ul role="listbox" className="max-h-56 overflow-y-auto py-1">
                      {patients
                        .filter(p => {
                          const q = patientQuery.trim().toLowerCase();
                          if (!q) return true;
                          const label = `${p.name || ''} ${p.id || ''} ${p.gender || ''} ${p.age || ''}`.toLowerCase();
                          return label.includes(q);
                        })
                        .map((p) => (
                          <li key={p.id} role="option">
                            <button
                              type="button"
                              onClick={() => { setPatientId(p.id); setPatientMenuOpen(false); }}
                              className={`w-full text-left px-4 py-2.5 hover:bg-blue-50 flex items-center justify-between ${patientId===p.id ? 'bg-blue-50' : ''}`}
                            >
                              <div className="flex flex-col">
                                <span className="text-sm font-semibold text-gray-900">{p.name || p.id}</span>
                                <span className="text-xs text-gray-600">ID: {p.id}{p.age ? ` • ${p.age}` : ''}{p.gender ? ` • ${p.gender}` : ''}</span>
                              </div>
                              {patientId === p.id && (
                                <CheckCircle className="w-4 h-4 text-blue-600" />
                              )}
                            </button>
                          </li>
                        ))}
                      {patients.filter(p => {
                        const q = patientQuery.trim().toLowerCase();
                        if (!q) return true;
                        const label = `${p.name || ''} ${p.id || ''} ${p.gender || ''} ${p.age || ''}`.toLowerCase();
                        return label.includes(q);
                      }).length === 0 && (
                        <li className="px-4 py-3 text-sm text-gray-500">No matches</li>
                      )}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <div className="w-full px-4 py-3.5 border-2 border-yellow-300 rounded-xl bg-yellow-50 text-sm text-yellow-800">
                No patients found. Please create a patient first.
              </div>
            )}
          </div>

          {/* File Upload */}
          <div className="mb-6">
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              📁 Upload File
            </label>
            <div className={`border-2 border-dashed rounded-2xl p-10 text-center transition-all ${
              file 
                ? 'border-green-400 bg-green-50' 
                : 'border-gray-300 hover:border-blue-400 hover:bg-blue-50'
            }`}>
              <input
                type="file"
                onChange={handleFileChange}
                accept="image/*,.pdf,.dcm,.dicom,.nii,.nii.gz"
                multiple
                className="hidden"
                id="file-upload"
              />
              <label htmlFor="file-upload" className="cursor-pointer">
                {file ? (
                  <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-3" />
                ) : (
                  <UploadIcon className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                )}
                <p className="text-sm font-semibold text-gray-700">
                  {files && files.length > 1 ? `${files.length} files selected` : (file ? file.name : 'Click to upload or drag and drop')}
                </p>
                <p className="text-xs text-gray-500 mt-2">
                  PNG, JPG, PDF, DICOM (.dcm), NIfTI (.nii/.nii.gz) up to 10MB each
                </p>
              </label>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border-2 border-red-200 rounded-xl flex items-start shadow-sm">
              <AlertCircle className="w-5 h-5 text-red-600 mr-3 mt-0.5" />
              <span className="text-sm text-red-700 font-medium">{error}</span>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3">
            <button
              onClick={handleUploadAndProcess}
              disabled={!file || uploading || processing}
              className="flex-1 flex items-center justify-center py-4 px-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold rounded-xl hover:from-blue-700 hover:to-purple-700 disabled:from-gray-400 disabled:to-gray-400 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl transform hover:scale-105"
            >
              {uploading || processing ? (
                <>
                  <Loader className="w-5 h-5 mr-2 animate-spin" />
                  {uploading ? 'Uploading...' : 'Processing with AI...'}
                </>
              ) : (
                <>
                  <UploadIcon className="w-5 h-5 mr-2" />
                  Upload & Analyze
                </>
              )}
            </button>
            <button
              onClick={resetForm}
              className="px-6 py-3 border-2 border-gray-300 rounded-xl hover:bg-gray-50 transition-all font-semibold hover:border-gray-400"
            >
              Reset
            </button>
          </div>
        </div>

        {/* Preview and Results */}
        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className={`p-2 rounded-lg ${result ? 'bg-green-100' : 'bg-gray-100'}`}>
              {result ? (
                <CheckCircle className="w-5 h-5 text-green-600" />
              ) : (
                <ImageIcon className="w-5 h-5 text-gray-600" />
              )}
            </div>
            <h2 className="text-xl font-bold text-gray-900">
              {result ? '✅ Analysis Results' : '👁️ Preview'}
            </h2>
          </div>

          {preview && !result && (
            <div className="rounded-xl overflow-hidden border-2 border-gray-200 shadow-md">
              {typeof preview === 'string' && preview.startsWith('data:application/pdf') ? (
                <iframe
                  title="PDF Preview"
                  src={preview}
                  className="w-full h-[600px]"
                />
              ) : (
                <img src={preview} alt="Preview" className="w-full" />
              )}
            </div>
          )}

          {result && (
            <div className="space-y-5">
              {/* Batch Results */}
              {result.batch_results && Array.isArray(result.batch_results) && (
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <FileText className="w-5 h-5 text-gray-700" />
                    <h3 className="font-bold text-gray-900">📦 Batch Results</h3>
                    <span className="ml-auto text-xs font-bold px-2 py-1 rounded-full bg-gray-700 text-white">{result.total_files} files</span>
                  </div>
                  {result.skipped ? (
                    <div className="text-xs text-yellow-800 bg-yellow-50 border border-yellow-200 rounded-lg p-2">
                      {result.skipped} non-image file(s) were skipped in batch. Upload PDFs one at a time using Lab Report (PDF).
                    </div>
                  ) : null}
                  <div className="space-y-4">
                    {result.batch_results.map((r, idx) => {
                      const medsPaired = pairMeds(r.medicines, r.dosages, r.durations);
                      return (
                        <div key={idx} className="bg-white rounded-xl border shadow-sm overflow-hidden">
                          <div className="flex items-center gap-3 px-4 py-3 border-b bg-gray-50">
                            <div className="text-sm font-bold text-gray-900">File {r.file_number || (idx+1)}</div>
                            <span className="text-xs px-2 py-1 rounded-full bg-gray-100 border">{String(r.document_type || documentType)}</span>
                          </div>
                          <div className="p-4 space-y-3">
                            {medsPaired && medsPaired.length > 0 && (
                              <div>
                                <div className="text-sm font-bold text-gray-900 mb-1">Medicines</div>
                                <div className="grid grid-cols-1 gap-2">
                                  {medsPaired.map((m, i2) => (
                                    <div key={i2} className="p-3 bg-white border rounded">
                                      <div className="font-semibold text-gray-900">{m.name}</div>
                                      <div className="text-xs text-gray-600 mt-1 flex gap-4">
                                        {m.dosage && <span>Dosage: <span className="font-medium text-gray-800">{m.dosage}</span></span>}
                                        {m.duration && <span>Duration: <span className="font-medium text-gray-800">{m.duration}</span></span>}
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                            {r.ocr_text && (
                              <div className="text-xs text-gray-600 mt-1 max-h-40 overflow-y-auto border rounded p-2 bg-gray-50">{r.ocr_text}</div>
                            )}
                            {r.cnn_class && (
                              <div className="text-sm text-gray-700"><span className="font-medium">AI Imaging:</span> {r.cnn_class} ({((r.cnn_confidence||0)*100).toFixed(1)}%)</div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
              {/* Auto PDF Pages */}
              {result.pages && Array.isArray(result.pages) && (
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <FileText className="w-5 h-5 text-gray-700" />
                    <h3 className="font-bold text-gray-900">📚 Lab Report (PDF) Pages</h3>
                    <span className="ml-auto text-xs font-bold px-2 py-1 rounded-full bg-gray-700 text-white">{result.total_pages} pages</span>
                  </div>

                  {/* Pagination controls */}
                  <div className="flex items-center gap-2">
                    {(() => {
                      const totalGroups = Math.ceil(result.pages.length / 2);
                      const canPrev = autoPage > 0;
                      const canNext = autoPage < totalGroups - 1;
                      return (
                        <>
                          <button
                            onClick={() => canPrev && setAutoPage(autoPage - 1)}
                            disabled={!canPrev}
                            className={`px-3 py-1 rounded-lg border ${canPrev ? 'bg-white hover:bg-gray-50' : 'bg-gray-100 text-gray-400 cursor-not-allowed'}`}
                          >
                            ◀ Prev
                          </button>
                          <span className="text-xs font-semibold text-gray-700">
                            Page {autoPage + 1} of {totalGroups}
                          </span>
                          <button
                            onClick={() => canNext && setAutoPage(autoPage + 1)}
                            disabled={!canNext}
                            className={`px-3 py-1 rounded-lg border ${canNext ? 'bg-white hover:bg-gray-50' : 'bg-gray-100 text-gray-400 cursor-not-allowed'}`}
                          >
                            Next ▶
                          </button>
                        </>
                      );
                    })()}
                  </div>
                </div>
              )}

              {/* Auto PDF Pages - Detailed Panels (2 at a time) */}
              {result.pages && Array.isArray(result.pages) && (
                    <div className="space-y-4">
                      {result.pages.slice(autoPage * 2, autoPage * 2 + 2).map((p, i) => (
                        <div key={`detail-${i}`} className="bg-white rounded-xl border shadow-sm">
                          <div className="flex items-center gap-3 px-4 py-3 border-b bg-gray-50 rounded-t-xl">
                            <div className="text-sm font-bold text-gray-900">Page {p.page}</div>
                            <span className="text-xs px-2 py-1 rounded-full bg-gray-100 border">{String(p.detected_type || 'unknown')}</span>
                          </div>
                          <div className="p-4 space-y-4">
                            {/* X-RAY DETAILS */}
                            {p.detected_type === 'xray' && (
                              <div className="space-y-3">
                                <div className="flex items-center justify-between">
                                  <div className="text-sm text-gray-700"><span className="font-medium">Diagnosis:</span> {p.cnn_class}</div>
                                  <div className="flex items-center gap-2">
                                    <div className="w-40 bg-purple-200 rounded-full h-2"><div className="bg-purple-600 h-2 rounded-full" style={{ width: `${(p.cnn_confidence||0)*100}%` }}></div></div>
                                    <span className="text-xs font-semibold text-purple-700">{(((p.cnn_confidence||0)*100).toFixed(1))}%</span>
                                  </div>
                                </div>
                                {p.cnn_image_stats && (
                                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
                                    {Object.entries(p.cnn_image_stats).map(([k,v]) => (
                                      (typeof v==='number' || typeof v==='string') && (
                                        <div key={k} className="p-3 rounded-lg bg-purple-50 border border-purple-100">
                                          <div className="text-xs uppercase text-purple-600 font-bold mb-1">{k.replace(/_/g,' ')}</div>
                                          <div className="text-gray-800 font-semibold">{typeof v==='number'? v : v}</div>
                                        </div>
                                      )
                                    ))}
                                  </div>
                                )}
                                {p.cnn_findings && p.cnn_findings.length>0 && (
                                  <div>
                                    <div className="text-sm font-bold text-purple-900 mb-2">Key Findings</div>
                                    <ul className="list-disc pl-5 text-sm text-gray-800 space-y-1">
                                      {p.cnn_findings.map((f,idx)=>(<li key={idx}>{f}</li>))}
                                    </ul>
                                  </div>
                                )}
                                {p.heatmap_url && (
                                  <div>
                                    <div className="text-sm font-bold text-orange-900 mb-2">Grad‑CAM Heatmap</div>
                                    <img src={p.heatmap_url} alt={`heatmap-${i}`} className="w-full rounded-lg border" />
                                  </div>
                                )}
                              </div>
                            )}

                            {/* MRI DETAILS */}
                            {p.detected_type === 'mri' && (
                              <div className="space-y-3">
                                <div className="flex items-center justify-between">
                                  <div className="text-sm text-gray-700"><span className="font-bold">Label:</span> {p.mri_label}</div>
                                  <div className="flex items-center gap-2">
                                    <div className="w-40 bg-indigo-200 rounded-full h-2"><div className="bg-indigo-600 h-2 rounded-full" style={{ width: `${(p.mri_confidence||0)*100}%` }}></div></div>
                                    <span className="text-xs font-semibold text-indigo-700">{(((p.mri_confidence||0)*100).toFixed(1))}%</span>
                                  </div>
                                </div>
                                {p.mri_stats && (
                                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
                                    {Object.entries(p.mri_stats).map(([k,v]) => (
                                      (typeof v==='number' || typeof v==='string') && (
                                        <div key={k} className="p-3 rounded-lg bg-indigo-50 border border-indigo-100">
                                          <div className="text-xs uppercase text-indigo-600 font-bold mb-1">{k.replace(/_/g,' ')}</div>
                                          <div className="text-gray-800 font-semibold">{typeof v==='number'? v : v}</div>
                                        </div>
                                      )
                                    ))}
                                  </div>
                                )}
                                {p.mri_findings && p.mri_findings.length>0 && (
                                  <div>
                                    <div className="text-sm font-bold text-indigo-900 mb-2">Key Findings</div>
                                    <ul className="list-disc pl-5 text-sm text-gray-800 space-y-1">
                                      {p.mri_findings.map((f,idx)=>(<li key={idx}>{f}</li>))}
                                    </ul>
                                  </div>
                                )}
                              </div>
                            )}

                            {/* CT DETAILS */}
                            {p.detected_type === 'ct_scan' && (
                              <div className="space-y-3">
                                <div className="flex items-center justify-between">
                                  <div className="text-sm text-gray-700"><span className="font-bold">Label:</span> {p.ct_label}</div>
                                  <div className="flex items-center gap-2">
                                    <div className="w-40 bg-amber-200 rounded-full h-2"><div className="bg-amber-600 h-2 rounded-full" style={{ width: `${(p.ct_confidence||0)*100}%` }}></div></div>
                                    <span className="text-xs font-semibold text-amber-700">{(((p.ct_confidence||0)*100).toFixed(1))}%</span>
                                  </div>
                                </div>
                                {p.ct_stats && (
                                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
                                    {Object.entries(p.ct_stats).map(([k,v]) => (
                                      (typeof v==='number' || typeof v==='string') && (
                                        <div key={k} className="p-3 rounded-lg bg-amber-50 border border-amber-100">
                                          <div className="text-xs uppercase text-amber-600 font-bold mb-1">{k.replace(/_/g,' ')}</div>
                                          <div className="text-gray-800 font-semibold">{typeof v==='number'? v : v}</div>
                                        </div>
                                      )
                                    ))}
                                  </div>
                                )}
                                {p.ct_findings && p.ct_findings.length>0 && (
                                  <div>
                                    <div className="text-sm font-bold text-amber-900 mb-2">Key Findings</div>
                                    <ul className="list-disc pl-5 text-sm text-gray-800 space-y-1">
                                      {p.ct_findings.map((f,idx)=>(<li key={idx}>{f}</li>))}
                                    </ul>
                                  </div>
                                )}
                              </div>
                            )}

                            {/* LAB DETAILS */}
                            {p.detected_type === 'lab_report' && p.lab_values && (
                              <div className="space-y-3">
                                <div className="flex items-center gap-2">
                                  <div className="text-sm font-bold text-gray-900">Parsed Lab Values</div>
                                  <span className={`text-xs font-bold px-2 py-1 rounded-full ${p.lab_abnormal_count>0 ? 'bg-red-600' : 'bg-emerald-600'} text-white`}>
                                    {p.lab_abnormal_count>0 ? `${p.lab_abnormal_count} Abnormal` : 'All Normal'}
                                  </span>
                                </div>
                                <div className="overflow-x-auto">
                                  <table className="min-w-full bg-white rounded-lg border">
                                    <thead>
                                      <tr className="text-xs uppercase text-gray-600 bg-emerald-100">
                                        <th className="px-3 py-2 text-left">Test</th>
                                        <th className="px-3 py-2 text-left">Value</th>
                                        <th className="px-3 py-2 text-left">Unit</th>
                                        <th className="px-3 py-2 text-left">Reference</th>
                                        <th className="px-3 py-2 text-left">Flag</th>
                                      </tr>
                                    </thead>
                                    <tbody>
                                      {p.lab_values.map((row, idx) => (
                                        <tr key={idx} className="text-sm border-t">
                                          <td className="px-3 py-2 font-medium text-gray-900">{row.test}</td>
                                          <td className="px-3 py-2">{row.value}</td>
                                          <td className="px-3 py-2">{row.unit || '-'}</td>
                                          <td className="px-3 py-2 text-gray-600">{row.ref_low!=null && row.ref_high!=null ? `${row.ref_low} - ${row.ref_high}` : '-'}</td>
                                          <td className="px-3 py-2">
                                            <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${row.flag==='High' ? 'bg-red-100 text-red-700' : row.flag==='Low' ? 'bg-yellow-100 text-yellow-700' : 'bg-emerald-100 text-emerald-700'}`}>
                                              {row.flag}
                                            </span>
                                          </td>
                                        </tr>
                                      ))}
                                    </tbody>
                                  </table>
                                </div>
                              </div>
                            )}

                            {/* PRESCRIPTION DETAILS */}
                            {p.detected_type === 'prescription' && (
                              <div className="space-y-2">
                                <div className="text-sm font-bold text-gray-900">Medicines</div>
                                <div className="grid grid-cols-1 gap-2">
                                  {pairMeds(p.medicines, p.dosages, p.durations).map((m,idx)=> (
                                    <div key={idx} className="p-2 bg-white border rounded">
                                      <div className="font-semibold text-gray-900">{m.name}</div>
                                      <div className="text-xs text-gray-600 mt-1 flex gap-4">
                                        {m.dosage && <span>Dosage: <span className="font-medium text-gray-800">{m.dosage}</span></span>}
                                        {m.duration && <span>Duration: <span className="font-medium text-gray-800">{m.duration}</span></span>}
                                      </div>
                                    </div>
                                  ))}
                                </div>
                                {p.ocr_text && (
                                  <div className="text-xs text-gray-600 mt-2 max-h-40 overflow-y-auto border rounded p-2 bg-gray-50">{p.ocr_text}</div>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
              )}
              {/* Success Message + Type Mismatch Warning */}
              <div className="space-y-3">
                <div className="p-4 bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-200 rounded-xl flex items-start shadow-md">
                  <CheckCircle className="w-6 h-6 text-green-600 mr-3 mt-0.5" />
                  <div>
                    <p className="text-base font-bold text-green-800">✨ Analysis Complete!</p>
                    <p className="text-sm text-green-700 mt-1">{result.diagnosis_summary}</p>
                  </div>
                </div>
                {result.type_mismatch_warning && (
                  <div className="p-4 bg-yellow-50 border-2 border-yellow-300 rounded-xl text-sm text-yellow-900 shadow-sm">
                    <div className="font-bold mb-1">⚠️ Type Mismatch Detected</div>
                    <div className="mb-2">{result.type_mismatch_warning}</div>
                    {result.recommended_type && (
                      <div className="text-xs font-semibold text-yellow-800">Suggested type: {result.recommended_type.toUpperCase()}</div>
                    )}
                  </div>
                )}
              </div>

              {/* OCR Results - Formatted */}
              {result.ocr_text && (
                <div className="bg-blue-50 rounded-xl p-5 border border-blue-200">
                  <div className="flex items-center gap-2 mb-4">
                    <FileText className="w-5 h-5 text-blue-600" />
                    <h3 className="font-bold text-gray-900">📝 Extracted Text (OCR)</h3>
                    <div className="ml-auto flex items-center gap-2">
                      <div className="bg-blue-200 rounded-full h-2 w-24">
                        <div 
                          className="bg-blue-600 h-2 rounded-full" 
                          style={{ width: `${result.ocr_confidence * 100}%` }}
                        ></div>
                      </div>
                      <span className="text-xs font-semibold text-blue-700">
                        {(result.ocr_confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>

                  {result.ocr_text_formatted ? (
                    <div className="p-4 bg-white rounded-lg text-sm text-gray-700 space-y-4 border border-blue-100">
                      {/* Header Section */}
                      {result.ocr_text_formatted.header && (
                        <div>
                          <div className="text-xs font-bold text-blue-600 uppercase tracking-wider mb-1">🏥 Medical Center</div>
                          <div className="text-sm font-medium text-gray-800">{result.ocr_text_formatted.header}</div>
                        </div>
                      )}

                      {/* Patient Info Section */}
                      {result.ocr_text_formatted.patient_info && (
                        <div className="border-t border-gray-200 pt-3">
                          <div className="text-xs font-bold text-purple-600 uppercase tracking-wider mb-1">👤 Patient Information</div>
                          <div className="text-sm text-gray-800">{result.ocr_text_formatted.patient_info}</div>
                        </div>
                      )}

                      {/* Medications Section */}
                      {result.ocr_text_formatted.medications && result.ocr_text_formatted.medications.length > 0 && (
                        <div className="border-t border-gray-200 pt-3">
                          <div className="text-xs font-bold text-green-600 uppercase tracking-wider mb-2">💊 Medications Prescribed</div>
                          <div className="space-y-1.5">
                            {result.ocr_text_formatted.medications.map((med, idx) => (
                              <div key={idx} className="flex items-start gap-2 text-sm">
                                <span className="text-green-600 font-bold mt-0.5">•</span>
                                <span className="text-gray-800 font-medium">{med}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Doctor Info Section */}
                      {result.ocr_text_formatted.doctor_info && (
                        <div className="border-t border-gray-200 pt-3">
                          <div className="text-xs font-bold text-indigo-600 uppercase tracking-wider mb-1">👨‍⚕️ Doctor</div>
                          <div className="text-sm text-gray-800">{result.ocr_text_formatted.doctor_info}</div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="p-3 bg-white rounded-lg text-sm text-gray-700 max-h-40 overflow-y-auto border border-blue-100">
                      {result.ocr_text}
                    </div>
                  )}
                </div>
              )}

              {/* Lab Report Results */}
              {result.lab_values && result.lab_values.length > 0 && (
                <div className="bg-emerald-50 rounded-xl p-5 border border-emerald-200">
                  <div className="flex items-center gap-2 mb-4">
                    <FileText className="w-5 h-5 text-emerald-600" />
                    <h3 className="font-bold text-gray-900">🧪 Parsed Lab Values</h3>
                    {typeof result.lab_abnormal_count === 'number' && (
                      <span className={`ml-auto text-xs font-bold px-3 py-1 rounded-full ${result.lab_abnormal_count>0 ? 'bg-red-600' : 'bg-emerald-600'} text-white`}>
                        {result.lab_abnormal_count>0 ? `${result.lab_abnormal_count} Abnormal` : 'All Normal'}
                      </span>
                    )}
                  </div>
                  <div className="overflow-x-auto">
                    <table className="min-w-full bg-white rounded-lg border">
                      <thead>
                        <tr className="text-xs uppercase text-gray-600 bg-emerald-100">
                          <th className="px-3 py-2 text-left">Test</th>
                          <th className="px-3 py-2 text-left">Value</th>
                          <th className="px-3 py-2 text-left">Unit</th>
                          <th className="px-3 py-2 text-left">Reference</th>
                          <th className="px-3 py-2 text-left">Flag</th>
                        </tr>
                      </thead>
                      <tbody>
                        {result.lab_values.map((row, idx) => (
                          <tr key={idx} className="text-sm border-t">
                            <td className="px-3 py-2 font-medium text-gray-900">{row.test}</td>
                            <td className="px-3 py-2">{row.value}</td>
                            <td className="px-3 py-2">{row.unit || '-'}</td>
                            <td className="px-3 py-2 text-gray-600">{row.ref_low!=null && row.ref_high!=null ? `${row.ref_low} - ${row.ref_high}` : '-'}</td>
                            <td className="px-3 py-2">
                              <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${row.flag==='High' ? 'bg-red-100 text-red-700' : row.flag==='Low' ? 'bg-yellow-100 text-yellow-700' : 'bg-emerald-100 text-emerald-700'}`}>
                                {row.flag}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  {result.lab_critical_flags && result.lab_critical_flags.length>0 && (
                    <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-800">
                      <div className="font-bold mb-1">Critical Alerts</div>
                      <ul className="list-disc pl-5">
                        {result.lab_critical_flags.map((c, idx) => (
                          <li key={idx}>{c}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Medicines */}
              {result.medicines && result.medicines.length > 0 && (
                <div className="bg-green-50 rounded-xl p-5 border border-green-200">
                  <div className="flex items-center gap-2 mb-3">
                    <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                    </svg>
                    <h3 className="font-bold text-gray-900">💊 Identified Medicines</h3>
                  </div>
                  <div className="grid grid-cols-1 gap-2">
                    {pairMeds(result.medicines, result.dosages, result.durations).map((med, idx) => (
                      <div key={idx} className="p-3 bg-white border border-green-200 rounded-lg shadow-sm">
                        <div className="font-semibold text-green-900">{med.name}</div>
                        <div className="text-xs text-gray-700 mt-1 flex gap-4">
                          {med.dosage && <span>Dosage: <span className="font-medium text-gray-900">{med.dosage}</span></span>}
                          {med.duration && <span>Duration: <span className="font-medium text-gray-900">{med.duration}</span></span>}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Imaging Recommendations (CT/MRI/X-ray) */}
              {result.imaging_recommendations && (
                <div className="bg-gradient-to-r from-red-50 to-orange-50 rounded-xl p-5 border-2 border-red-300 shadow-lg">
                  <div className="flex items-center gap-2 mb-4">
                    <AlertCircle className="w-6 h-6 text-red-600" />
                    <h3 className="font-bold text-gray-900 text-lg">🩺 Medical Imaging Recommendations</h3>
                    {result.imaging_recommendations.urgency_level && (
                      <span className={`ml-auto text-xs font-bold px-3 py-1 rounded-full shadow-md ${
                        result.imaging_recommendations.urgency_level === 'HIGH' ? 'bg-red-600 text-white' :
                        result.imaging_recommendations.urgency_level.includes('MODERATE') ? 'bg-orange-500 text-white' :
                        'bg-green-500 text-white'
                      }`}>
                        {result.imaging_recommendations.urgency_level}
                      </span>
                    )}
                  </div>

                  {/* What It Means */}
                  {result.imaging_recommendations.what_it_means && (
                    <div className="bg-blue-50 rounded-lg p-4 border-2 border-blue-200 mb-4">
                      <h4 className="font-bold text-blue-900 mb-2 text-sm flex items-center gap-2">
                        <span>📖</span>
                        <span>What This Finding Means:</span>
                      </h4>
                      <p className="text-sm text-blue-800">{result.imaging_recommendations.what_it_means}</p>
                    </div>
                  )}

                  {/* Specialist Recommendation */}
                  {result.imaging_recommendations.specialist && (
                    <div className="bg-gradient-to-r from-emerald-50 to-teal-50 rounded-lg p-4 border-2 border-emerald-300 mb-4 shadow-md">
                      <h4 className="font-bold text-emerald-900 mb-3 text-base flex items-center gap-2">
                        <span>👨‍⚕️</span>
                        <span>Recommended Specialist:</span>
                      </h4>
                      <div className="space-y-2">
                        <div>
                          <span className="text-sm font-semibold text-emerald-900">Specialist: </span>
                          <span className="text-sm text-emerald-800 font-bold">{result.imaging_recommendations.specialist.name}</span>
                        </div>
                        <div>
                          <span className="text-sm font-semibold text-orange-900">Urgency: </span>
                          <span className="text-sm text-orange-800 font-bold">{result.imaging_recommendations.specialist.urgency}</span>
                        </div>
                        <div>
                          <span className="text-sm font-semibold text-gray-700">Why: </span>
                          <span className="text-sm text-gray-800">{result.imaging_recommendations.specialist.reason}</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Warning Signs - Prominent Display */}
                  {result.imaging_recommendations.warning_signs && result.imaging_recommendations.warning_signs.length > 0 && (
                    <div className="bg-red-100 rounded-lg p-4 border-2 border-red-400 mb-4 shadow-md">
                      <h4 className="font-bold text-red-900 mb-3 text-base flex items-center gap-2">
                        <span>⚠️</span>
                        <span>WARNING SIGNS - Seek Help If:</span>
                      </h4>
                      <ul className="space-y-2">
                        {result.imaging_recommendations.warning_signs.map((sign, idx) => (
                          <li key={idx} className="text-sm text-red-900 flex items-start gap-2 font-medium">
                            <span className="text-red-600 font-bold mt-0.5">⚠️</span>
                            <span>{sign}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Next Steps */}
                  {result.imaging_recommendations.next_steps && result.imaging_recommendations.next_steps.length > 0 && (
                    <div className="bg-purple-50 rounded-lg p-4 border-2 border-purple-200 mb-4">
                      <h4 className="font-bold text-purple-900 mb-3 text-sm flex items-center gap-2">
                        <span>📋</span>
                        <span>Next Steps:</span>
                      </h4>
                      <ul className="space-y-2">
                        {result.imaging_recommendations.next_steps.map((step, idx) => (
                          <li key={idx} className="text-sm text-purple-800 flex items-start gap-2">
                            <span className="text-purple-600 font-bold mt-0.5">•</span>
                            <span>{step}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Lifestyle Recommendations */}
                  {result.imaging_recommendations.recommendations && result.imaging_recommendations.recommendations.length > 0 && (
                    <div className="bg-green-50 rounded-lg p-4 border-2 border-green-200 mb-4">
                      <h4 className="font-bold text-green-900 mb-3 text-sm flex items-center gap-2">
                        <span>💪</span>
                        <span>Lifestyle Recommendations:</span>
                      </h4>
                      <ul className="space-y-2">
                        {result.imaging_recommendations.recommendations.map((rec, idx) => (
                          <li key={idx} className="text-sm text-green-800 flex items-start gap-2">
                            <span className="text-green-600 font-bold mt-0.5">•</span>
                            <span>{rec}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Region Guidance */}
                  {result.imaging_recommendations.region_guidance && (
                    <div className="bg-indigo-50 rounded-lg p-4 border-2 border-indigo-200 mb-3">
                      <h4 className="font-bold text-indigo-900 mb-2 text-sm flex items-center gap-2">
                        <span>🏥</span>
                        <span>Medical Follow-up:</span>
                      </h4>
                      <div className="space-y-1 text-sm text-indigo-800">
                        <p><strong>Recommendation:</strong> {result.imaging_recommendations.region_guidance.general}</p>
                        <p><strong>Follow-up Care:</strong> {result.imaging_recommendations.region_guidance.monitoring}</p>
                      </div>
                    </div>
                  )}

                  {/* Confidence Note */}
                  {result.imaging_recommendations.confidence_note && (
                    <div className="bg-gray-50 rounded-lg p-3 border border-gray-200 mb-3">
                      <p className="text-xs text-gray-700 font-medium">
                        {result.imaging_recommendations.confidence_note}
                      </p>
                    </div>
                  )}

                  {/* Disclaimer */}
                  <div className="p-3 bg-yellow-50 border-2 border-yellow-300 rounded-lg">
                    <p className="text-xs text-yellow-900 font-medium flex items-start gap-2">
                      <span className="text-yellow-600">⚠️</span>
                      <span>{result.imaging_recommendations.disclaimer || 'Imaging interpretation for educational purposes. Radiologist report is definitive.'}</span>
                    </p>
                  </div>
                </div>
              )}

              {/* AI-Assisted Diagnosis Suggestions (NEW!) */}
              {result.diagnosis_suggestions && result.diagnosis_suggestions.possible_conditions && result.diagnosis_suggestions.possible_conditions.length > 0 && (
                <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl p-5 border-2 border-purple-300 shadow-lg">
                  <div className="flex items-center gap-2 mb-4">
                    <Activity className="w-6 h-6 text-purple-600" />
                    <h3 className="font-bold text-gray-900 text-lg">🩺 AI-Assisted Diagnosis Suggestions</h3>
                    <span className="ml-auto text-xs font-bold px-3 py-1 bg-purple-600 text-white rounded-full shadow-md">
                      NEW!
                    </span>
                  </div>

                  {/* Possible Conditions */}
                  <div className="space-y-3 mb-4">
                    {result.diagnosis_suggestions.possible_conditions.slice(0, 3).map((condition, idx) => (
                      <div key={idx} className="bg-white rounded-lg p-4 border-2 border-purple-200 hover:border-purple-400 hover:shadow-md transition-all">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1">
                            <h4 className="font-bold text-purple-900 text-base">
                              {idx + 1}. {condition.condition}
                            </h4>
                            <p className="text-sm text-gray-600 mt-1">
                              <span className="font-medium">Supporting Evidence:</span> {condition.supporting_medicines.join(', ')}
                            </p>
                          </div>
                          <span className={`ml-3 px-3 py-1 rounded-full text-xs font-bold whitespace-nowrap ${
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

                  {/* Recommendations */}
                  {result.diagnosis_suggestions.recommendations && result.diagnosis_suggestions.recommendations.length > 0 && (
                    <div className="bg-blue-50 rounded-lg p-4 border-2 border-blue-200 mb-3">
                      <h4 className="font-bold text-blue-900 mb-3 text-sm flex items-center gap-2">
                        <span>📋</span>
                        <span>Clinical Recommendations:</span>
                      </h4>
                      <ul className="space-y-2">
                        {result.diagnosis_suggestions.recommendations.map((rec, idx) => (
                          <li key={idx} className="text-sm text-blue-800 flex items-start gap-2">
                            <span className="text-blue-600 font-bold mt-0.5">•</span>
                            <span>{rec}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Suggested Specialists */}
                  {result.diagnosis_suggestions.specialists && result.diagnosis_suggestions.specialists.length > 0 && (
                    <div className="bg-emerald-50 rounded-lg p-4 border-2 border-emerald-200 mb-3">
                      <h4 className="font-bold text-emerald-900 mb-3 text-sm flex items-center gap-2">
                        <span>🧑‍⚕️</span>
                        <span>Suggested Specialists:</span>
                      </h4>
                      <div className="space-y-3">
                        {result.diagnosis_suggestions.specialists.map((spec, i) => (
                          <div key={i} className="bg-white rounded-lg p-3 border border-emerald-200">
                            {typeof spec === 'object' ? (
                              <div className="space-y-1">
                                <div className="font-bold text-emerald-900">{spec.specialist}</div>
                                <div className="text-xs text-gray-700">
                                  <strong>Why:</strong> {spec.reason}
                                </div>
                                <div className="text-xs text-orange-700">
                                  <strong>When:</strong> {spec.when_to_schedule}
                                </div>
                                <div className="text-xs text-blue-700">
                                  <strong>For:</strong> {spec.condition}
                                </div>
                              </div>
                            ) : (
                              <span className="text-sm font-bold text-emerald-800">{spec}</span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Disclaimer */}
                  <div className="p-3 bg-yellow-50 border-2 border-yellow-300 rounded-lg">
                    <p className="text-xs text-yellow-900 font-medium flex items-start gap-2">
                      <span className="text-yellow-600">⚠️</span>
                      <span>{result.diagnosis_suggestions.disclaimer || 'AI-suggested diagnosis for reference only. Doctor verification required.'}</span>
                    </p>
                  </div>
                </div>
              )}

              {/* CNN Results */}
              {result.cnn_class && (
                <div className="bg-purple-50 rounded-xl p-5 border border-purple-200">
                  <div className="flex items-center gap-2 mb-3">
                    <ImageIcon className="w-5 h-5 text-purple-600" />
                    <h3 className="font-bold text-gray-900">🔬 AI Image Analysis</h3>
                  </div>
                  <div className="bg-white p-4 rounded-lg border border-purple-100">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-700">Diagnosis:</span>
                      <span className="text-base font-bold text-purple-900">{result.cnn_class}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-gray-700">Confidence:</span>
                      <div className="flex-1 bg-purple-200 rounded-full h-2">
                        <div 
                          className="bg-purple-600 h-2 rounded-full" 
                          style={{ width: `${result.cnn_confidence * 100}%` }}
                        ></div>
                      </div>
                      <span className="text-xs font-semibold text-purple-700">
                        {(result.cnn_confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                    {/* Modality banner */}
                    {result.cnn_image_stats && result.cnn_image_stats.modality && (
                      <div className="mt-3 px-3 py-2 rounded-lg border text-xs font-semibold inline-flex items-center gap-2 
                        bg-indigo-50 border-indigo-200 text-indigo-700">
                        <span>🖼️ Modality:</span>
                        <span>{result.cnn_image_stats.modality}</span>
                        {typeof result.cnn_image_stats.modality_confidence === 'number' && (
                          <span className="ml-2 text-indigo-500">({(result.cnn_image_stats.modality_confidence * 100).toFixed(0)}%)</span>
                        )}
                      </div>
                    )}
                  </div>
                  {/* Probabilities */}
                  {result.cnn_all_probabilities && (
                    <div className="mt-4 bg-white p-4 rounded-lg border border-purple-100">
                      <h4 className="text-sm font-bold text-purple-900 mb-3">Class Probabilities</h4>
                      <div className="space-y-2">
                        {Object.entries(result.cnn_all_probabilities).map(([label, prob]) => (
                          <div key={label} className="flex items-center gap-3 text-sm">
                            <span className="w-28 text-gray-700 font-medium">{label}</span>
                            <div className="flex-1 bg-purple-100 h-2 rounded-full">
                              <div className="bg-purple-500 h-2 rounded-full" style={{ width: `${(prob * 100).toFixed(1)}%` }}></div>
                            </div>
                            <span className="w-12 text-right text-purple-700 font-semibold">{(prob * 100).toFixed(1)}%</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Quality Stats */}
                  {result.cnn_image_stats && (
                    <div className="mt-4 bg-white p-4 rounded-lg border border-purple-100">
                      <h4 className="text-sm font-bold text-purple-900 mb-3">Image Quality & Metrics</h4>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
                        {Object.entries(result.cnn_image_stats).map(([k, v]) => (
                          (typeof v === 'number' || typeof v === 'string') && (
                            <div key={k} className="p-3 rounded-lg bg-purple-50 border border-purple-100">
                              <div className="text-xs uppercase text-purple-600 font-bold mb-1">{k.replace(/_/g, ' ')}</div>
                              <div className="text-gray-800 font-semibold">{typeof v === 'number' ? v : v}</div>
                            </div>
                          )
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Findings */}
                  {result.cnn_findings && result.cnn_findings.length > 0 && (
                    <div className="mt-4 bg-white p-4 rounded-lg border border-purple-100">
                      <h4 className="text-sm font-bold text-purple-900 mb-2">Key Findings</h4>
                      <ul className="list-disc pl-5 text-sm text-gray-800 space-y-1">
                        {result.cnn_findings.map((f, idx) => (
                          <li key={idx}>{f}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* MRI Results */}
              {result.mri_label && (
                <div className="bg-indigo-50 rounded-xl p-5 border border-indigo-200">
                  <div className="flex items-center gap-2 mb-3">
                    <ImageIcon className="w-5 h-5 text-indigo-600" />
                    <h3 className="font-bold text-gray-900">🧠 MRI Analysis</h3>
                    {result.mri_backend && (
                      <span className="ml-auto text-xs font-bold px-2 py-1 rounded-full bg-indigo-600 text-white">
                        {String(result.mri_backend).toUpperCase()}
                      </span>
                    )}
                  </div>
                  <div className="bg-white p-4 rounded-lg border border-indigo-100">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-700">Label:</span>
                      <span className="text-base font-bold text-indigo-900">{result.mri_label}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-gray-700">Confidence:</span>
                      <div className="flex-1 bg-indigo-200 rounded-full h-2">
                        <div
                          className="bg-indigo-600 h-2 rounded-full"
                          style={{ width: `${(result.mri_confidence || 0) * 100}%` }}
                        ></div>
                      </div>
                      <span className="text-xs font-semibold text-indigo-700">
                        {(((result.mri_confidence || 0) * 100).toFixed(1))}%
                      </span>
                    </div>
                    {/* Body region badge */}
                    {result.mri_body_region && (
                      <div className="mt-3 px-3 py-2 rounded-lg border text-xs font-semibold inline-flex items-center gap-2 bg-blue-50 border-blue-200 text-blue-700">
                        <span>🧩 Region:</span>
                        <span>{String(result.mri_body_region)}</span>
                      </div>
                    )}
                  </div>
                  {/* MRI Stats */}
                  {result.mri_stats && (
                    <div className="mt-4 bg-white p-4 rounded-lg border border-indigo-100">
                      <h4 className="text-sm font-bold text-indigo-900 mb-3">MRI Image Metrics</h4>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
                        {Object.entries(result.mri_stats).map(([k, v]) => (
                          (typeof v === 'number' || typeof v === 'string') && (
                            <div key={k} className="p-3 rounded-lg bg-indigo-50 border border-indigo-100">
                              <div className="text-xs uppercase text-indigo-600 font-bold mb-1">{k.replace(/_/g, ' ')}</div>
                              <div className="text-gray-800 font-semibold">{typeof v === 'number' ? v : v}</div>
                            </div>
                          )
                        ))}
                      </div>
                    </div>
                  )}
                  {/* MRI Findings */}
                  {result.mri_findings && result.mri_findings.length > 0 && (
                    <div className="mt-4 bg-white p-4 rounded-lg border border-indigo-100">
                      <h4 className="text-sm font-bold text-indigo-900 mb-2">Key Findings</h4>
                      <ul className="list-disc pl-5 text-sm text-gray-800 space-y-1">
                        {result.mri_findings.map((f, idx) => (
                          <li key={idx}>{f}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* CT Results */}
              {result.ct_label && (
                <div className="bg-amber-50 rounded-xl p-5 border border-amber-200">
                  <div className="flex items-center gap-2 mb-3">
                    <ImageIcon className="w-5 h-5 text-amber-600" />
                    <h3 className="font-bold text-gray-900">🖥️ CT Analysis</h3>
                    {result.ct_backend && (
                      <span className="ml-auto text-xs font-bold px-2 py-1 rounded-full bg-amber-600 text-white">
                        {String(result.ct_backend).toUpperCase()}
                      </span>
                    )}
                  </div>
                  <div className="bg-white p-4 rounded-lg border border-amber-100">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-700">Label:</span>
                      <span className="text-base font-bold text-amber-900">{result.ct_label}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-gray-700">Confidence:</span>
                      <div className="flex-1 bg-amber-200 rounded-full h-2">
                        <div
                          className="bg-amber-600 h-2 rounded-full"
                          style={{ width: `${(result.ct_confidence || 0) * 100}%` }}
                        ></div>
                      </div>
                      <span className="text-xs font-semibold text-amber-700">
                        {(((result.ct_confidence || 0) * 100).toFixed(1))}%
                      </span>
                    </div>
                    {result.ct_body_region && (
                      <div className="mt-3 px-3 py-2 rounded-lg border text-xs font-semibold inline-flex items-center gap-2 bg-yellow-50 border-yellow-200 text-yellow-700">
                        <span>🧩 Region:</span>
                        <span>{String(result.ct_body_region)}</span>
                      </div>
                    )}
                  </div>
                  {result.ct_stats && (
                    <div className="mt-4 bg-white p-4 rounded-lg border border-amber-100">
                      <h4 className="text-sm font-bold text-amber-900 mb-3">CT Image Metrics</h4>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
                        {Object.entries(result.ct_stats).map(([k, v]) => (
                          (typeof v === 'number' || typeof v === 'string') && (
                            <div key={k} className="p-3 rounded-lg bg-amber-50 border border-amber-100">
                              <div className="text-xs uppercase text-amber-600 font-bold mb-1">{k.replace(/_/g, ' ')}</div>
                              <div className="text-gray-800 font-semibold">{typeof v === 'number' ? v : v}</div>
                            </div>
                          )
                        ))}
                      </div>
                    </div>
                  )}
                  {result.ct_findings && result.ct_findings.length > 0 && (
                    <div className="mt-4 bg-white p-4 rounded-lg border border-amber-100">
                      <h4 className="text-sm font-bold text-amber-900 mb-2">Key Findings</h4>
                      <ul className="list-disc pl-5 text-sm text-gray-800 space-y-1">
                        {result.ct_findings.map((f, idx) => (
                          <li key={idx}>{f}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Heatmap */}
              {result.heatmap_url && (
                <div className="bg-orange-50 rounded-xl p-5 border border-orange-200">
                  <div className="flex items-center gap-2 mb-3">
                    <Activity className="w-5 h-5 text-orange-600" />
                    <h3 className="font-bold text-gray-900">🔥 Explainability Heatmap</h3>
                  </div>
                  <img
                    src={result.heatmap_url}
                    alt="Grad-CAM Heatmap"
                    className="w-full rounded-lg border-2 border-orange-200 shadow-md"
                  />
                  <p className="text-xs text-orange-700 mt-2">
                    Red areas show where the AI focused its attention during analysis
                  </p>
                </div>
              )}
            </div>
          )}

          {!preview && !result && (
            <div className="flex items-center justify-center h-96 bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl border-2 border-dashed border-gray-300">
              <div className="text-center">
                <ImageIcon className="w-20 h-20 mx-auto mb-4 text-gray-300" />
                <p className="text-gray-500 font-medium">Upload a file to see preview</p>
                <p className="text-sm text-gray-400 mt-1">Supported: PNG, JPG</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Upload;

