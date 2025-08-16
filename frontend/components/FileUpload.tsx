'use client';

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';

interface FileUploadProps {
  onUploadComplete: (data: any) => void;
}

export default function FileUpload({ onUploadComplete }: FileUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    setUploading(true);
    setUploadProgress(0);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://127.0.0.1:8000/report/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        onUploadComplete(data);
        setUploadProgress(100);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }
    } catch (error) {
      console.error('Upload error:', error);
      alert(`Error processing file: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  }, [onUploadComplete]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg'],
      'application/pdf': ['.pdf']
    },
    multiple: false
  });

  return (
    <div className="space-y-6">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-apple-lg p-12 text-center cursor-pointer transition-all duration-200 ${
          isDragActive
            ? 'border-primary-500 bg-primary-50 shadow-apple'
            : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
        }`}
      >
        <input {...getInputProps()} />
        <div className="space-y-4">
          <div className="text-4xl">📄</div>
          {isDragActive ? (
            <div>
              <p className="text-primary-600 font-medium">Drop the file here...</p>
              <p className="text-sm text-primary-500 mt-1">Release to upload</p>
            </div>
          ) : (
            <div>
              <p className="text-gray-700 font-medium">
                Drag & drop a health report file here
              </p>
              <p className="text-gray-500 mt-2">
                or click to browse files
              </p>
              <p className="text-sm text-gray-400 mt-3">
                Supports PDF, PNG, JPG, JPEG files
              </p>
            </div>
          )}
        </div>
      </div>

      {uploading && (
        <div className="bg-white p-6 rounded-apple-lg border border-gray-100 shadow-apple">
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium text-gray-700">Processing file...</span>
              <span className="text-sm text-gray-500">{uploadProgress}%</span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
              <div
                className="bg-primary-600 h-2 rounded-full transition-all duration-300 ease-out"
                style={{ width: `${uploadProgress}%` }}
              ></div>
            </div>
            <p className="text-xs text-gray-500">
              This may take a few moments depending on file size
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
