# 🚀 Health Insights AI - Deployment Guide

This guide will help you deploy the Health Insights AI application to production.

## 📋 Prerequisites

- GitHub account
- Vercel account (for frontend)
- Railway/Render account (for backend)
- PostgreSQL database (Railway/Render/Neon)

## 🎯 Deployment Architecture

```
Frontend (Vercel) ←→ Backend (Railway/Render) ←→ Database (PostgreSQL)
```

## 🔧 Phase 1: Frontend Deployment (Vercel)

### Step 1: Prepare Frontend Repository
1. **Push your code to GitHub:**
   ```bash
   git add .
   git commit -m "Prepare for deployment"
   git push origin main
   ```

2. **Connect to Vercel:**
   - Go to [vercel.com](https://vercel.com)
   - Sign up/Login with GitHub
   - Click "New Project"
   - Import your GitHub repository
   - Select the `frontend` folder as root directory

### Step 2: Configure Environment Variables
In Vercel project settings, add these environment variables:

```
NEXT_PUBLIC_BACKEND_URL=https://your-backend-url.railway.app
```

### Step 3: Deploy
- Vercel will automatically detect Next.js
- Click "Deploy"
- Your frontend will be available at: `https://your-app.vercel.app`

## 🔧 Phase 2: Backend Deployment (Railway)

### Step 1: Prepare Backend Repository
1. **Create a separate repository for backend** (recommended)
2. **Or deploy from the same repository** (select backend folder)

### Step 2: Connect to Railway
1. Go to [railway.app](https://railway.app)
2. Sign up/Login with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your repository and `backend` folder

### Step 3: Configure Environment Variables
Add these environment variables in Railway:

```
DATABASE_URL=postgresql://username:password@host:port/database_name
JWT_SECRET=your-super-secret-jwt-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
FIELD_ENCRYPTION_KEY=your-encryption-key-here
ENVIRONMENT=production
DEBUG=false
ALLOWED_ORIGINS=https://your-frontend-domain.vercel.app
```

### Step 4: Add PostgreSQL Database
1. In Railway dashboard, click "New"
2. Select "Database" → "PostgreSQL"
3. Railway will automatically set `DATABASE_URL`

### Step 5: Deploy
- Railway will automatically detect Python/FastAPI
- The app will deploy using the `railway.json` configuration
- Your backend will be available at: `https://your-app.railway.app`

## 🔧 Phase 3: Database Migration

### Step 1: Run Migration Script
```bash
cd backend
python migrate_to_postgres.py
```

### Step 2: Verify Migration
Check that all data has been migrated correctly.

## 🔧 Phase 4: Update Frontend Configuration

### Step 1: Update Backend URL
In Vercel, update the environment variable:
```
NEXT_PUBLIC_BACKEND_URL=https://your-backend-url.railway.app
```

### Step 2: Redeploy Frontend
Vercel will automatically redeploy with the new configuration.

## 🔧 Phase 5: Testing Production

### Step 1: Test Frontend
1. Visit your Vercel URL
2. Test registration/login
3. Test all features

### Step 2: Test Backend
1. Test API endpoints
2. Verify database connections
3. Check logs for errors

## 🔧 Alternative Deployment Options

### Render (Backend Alternative)
1. Go to [render.com](https://render.com)
2. Create new "Web Service"
3. Connect GitHub repository
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Heroku (Backend Alternative)
1. Go to [heroku.com](https://heroku.com)
2. Create new app
3. Connect GitHub repository
4. Add PostgreSQL addon
5. Deploy using Procfile

## 🔧 Environment Variables Reference

### Frontend (Vercel)
```
NEXT_PUBLIC_BACKEND_URL=https://your-backend-url.railway.app
```

### Backend (Railway/Render/Heroku)
```
DATABASE_URL=postgresql://username:password@host:port/database_name
JWT_SECRET=your-super-secret-jwt-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
FIELD_ENCRYPTION_KEY=your-encryption-key-here
ENVIRONMENT=production
DEBUG=false
ALLOWED_ORIGINS=https://your-frontend-domain.vercel.app
```

## 🔧 Troubleshooting

### Common Issues

1. **CORS Errors:**
   - Ensure `ALLOWED_ORIGINS` includes your frontend URL
   - Check that the URL format is correct

2. **Database Connection Issues:**
   - Verify `DATABASE_URL` is correct
   - Check that PostgreSQL is running
   - Ensure network access is configured

3. **Build Failures:**
   - Check `requirements.txt` for missing dependencies
   - Verify Python version compatibility
   - Check build logs for specific errors

4. **Environment Variables:**
   - Ensure all required variables are set
   - Check variable names match exactly
   - Verify no extra spaces or characters

### Getting Help

1. Check deployment platform logs
2. Verify environment variables
3. Test locally with production settings
4. Check GitHub issues for similar problems

## 🎉 Success!

Once deployed, your Health Insights AI app will be available at:
- **Frontend:** `https://your-app.vercel.app`
- **Backend:** `https://your-app.railway.app`

## 📝 Next Steps

1. **Set up monitoring** (optional)
2. **Configure custom domain** (optional)
3. **Set up CI/CD** (optional)
4. **Add SSL certificates** (automatic with Vercel/Railway)
5. **Monitor performance** and scale as needed

---

**Need help?** Check the troubleshooting section or create an issue in the repository.
