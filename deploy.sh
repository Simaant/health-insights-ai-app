#!/bin/bash

# 🚀 Health Insights AI - Quick Deployment Script
# This script helps automate the deployment process

set -e  # Exit on any error

echo "🚀 Health Insights AI - Deployment Script"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if git is installed
if ! command -v git &> /dev/null; then
    print_error "Git is not installed. Please install git first."
    exit 1
fi

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    print_error "Not in a git repository. Please initialize git first."
    exit 1
fi

print_status "Starting deployment preparation..."

# Step 1: Build frontend
print_status "Building frontend..."
cd frontend
npm run build
print_success "Frontend build completed!"

# Step 2: Check if all required files exist
print_status "Checking deployment files..."
cd ..

required_files=(
    "frontend/vercel.json"
    "backend/railway.json"
    "backend/Procfile"
    "backend/requirements.txt"
    "backend/migrate_to_postgres.py"
    "DEPLOYMENT_GUIDE.md"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        print_success "✓ $file exists"
    else
        print_error "✗ $file missing"
        exit 1
    fi
done

# Step 3: Commit changes
print_status "Committing changes..."
cd ..
git add .
git commit -m "🚀 Prepare for deployment - $(date)"
print_success "Changes committed!"

# Step 4: Push to remote
print_status "Pushing to remote repository..."
git push origin main
print_success "Code pushed to remote!"

# Step 5: Display next steps
echo ""
echo "🎉 Deployment preparation completed!"
echo "====================================="
echo ""
echo "Next steps:"
echo "1. Go to https://vercel.com and deploy frontend"
echo "2. Go to https://railway.app and deploy backend"
echo "3. Set up PostgreSQL database"
echo "4. Configure environment variables"
echo "5. Run database migration"
echo ""
echo "📖 See DEPLOYMENT_GUIDE.md for detailed instructions"
echo ""
print_warning "Don't forget to set up environment variables in your deployment platforms!"
