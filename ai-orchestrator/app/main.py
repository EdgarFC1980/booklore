from fastapi import FastAPI
from .routes_chat import router as chat_router
from .routes_plan import router as plan_router

app = FastAPI(title="booklore ai orchestrator", version="0.1.0")

@app.get("/health")
async def health() -> dict:
    return {"ok": True}

app.include_router(chat_router, prefix="/api")
app.include_router(plan_router, prefix="/api")
