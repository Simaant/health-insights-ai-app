'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import axios from 'axios';

export default function ResetPasswordPage() {
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [tokenValid, setTokenValid] = useState(false);
  const [token, setToken] = useState('');
  const [isClient, setIsClient] = useState(false);
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    setIsClient(true);
  }, []);

  useEffect(() => {
    const tokenFromUrl = searchParams.get('token');
    if (tokenFromUrl) {
      setToken(tokenFromUrl);
      verifyToken(tokenFromUrl);
    }
  }, [searchParams]);

  const verifyToken = async (tokenToVerify: string) => {
    try {
      await axios.get(`http://127.0.0.1:8000/auth/verify-reset-token/${tokenToVerify}`);
      setTokenValid(true);
    } catch (err) {
      setError('Invalid or expired reset token. Please request a new one.');
      setTokenValid(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (newPassword.length < 6) {
      setError('Password must be at least 6 characters long');
      return;
    }

    setIsLoading(true);
    setError('');
    setMessage('');

    try {
      const response = await axios.post('http://127.0.0.1:8000/auth/reset-password', {
        token: token,
        new_password: newPassword
      });

      setMessage(response.data.message);
      
      // Redirect to login after 2 seconds
      setTimeout(() => {
        router.push('/auth/login');
      }, 2000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to reset password. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isClient) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded mb-4"></div>
            <div className="h-4 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8">
          <div className="text-center">
            <h2 className="text-3xl font-extrabold text-gray-900">Invalid Reset Link</h2>
            <p className="mt-2 text-sm text-gray-600">
              The reset link is missing the token. Please request a new password reset.
            </p>
            <div className="mt-4">
              <Link href="/auth/forgot-password" className="font-medium text-primary-600 hover:text-primary-500">
                Request new reset link
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!tokenValid && error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8">
          <div className="text-center">
            <h2 className="text-3xl font-extrabold text-gray-900">Invalid Reset Token</h2>
            <p className="mt-2 text-sm text-gray-600">{error}</p>
            <div className="mt-4">
              <Link href="/auth/forgot-password" className="font-medium text-primary-600 hover:text-primary-500">
                Request new reset link
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Set new password
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Enter your new password below.
          </p>
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label htmlFor="newPassword" className="block text-sm font-medium text-gray-700">
                New Password
              </label>
              <input
                id="newPassword"
                name="newPassword"
                type="password"
                required
                className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 focus:z-10 sm:text-sm"
                placeholder="Enter new password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
              />
            </div>
            
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
                Confirm Password
              </label>
              <input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                required
                className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 focus:z-10 sm:text-sm"
                placeholder="Confirm new password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
              />
            </div>
          </div>

          {error && (
            <div className="rounded-md bg-red-50 p-4">
              <div className="text-sm text-red-700">{error}</div>
            </div>
          )}

          {message && (
            <div className="rounded-md bg-green-50 p-4">
              <div className="text-sm text-green-700">{message}</div>
            </div>
          )}

          <div>
            <button
              type="submit"
              disabled={isLoading || !tokenValid}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
            >
              {isLoading ? 'Resetting...' : 'Reset password'}
            </button>
          </div>

          <div className="text-center">
            <Link href="/auth/login" className="font-medium text-primary-600 hover:text-primary-500">
              Back to login
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}
