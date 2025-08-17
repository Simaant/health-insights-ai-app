from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.report import router as report_router
from routes.auth import router as auth_router
from routes.chat import router as chat_router
from routes.wearable import router as wearable_router
from database import engine, Base
import os

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Health Insights AI",
    description="AI-powered health insights from lab reports and wearable data",
    version="1.0.0"
)

# Get allowed origins from environment or use defaults
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://health-insights-ai-app.vercel.app",
    "https://health-insights-ai-ceb4ok6ak-simaants-projects.vercel.app",
    "https://health-insights-ai-app.railway.app",
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(report_router, prefix="/reports", tags=["Reports"])
app.include_router(chat_router, prefix="/chat", tags=["Chat"])
app.include_router(wearable_router, prefix="/wearable", tags=["Wearable Data"])

@app.get("/")
async def root():
    return {"message": "Health Insights AI API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}