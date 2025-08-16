# 🚀 Deployment Guide - Health Insights AI

## **Free Hosting Setup: Vercel (Frontend) + Railway (Backend)**

### **Step 1: Deploy Backend to Railway**

1. **Go to**: https://railway.app
2. **Sign up with GitHub**
3. **Click "New Project"**
4. **Select "Deploy from GitHub repo"**
5. **Choose**: `Simaant/health-insights-ai-app`
6. **Configure**:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

7. **Add Environment Variables**:
   ```
   DATABASE_URL=postgresql://... (Railway will provide this)
   JWT_SECRET=your-super-secret-jwt-key-here
   FIELD_ENCRYPTION_KEY=your-32-character-encryption-key
   ENVIRONMENT=production
   DEBUG=false
   ALLOWED_ORIGINS=https://your-vercel-app.vercel.app
   ```

8. **Click "Deploy"**
9. **Copy your Railway URL** (e.g., `https://your-app.railway.app`)

### **Step 2: Deploy Frontend to Vercel**

1. **Go to**: https://vercel.com
2. **Sign up with GitHub**
3. **Click "New Project"**
4. **Import**: `Simaant/health-insights-ai-app`
5. **Configure**:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`
   - **Install Command**: `npm install`

6. **Add Environment Variable**:
   ```
   NEXT_PUBLIC_BACKEND_URL=https://your-app.railway.app
   ```

7. **Click "Deploy"**

### **Step 3: Test Your Live App**

1. **Frontend**: https://your-app.vercel.app
2. **Test registration and login**
3. **Test all features**

### **Step 4: Custom Domain (Optional)**

1. **Vercel**: Add custom domain in project settings
2. **Railway**: Update ALLOWED_ORIGINS with your domain

## **🔧 Troubleshooting**

### **If Backend Fails:**
- Check Railway logs
- Verify environment variables
- Ensure requirements.txt is correct

### **If Frontend Fails:**
- Check Vercel build logs
- Verify environment variables
- Ensure backend URL is correct

### **If Auth Doesn't Work:**
- Check CORS settings
- Verify backend URL in frontend
- Check JWT_SECRET is set

## **💰 Cost Breakdown**

- **Vercel**: Free tier (unlimited deployments)
- **Railway**: Free tier (500 hours/month)
- **Total**: $0/month

## **📈 Scaling Up**

When you need more:
- **Railway**: Upgrade to paid plan ($5/month)
- **Vercel**: Upgrade to Pro ($20/month)
- **Database**: Railway PostgreSQL or external service

## **🎯 Next Steps**

1. **Deploy following the steps above**
2. **Test all features**
3. **Add custom domain**
4. **Set up monitoring**
5. **Add more features!**
