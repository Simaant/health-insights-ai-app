# 🏥 Health Insights AI

A comprehensive health monitoring and AI-powered insights application that helps users track their health data, analyze lab reports, and get personalized health recommendations.

## ✨ Features

- **🔐 User Authentication**: Secure login/register with JWT tokens
- **💬 AI Chat Interface**: Context-aware health conversations with session management
- **📄 File Upload & OCR**: Extract health data from lab reports and images
- **📊 Health Dashboard**: Visualize health metrics and trends
- **📱 Manual Data Entry**: Add health markers manually
- **🔄 Session Management**: Collapsible sidebar with chat history
- **🎨 Modern UI**: Apple-inspired design with responsive layout

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL (for production)
- Tesseract OCR

### Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd health-insights-ai-app
   ```

2. **Set up Python environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   cd backend
   pip install -r requirements.txt
   ```

3. **Set up Node.js environment**
   ```bash
   cd frontend
   npm install
   ```

4. **Start the servers**
   ```bash
   # Terminal 1 - Backend
   cd backend
   source ../venv/bin/activate
   python -m uvicorn main:app --host 127.0.0.1 --port 8000
   
   # Terminal 2 - Frontend
   cd frontend
   npm run dev
   ```

5. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://127.0.0.1:8000
   - API Docs: http://127.0.0.1:8000/docs

## 🚀 Deployment

### Quick Deployment
```bash
./deploy.sh
```

### Manual Deployment
See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions.

**Recommended Stack:**
- **Frontend**: Vercel
- **Backend**: Railway/Render
- **Database**: PostgreSQL (Railway/Render/Neon)

## 📁 Project Structure

```
health-insights-ai-app/
├── frontend/                 # Next.js frontend
│   ├── app/                 # App router pages
│   ├── components/          # React components
│   ├── lib/                 # Utility functions
│   └── tailwind.config.js   # Tailwind configuration
├── backend/                 # FastAPI backend
│   ├── routers/            # API route handlers
│   ├── models/             # Database models
│   ├── schemas/            # Pydantic schemas
│   ├── utils/              # Utility functions
│   └── main.py             # FastAPI application
├── venv/                   # Python virtual environment
├── deploy.sh               # Deployment script
└── DEPLOYMENT_GUIDE.md     # Deployment documentation
```

## 🔧 Configuration

### Environment Variables

**Frontend (.env.local)**
```
NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8000
```

**Backend (.env)**
```
DATABASE_URL=sqlite:///./health_insights.db
JWT_SECRET=your-secret-key
FIELD_ENCRYPTION_KEY=your-encryption-key
```

## 🎨 UI/UX Features

- **Apple-inspired Design**: Clean, modern interface with rounded corners and subtle shadows
- **Responsive Layout**: Works seamlessly on desktop, tablet, and mobile
- **Collapsible Sidebar**: Session management with hamburger menu
- **Card-based Layout**: Organized content with visual hierarchy
- **Smooth Animations**: Subtle transitions and hover effects

## 🔐 Security Features

- JWT-based authentication
- Password hashing with bcrypt
- CORS protection
- Input validation and sanitization
- Secure file upload handling

## 📊 Health Data Processing

- **OCR Integration**: Extract text from lab reports and images
- **Health Marker Detection**: Automatic identification of health metrics
- **Data Validation**: Range checking and normalization
- **AI Insights**: Context-aware health recommendations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
1. Check the [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
2. Review the troubleshooting section
3. Create an issue in the repository

---

**Built with ❤️ using Next.js, FastAPI, and Tailwind CSS**


