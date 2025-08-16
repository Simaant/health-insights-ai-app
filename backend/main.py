from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.report import router as report_router
from routes.auth import router as auth_router
from routes.chat import router as chat_router
from routes.wearable import router as wearable_router
from database import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Health Insights AI",
    description="AI-powered health insights from lab reports and wearable data",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
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