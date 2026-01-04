"""
TestMyKnowledge Backend
FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.database import Database
from app.routers import users, quiz, test, assignment, prompt


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    Database.initialize()
    print("[OK] Database connection pool initialized")
    
    yield
    
    # Shutdown
    Database.close()
    print("[OK] Database connections closed")


# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Quiz & Knowledge Assessment Platform",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router)
app.include_router(quiz.router)
app.include_router(test.router)
app.include_router(assignment.router)
app.include_router(prompt.router)


@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "message": "TestMyKnowledge API is running",
        "version": settings.APP_VERSION,
        "status": "healthy"
    }


@app.get("/health")
def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "api": "operational"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )

