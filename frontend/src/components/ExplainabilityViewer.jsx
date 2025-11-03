import React, { useState, useEffect } from 'react';
import { Loader2, Info, AlertCircle } from 'lucide-react';

const ExplainabilityViewer = ({ analysisData, analysisId }) => {
  const [activeTab, setActiveTab] = useState('gradcam');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [shapData, setShapData] = useState(null);
  const [limeData, setLimeData] = useState(null);

  // Extract explainability data from analysis
  const gradcamUrl = analysisData?.heatmap_url || analysisData?.explainability?.gradcam_url;
  const shapUrl = analysisData?.shap_visualization || analysisData?.explainability?.shap_url;
  const limeUrl = analysisData?.lime_visualization_positive || analysisData?.explainability?.lime_url;

  const hasGradcam = !!gradcamUrl;
  const hasShap = analysisData?.explainability?.shap_supported || !!shapUrl;
  const hasLime = analysisData?.explainability?.lime_supported || !!limeUrl;

  const generateExplainability = async (type) => {
    if (!analysisId) return;
    
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'https://mediai-t6oo.onrender.com'}/api/explainability/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          analysis_id: analysisId,
          type: type,
          user_id: 'user_001' // TODO: Get from auth context
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate explainability');
      }

      const data = await response.json();
      
      if (type === 'shap' || type === 'all') {
        setShapData(data.shap);
      }
      if (type === 'lime' || type === 'all') {
        setLimeData(data.lime);
      }

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const ExplanationInfo = ({ method }) => {
    const info = {
      gradcam: {
        title: 'Grad-CAM (Gradient-weighted Class Activation Mapping)',
        description: 'Highlights the regions in the image that were most important for the AI\'s prediction. Warmer colors (red/yellow) indicate higher importance.',
        best: 'Fast and efficient, good for quick interpretation'
      },
      shap: {
        title: 'SHAP (SHapley Additive exPlanations)',
        description: 'Provides a game-theory based explanation showing which features contributed to the prediction and by how much.',
        best: 'More thorough analysis with quantified feature importance'
      },
      lime: {
        title: 'LIME (Local Interpretable Model-agnostic Explanations)',
        description: 'Creates an interpretable model locally around the prediction, highlighting superpixels that contributed most.',
        best: 'Model-agnostic and easy to interpret visually'
      }
    };

    const current = info[method];

    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
        <div className="flex items-start gap-2">
          <Info className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
          <div>
            <h4 className="font-semibold text-blue-900 mb-1">{current.title}</h4>
            <p className="text-sm text-blue-800 mb-2">{current.description}</p>
            <p className="text-xs text-blue-700 font-medium">✓ Best for: {current.best}</p>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-4">
        🔍 AI Explainability
      </h2>

      {/* Tab Navigation */}
      <div className="flex gap-2 mb-6 border-b border-gray-200">
        {hasGradcam && (
          <button
            onClick={() => setActiveTab('gradcam')}
            className={`px-4 py-2 font-medium transition-colors ${
              activeTab === 'gradcam'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Grad-CAM
          </button>
        )}
        {hasShap && (
          <button
            onClick={() => setActiveTab('shap')}
            className={`px-4 py-2 font-medium transition-colors ${
              activeTab === 'shap'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            SHAP
          </button>
        )}
        {hasLime && (
          <button
            onClick={() => setActiveTab('lime')}
            className={`px-4 py-2 font-medium transition-colors ${
              activeTab === 'lime'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            LIME
          </button>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4 flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-red-600" />
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {/* Grad-CAM Tab */}
      {activeTab === 'gradcam' && (
        <div>
          <ExplanationInfo method="gradcam" />
          {gradcamUrl ? (
            <img
              src={gradcamUrl}
              alt="Grad-CAM Heatmap"
              className="w-full rounded-lg shadow-md"
            />
          ) : (
            <div className="text-center py-12 bg-gray-50 rounded-lg">
              <p className="text-gray-600">No Grad-CAM visualization available</p>
            </div>
          )}
        </div>
      )}

      {/* SHAP Tab */}
      {activeTab === 'shap' && (
        <div>
          <ExplanationInfo method="shap" />
          
          {shapUrl || shapData ? (
            <div>
              <img
                src={shapUrl || shapData?.visualization}
                alt="SHAP Explanation"
                className="w-full rounded-lg shadow-md mb-4"
              />
              
              {/* SHAP Importance Scores */}
              {(analysisData?.shap_importance || shapData?.importance_scores) && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-semibold text-gray-900 mb-3">Regional Importance</h4>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    {Object.entries(analysisData?.shap_importance || shapData?.importance_scores).map(([region, score]) => (
                      <div key={region} className="bg-white rounded p-3 border border-gray-200">
                        <div className="text-xs text-gray-600 mb-1 capitalize">
                          {region.replace('_', ' ')}
                        </div>
                        <div className="text-lg font-bold text-blue-600">
                          {score.toFixed(1)}%
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-12 bg-gray-50 rounded-lg">
              <p className="text-gray-600 mb-4">SHAP visualization not yet generated</p>
              <button
                onClick={() => generateExplainability('shap')}
                disabled={loading}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2 mx-auto"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  'Generate SHAP Explanation'
                )}
              </button>
            </div>
          )}
        </div>
      )}

      {/* LIME Tab */}
      {activeTab === 'lime' && (
        <div>
          <ExplanationInfo method="lime" />
          
          {limeUrl || limeData ? (
            <div className="space-y-4">
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">Positive Features</h4>
                <img
                  src={limeUrl || limeData?.visualization_positive}
                  alt="LIME Positive Features"
                  className="w-full rounded-lg shadow-md"
                />
              </div>
              
              {(analysisData?.lime_visualization_both || limeData?.visualization_both) && (
                <div>
                  <h4 className="font-semibold text-gray-900 mb-2">All Features</h4>
                  <img
                    src={analysisData.lime_visualization_both || limeData.visualization_both}
                    alt="LIME All Features"
                    className="w-full rounded-lg shadow-md"
                  />
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-12 bg-gray-50 rounded-lg">
              <p className="text-gray-600 mb-4">LIME visualization not yet generated</p>
              <button
                onClick={() => generateExplainability('lime')}
                disabled={loading}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2 mx-auto"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  'Generate LIME Explanation'
                )}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ExplainabilityViewer;

