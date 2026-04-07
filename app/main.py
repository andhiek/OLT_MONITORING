import asyncio
from fastapi import FastAPI
import app.db.models
from app.database.connection import engine
from app.telegram.bot import start_bot
app = FastAPI()


from app.api.dashboard import router as dashboard_router
app.include_router(dashboard_router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(start_bot())  # 🔥 penting!