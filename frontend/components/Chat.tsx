'use client';

import React, { useState, useEffect } from 'react';
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

export default function Chat() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    loadChatSessions();
  }, []);

  useEffect(() => {
    if (sessions.length > 0 && !currentSession) {
      loadLastSession();
    }
  }, [sessions]);

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
      setLoadingHistory(false);
    }
  };

  const loadLastSession = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'}/chat/last-session`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (response.data) {
        await loadSessionMessages(response.data.id);
      } else if (sessions.length > 0) {
        const latestSession = sessions[sessions.length - 1];
        await loadSessionMessages(latestSession.id);
      }
    } catch (error) {
      console.error('Error loading last session:', error);
      if (sessions.length > 0) {
        const latestSession = sessions[sessions.length - 1];
        await loadSessionMessages(latestSession.id);
      }
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
      
      if (sessionData && sessionData.messages && Array.isArray(sessionData.messages)) {
        setMessages(sessionData.messages);
      } else {
        setMessages([]);
      }
      
      // Close sidebar on mobile after selecting a session
      if (window.innerWidth < 768) {
        setSidebarOpen(false);
      }
    } catch (error) {
      console.error('Error loading session messages:', error);
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
      setMessages([]);
      
      // Close sidebar on mobile after creating a session
      if (window.innerWidth < 768) {
        setSidebarOpen(false);
      }
    } catch (error) {
      console.error('Error creating new session:', error);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || !currentSession || isLoading) return;

    const userMessage = {
      id: Date.now().toString(),
      content: inputMessage,
      role: 'user' as const,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'}/chat/sessions/${currentSession.id}/messages`, {
        content: inputMessage
      }, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      const assistantMessage = response.data;
      setMessages(prev => [...prev, assistantMessage]);
      
      // Update the current session with new messages
      setCurrentSession(prev => prev ? {
        ...prev,
        messages: [...prev.messages, userMessage, assistantMessage]
      } : null);
    } catch (error) {
      console.error('Error sending message:', error);
      // Remove the user message if there was an error
      setMessages(prev => prev.filter(msg => msg.id !== userMessage.id));
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatSessionTitle = (title: string) => {
    return title.length > 25 ? title.substring(0, 25) + '...' : title;
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

  if (loadingHistory) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="flex h-full relative">
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
              className="bg-primary-600 text-white p-2 rounded-apple hover:bg-primary-700 transition-colors shadow-apple"
              title="New Chat"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            </button>
          </div>

          {/* Sessions List */}
          <div className="flex-1 overflow-y-auto p-4">
            {sessions.length === 0 ? (
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
                    onClick={() => loadSessionMessages(session.id)}
                    className={`
                      p-4 rounded-apple cursor-pointer transition-all duration-200 border
                      ${currentSession?.id === session.id
                        ? 'bg-primary-50 border-primary-200 shadow-apple'
                        : 'bg-gray-50 border-gray-200 hover:bg-gray-100 hover:border-gray-300'
                      }
                    `}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-sm text-gray-900 truncate">
                          {formatSessionTitle(session.title)}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          {formatSessionDate(session.created_at)}
                        </div>
                      </div>
                      {currentSession?.id === session.id && (
                        <div className="ml-2 w-2 h-2 bg-primary-600 rounded-full"></div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Chat Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-100 bg-white">
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="md:hidden p-2 rounded-apple hover:bg-gray-100 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <div>
              <h2 className="text-lg font-semibold text-gray-900">
                {currentSession ? currentSession.title : 'AI Chat Assistant'}
              </h2>
              {currentSession && (
                <p className="text-sm text-gray-500">
                  Created {formatSessionDate(currentSession.created_at)}
                </p>
              )}
            </div>
          </div>
          
          {!currentSession && (
            <button
              onClick={createNewSession}
              className="bg-primary-600 text-white px-4 py-2 rounded-apple hover:bg-primary-700 transition-colors text-sm font-medium shadow-apple"
            >
              New Chat
            </button>
          )}
        </div>

        {/* Messages Area */}
        <div className="flex-1 p-6 overflow-y-auto space-y-4 bg-gray-50">
          {messages.length === 0 ? (
            <div className="text-center text-gray-500 mt-8">
              {currentSession ? (
                <div className="space-y-4">
                  <div className="text-6xl">🤖</div>
                  <p className="text-lg font-medium">Start a conversation!</p>
                  <p className="text-sm">Ask me anything about your health or upload reports for analysis.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="text-6xl">💬</div>
                  <p className="text-lg font-medium">No session selected</p>
                  <button
                    onClick={createNewSession}
                    className="bg-primary-600 text-white px-6 py-3 rounded-apple hover:bg-primary-700 font-medium transition-colors shadow-apple"
                  >
                    Create New Session
                  </button>
                </div>
              )}
            </div>
          ) : (
            (Array.isArray(messages) ? messages : []).map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`
                    max-w-xs lg:max-w-md px-4 py-3 rounded-apple-lg shadow-apple
                    ${message.role === 'user'
                      ? 'bg-primary-600 text-white'
                      : 'bg-white text-gray-800 border border-gray-100'
                    }
                  `}
                >
                  <div className="text-sm leading-relaxed">{message.content}</div>
                  <div className={`text-xs mt-2 ${
                    message.role === 'user' ? 'text-primary-100' : 'text-gray-500'
                  }`}>
                    {new Date(message.timestamp).toLocaleTimeString([], { 
                      hour: '2-digit', 
                      minute: '2-digit' 
                    })}
                  </div>
                </div>
              </div>
            ))
          )}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white text-gray-800 px-4 py-3 rounded-apple-lg border border-gray-100 shadow-apple">
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600"></div>
                  <span className="text-sm">AI is thinking...</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="border-t border-gray-100 p-6 bg-white">
          <div className="flex space-x-3">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message..."
              disabled={!currentSession || isLoading}
              className="flex-1 px-4 py-3 border border-gray-300 rounded-apple focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors"
            />
            <button
              onClick={sendMessage}
              disabled={!inputMessage.trim() || !currentSession || isLoading}
              className="bg-primary-600 text-white px-6 py-3 rounded-apple hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium shadow-apple"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
