from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

# Include routers with error handling
print("🔄 Loading routers...")

try:
    from routes.auth import router as auth_router
    app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
    print("✅ Auth router loaded successfully")
except Exception as e:
    print(f"❌ Error loading auth router: {e}")
    print(f"   Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()

try:
    from routes.report import router as report_router
    app.include_router(report_router, prefix="/reports", tags=["Reports"])
    print("✅ Report router loaded successfully")
except Exception as e:
    print(f"❌ Error loading report router: {e}")
    print(f"   Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()

try:
    from routes.chat import router as chat_router
    app.include_router(chat_router, prefix="/chat", tags=["Chat"])
    print("✅ Chat router loaded successfully")
except Exception as e:
    print(f"❌ Error loading chat router: {e}")
    print(f"   Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()

try:
    from routes.wearable import router as wearable_router
    app.include_router(wearable_router, prefix="/wearable", tags=["Wearable Data"])
    print("✅ Wearable router loaded successfully")
except Exception as e:
    print(f"❌ Error loading wearable router: {e}")
    print(f"   Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()

print("🎉 All routers loaded!")

@app.get("/")
async def root():
    return {"message": "Health Insights AI API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/simple")
async def simple_test():
    """Simple test route to check if sub-paths work"""
    return {"message": "Simple route working!"}

@app.get("/debug/routes")
async def debug_routes():
    """Debug endpoint to see all registered routes"""
    routes = []
    for route in app.routes:
        if hasattr(route, 'path'):
            routes.append({
                "path": route.path,
                "methods": list(route.methods) if hasattr(route, 'methods') else [],
                "name": route.name if hasattr(route, 'name') else "Unknown"
            })
    return {"routes": routes}