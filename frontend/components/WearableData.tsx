'use client';

import { useState, useEffect } from 'react';

interface WearableDataProps {
  onDataUpdate: () => void;
}

interface WearableSummary {
  steps: {
    latest: number;
    average: number;
  };
  heart_rate: {
    latest: number;
    average: number;
  };
  sleep: {
    latest: number;
    average: number;
  };
}

export default function WearableData({ onDataUpdate }: WearableDataProps) {
  const [summary, setSummary] = useState<WearableSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [formData, setFormData] = useState({
    steps: '',
    heart_rate: '',
    sleep: '',
    date: new Date().toISOString().split('T')[0]
  });

  useEffect(() => {
    fetchSummary();
  }, []);

  const fetchSummary = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'}/wearable/summary`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setSummary(data);
      }
    } catch (error) {
      console.error('Error fetching wearable summary:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'}/wearable/add`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          steps: parseInt(formData.steps) || 0,
          heart_rate: parseInt(formData.heart_rate) || 0,
          sleep_hours: parseFloat(formData.sleep) || 0,
          date: formData.date
        }),
      });

      if (response.ok) {
        setShowAddForm(false);
        setFormData({
          steps: '',
          heart_rate: '',
          sleep: '',
          date: new Date().toISOString().split('T')[0]
        });
        fetchSummary();
        onDataUpdate();
      } else {
        const errorData = await response.json();
        alert(`Error: ${errorData.detail || 'Failed to add data'}`);
      }
    } catch (error) {
      console.error('Error adding wearable data:', error);
      alert('Error adding wearable data');
    }
  };

  if (loading) {
    return <div className="text-center py-8">Loading wearable data...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">Wearable Device Data</h2>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          {showAddForm ? 'Cancel' : 'Add Data'}
        </button>
      </div>

      {showAddForm && (
        <form onSubmit={handleSubmit} className="bg-gray-50 p-6 rounded-lg space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Steps
              </label>
              <input
                type="number"
                value={formData.steps}
                onChange={(e) => setFormData({ ...formData, steps: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., 8500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Heart Rate (bpm)
              </label>
              <input
                type="number"
                value={formData.heart_rate}
                onChange={(e) => setFormData({ ...formData, heart_rate: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., 72"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Sleep Hours
              </label>
              <input
                type="number"
                step="0.1"
                value={formData.sleep}
                onChange={(e) => setFormData({ ...formData, sleep: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., 7.5"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Date
              </label>
              <input
                type="date"
                value={formData.date}
                onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          <button
            type="submit"
            className="w-full bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 transition-colors"
          >
            Add Data
          </button>
        </form>
      )}

      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h3 className="text-lg font-medium text-gray-900 mb-2">Daily Steps</h3>
            <div className="text-3xl font-bold text-blue-600">{summary.steps.latest.toLocaleString()}</div>
            <p className="text-sm text-gray-500 mt-1">
              Avg: {summary.steps.average.toLocaleString()}
            </p>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h3 className="text-lg font-medium text-gray-900 mb-2">Heart Rate</h3>
            <div className="text-3xl font-bold text-red-600">{summary.heart_rate.latest} bpm</div>
            <p className="text-sm text-gray-500 mt-1">
              Avg: {summary.heart_rate.average} bpm
            </p>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h3 className="text-lg font-medium text-gray-900 mb-2">Sleep</h3>
            <div className="text-3xl font-bold text-purple-600">{summary.sleep.latest}h</div>
            <p className="text-sm text-gray-500 mt-1">
              Avg: {summary.sleep.average}h
            </p>
          </div>
        </div>
      )}

      {!summary && (
        <div className="text-center py-8 text-gray-500">
          No wearable data available. Add some data to get started!
        </div>
      )}
    </div>
  );
}

