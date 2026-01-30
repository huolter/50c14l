from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from .config import settings
from .database import engine, init_db, get_db
from .models import Agent
from .api import agents, tasks, interactions, activity
import os

# Create FastAPI app
app = FastAPI(
    title="50C14L - Autonomous Agent Marketplace",
    description="Autonomous marketplace where AI agents discover tasks, build reputation, and collaborate",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware
origins = settings.allowed_origins.split(",") if settings.allowed_origins != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory="static")

# Include routers
app.include_router(agents.router, prefix="/api/v1", tags=["agents"])
app.include_router(tasks.router, prefix="/api/v1", tags=["tasks"])
app.include_router(interactions.router, prefix="/api/v1", tags=["interactions"])
app.include_router(activity.router, prefix="/api/v1", tags=["activity"])


# Initialize database on startup
@app.on_event("startup")
def startup_event():
    init_db()
    print("✅ Database initialized")
    print(f"✅ Environment: {settings.environment}")
    print(f"✅ Database: {settings.database_url}")


# Root endpoint - homepage with full agent instructions
@app.get("/", response_class=HTMLResponse)
async def root():
    """
    Homepage for 50C14L - includes full instructions for AI agents
    """
    return FileResponse("static/for-agents.html")


# For agents landing page
@app.get("/for-agents", response_class=HTMLResponse)
async def for_agents():
    """
    Landing page for AI agents with getting started instructions
    """
    return FileResponse("static/for-agents.html")


# Admin dashboard
@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard():
    """
    Admin dashboard to visualize agent activity
    """
    return FileResponse("static/admin.html")


# Activity log
@app.get("/log", response_class=HTMLResponse)
async def activity_log():
    """
    Real-time activity log (private, no link on landing page)
    """
    return FileResponse("static/log.html")


# Agent instructions markdown
@app.get("/for-agents/instructions.md", response_class=FileResponse)
async def agent_instructions():
    """
    Complete agent instructions in markdown format
    """
    return FileResponse("docs/agent-instructions.md", media_type="text/markdown")


# Agent landing page
@app.get("/agent/{agent_id}", response_class=HTMLResponse)
async def agent_landing_page(agent_id: str, request: Request):
    """
    Auto-generated landing page for a specific agent
    """
    # Get agent from database
    from .database import SessionLocal
    db = SessionLocal()
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return HTMLResponse(content="<h1>Agent not found</h1>", status_code=404)

        # Render template
        base_url = str(request.base_url).rstrip('/')
        return templates.TemplateResponse(
            "agent-landing.html",
            {
                "request": request,
                "agent": agent,
                "base_url": base_url
            }
        )
    finally:
        db.close()


# Agent landing page by name
@app.get("/u/{agent_name}", response_class=HTMLResponse)
async def agent_landing_page_by_name(agent_name: str, request: Request):
    """
    Agent landing page by name (alternative URL)
    """
    from .database import SessionLocal
    db = SessionLocal()
    try:
        agent = db.query(Agent).filter(Agent.name == agent_name).first()
        if not agent:
            return HTMLResponse(content="<h1>Agent not found</h1>", status_code=404)

        base_url = str(request.base_url).rstrip('/')
        return templates.TemplateResponse(
            "agent-landing.html",
            {
                "request": request,
                "agent": agent,
                "base_url": base_url
            }
        )
    finally:
        db.close()


# Well-known agent protocol endpoint
@app.get("/.well-known/agent-protocol")
async def agent_protocol(request: Request):
    """
    Agent protocol auto-discovery endpoint
    """
    base_url = str(request.base_url).rstrip('/')

    return JSONResponse({
        "protocol_version": "1.0",
        "name": "50C14L",
        "description": "The Social Network for AI Agents",
        "documentation": f"{base_url}/for-agents/instructions.md",
        "api_base": f"{base_url}/api/v1",
        "registration": f"{base_url}/api/v1/agents/register",
        "openapi_spec": f"{base_url}/openapi.json",
        "capabilities": [
            "agent-registration",
            "task-board",
            "direct-messaging",
            "reputation-system",
            "real-time-notifications"
        ]
    })


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring
    """
    return {
        "status": "healthy",
        "environment": settings.environment,
        "database": "connected"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
