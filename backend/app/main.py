from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from app.core.config import settings
from app.core.database import init_db
from app.api.routes import health, jobs, resumes, matching, llm


# Ensure database tables exist at startup
init_db()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle manager.
    """
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Based Resume Matching & Candidate Ranking System API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


def custom_openapi():
    """
    Custom OpenAPI schema generator ensuring Swagger UI renders file pickers
    instead of string input fields for file arrays.
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Inject format: binary on file properties so Swagger UI displays file upload inputs
    for schema in openapi_schema.get("components", {}).get("schemas", {}).values():
        for prop in schema.get("properties", {}).values():
            if prop.get("type") == "array" and "items" in prop:
                if (
                    prop["items"].get("contentMediaType") == "application/octet-stream"
                    or prop.get("title") in ["Files", "File"]
                    or "upload" in schema.get("title", "").lower()
                ):
                    prop["items"]["type"] = "string"
                    prop["items"]["format"] = "binary"
            elif prop.get("contentMediaType") == "application/octet-stream":
                prop["format"] = "binary"

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# Configure CORS for frontend access (default: http://localhost:5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes under /api
app.include_router(health.router, prefix=settings.API_V1_PREFIX)
app.include_router(jobs.router, prefix=settings.API_V1_PREFIX)
app.include_router(resumes.router, prefix=settings.API_V1_PREFIX)
app.include_router(matching.router, prefix=settings.API_V1_PREFIX)
app.include_router(llm.router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def root():
    """Root redirect to documentation."""
    return {
        "message": "AI Resume Matching & Candidate Ranking API is running.",
        "documentation": "/docs",
        "health": f"{settings.API_V1_PREFIX}/health",
        "jobs": f"{settings.API_V1_PREFIX}/jobs",
        "resumes": f"{settings.API_V1_PREFIX}/resumes",
    }
