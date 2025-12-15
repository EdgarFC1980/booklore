from fastapi import APIRouter
from pydantic import BaseModel
from .booklore_client import BookloreClient
from .planner import naive_plan_from_user_request, Plan

router = APIRouter()

class ChatIn(BaseModel):
    text: str
    limit: int = 20

class ChatOut(BaseModel):
    plan: Plan

@router.post("/chat", response_model=ChatOut)
async def chat(payload: ChatIn) -> ChatOut:
    bl = BookloreClient()
    books = await bl.list_books(limit=payload.limit, offset=0)

    ids = []
    for b in books.get("items", books if isinstance(books, list) else []):
        if "id" in b:
            ids.append(str(b["id"]))

    plan = naive_plan_from_user_request(payload.text, ids)
    return ChatOut(plan=plan)
