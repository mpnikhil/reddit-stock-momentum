from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import router
from app.database import engine, Base
from app.scheduler import start_scheduler
import os

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Reddit Stock Momentum Monitor",
    description="API for tracking stock discussions across Reddit",
    version="1.0.0"
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    """Initialize background scheduler on startup"""
    if os.getenv("DISABLE_SCHEDULER") != "true":
        start_scheduler()

@app.get("/")
async def root():
    return {"message": "Reddit Stock Momentum Monitor API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)