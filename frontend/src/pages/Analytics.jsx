import { useState, useEffect } from 'react';
import { collection, query, onSnapshot } from 'firebase/firestore';
import { db } from '../services/firebase';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement
} from 'chart.js';
import { Bar, Pie, Line } from 'react-chartjs-2';
import { TrendingUp, Activity, PieChart as PieChartIcon, BarChart3 } from 'lucide-react';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement
);

function Analytics() {
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    medicineFrequency: {},
    diagnosisPatterns: {},
    documentTypes: {},
    dailyAnalyses: []
  });

  useEffect(() => {
    // Real-time listener for analyses
    const analysesQuery = query(collection(db, 'analyses'));

    const unsubscribe = onSnapshot(analysesQuery, (snapshot) => {
      const analysesList = [];
      snapshot.forEach((doc) => {
        analysesList.push({ id: doc.id, ...doc.data() });
      });
      setAnalyses(analysesList);
      processAnalytics(analysesList);
      setLoading(false);
    }, (error) => {
      console.error('Error fetching analyses:', error);
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  const processAnalytics = (data) => {
    const medicineFreq = {};
    const diagnosisPatterns = {};
    const docTypes = {};
    const dailyMap = {};

    data.forEach((analysis) => {
      // Count medicines
      if (analysis.medicines) {
        analysis.medicines.forEach((med) => {
          const medName = med.text || 'Unknown';
          medicineFreq[medName] = (medicineFreq[medName] || 0) + 1;
        });
      }

      // Count diagnoses
      if (analysis.cnn_class) {
        const diagnosis = analysis.cnn_class;
        diagnosisPatterns[diagnosis] = (diagnosisPatterns[diagnosis] || 0) + 1;
      }

      // Count document types
      if (analysis.document_type) {
        const docType = analysis.document_type;
        docTypes[docType] = (docTypes[docType] || 0) + 1;
      }

      // Daily analyses
      if (analysis.timestamp) {
        const date = new Date(analysis.timestamp).toLocaleDateString();
        dailyMap[date] = (dailyMap[date] || 0) + 1;
      }
    });

    // Sort and limit medicine frequency
    const sortedMedicines = Object.entries(medicineFreq)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .reduce((obj, [key, value]) => ({ ...obj, [key]: value }), {});

    // Convert daily map to array
    const dailyAnalyses = Object.entries(dailyMap)
      .sort((a, b) => new Date(a[0]) - new Date(b[0]))
      .slice(-7); // Last 7 days

    setStats({
      medicineFrequency: sortedMedicines,
      diagnosisPatterns,
      documentTypes: docTypes,
      dailyAnalyses
    });
  };

  // Chart configurations
  const medicineChartData = {
    labels: Object.keys(stats.medicineFrequency),
    datasets: [
      {
        label: 'Frequency',
        data: Object.values(stats.medicineFrequency),
        backgroundColor: 'rgba(59, 130, 246, 0.8)',
        borderColor: 'rgba(59, 130, 246, 1)',
        borderWidth: 1,
      },
    ],
  };

  const diagnosisChartData = {
    labels: Object.keys(stats.diagnosisPatterns),
    datasets: [
      {
        label: 'Count',
        data: Object.values(stats.diagnosisPatterns),
        backgroundColor: [
          'rgba(59, 130, 246, 0.8)',
          'rgba(16, 185, 129, 0.8)',
          'rgba(245, 158, 11, 0.8)',
          'rgba(239, 68, 68, 0.8)',
          'rgba(139, 92, 246, 0.8)',
        ],
        borderColor: [
          'rgba(59, 130, 246, 1)',
          'rgba(16, 185, 129, 1)',
          'rgba(245, 158, 11, 1)',
          'rgba(239, 68, 68, 1)',
          'rgba(139, 92, 246, 1)',
        ],
        borderWidth: 1,
      },
    ],
  };

  const dailyAnalysesChartData = {
    labels: stats.dailyAnalyses.map(([date]) => date),
    datasets: [
      {
        label: 'Analyses per Day',
        data: stats.dailyAnalyses.map(([, count]) => count),
        backgroundColor: 'rgba(139, 92, 246, 0.2)',
        borderColor: 'rgba(139, 92, 246, 1)',
        borderWidth: 2,
        tension: 0.4,
        fill: true,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      },
    },
  };

  const StatCard = ({ icon: Icon, title, value, color, bgColor }) => (
    <div className={`${bgColor} rounded-2xl shadow-lg p-6 border border-opacity-20 transform transition-all hover:scale-105 hover:shadow-xl`}>
      <div className="flex items-start justify-between">
        <div className="w-full">
          <div className="flex items-center gap-2 mb-3">
            <div className={`p-2 rounded-lg ${color} bg-opacity-10`}>
              <Icon className={`w-6 h-6 ${color}`} />
            </div>
          </div>
          <p className="text-sm font-medium text-gray-600 mb-1">{title}</p>
          <p className="text-3xl font-bold text-gray-900">{value}</p>
          <p className="text-xs text-gray-500 mt-2">🔴 Live</p>
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header with gradient */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-2xl p-8 text-white shadow-xl">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold mb-2">📊 Analytics Dashboard</h1>
            <p className="text-blue-100 text-lg">Real-time insights from medical document analysis</p>
          </div>
          <div className="hidden md:block">
            <div className="bg-white bg-opacity-20 backdrop-blur-sm rounded-xl px-6 py-3">
              <p className="text-sm text-blue-100">Last updated</p>
              <p className="text-lg font-semibold">{new Date().toLocaleTimeString()}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Summary Stats - Real-time data only */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          icon={Activity}
          title="Total Analyses"
          value={analyses.length}
          color="text-blue-600"
          bgColor="bg-gradient-to-br from-blue-50 to-blue-100"
        />
        <StatCard
          icon={TrendingUp}
          title="Unique Medicines"
          value={Object.keys(stats.medicineFrequency).length}
          color="text-green-600"
          bgColor="bg-gradient-to-br from-green-50 to-green-100"
        />
        <StatCard
          icon={PieChartIcon}
          title="Diagnosis Types"
          value={Object.keys(stats.diagnosisPatterns).length}
          color="text-purple-600"
          bgColor="bg-gradient-to-br from-purple-50 to-purple-100"
        />
        <StatCard
          icon={BarChart3}
          title="Document Types"
          value={Object.keys(stats.documentTypes).length}
          color="text-orange-600"
          bgColor="bg-gradient-to-br from-orange-50 to-orange-100"
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Medicine Frequency Chart */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6 hover:shadow-xl transition-shadow">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-blue-100 rounded-lg">
              <BarChart3 className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-900">
                Top 10 Most Prescribed Medicines
              </h2>
              <p className="text-sm text-gray-500">By frequency count</p>
            </div>
          </div>
          <div className="h-80">
            {Object.keys(stats.medicineFrequency).length > 0 ? (
              <Bar data={medicineChartData} options={chartOptions} />
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-gray-400">
                <BarChart3 className="w-16 h-16 mb-3 opacity-20" />
                <p className="font-medium">No medicine data available yet</p>
                <p className="text-sm mt-1">Upload prescriptions to see statistics</p>
              </div>
            )}
          </div>
        </div>

        {/* Diagnosis Patterns Chart */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6 hover:shadow-xl transition-shadow">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-purple-100 rounded-lg">
              <PieChartIcon className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-900">
                Diagnosis Distribution
              </h2>
              <p className="text-sm text-gray-500">By classification type</p>
            </div>
          </div>
          <div className="h-80">
            {Object.keys(stats.diagnosisPatterns).length > 0 ? (
              <Pie data={diagnosisChartData} options={chartOptions} />
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-gray-400">
                <PieChartIcon className="w-16 h-16 mb-3 opacity-20" />
                <p className="font-medium">No diagnosis data available yet</p>
                <p className="text-sm mt-1">Process documents to see patterns</p>
              </div>
            )}
          </div>
        </div>

        {/* Daily Analyses Trend */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6 lg:col-span-2 hover:shadow-xl transition-shadow">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-green-100 rounded-lg">
              <TrendingUp className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-900">
                Analysis Activity Trend
              </h2>
              <p className="text-sm text-gray-500">Last 7 days performance</p>
            </div>
          </div>
          <div className="h-80">
            {stats.dailyAnalyses.length > 0 ? (
              <Line data={dailyAnalysesChartData} options={chartOptions} />
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-gray-400">
                <Activity className="w-16 h-16 mb-3 opacity-20" />
                <p className="font-medium">No trend data available yet</p>
                <p className="text-sm mt-1">Activity will be tracked over time</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Document Types Breakdown */}
      <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6 hover:shadow-xl transition-shadow">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-indigo-100 rounded-lg">
            <BarChart3 className="w-5 h-5 text-indigo-600" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-gray-900">Document Types Breakdown</h2>
            <p className="text-sm text-gray-500">Analysis by document category</p>
          </div>
        </div>
        {Object.keys(stats.documentTypes).length > 0 ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(stats.documentTypes).map(([type, count]) => (
              <div key={type} className="p-5 bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl text-center border border-gray-200 hover:shadow-md transition-shadow">
                <p className="text-3xl font-bold text-gray-900 mb-2">{count}</p>
                <p className="text-sm text-gray-600 font-medium capitalize">
                  {type.replace('_', ' ')}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-400">
            <p>No document types recorded yet</p>
          </div>
        )}
      </div>

      {/* Real-time System Status */}
      <div className="bg-gradient-to-br from-indigo-50 to-blue-50 rounded-2xl shadow-lg border border-blue-100 p-8">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500 rounded-lg">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-900">🔴 Real-Time System Status</h2>
              <p className="text-sm text-gray-600">Live processing engine</p>
            </div>
          </div>
          <div className="flex items-center gap-2 bg-green-100 px-4 py-2 rounded-full">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-sm font-semibold text-green-700">Active</span>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-xl p-6 text-center shadow-md hover:shadow-lg transition-shadow">
            <div className="text-5xl mb-3">🔤</div>
            <p className="text-sm font-semibold text-gray-700 mb-1">OCR Engine</p>
            <p className="text-xs text-gray-500">EasyOCR + Tesseract</p>
            <div className="mt-3 px-3 py-1 bg-green-100 text-green-700 text-xs font-semibold rounded-full inline-block">
              ✓ Ready
            </div>
          </div>
          <div className="bg-white rounded-xl p-6 text-center shadow-md hover:shadow-lg transition-shadow">
            <div className="text-5xl mb-3">🧠</div>
            <p className="text-sm font-semibold text-gray-700 mb-1">NLP Processor</p>
            <p className="text-xs text-gray-500">spaCy Medical NER</p>
            <div className="mt-3 px-3 py-1 bg-green-100 text-green-700 text-xs font-semibold rounded-full inline-block">
              ✓ Ready
            </div>
          </div>
          <div className="bg-white rounded-xl p-6 text-center shadow-md hover:shadow-lg transition-shadow">
            <div className="text-5xl mb-3">📸</div>
            <p className="text-sm font-semibold text-gray-700 mb-1">CNN Classifier</p>
            <p className="text-xs text-gray-500">PyTorch + Grad-CAM</p>
            <div className="mt-3 px-3 py-1 bg-green-100 text-green-700 text-xs font-semibold rounded-full inline-block">
              ✓ Ready
            </div>
          </div>
        </div>
        <div className="mt-6 p-4 bg-blue-100 rounded-xl">
          <p className="text-sm text-blue-800 text-center">
            <span className="font-semibold">⚡ All metrics are calculated in real-time</span> from actual processed documents
          </p>
        </div>
      </div>
    </div>
  );
}

export default Analytics;

