from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.session import init_db
from app.api.routes import router
from app.services.scheduler import start_scheduler
@asynccontextmanager
async def lifespan(app):
    init_db(); scheduler=start_scheduler(); yield; scheduler.shutdown(wait=False)
app=FastAPI(title="Football Predictor API",version="1.0.0",lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=["http://localhost:3000"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
app.include_router(router)
@app.get("/health")
def health():return {"status":"ok"}
