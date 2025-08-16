"use client";
import { useState } from 'react';
import axios from 'axios';

interface HealthMarker {
  name: string;
  value: number;
  unit: string;
  normalRange: string;
  status: string;
  recommendation: string;
}

export default function ManualEntry() {
  const [text, setText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<{
    extractedText: string;
    markers: HealthMarker[];
    textLength: number;
    markersFound: number;
  } | null>(null);
  const [error, setError] = useState('');

  const handleTestText = async () => {
    if (!text.trim()) {
      setError('Please enter some text to test');
      return;
    }

    setIsLoading(true);
    setError('');
    setResults(null);

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/reports/debug-text`,
        { text: text.trim() },
        {
          headers: {
            'Content-Type': 'application/json',
            ...(token && { Authorization: `Bearer ${token}` }),
          },
        }
      );

      setResults(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to process text');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveToReports = async () => {
    if (!results?.markers || results.markers.length === 0) {
      setError('No markers detected to save');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const token = localStorage.getItem('token');
      
      // Create FormData for multipart/form-data
      const formData = new FormData();
      formData.append('filename', 'Manual Entry');
      formData.append('text_content', text);
      
      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/reports/upload`,
        formData,
        {
          headers: {
            ...(token && { Authorization: `Bearer ${token}` }),
          },
        }
      );

      alert('Health markers saved successfully! You can now ask questions about them in the AI Chat tab.');
      setText('');
      setResults(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save markers');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-sm font-medium text-blue-800 mb-2">How to use Manual Entry</h3>
        <p className="text-sm text-blue-700">
          If OCR doesn't work with your lab report image, you can manually enter your health markers here. 
          Simply paste the text from your lab report or type your markers in a format like:
        </p>
        <div className="mt-2 text-sm text-blue-600 font-mono bg-blue-100 p-2 rounded">
          FERRITIN: 22 ng/mL (Low)<br/>
          Normal Range: 38-380 ng/mL<br/>
          GLUCOSE: 95 mg/dL<br/>
          Normal Range: 70-100 mg/dL
        </div>
      </div>

      <div>
        <label htmlFor="text-input" className="block text-sm font-medium text-gray-700 mb-2">
          Enter your lab report text or health markers:
        </label>
        <textarea
          id="text-input"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Paste your lab report text here or enter markers manually..."
          className="w-full h-32 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
        />
      </div>

      <div className="flex space-x-4">
        <button
          onClick={handleTestText}
          disabled={isLoading || !text.trim()}
          className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Processing...' : 'Test Text'}
        </button>
        
        {results?.markers && results.markers.length > 0 && (
          <button
            onClick={handleSaveToReports}
            disabled={isLoading}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Saving...' : 'Save to Reports'}
          </button>
        )}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {results && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Results:</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <p className="text-sm font-medium text-gray-700">Extracted Text:</p>
              <p className="text-sm text-gray-600 mt-1">{results.extractedText}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-700">Text Length:</p>
              <p className="text-sm text-gray-600 mt-1">{results.textLength}</p>
            </div>
          </div>

          <div className="mb-4">
            <p className="text-sm font-medium text-gray-700">Markers Found: {results.markersFound}</p>
          </div>

          {results.markers.length > 0 && (
            <div>
              <h4 className="text-md font-medium text-gray-900 mb-2">Detected Markers:</h4>
              <div className="space-y-2">
                {results.markers.map((marker, index) => (
                  <div key={index} className="bg-white border border-gray-200 rounded-lg p-3">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-medium text-gray-900">{marker.name}</p>
                        <p className="text-sm text-gray-600">
                          {marker.value} {marker.unit}
                        </p>
                        <p className="text-sm text-gray-500">
                          Normal Range: {marker.normalRange}
                        </p>
                      </div>
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                        marker.status === 'normal' 
                          ? 'bg-green-100 text-green-800'
                          : marker.status === 'low'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {marker.status.toUpperCase()}
                      </span>
                    </div>
                    {marker.recommendation && (
                      <p className="text-sm text-gray-700 mt-2">{marker.recommendation}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
