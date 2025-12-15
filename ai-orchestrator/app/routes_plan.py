from fastapi import APIRouter
from pydantic import BaseModel
from .booklore_client import BookloreClient
from .executor import Executor
from .planner import Plan

router = APIRouter()

class ApplyIn(BaseModel):
    plan: Plan

@router.post("/plan/apply")
async def apply(payload: ApplyIn) -> dict:
    bl = BookloreClient()
    ex = Executor(bl)
    return await ex.apply(payload.plan)
