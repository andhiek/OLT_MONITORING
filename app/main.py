import asyncio
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import app.db.models
from app.core.scheduler import monitoring_loop
from app.database.connection import engine
from app.telegram.bot import start_bot
app = FastAPI()


from app.api.dashboard import router as dashboard_router
app.include_router(dashboard_router, prefix="/api")



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # sementara open dulu
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)   

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(start_bot())  # 🔥 penting!
    
@app.get("/dashboard")
async def dashboard():
    return FileResponse("dashboard.html")