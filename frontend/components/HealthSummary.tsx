"use client";
import { useState, useEffect } from 'react';
import axios from 'axios';

export default function HealthSummary() {
  const [summary, setSummary] = useState<any>({});
  const [recentReports, setRecentReports] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchSummary();
  }, []);

  const fetchSummary = async () => {
    try {
      const token = localStorage.getItem('token');
      
      // Fetch wearable summary
      const wearableResponse = await axios.get(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/wearable/data/summary`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      // Fetch recent reports
      const reportsResponse = await axios.get(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/reports/reports`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      setSummary(wearableResponse.data);
      setRecentReports(reportsResponse.data.slice(0, 3)); // Get last 3 reports
    } catch (error) {
      console.error('Error fetching summary:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white border border-gray-200 rounded-lg p-4 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
            <div className="h-6 bg-gray-200 rounded w-1/2"></div>
          </div>
        ))}
      </div>
    );
  }

  const getHealthScore = () => {
    let score = 100;
    let factors = [];

    // Check wearable data - only if it exists and has valid values
    if (summary.steps && summary.steps.latest && summary.steps.latest > 0) {
      if (summary.steps.latest < 8000) {
        score -= 10;
        factors.push('Low step count');
      }
    }
    if (summary.heart_rate && summary.heart_rate.latest && summary.heart_rate.latest > 0) {
      if (summary.heart_rate.latest < 60 || summary.heart_rate.latest > 100) {
        score -= 15;
        factors.push('Heart rate outside normal range');
      }
    }
    if (summary.sleep && summary.sleep.latest && summary.sleep.latest > 0) {
      if (summary.sleep.latest < 7) {
        score -= 15;
        factors.push('Insufficient sleep');
      }
    }

    // Check recent reports for abnormal markers
    recentReports.forEach(report => {
      if (report.flagged_markers && Object.keys(report.flagged_markers).length > 0) {
        score -= 20;
        factors.push(`${Object.keys(report.flagged_markers).length} abnormal lab markers`);
      }
    });

    return { score: Math.max(0, score), factors };
  };

  const healthScore = getHealthScore();
  
  // Check if user has actual wearable data (not just empty objects)
  const hasWearableData = (summary.steps && summary.steps.latest && summary.steps.latest > 0) || 
                         (summary.heart_rate && summary.heart_rate.latest && summary.heart_rate.latest > 0) || 
                         (summary.sleep && summary.sleep.latest && summary.sleep.latest > 0);
  
  // Check if user has uploaded reports
  const hasReports = recentReports.length > 0;

  // Debug logging
  console.log('Summary data:', summary);
  console.log('Summary steps:', summary.steps);
  console.log('Summary heart_rate:', summary.heart_rate);
  console.log('Summary sleep:', summary.sleep);
  console.log('Has wearable data:', hasWearableData);
  console.log('Has reports:', hasReports);
  console.log('Health score:', healthScore);

  return (
    <div className="space-y-6">
      {/* Health Score - Only show if user has wearable data */}
      {hasWearableData && (
        <div className="bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-medium text-gray-900">Health Score</h3>
              <p className="text-sm text-gray-600">Based on your wearable data</p>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold text-green-600">{healthScore.score}/100</div>
              <div className="text-sm text-gray-500">
                {healthScore.score >= 80 ? 'Excellent' : 
                 healthScore.score >= 60 ? 'Good' : 
                 healthScore.score >= 40 ? 'Fair' : 'Needs Attention'}
              </div>
            </div>
          </div>
          {healthScore.factors.length > 0 && (
            <div className="mt-4">
              <p className="text-sm font-medium text-gray-700 mb-2">Areas for improvement:</p>
              <ul className="text-sm text-gray-600 space-y-1">
                {healthScore.factors.map((factor, index) => (
                  <li key={index} className="flex items-center">
                    <span className="text-red-500 mr-2">•</span>
                    {factor}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Areas for improvement - Only show if user has reports with abnormal markers */}
      {hasReports && healthScore.factors.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h3 className="text-lg font-medium text-gray-900 mb-3">Areas for improvement:</h3>
          <ul className="text-sm text-gray-600 space-y-1">
            {healthScore.factors.map((factor, index) => (
              <li key={index} className="flex items-center">
                <span className="text-red-500 mr-2">•</span>
                {factor}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Quick Stats - Only show if user has wearable data */}
      {hasWearableData && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Steps */}
          {summary.steps && summary.steps.latest && summary.steps.latest > 0 && (
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">Daily Steps</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {summary.steps.latest.toLocaleString()}
                  </p>
                </div>
                <div className="text-2xl">👟</div>
              </div>
              <div className="mt-2">
                <div className="flex items-center">
                  <div className="flex-1 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-green-500 h-2 rounded-full"
                      style={{ width: `${Math.min((summary.steps.latest / 10000) * 100, 100)}%` }}
                    ></div>
                  </div>
                  <span className="ml-2 text-xs text-gray-500">
                    {Math.round((summary.steps.latest / 10000) * 100)}%
                  </span>
                </div>
                <p className="text-xs text-gray-500 mt-1">Goal: 10,000 steps</p>
              </div>
            </div>
          )}

          {/* Heart Rate */}
          {summary.heart_rate && summary.heart_rate.latest && summary.heart_rate.latest > 0 && (
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">Heart Rate</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {summary.heart_rate.latest} {summary.heart_rate.unit}
                  </p>
                </div>
                <div className="text-2xl">❤️</div>
              </div>
              <div className="mt-2">
                <span className={`text-xs px-2 py-1 rounded-full ${
                  summary.heart_rate.latest >= 60 && summary.heart_rate.latest <= 100
                    ? 'bg-green-100 text-green-800'
                    : 'bg-yellow-100 text-yellow-800'
                }`}>
                  {summary.heart_rate.latest >= 60 && summary.heart_rate.latest <= 100 ? 'Normal' : 'Check'}
                </span>
              </div>
            </div>
          )}

          {/* Sleep */}
          {summary.sleep && summary.sleep.latest && summary.sleep.latest > 0 && (
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">Sleep</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {summary.sleep.latest} {summary.sleep.unit}
                  </p>
                </div>
                <div className="text-2xl">😴</div>
              </div>
              <div className="mt-2">
                <span className={`text-xs px-2 py-1 rounded-full ${
                  summary.sleep.latest >= 7
                    ? 'bg-green-100 text-green-800'
                    : 'bg-yellow-100 text-yellow-800'
                }`}>
                  {summary.sleep.latest >= 7 ? 'Good' : 'Short'}
                </span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Recent Reports - Only show if user has uploaded reports */}
      {hasReports && (
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Recent Reports</p>
              <p className="text-2xl font-bold text-gray-900">{recentReports.length}</p>
            </div>
            <div className="text-2xl">📄</div>
          </div>
          <div className="mt-2">
            <div className="text-xs text-gray-500">
              {recentReports.filter(r => r.flagged_markers && Object.keys(r.flagged_markers).length > 0).length} with abnormal markers
            </div>
          </div>
        </div>
      )}

      {/* Empty state when no data */}
      {!hasWearableData && !hasReports && (
        <div className="bg-white border border-gray-200 rounded-lg p-8 text-center">
          <div className="text-4xl mb-4">📊</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Health Data Available</h3>
          <p className="text-gray-600 mb-4">
            Upload your lab reports or add wearable device data to see your health summary.
          </p>
          <div className="space-y-2 text-sm text-gray-500">
            <p>• Use the "Upload Reports" tab to add lab results</p>
            <p>• Use the "Wearable Data" tab to add activity metrics</p>
            <p>• Use the "Manual Entry" tab to manually input health markers</p>
          </div>
        </div>
      )}
    </div>
  );
}
