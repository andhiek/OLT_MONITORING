import asyncio
import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.scheduler import monitoring_loop
from app.telegram.bot import start_bot, bot

from app.api.dashboard import router as dashboard_router
from app.api.incidents import router as incidents_router

app = FastAPI()

# ROUTERS
app.include_router(dashboard_router, prefix="/api")
app.include_router(incidents_router, prefix="/api")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔥 GLOBAL FLAG (ANTI DOUBLE RUN)
started = False

# STARTUP
@app.on_event("startup")
async def startup_event():
    global started

    print("🚀 APP STARTED PID:", os.getpid())

    # 🔥 cegah double run
    if started:
        print("⚠️ Already started, skip...")
        return

    started = True

    print("🔥 Starting scheduler + bot...")

    asyncio.create_task(start_bot())
    asyncio.create_task(monitoring_loop(bot))


# DASHBOARD PAGE
@app.get("/dashboard")
async def dashboard():
    return FileResponse(os.path.join(os.getcwd(), "dashboard.html"))