"use client";
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Chat from "../../components/Chat";
import FileUpload from "../../components/FileUpload";
import WearableData from "../../components/WearableData";
import HealthSummary from "../../components/HealthSummary";
import ManualEntry from "../../components/ManualEntry";
import axios from 'axios';

interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: string;
}

interface ChatSession {
  id: string;
  title: string;
  created_at: string;
  messages: Message[];
}

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState('chat');
  const [user, setUser] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [loadingSessions, setLoadingSessions] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/auth/login');
      return;
    }

    // Verify token and get user info
    const verifyAuth = async () => {
      try {
        const response = await axios.get(`${process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'}/auth/me`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        setUser(response.data);
      } catch (error) {
        console.error('Auth error:', error);
        localStorage.removeItem('token');
        router.push('/auth/login');
      } finally {
        setIsLoading(false);
      }
    };

    verifyAuth();
    loadChatSessions();
  }, [router]);

  const loadChatSessions = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'}/chat/sessions`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      const sessionsData = response.data;
      setSessions(sessionsData);
    } catch (error) {
      console.error('Error loading chat sessions:', error);
    } finally {
      setLoadingSessions(false);
    }
  };

  const createNewSession = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'}/chat/sessions`, {
        title: `New Chat ${new Date().toLocaleString()}`
      }, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      const newSession = response.data;
      setSessions(prev => [...prev, newSession]);
      setCurrentSession(newSession);
      
      // Close sidebar on mobile after creating a session
      if (window.innerWidth < 768) {
        setSidebarOpen(false);
      }
    } catch (error) {
      console.error('Error creating new session:', error);
    }
  };

  const deleteSession = async (sessionId: string) => {
    if (!confirm('Are you sure you want to delete this session?')) return;
    
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'}/chat/sessions/${sessionId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      setSessions(prev => prev.filter(session => session.id !== sessionId));
      
      // If the deleted session was the current session, clear it
      if (currentSession?.id === sessionId) {
        setCurrentSession(null);
      }
    } catch (error) {
      console.error('Error deleting session:', error);
    }
  };

  const loadSessionMessages = async (sessionId: string) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'}/chat/sessions/${sessionId}/messages`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      const sessionData = response.data;
      setCurrentSession(sessionData);
      
      // Close sidebar on mobile after selecting a session
      if (window.innerWidth < 768) {
        setSidebarOpen(false);
      }
    } catch (error) {
      console.error('Error loading session messages:', error);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    router.push('/');
  };

  const formatSessionTitle = (title: string) => {
    return title.length > 30 ? title.substring(0, 30) + '...' : title;
  };

  const formatSessionDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);
    
    if (diffInHours < 24) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (diffInHours < 48) {
      return 'Yesterday';
    } else {
      return date.toLocaleDateString();
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="bg-white border-b border-gray-100 sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="p-2 rounded-apple hover:bg-gray-100 transition-colors md:hidden"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
              <h1 className="text-xl font-semibold text-gray-900">Health Insights AI</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">
                Welcome, {user?.first_name || user?.email}
              </span>
              <button
                onClick={handleLogout}
                className="text-gray-600 hover:text-gray-900 px-4 py-2 rounded-apple text-sm font-medium transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="flex">
        {/* Mobile Overlay */}
        {sidebarOpen && (
          <div 
            className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Sidebar */}
        <div className={`
          fixed md:relative inset-y-0 left-0 z-50 w-80 bg-white border-r border-gray-100 transform transition-transform duration-300 ease-in-out
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
        `}>
          <div className="flex flex-col h-full">
            {/* Sidebar Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-100">
              <h3 className="text-lg font-semibold text-gray-900">Chat Sessions</h3>
              <button
                onClick={createNewSession}
                className="bg-primary-600 text-white px-4 py-2 rounded-apple hover:bg-primary-700 transition-colors text-sm font-medium shadow-apple"
              >
                Start New Session
              </button>
            </div>

            {/* Sessions List */}
            <div className="flex-1 overflow-y-auto p-4">
              {loadingSessions ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
                </div>
              ) : sessions.length === 0 ? (
                <div className="text-center text-gray-500 py-8">
                  <div className="text-4xl mb-4">💬</div>
                  <p className="text-sm">No chat sessions yet</p>
                  <button
                    onClick={createNewSession}
                    className="mt-4 bg-primary-600 text-white px-4 py-2 rounded-apple hover:bg-primary-700 text-sm shadow-apple"
                  >
                    Start Your First Chat
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  {sessions.map((session) => (
                    <div
                      key={session.id}
                      className={`
                        p-4 rounded-apple border transition-all duration-200 cursor-pointer
                        ${currentSession?.id === session.id
                          ? 'bg-primary-50 border-primary-200 shadow-apple'
                          : 'bg-gray-50 border-gray-200 hover:bg-gray-100 hover:border-gray-300'
                        }
                      `}
                    >
                      <div className="flex items-start justify-between">
                        <div 
                          className="flex-1 min-w-0"
                          onClick={() => loadSessionMessages(session.id)}
                        >
                          <div className="font-medium text-sm text-gray-900 truncate">
                            {formatSessionTitle(session.title)}
                          </div>
                          <div className="text-xs text-gray-500 mt-1">
                            {formatSessionDate(session.created_at)}
                          </div>
                        </div>
                        <div className="flex items-center space-x-2 ml-2">
                          {currentSession?.id === session.id && (
                            <div className="w-2 h-2 bg-primary-600 rounded-full"></div>
                          )}
                          <button
                            onClick={() => deleteSession(session.id)}
                            className="text-error-600 hover:text-error-700 text-xs font-medium px-2 py-1 rounded-apple hover:bg-error-50 transition-colors"
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Health Summary */}
            <div className="mb-8">
              <HealthSummary />
            </div>

            {/* Tab Navigation */}
            <div className="bg-white rounded-apple-lg shadow-apple border border-gray-100 mb-8">
              <nav className="flex">
                {[
                  { id: 'chat', name: 'AI Chat', icon: '💬' },
                  { id: 'upload', name: 'Upload Reports', icon: '📄' },
                  { id: 'manual', name: 'Manual Entry', icon: '✏️' },
                  { id: 'wearable', name: 'Wearable Data', icon: '⌚' },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex-1 py-4 px-6 text-sm font-medium transition-colors ${
                      activeTab === tab.id
                        ? 'text-primary-600 border-b-2 border-primary-600 bg-primary-50'
                        : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <span className="mr-2">{tab.icon}</span>
                    {tab.name}
                  </button>
                ))}
              </nav>
            </div>

            {/* Tab Content */}
            <div className="bg-white rounded-apple-lg shadow-apple border border-gray-100">
              {activeTab === 'chat' && (
                <div className="h-[600px]">
                  <Chat />
                </div>
              )}
              
              {activeTab === 'upload' && (
                <div className="p-8">
                  <h2 className="text-xl font-semibold text-gray-900 mb-6">Upload Lab Reports</h2>
                  <FileUpload onUploadComplete={(data: any) => console.log('Upload complete:', data)} />
                </div>
              )}
              
              {activeTab === 'manual' && (
                <div className="p-8">
                  <h2 className="text-xl font-semibold text-gray-900 mb-6">Manual Health Marker Entry</h2>
                  <ManualEntry />
                </div>
              )}
              
              {activeTab === 'wearable' && (
                <div className="p-8">
                  <h2 className="text-xl font-semibold text-gray-900 mb-6">Wearable Device Data</h2>
                  <WearableData onDataUpdate={() => {}} />
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}