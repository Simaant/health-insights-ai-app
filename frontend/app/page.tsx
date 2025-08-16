"use client";
import { useState } from 'react';
import Link from 'next/link';

export default function HomePage() {
  const [isLoading, setIsLoading] = useState(false);

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="bg-white border-b border-gray-100 sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">Health Insights AI</h1>
            </div>
            <div className="flex items-center space-x-4">
              <Link 
                href="/auth/login"
                className="text-gray-600 hover:text-gray-900 px-4 py-2 rounded-apple text-sm font-medium transition-colors"
              >
                Login
              </Link>
              <Link 
                href="/auth/register"
                className="bg-primary-600 text-white px-4 py-2 rounded-apple text-sm font-medium hover:bg-primary-700 transition-colors shadow-apple"
              >
                Sign Up
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 sm:text-5xl md:text-6xl tracking-tight">
            <span className="block">AI-Powered</span>
            <span className="block text-primary-600">Health Insights</span>
          </h1>
          <p className="mt-6 max-w-2xl mx-auto text-lg text-gray-600 leading-relaxed">
            Upload your lab reports and connect your wearable devices to get personalized health recommendations powered by artificial intelligence.
          </p>
          <div className="mt-8 flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/auth/register"
              className="inline-flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-apple text-white bg-primary-600 hover:bg-primary-700 transition-colors shadow-apple"
            >
              Get Started
            </Link>
            <Link
              href="/dashboard"
              className="inline-flex items-center justify-center px-8 py-3 border border-gray-300 text-base font-medium rounded-apple text-gray-700 bg-white hover:bg-gray-50 transition-colors shadow-apple"
            >
              Try Demo
            </Link>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="py-16 bg-gray-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-base text-primary-600 font-semibold tracking-wide uppercase mb-2">Features</h2>
            <p className="text-3xl font-bold text-gray-900">
              Everything you need for better health insights
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="bg-white p-8 rounded-apple-lg shadow-apple-md border border-gray-100">
              <div className="flex items-center mb-4">
                <div className="flex items-center justify-center h-12 w-12 rounded-apple bg-primary-100 text-primary-600 mr-4">
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-gray-900">Lab Report Analysis</h3>
              </div>
              <p className="text-gray-600 leading-relaxed">
                Upload PDFs or images of your lab reports and get instant analysis of your health markers with AI-powered insights.
              </p>
            </div>

            <div className="bg-white p-8 rounded-apple-lg shadow-apple-md border border-gray-100">
              <div className="flex items-center mb-4">
                <div className="flex items-center justify-center h-12 w-12 rounded-apple bg-primary-100 text-primary-600 mr-4">
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-gray-900">Wearable Integration</h3>
              </div>
              <p className="text-gray-600 leading-relaxed">
                Connect your Fitbit, Apple Watch, or other wearable devices for comprehensive health tracking and insights.
              </p>
            </div>

            <div className="bg-white p-8 rounded-apple-lg shadow-apple-md border border-gray-100">
              <div className="flex items-center mb-4">
                <div className="flex items-center justify-center h-12 w-12 rounded-apple bg-primary-100 text-primary-600 mr-4">
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-gray-900">AI Chat Assistant</h3>
              </div>
              <p className="text-gray-600 leading-relaxed">
                Chat with our AI assistant to get personalized health recommendations and answers to your questions.
              </p>
            </div>

            <div className="bg-white p-8 rounded-apple-lg shadow-apple-md border border-gray-100">
              <div className="flex items-center mb-4">
                <div className="flex items-center justify-center h-12 w-12 rounded-apple bg-primary-100 text-primary-600 mr-4">
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-gray-900">Health Tracking</h3>
              </div>
              <p className="text-gray-600 leading-relaxed">
                Track your health progress over time with detailed analytics and trend analysis.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

