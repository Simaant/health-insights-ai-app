#!/bin/bash

echo "🚀 Setting up Health Insights AI Application..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3.8+ and try again."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed. Please install Node.js 16+ and try again."
    exit 1
fi

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "⚠️  PostgreSQL is not installed. You'll need to install it or use a cloud database."
    echo "   For local development, you can install PostgreSQL from: https://www.postgresql.org/download/"
fi

echo "📦 Setting up backend..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r backend/requirements.txt

echo "📦 Setting up frontend..."

# Install Node.js dependencies
cd frontend
npm install
cd ..

echo "🔧 Configuration setup..."

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp env.example .env
    echo "⚠️  Please edit .env file with your actual configuration values."
fi

# Create uploads directory
mkdir -p uploads

echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file with your database and API keys"
echo "2. Set up your PostgreSQL database"
echo "3. Run the backend: cd backend && python -m uvicorn main:app --reload"
echo "4. Run the frontend: cd frontend && npm run dev"
echo ""
echo "🌐 The application will be available at:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"


