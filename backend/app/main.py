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
    print("=" * 80)
    print("DATABASE CONFIGURATION")
    print("=" * 80)
    print(f"DATABASE URI: {settings.database_url}")
    print(f"Host: {settings.DATABASE_HOST}")
    print(f"Port: {settings.DATABASE_PORT}")
    print(f"Database: {settings.DATABASE_NAME}")
    print(f"User: {settings.DATABASE_USER}")
    print("=" * 80)
    
    Database.initialize()
    print("[OK] Database connection pool initialized")
    
    # Verify tables exist
    try:
        from app.database import Database
        with Database.get_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            tables = cursor.fetchall()
            print("\n[DATABASE TABLES]")
            if tables:
                for table in tables:
                    print(f"  ✓ {table['table_name']}")
            else:
                print("  ⚠️  WARNING: No tables found!")
                print("  Run: python reset_database.py")
            print()
    except Exception as e:
        print(f"[ERROR] Failed to check tables: {e}")
    
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

